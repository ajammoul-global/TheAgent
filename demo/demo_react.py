#!/usr/bin/env python3
"""
Demo: ReAct Agent

Shows multi-step reasoning in action
"""

from models.ollama import OllamaModel
from infra.tool_registry import ToolRegistry
from agents.react_agent import ReActAgent

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def main():
    print_section("ReAct Agent Demo")
    
    # Setup
    print("Setting up...")
    model = OllamaModel()
    registry = ToolRegistry()
    agent = ReActAgent(model, registry, max_steps=5)
    
    print(f"✓ Agent ready with {len(registry)} tools")
    print(f"✓ Max reasoning steps: {agent.max_steps}")
    
    # Test queries
    queries = [
        "What is Python?",  # Simple (should be 1-2 steps)
        "Find Python tutorials and recommend the best one",  # Complex (3-4 steps)
        "Search for AI news and summarize the most interesting story"  # Complex (4-5 steps)
    ]
    
    for i, query in enumerate(queries, 1):
        print_section(f"Query {i}: {query}")
        
        print("Agent is reasoning...")
        response = agent.run(query)
        
        print("\n" + "─"*60)
        print("FINAL ANSWER:")
        print("─"*60)
        print(response)
        print()
        
        input("Press Enter for next query...")
    
    print_section("Demo Complete!")
    print("The ReAct agent can handle both simple and complex queries.")
    print("Notice how it breaks down complex tasks into steps!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()