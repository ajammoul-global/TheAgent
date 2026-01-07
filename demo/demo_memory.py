"""
Demo: Conversation Store - Memory System Foundation
Shows how to save and retrieve conversations
"""
from memory import conversation_store
from memory.conversation_store import ConversationStore
from datetime import datetime, timedelta
import uuid


def demo_basic_operations():
    """Demonstrate basic save and retrieve"""
    print("=" * 80)
    print("DEMO 1: Basic Operations")
    print("=" * 80)
    
    store = ConversationStore()
    
    # Save some conversations
    print("\n1. Saving conversations...")
    
    conv_id1 = store.save(
        user_message="Schedule dentist appointment tomorrow at 10am",
        agent_response="✅ Scheduled dentist appointment for Dec 6 at 10am",
        agent_type="task_scheduler",
        metadata={"task_type": "scheduling", "scheduled_date": "2025-12-06"}
    )
    print(f"   ✓ Saved conversation {conv_id1}")
    
    conv_id2 = store.save(
        user_message="What are good Python tutorials?",
        agent_response="Here are some excellent Python tutorials...",
        agent_type="react",
        metadata={"topic": "python", "used_search": True}
    )
    print(f"   ✓ Saved conversation {conv_id2}")
    
    conv_id3 = store.save(
        user_message="Should I learn React or Vue?",
        agent_response="Based on evaluation, React is recommended...",
        agent_type="tot",
        metadata={"topic": "web_frameworks", "decision": "react"}
    )
    print(f"   ✓ Saved conversation {conv_id3}")
    
    # Retrieve by ID
    print("\n2. Retrieving by ID...")
    conv = store.get_by_id(conv_id1)
    print(f"   User: {conv['user_message'][:50]}...")
    print(f"   Agent: {conv['agent_response'][:50]}...")
    print(f"   Metadata: {conv['metadata']}")
    
    # Get recent
    print("\n3. Getting recent conversations...")
    recent = store.get_recent(limit=5)
    print(f"   Found {len(recent)} recent conversations:")
    for i, conv in enumerate(recent, 1):
        print(f"   {i}. [{conv['agent_type']}] {conv['user_message'][:40]}...")
    
    # Stats
    print("\n4. Statistics...")
    stats = store.get_stats()
    print(f"   Total conversations: {stats['total_conversations']}")
    print(f"   By agent type: {stats['by_agent_type']}")


def demo_search():
    """Demonstrate full-text search"""
    print("\n" + "=" * 80)
    print("DEMO 2: Full-Text Search")
    print("=" * 80)
    
    store = ConversationStore()
    
    # Add more conversations for better search demo
    conversations = [
        ("How do I deploy a Python app?", "Here's how to deploy Python applications...", "react"),
        ("Explain Python decorators", "Python decorators are...", "cot"),
        ("Best Python web frameworks", "Django and Flask are popular Python frameworks...", "tot"),
        ("Schedule Python study session Monday", "✅ Scheduled Python study for Monday...", "task_scheduler"),
    ]
    
    print("\n1. Adding sample conversations...")
    for user_msg, agent_msg, agent_type in conversations:
        store.save(user_msg, agent_msg, agent_type=agent_type)
    print(f"   ✓ Added {len(conversations)} conversations")
    
    # Search for "Python"
    print("\n2. Searching for 'Python'...")
    results = store.search("Python", limit=5)
    print(f"   Found {len(results)} results:")
    for i, conv in enumerate(results, 1):
        print(f"   {i}. {conv['user_message'][:60]}...")
    
    # Search for "schedule"
    print("\n3. Searching for 'schedule'...")
    results = store.search("schedule", limit=5)
    print(f"   Found {len(results)} results:")
    for i, conv in enumerate(results, 1):
        print(f"   {i}. {conv['user_message'][:60]}...")
    
    # Search with filter
    print("\n4. Searching 'Python' in 'react' agent only...")
    results = store.search("Python", agent_type="react", limit=5)
    print(f"   Found {len(results)} results:")
    for i, conv in enumerate(results, 1):
        print(f"   {i}. [{conv['agent_type']}] {conv['user_message'][:50]}...")


