import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta

from src.agent import SimpleMemoryAgent
from src.models import MemoryType, MemoryItem
from src.memory_store import InMemoryStore


# Mock LLM Client for testing
class MockLLMClient:
    """Mock LLM client that returns predefined responses"""
    
    def __init__(self):
        self.responses = {}
        self.call_count = 0
    
    def set_response(self, pattern: str, response: str):
        """Set mock response for a pattern"""
        self.responses[pattern] = response
    
    async def chat(self, messages, **kwargs):
        """Return mock response"""
        self.call_count += 1
        
        # Get user message
        user_msg = messages[-1]["content"].lower()
        
        # Find matching response
        for pattern, response in self.responses.items():
            if pattern.lower() in user_msg:
                return {
                    "content": response,
                    "usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "total_tokens": 150
                    },
                    "model": "mock-model",
                    "finish_reason": "stop"
                }
        
        # Default response
        return {
            "content": "I understand.",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120
            },
            "model": "mock-model",
            "finish_reason": "stop"
        }
    
    def count_tokens(self, text: str) -> int:
        return len(text) // 4


@pytest.fixture
def mock_llm():
    """Fixture for mock LLM client"""
    return MockLLMClient()


@pytest.fixture
def memory_store():
    """Fixture for in-memory store"""
    return InMemoryStore()


@pytest_asyncio.fixture
async def agent(mock_llm, memory_store):
    """Fixture for agent instance"""
    agent = SimpleMemoryAgent(
        llm_client=mock_llm,
        memory_store=memory_store,
        session_id="test_session"
    )
    await agent.initialize()
    return agent


# Test Memory Storage and Retrieval
@pytest.mark.asyncio
async def test_remember_and_recall(agent):
    """Test basic memory storage and retrieval"""
    # Store a memory
    agent.remember("user_name", "John", importance=0.9)
    
    # Recall the memory
    name = agent.recall("user_name")
    assert name == "John"


@pytest.mark.asyncio
async def test_recall_nonexistent(agent):
    """Test recalling non-existent memory"""
    value = agent.recall("nonexistent_key")
    assert value is None


@pytest.mark.asyncio
async def test_memory_types(agent):
    """Test different memory types"""
    # Semantic memory
    agent.remember("fact", "Paris is the capital", memory_type=MemoryType.SEMANTIC)
    
    # Preference memory
    agent.remember("color", "blue", memory_type=MemoryType.PREFERENCE)
    
    # Episodic memory
    agent.remember("event_1", "Had coffee", memory_type=MemoryType.EPISODIC)
    
    assert agent.recall("fact") == "Paris is the capital"
    assert agent.recall("color") == "blue"
    assert len(agent.episodic_memory) == 1


# Test Memory Decay
@pytest.mark.asyncio
async def test_memory_decay(agent):
    """Test that old memories expire"""
    # Create old memory (simulate by modifying timestamp)
    old_memory = MemoryItem(
        key="old_fact",
        value="Old information",
        importance=0.3
    )
    # Set timestamp to 30 days ago
    old_memory.timestamp = datetime.now() - timedelta(days=30)
    
    agent.semantic_memory["old_fact"] = old_memory
    
    # Create recent memory
    agent.remember("new_fact", "New information", importance=0.3)
    
    # Clean expired memories (default decay is 24 hours)
    agent.clean_expired_memories()
    
    # Old memory should be gone
    assert "old_fact" not in agent.semantic_memory
    # New memory should remain
    assert "new_fact" in agent.semantic_memory


@pytest.mark.asyncio
async def test_important_memory_decay_slower(agent):
    """Test that important memories decay slower"""
    agent.decay_hours = 24  # 24 hour decay
    
    # Create important memory
    important_memory = MemoryItem(
        key="important",
        value="Important info",
        importance=0.9
    )
    # 30 hours old (past normal decay but within importance-adjusted decay)
    important_memory.timestamp = datetime.now() - timedelta(hours=30)
    
    agent.semantic_memory["important"] = important_memory
    
    # Clean - important memory should survive
    agent.clean_expired_memories()
    
    assert "important" in agent.semantic_memory


# Test Conversation History
@pytest.mark.asyncio
async def test_conversation_history(agent, mock_llm):
    """Test conversation history management"""
    mock_llm.set_response("hello", "Hi there!")
    
    # First message
    await agent.process("Hello")
    assert len(agent.conversation_history.messages) == 2  # user + assistant
    
    # Second message
    await agent.process("How are you?")
    assert len(agent.conversation_history.messages) == 4


@pytest.mark.asyncio
async def test_conversation_history_limit(agent, mock_llm):
    """Test that conversation history respects max size"""
    agent.max_history = 4  # 4 messages = 2 exchanges
    agent.conversation_history.max_messages = 4
    
    mock_llm.set_response("", "Response")
    
    # Send 5 messages
    for i in range(5):
        await agent.process(f"Message {i}")
    
    # Should only keep last 4 messages (2 exchanges)
    assert len(agent.conversation_history.messages) == 4


