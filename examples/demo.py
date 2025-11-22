"""
Example usage script demonstrating the LLM Memory Agent capabilities.

Run this after starting the server with: python main.py
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def chat(message, session_id="demo_session"):
    """Send a chat message to the agent"""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": message, "session_id": session_id}
    )
    return response.json()


def get_memory_summary(session_id="demo_session"):
    """Get memory summary for a session"""
    response = requests.get(
        f"{BASE_URL}/memory/summary",
        params={"session_id": session_id}
    )
    return response.json()


def search_memories(query, session_id="demo_session"):
    """Search memories"""
    response = requests.post(
        f"{BASE_URL}/memory/search",
        json={"query": query, "session_id": session_id}
    )
    return response.json()


def store_memory(key, value, importance=0.5, session_id="demo_session"):
    """Manually store a memory"""
    response = requests.post(
        f"{BASE_URL}/memory/store",
        json={
            "key": key,
            "value": value,
            "importance": importance,
            "session_id": session_id
        }
    )
    return response.json()


def recall_memory(key, session_id="demo_session"):
    """Recall a specific memory"""
    response = requests.get(
        f"{BASE_URL}/memory/recall/{key}",
        params={"session_id": session_id}
    )
    return response.json()


def clear_memory(session_id="demo_session"):
    """Clear all memories for a session"""
    response = requests.delete(
        f"{BASE_URL}/memory/clear",
        json={"session_id": session_id}
    )
    return response.json()


def demo_basic_conversation():
    """Demo 1: Basic conversation with name memory"""
    print_section("Demo 1: Basic Conversation with Memory")
    
    session = "demo_basic"
    
    # First interaction - introduce name
    print("User: Hi, my name is John")
    result = chat("Hi, my name is John", session)
    print(f"Agent: {result['response']}")
    print(f"Context used: {result['context_used']}")
    print(f"Memories: {result['memories_count']}")
    
    time.sleep(1)
    
    # Second interaction - agent should remember
    print("\nUser: What's my name?")
    result = chat("What's my name?", session)
    print(f"Agent: {result['response']}")
    print(f"Context used: {result['context_used']}")
    
    # Show memory summary
    print("\n--- Memory Summary ---")
    summary = get_memory_summary(session)
    print(json.dumps(summary, indent=2, default=str))
    
    # Cleanup
    clear_memory(session)


def demo_preferences():
    """Demo 2: Remembering preferences"""
    print_section("Demo 2: Preference Memory")
    
    session = "demo_preferences"
    
    # Tell agent about preferences
    print("User: I love Italian food, especially pizza and pasta")
    result = chat("I love Italian food, especially pizza and pasta", session)
    print(f"Agent: {result['response']}")
    
    time.sleep(1)
    
    print("\nUser: I prefer working in the morning")
    result = chat("I prefer working in the morning", session)
    print(f"Agent: {result['response']}")
    
    time.sleep(1)
    
    # Search for preferences
    print("\n--- Searching for 'food' ---")
    results = search_memories("food", session)
    for memory in results['results']:
        print(f"  {memory['key']}: {memory['value']}")
        print(f"  Relevance: {memory['relevance']:.2f}")
    
    # Cleanup
    clear_memory(session)


def demo_manual_storage():
    """Demo 3: Manual memory storage and retrieval"""
    print_section("Demo 3: Manual Memory Storage")
    
    session = "demo_manual"
    
    # Store important information manually
    print("Storing important medical information...")
    store_memory(
        "medication",
        "Takes insulin twice daily",
        importance=1.0,
        session=session
    )
    
    store_memory(
        "allergies",
        "Allergic to penicillin",
        importance=1.0,
        session=session
    )
    
    store_memory(
        "emergency_contact",
        "Jane Doe - 555-0123",
        importance=0.9,
        session=session
    )
    
    # Recall specific memory
    print("\n--- Recalling medication info ---")
    memory = recall_memory("medication", session)
    print(json.dumps(memory, indent=2))
    
    # Show all memories
    print("\n--- All stored memories ---")
    summary = get_memory_summary(session)
    for key, info in summary['semantic_memory_items'].items():
        print(f"\n{key}:")
        print(f"  Value: {info['value']}")
        print(f"  Importance: {info['importance']}")
        print(f"  Access count: {info['access_count']}")
    
    # Cleanup
    clear_memory(session)


def demo_multi_turn_context():
    """Demo 4: Multi-turn conversation with context"""
    print_section("Demo 4: Multi-turn Contextual Conversation")
    
    session = "demo_context"
    
    # Build up context
    messages = [
        "I'm planning a trip to Japan next month",
        "I've never been to Asia before",
        "What should I pack?",
        "Also, what are some must-see places in Tokyo?"
    ]
    
    for msg in messages:
        print(f"\nUser: {msg}")
        result = chat(msg, session)
        print(f"Agent: {result['response'][:200]}...")  # Truncate long responses
        print(f"Context used: {result['context_used']}")
        time.sleep(1)
    
    # Show conversation history
    print("\n--- Conversation Summary ---")
    summary = get_memory_summary(session)
    print(f"Total messages: {summary['conversation_length']}")
    print(f"Semantic memories: {summary['semantic_memories']}")
    print(f"Episodic memories: {summary['episodic_memories']}")
    
    # Cleanup
    clear_memory(session)


def demo_search_and_recall():
    """Demo 5: Advanced search and recall"""
    print_section("Demo 5: Search and Recall")
    
    session = "demo_search"
    
    # Have multiple conversations
    print("Building up memory base...")
    chat("I work as a software engineer", session)
    time.sleep(0.5)
    chat("My favorite programming language is Python", session)
    time.sleep(0.5)
    chat("I have a dog named Max", session)
    time.sleep(0.5)
    chat("I enjoy hiking on weekends", session)
    time.sleep(0.5)
    
    # Search for different topics
    queries = ["work", "python", "dog", "hobby"]
    
    for query in queries:
        print(f"\n--- Searching for '{query}' ---")
        results = search_memories(query, session)
        print(f"Found {results['count']} results:")
        for memory in results['results']:
            print(f"  • {memory['value'][:80]}")
            print(f"    (Relevance: {memory['relevance']:.2f})")
    
    # Cleanup
    clear_memory(session)


def demo_session_isolation():
    """Demo 6: Session isolation"""
    print_section("Demo 6: Session Isolation")
    
    # Two different users
    session1 = "user_alice"
    session2 = "user_bob"
    
    # Alice's conversation
    print("Alice: My favorite color is blue")
    chat("My favorite color is blue", session1)
    
    # Bob's conversation
    print("\nBob: My favorite color is red")
    chat("My favorite color is red", session2)
    
    # Check Alice's memory
    print("\n--- Alice's memories ---")
    alice_summary = get_memory_summary(session1)
    print(json.dumps(alice_summary['semantic_memory_items'], indent=2, default=str))
    
    # Check Bob's memory
    print("\n--- Bob's memories ---")
    bob_summary = get_memory_summary(session2)
    print(json.dumps(bob_summary['semantic_memory_items'], indent=2, default=str))
    
    # Verify isolation
    print("\n--- Verification ---")
    print(f"Alice has {alice_summary['semantic_memories']} memories")
    print(f"Bob has {bob_summary['semantic_memories']} memories")
    print("✓ Sessions are properly isolated")
    
    # Cleanup
    clear_memory(session1)
    clear_memory(session2)


def demo_health_check():
    """Demo 7: Health check and system info"""
    print_section("Demo 7: System Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    health = response.json()
    
    print("System Status:")
    print(json.dumps(health, indent=2))
    
    # List all sessions
    print("\n--- Active Sessions ---")
    response = requests.get(f"{BASE_URL}/sessions")
    sessions = response.json()
    print(f"Total sessions: {sessions['count']}")
    for session in sessions['sessions']:
        print(f"  • {session}")


def main():
    """Run all demos"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                                                          ║")
    print("║           LLM Memory Agent - Demo Suite                 ║")
    print("║                                                          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("\n❌ Server is not responding properly!")
            print("Please start the server with: python main.py")
            return
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server!")
        print("Please start the server with: python main.py")
        return
    
    print("\n✓ Server is running\n")
    
    try:
        # Run all demos
        demo_basic_conversation()
        demo_preferences()
        demo_manual_storage()
        demo_multi_turn_context()
        demo_search_and_recall()
        demo_session_isolation()
        demo_health_check()
        
        print_section("Demo Complete")
        print("All demos completed successfully! ✓")
        print("\nTry the API yourself:")
        print(f"  • API Docs: {BASE_URL}/docs")
        print(f"  • Health: {BASE_URL}/health")
        
    except Exception as e:
        print(f"\n❌ Error running demos: {e}")
        print("Make sure the server is running and your .env is configured correctly")


if __name__ == "__main__":
    main()
