from typing import Dict, List, Optional, Any
import json
import re
from datetime import datetime

from .models import (
    MemoryItem, MemoryType, ConversationHistory,
    ConversationMessage, MemorySnapshot
)
from .llm_client import LLMClient
from .memory_store import MemoryStore
from .config import settings


class SimpleMemoryAgent:
    """
    Production-ready LLM agent with structured memory management.
    
    Features:
    - Episodic memory (conversation events)
    - Semantic memory (facts and knowledge)
    - Memory decay based on time and importance
    - Automatic memory extraction from conversations
    - Persistent storage support
    """
    
    def __init__(
        self, 
        llm_client: LLMClient,
        memory_store: MemoryStore,
        session_id: str = "default"
    ):
        self.llm = llm_client
        self.memory_store = memory_store
        self.session_id = session_id
        
        # Initialize memory structures
        self.conversation_history = ConversationHistory(
            max_messages=settings.max_conversation_history
        )
        self.semantic_memory: Dict[str, MemoryItem] = {}
        self.episodic_memory: List[MemoryItem] = []
        
        # Configuration
        self.max_history = settings.max_conversation_history
        self.decay_hours = settings.memory_decay_hours
        self.enable_semantic = settings.enable_semantic_memory
        self.enable_episodic = settings.enable_episodic_memory
    
    async def initialize(self):
        """Load existing memory from storage"""
        snapshot = await self.memory_store.load(self.session_id)
        if snapshot:
            self.conversation_history = snapshot.conversation_history
            self.semantic_memory = snapshot.semantic_memory
            self.episodic_memory = snapshot.episodic_memory
    
    async def save(self):
        """Persist current memory state"""
        snapshot = MemorySnapshot(
            conversation_history=self.conversation_history,
            semantic_memory=self.semantic_memory,
            episodic_memory=self.episodic_memory
        )
        await self.memory_store.save(self.session_id, snapshot)
    
    def remember(
        self, 
        key: str, 
        value: Any, 
        memory_type: MemoryType = MemoryType.SEMANTIC,
        importance: float = 0.5,
        metadata: Optional[Dict] = None
    ):
        """
        Store information in memory.
        
        Args:
            key: Unique identifier for the memory
            value: The memory content
            memory_type: Type of memory (semantic, episodic, preference)
            importance: Importance score (0-1), affects decay rate
            metadata: Additional metadata
        """
        memory_item = MemoryItem(
            key=key,
            value=value,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata or {}
        )
        
        if memory_type == MemoryType.EPISODIC:
            self.episodic_memory.append(memory_item)
            # Keep only recent episodic memories
            if len(self.episodic_memory) > 50:
                self.episodic_memory = self.episodic_memory[-50:]
        else:
            # Semantic and preference memories stored by key
            self.semantic_memory[key] = memory_item
    
    def recall(self, key: str) -> Optional[Any]:
        """
        Retrieve from semantic memory by key.
        
        Args:
            key: Memory key to retrieve
            
        Returns:
            Memory value if found, None otherwise
        """
        if key in self.semantic_memory:
            memory = self.semantic_memory[key]
            memory.access()
            return memory.value
        return None
    
    def search_memories(
        self, 
        query: str, 
        memory_type: Optional[MemoryType] = None,
        limit: int = 5
    ) -> List[MemoryItem]:
        """
        Search memories by keyword matching.
        
        Args:
            query: Search query
            memory_type: Filter by memory type
            limit: Maximum results to return
            
        Returns:
            List of matching memories sorted by relevance
        """
        query_lower = query.lower()
        matches = []
        
        # Search semantic memory
        for memory in self.semantic_memory.values():
            if memory_type and memory.memory_type != memory_type:
                continue
            
            # Simple keyword matching
            if query_lower in str(memory.value).lower() or query_lower in memory.key.lower():
                matches.append(memory)
        
        # Search episodic memory
        for memory in self.episodic_memory:
            if memory_type and memory.memory_type != memory_type:
                continue
            
            if query_lower in str(memory.value).lower() or query_lower in memory.key.lower():
                matches.append(memory)
        
        # Sort by relevance score
        matches.sort(key=lambda m: m.calculate_relevance(), reverse=True)
        
        # Update access tracking
        for memory in matches[:limit]:
            memory.access()
        
        return matches[:limit]
    
    def clean_expired_memories(self):
        """Remove expired memories based on decay settings"""
        # Clean semantic memory
        expired_keys = [
            key for key, memory in self.semantic_memory.items()
            if memory.is_expired(self.decay_hours)
        ]
        for key in expired_keys:
            del self.semantic_memory[key]
        
        # Clean episodic memory
        self.episodic_memory = [
            memory for memory in self.episodic_memory
            if not memory.is_expired(self.decay_hours)
        ]
    
    def _build_context(self) -> str:
        """Build context string from relevant memories"""
        context_parts = []
        
        # Add important semantic memories
        if self.semantic_memory:
            important_memories = sorted(
                self.semantic_memory.values(),
                key=lambda m: m.calculate_relevance(),
                reverse=True
            )[:5]  # Top 5 relevant memories
            
            if important_memories:
                context_parts.append("Relevant information I remember:")
                for memory in important_memories:
                    context_parts.append(f"- {memory.key}: {memory.value}")
        
        # Add recent episodic memories
        if self.episodic_memory:
            recent_episodes = self.episodic_memory[-3:]  # Last 3 episodes
            if recent_episodes:
                context_parts.append("\nRecent interactions:")
                for episode in recent_episodes:
                    context_parts.append(f"- {episode.value}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _prepare_messages(self, user_input: str, context: str) -> List[Dict[str, str]]:
        """Prepare messages for LLM including history and context"""
        messages = []
        
        # System message with memory context
        system_message = """You are a helpful AI assistant with memory capabilities.
You can remember information from previous conversations and use it to provide better responses.

When users tell you personal information (name, preferences, facts about themselves), 
acknowledge it and remember it for future conversations."""
        
        if context:
            system_message += f"\n\n{context}"
        
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history
        messages.extend(self.conversation_history.get_messages_for_llm())
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _extract_memory(self, user_input: str, response: str):
        """
        Extract and store memorable information from conversation.
        Uses pattern matching to identify important information.
        """
        text = f"{user_input} {response}".lower()
        
        # Pattern: "my name is X" or "I'm X" or "I am X"
        name_patterns = [
            r"my name is ([a-z]+)",
            r"i'm ([a-z]+)",
            r"i am ([a-z]+)",
            r"call me ([a-z]+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                name = match.group(1).capitalize()
                self.remember(
                    "user_name", 
                    name, 
                    memory_type=MemoryType.PREFERENCE,
                    importance=0.9
                )
                break
        
        # Pattern: "I like/love/prefer X"
        preference_patterns = [
            r"i (?:like|love|prefer|enjoy) ([^.!?]+)",
            r"my favorite .+ is ([^.!?]+)"
        ]
        
        for pattern in preference_patterns:
            matches = re.findall(pattern, user_input.lower())
            for match in matches:
                preference = match.strip()
                if preference and len(preference) < 100:
                    key = f"preference_{len(self.semantic_memory)}"
                    self.remember(
                        key,
                        preference,
                        memory_type=MemoryType.PREFERENCE,
                        importance=0.7
                    )
        
        # Store conversation as episodic memory
        if self.enable_episodic:
            episode_key = f"conversation_{datetime.now().isoformat()}"
            self.remember(
                episode_key,
                f"User said: {user_input[:100]}... Response: {response[:100]}...",
                memory_type=MemoryType.EPISODIC,
                importance=0.3
            )
    
    async def process(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and generate response.
        
        Args:
            user_input: User's message
            
        Returns:
            Dict containing response and metadata
        """
        # Clean expired memories
        self.clean_expired_memories()
        
        # Build context from memories
        context = self._build_context()
        
        # Prepare messages
        messages = self._prepare_messages(user_input, context)
        
        # Get LLM response
        try:
            llm_response = await self.llm.chat(messages)
            response_text = llm_response["content"]
            usage = llm_response["usage"]
            
            # Update conversation history
            self.conversation_history.add_message(
                "user", 
                user_input, 
                tokens=usage.get("prompt_tokens")
            )
            self.conversation_history.add_message(
                "assistant", 
                response_text,
                tokens=usage.get("completion_tokens")
            )
            
            # Extract and store memorable information
            self._extract_memory(user_input, response_text)
            
            # Save to persistent storage
            await self.save()
            
            return {
                "response": response_text,
                "usage": usage,
                "context_used": bool(context),
                "memories_count": {
                    "semantic": len(self.semantic_memory),
                    "episodic": len(self.episodic_memory)
                }
            }
            
        except Exception as e:
            raise Exception(f"Error processing request: {str(e)}")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of current memory state"""
        return {
            "session_id": self.session_id,
            "conversation_length": len(self.conversation_history.messages),
            "semantic_memories": len(self.semantic_memory),
            "episodic_memories": len(self.episodic_memory),
            "semantic_memory_items": {
                key: {
                    "value": str(memory.value)[:100],
                    "type": memory.memory_type,
                    "importance": memory.importance,
                    "access_count": memory.access_count,
                    "age_hours": (datetime.now() - memory.timestamp).total_seconds() / 3600
                }
                for key, memory in self.semantic_memory.items()
            }
        }
    
    async def clear_memory(self):
        """Clear all memories and conversation history"""
        self.conversation_history.clear()
        self.semantic_memory.clear()
        self.episodic_memory.clear()
        await self.save()