# Test Memory Extraction
@pytest.mark.asyncio
async def test_extract_name(agent, mock_llm):
    """Test automatic extraction of user name"""
    mock_llm.set_response("name", "Nice to meet you, John!")
    
    await agent.process("My name is John")
    
    # Should have extracted and stored the name
    assert agent.recall("user_name") == "John"


@pytest.mark.asyncio
async def test_extract_preferences(agent, mock_llm):
    """Test automatic extraction of preferences"""
    mock_llm.set_response("like", "That's great!")
    
    await agent.process("I like pizza and pasta")
    
    # Should have extracted preferences
    preferences = [m.value for m in agent.semantic_memory.values() 
                   if m.memory_type == MemoryType.PREFERENCE]
    
    assert any("pizza" in str(p).lower() for p in preferences)


# Test Memory Search
@pytest.mark.asyncio
async def test_search_memories(agent):
    """Test memory search functionality"""
    # Add some memories
    agent.remember("hobby_1", "Playing guitar", importance=0.8)
    agent.remember("hobby_2", "Playing chess", importance=0.6)
    agent.remember("food", "Pizza", importance=0.5)
    
    # Search for "playing"
    results = agent.search_memories("playing")
    
    assert len(results) == 2
    assert all("playing" in str(m.value).lower() for m in results)


@pytest.mark.asyncio
async def test_search_relevance_ordering(agent):
    """Test that search results are ordered by relevance"""
    # Add memories with different importance
    agent.remember("low", "Low importance", importance=0.2)
    agent.remember("high", "High importance", importance=0.9)
    agent.remember("med", "Medium importance", importance=0.5)
    
    # Search should return by relevance
    results = agent.search_memories("importance")
    
    # High importance should be first
    assert results[0].key == "high"


# Test Memory Access Tracking
@pytest.mark.asyncio
async def test_memory_access_tracking(agent):
    """Test that memory access is tracked"""
    agent.remember("test_key", "test_value")
    
    # Access the memory multiple times
    agent.recall("test_key")
    agent.recall("test_key")
    agent.recall("test_key")
    
    memory = agent.semantic_memory["test_key"]
    assert memory.access_count == 3
    assert memory.last_accessed is not None


# Test Memory Persistence
@pytest.mark.asyncio
async def test_memory_persistence(mock_llm, memory_store):
    """Test saving and loading memory"""
    # Create agent and add memory
    agent1 = SimpleMemoryAgent(mock_llm, memory_store, "persist_test")
    await agent1.initialize()
    
    agent1.remember("saved_key", "saved_value")
    await agent1.process("Hello")
    await agent1.save()
    
    # Create new agent instance with same session
    agent2 = SimpleMemoryAgent(mock_llm, memory_store, "persist_test")
    await agent2.initialize()
    
    # Should have loaded saved memory
    assert agent2.recall("saved_key") == "saved_value"
    assert len(agent2.conversation_history.messages) > 0


# Test Context Building
@pytest.mark.asyncio
async def test_context_building(agent):
    """Test that context is built from memories"""
    agent.remember("name", "John", importance=0.9)
    agent.remember("city", "New York", importance=0.8)
    
    context = agent._build_context()
    
    assert "name" in context.lower() or "john" in context.lower()
    assert "city" in context.lower() or "new york" in context.lower()


# Test Full Interaction Flow
@pytest.mark.asyncio
async def test_full_interaction_flow(agent, mock_llm):
    """Test complete interaction: introduce name, then ask for recall"""
    # Setup mock responses
    mock_llm.set_response("name is john", "Nice to meet you, John!")
    mock_llm.set_response("what's my name", "Your name is John!")
    
    # First interaction - introduce name
    result1 = await agent.process("Hi, my name is John")
    assert "john" in result1["response"].lower()
    
    # Verify name was stored
    assert agent.recall("user_name") == "John"
    
    # Second interaction - ask for name
    result2 = await agent.process("What's my name?")
    
    # Context should have been used
    assert result2["context_used"] == True


# Test Memory Summary
@pytest.mark.asyncio
async def test_memory_summary(agent):
    """Test memory summary generation"""
    agent.remember("test1", "value1")
    agent.remember("test2", "value2")
    
    summary = agent.get_memory_summary()
    
    assert summary["session_id"] == "test_session"
    assert summary["semantic_memories"] == 2
    assert "test1" in summary["semantic_memory_items"]
    assert "test2" in summary["semantic_memory_items"]


# Test Clear Memory
@pytest.mark.asyncio
async def test_clear_memory(agent):
    """Test clearing all memories"""
    # Add some data
    agent.remember("test", "value")
    await agent.process("Hello")
    
    # Clear
    await agent.clear_memory()
    
    # Verify everything is cleared
    assert len(agent.semantic_memory) == 0
    assert len(agent.conversation_history.messages) == 0
    assert len(agent.episodic_memory) == 0


# Performance Tests
@pytest.mark.asyncio
async def test_large_memory_performance(agent):
    """Test agent performance with many memories"""
    # Add 100 memories
    for i in range(100):
        agent.remember(f"key_{i}", f"value_{i}", importance=0.5)
    
    # Search should still be fast
    import time
    start = time.time()
    results = agent.search_memories("value", limit=10)
    duration = time.time() - start
    
    assert duration < 1.0  # Should complete in under 1 second
    assert len(results) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
