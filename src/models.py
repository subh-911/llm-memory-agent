from datetime import datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class MemoryType(str, Enum):
    """Types of memory for categorization"""
    EPISODIC = "episodic"  # Specific events/conversations
    SEMANTIC = "semantic"  # Facts and knowledge
    PREFERENCE = "preference"  # User preferences


class MemoryItem(BaseModel):
    """Structured memory item with metadata"""
    key: str = Field(..., description="Unique identifier for the memory")
    value: Any = Field(..., description="The actual memory content")
    memory_type: MemoryType = Field(default=MemoryType.SEMANTIC)
    timestamp: datetime = Field(default_factory=datetime.now)
    access_count: int = Field(default=0, description="Number of times accessed")
    last_accessed: Optional[datetime] = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Memory importance score")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def access(self):
        """Update access tracking"""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def is_expired(self, decay_hours: int) -> bool:
        """Check if memory should decay based on age"""
        age = (datetime.now() - self.timestamp).total_seconds() / 3600
        # Important memories decay slower
        adjusted_decay = decay_hours * (1 + self.importance)
        return age > adjusted_decay
    
    def calculate_relevance(self) -> float:
        """Calculate memory relevance score based on recency and importance"""
        age_hours = (datetime.now() - self.timestamp).total_seconds() / 3600
        recency_score = max(0, 1 - (age_hours / 168))  # Decay over 1 week
        access_score = min(1, self.access_count / 10)  # Normalize access count
        return (recency_score * 0.4) + (self.importance * 0.4) + (access_score * 0.2)


class ConversationMessage(BaseModel):
    """Conversation history message"""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    tokens_used: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationHistory(BaseModel):
    """Conversation history with size management"""
    messages: List[ConversationMessage] = Field(default_factory=list)
    max_messages: int = Field(default=10)
    
    def add_message(self, role: str, content: str, tokens: Optional[int] = None):
        """Add message and maintain size limit"""
        message = ConversationMessage(
            role=role,
            content=content,
            tokens_used=tokens
        )
        self.messages.append(message)
        
        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Convert to LLM-compatible format"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]
    
    def clear(self):
        """Clear all messages"""
        self.messages.clear()


class MemorySnapshot(BaseModel):
    """Complete memory state for persistence"""
    conversation_history: ConversationHistory
    semantic_memory: Dict[str, MemoryItem] = Field(default_factory=dict)
    episodic_memory: List[MemoryItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def update_timestamp(self):
        """Update last modified timestamp"""
        self.last_updated = datetime.now()