def demo_sessions():
    """Demonstrate session-based retrieval"""
    print("\n" + "=" * 80)
    print("DEMO 3: Session Management")
    print("=" * 80)
    
    store = ConversationStore()
    
    # Create a session
    session_id = str(uuid.uuid4())[:8]
    print(f"\n1. Creating session: {session_id}")
    
    # Simulate a conversation in this session
    conversation_flow = [
        "What is Python?",
        "Python is a high-level programming language...",
        "How do I install Python?",
        "You can download Python from python.org...",
        "Show me a Python example",
        "Here's a simple Python example: print('Hello')",
    ]
    
    print("\n2. Simulating conversation...")
    for i in range(0, len(conversation_flow), 2):
        user_msg = conversation_flow[i]
        agent_msg = conversation_flow[i+1]
        
        store.save(
            user_message=user_msg,
            agent_response=agent_msg,
            session_id=session_id,
            agent_type="cot"
        )
        print(f"   Turn {i//2 + 1}:")
        print(f"   User: {user_msg}")
        print(f"   Agent: {agent_msg[:50]}...")
    
    # Retrieve full session
    print(f"\n3. Retrieving session {session_id}...")
    history = store.get_session_history(session_id)
    print(f"   Found {len(history)} messages in session:")
    for i, conv in enumerate(history, 1):
        print(f"   {i}. User: {conv['user_message'][:40]}...")


def demo_date_filtering():
    """Demonstrate date-based filtering"""
    print("\n" + "=" * 80)
    print("DEMO 4: Date-Based Filtering")
    print("=" * 80)
    
    store = ConversationStore()
    
    # Get conversations from last 24 hours
    print("\n1. Conversations from last 24 hours...")
    start = datetime.now() - timedelta(hours=24)
    recent = store.get_by_date_range(start)
    print(f"   Found {len(recent)} conversations")
    
    # Get all conversations
    print("\n2. All stored conversations...")
    start = datetime.now() - timedelta(days=365)  # Last year
    all_convs = store.get_by_date_range(start)
    print(f"   Total: {len(all_convs)} conversations")
    
    # Show stats
    print("\n3. Overall statistics...")
    stats = store.get_stats()
    print(f"   Total: {stats['total_conversations']}")
    print(f"   Earliest: {stats['earliest_conversation']}")
    print(f"   Latest: {stats['latest_conversation']}")
    print(f"   By agent type:")
    for agent, count in stats['by_agent_type'].items():
        print(f"     - {agent}: {count}")


def demo_practical_use_case():
    """Show practical use case - remembering scheduled tasks"""
    print("\n" + "=" * 80)
    print("DEMO 5: Practical Use Case - Task Memory")
    print("=" * 80)
    
    store = ConversationStore()
    
    print("\n1. User schedules appointments...")
    
    # Schedule dentist
    store.save(
        user_message="Schedule dentist tomorrow at 10am",
        agent_response="✅ Scheduled dentist for Dec 6 at 10am",
        agent_type="task_scheduler",
        metadata={
            "task_type": "appointment",
            "event": "dentist",
            "date": "2025-12-06",
            "time": "10:00"
        }
    )
    print("   ✓ Dentist scheduled")
    
    # Schedule gym
    store.save(
        user_message="Gym session Friday 6am",
        agent_response="✅ Scheduled gym for Friday 6am",
        agent_type="task_scheduler",
        metadata={
            "task_type": "workout",
            "event": "gym",
            "date": "2025-12-08",
            "time": "06:00"
        }
    )
    print("   ✓ Gym scheduled")
    
    # Schedule team meeting
    store.save(
        user_message="Team meeting Monday 2pm",
        agent_response="✅ Scheduled team meeting Monday 2pm",
        agent_type="task_scheduler",
        metadata={
            "task_type": "meeting",
            "event": "team_meeting",
            "date": "2025-12-09",
            "time": "14:00"
        }
    )
    print("   ✓ Team meeting scheduled")
    
    # User asks about dentist
    print("\n2. User asks: 'What time is my dentist appointment?'")
    results = store.search("dentist", agent_type="task_scheduler")
    if results:
        conv = results[0]
        print(f"   Found: {conv['agent_response']}")
        print(f"   Metadata: {conv['metadata']}")
    
    # User asks about all appointments
    print("\n3. User asks: 'What appointments do I have?'")
    results = store.get_recent(agent_type="task_scheduler", limit=10)
    print(f"   Found {len(results)} scheduled items:")
    for i, conv in enumerate(results, 1):
        meta = conv['metadata']
        if meta and 'event' in meta:
            print(f"   {i}. {meta['event']}: {meta.get('date')} at {meta.get('time')}")


if __name__ == "__main__":
    print("\n🧠 CONVERSATION STORE DEMONSTRATION")
    print("Phase 3: Memory System - Foundation")
    print("\n")
    
    # Run all demos
    demo_basic_operations()
    demo_search()
    demo_sessions()
    demo_date_filtering()
    demo_practical_use_case()
    
    print("\n" + "=" * 80)
    print("✅ ALL DEMOS COMPLETE!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("✓ Conversations are persisted in SQLite")
    print("✓ Full-text search works across messages")
    print("✓ Session-based conversation tracking")
    print("✓ Date-based filtering and retrieval")
    print("✓ Metadata for structured information")
    print("\nYour agents can now REMEMBER! 🎉")