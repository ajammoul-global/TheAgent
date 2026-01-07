"""
Demo: Tree of Thoughts Agent
Shows how ToT explores multiple solutions and picks the best
"""
from models.ollama import OllamaModel
from infra.tool_registry import ToolRegistry
from agents.tot_agent import TreeOfThoughtsAgent
from infra.logging import logger


def demo_tree_of_thoughts():
    """Demonstrate ToT agent for complex decision-making"""
    
    print("=" * 80)
    print("TREE OF THOUGHTS AGENT DEMO")
    print("Explores multiple solutions and picks the best one")
    print("=" * 80)
    
    # Initialize
    model = OllamaModel()
    registry = ToolRegistry()
    
    # Create ToT agent
    # num_branches=3 means 3 options at each level
    # max_depth=2 means 2 levels deep (3 → 9 → 27 total paths explored)
    agent = TreeOfThoughtsAgent(
        model, 
        registry,
        num_branches=3,
        max_depth=2
    )
    
    # Test queries showing ToT's strength
    test_queries = [
        # Decision making - multiple valid options
        {
            "query": "Should I learn React, Vue, or Angular for my next project?",
            "why_tot": "Needs to explore each framework and evaluate trade-offs"
        },
        
        # Complex planning - many possible approaches
        {
            "query": "I have 10 hours free this week. How should I best use this time to learn Python?",
            "why_tot": "Multiple study strategies possible, needs optimization"
        },
        
        # Problem solving - various solutions
        {
            "query": "My website is slow. What's the best approach to improve performance?",
            "why_tot": "Many optimization strategies, needs to evaluate which is most effective"
        },
        
        # Scheduling optimization (your use case!)
        {
            "query": "I need to schedule 5 meetings this week. What's the optimal arrangement?",
            "why_tot": "Many scheduling patterns possible, needs to find most efficient"
        },
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"QUERY {i}: {test['query']}")
        print(f"Why ToT: {test['why_tot']}")
        print('=' * 80)
        
        try:
            answer = agent.run(test['query'])
            
            print(f"\n{'─' * 80}")
            print("FINAL ANSWER (Based on best evaluated path):")
            print('─' * 80)
            print(answer)
            print()
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nKey Observation:")
    print("ToT explored multiple paths, evaluated them, and selected the best approach.")
    print("This gives higher-quality answers for complex decisions!")


def demo_comparison_with_cot():
    """Compare ToT vs CoT on same query"""
    
    print("=" * 80)
    print("COMPARISON: Tree of Thoughts vs Chain of Thought")
    print("=" * 80)
    
    model = OllamaModel()
    registry = ToolRegistry()
    
    query = "What's the best way to learn machine learning in 3 months?"
    
    print(f"\nQuery: {query}\n")
    
    # CoT approach
    print("─" * 80)
    print("CHAIN OF THOUGHT (Linear reasoning):")
    print("─" * 80)
    
    try:
        from agents.cot_agent import CoTAgent
        cot_agent = CoTAgent(model, registry, num_thoughts=3)
        cot_answer = cot_agent.run(query)
        print(f"\nAnswer: {cot_answer[:300]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n")
    
    # ToT approach
    print("─" * 80)
    print("TREE OF THOUGHTS (Multi-path evaluation):")
    print("─" * 80)
    
    try:
        tot_agent = TreeOfThoughtsAgent(model, registry, num_branches=3, max_depth=2)
        tot_answer = tot_agent.run(query)
        print(f"\nAnswer: {tot_answer[:300]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)
    print("\nKey Difference:")
    print("- CoT: Single reasoning chain → answer")
    print("- ToT: Multiple chains → evaluated → best answer")
    print("\nToT typically produces better answers for complex decisions!")


def demo_scheduling_optimization():
    """Show ToT optimizing task scheduling"""
    
    print("=" * 80)
    print("TREE OF THOUGHTS: SCHEDULING OPTIMIZATION")
    print("Your specific use case!")
    print("=" * 80)
    
    model = OllamaModel()
    registry = ToolRegistry()
    
    agent = TreeOfThoughtsAgent(
        model, 
        registry,
        num_branches=3,
        max_depth=2,
        evaluation_criteria=[
            "Time efficiency",
            "Energy levels",
            "Context switching",
            "Productivity"
        ]
    )
    
    scheduling_queries = [
        "I have 3 client meetings, 2 team meetings, and 4 hours of focused work needed this week. How should I schedule these?",
        
        "Schedule my day: I need to code for 4 hours, attend 2 meetings, exercise, and have time for email. What's the optimal schedule?",
        
        "I want to learn Python (10 hours), prepare presentation (3 hours), and regular work (20 hours) this week. Best schedule?",
    ]
    
    for i, query in enumerate(scheduling_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"SCHEDULING SCENARIO {i}:")
        print(f"{query}")
        print('=' * 80)
        
        try:
            answer = agent.run(query)
            
            print(f"\n{'─' * 80}")
            print("OPTIMIZED SCHEDULE:")
            print('─' * 80)
            print(answer)
            print()
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
    
    print("\n" + "=" * 80)
    print("SCHEDULING OPTIMIZATION COMPLETE")
    print("=" * 80)
    print("\nToT Benefits for Scheduling:")
    print("✓ Explores multiple scheduling patterns")
    print("✓ Evaluates each against productivity criteria")
    print("✓ Selects most optimal arrangement")
    print("✓ Considers energy levels and context switching")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--compare':
            demo_comparison_with_cot()
        elif sys.argv[1] == '--schedule':
            demo_scheduling_optimization()
        else:
            print("Options: --compare or --schedule")
    else:
        demo_tree_of_thoughts()
        print("\nTip: Run with --compare or --schedule for specific demos")