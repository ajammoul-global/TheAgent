"""
Chain of Thought (CoT) Agent Implementation
Generates a reasoning chain before taking action
"""
from typing import List, Dict, Optional
from models.base import BaseModel
from infra.tool_registry import ToolRegistry
from infra.logging import logger
import json


class CoTAgent:
    """
    Chain of Thought agent that:
    1. Generates multiple reasoning steps upfront
    2. Decides on action based on complete reasoning chain
    3. Executes action once
    4. Generates final answer
    
    Best for: Tasks requiring logical deduction, math, planning
    """
    
    def __init__(self, model: BaseModel, registry: ToolRegistry, num_thoughts: int = 3):
        """
        Initialize CoT agent
        
        Args:
            model: Language model for reasoning
            registry: Tool registry for executing actions
            num_thoughts: Number of reasoning steps to generate
        """
        self.model = model
        self.registry = registry
        self.num_thoughts = num_thoughts
        logger.info(f"CoT agent initialized with {len(registry)} tools, {num_thoughts} thought steps")
    
    def run(self, query: str) -> str:
        """
        Execute Chain of Thought reasoning
        
        Args:
            query: User's question or task
            
        Returns:
            Final answer after reasoning and optional tool use
        """
        logger.info(f"CoT agent starting: {query}")
        
        # Phase 1: Generate reasoning chain
        thought_chain = self._generate_thought_chain(query)
        
        # Phase 2: Decide if tools are needed based on reasoning
        action = self._decide_action(query, thought_chain)
        
        # Phase 3: Execute action if needed
        observation = None
        if action:
            observation = self._execute_action(action)
        
        # Phase 4: Generate final answer
        answer = self._final_answer(query, thought_chain, observation)
        
        return answer
    
    def _generate_thought_chain(self, query: str) -> List[str]:
        """
        Generate a chain of reasoning steps
        
        Returns:
            List of thoughts in logical sequence
        """
        logger.info(f"Generating {self.num_thoughts} reasoning steps...")
        
        prompt = f"""Question: {query}

Let's think through this step by step:

Step 1:"""
        
        # Generate all thoughts in one go for coherent reasoning
        response = self.model.generate(
            prompt, 
            max_tokens=400,  # Enough for multiple thoughts
            temperature=0.7  # Moderate creativity
        )
        
        # Parse thoughts from response
        thoughts = []
        lines = response.strip().split('\n')
        current_thought = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('Step ') and current_thought:
                # Save previous thought
                thoughts.append(' '.join(current_thought))
                current_thought = []
            
            # Remove "Step X:" prefix if present
            if line.startswith('Step '):
                line = line.split(':', 1)[-1].strip()
            
            if line:
                current_thought.append(line)
        
        # Add final thought
        if current_thought:
            thoughts.append(' '.join(current_thought))
        
        # Log the reasoning chain
        for i, thought in enumerate(thoughts[:self.num_thoughts], 1):
            logger.info(f"Step {i}: {thought[:100]}...")
        
        return thoughts[:self.num_thoughts]
    
    def _decide_action(self, query: str, thought_chain: List[str]) -> Optional[Dict]:
        """
        Decide if tools are needed based on complete reasoning chain
        
        Args:
            query: Original query
            thought_chain: Complete chain of reasoning
            
        Returns:
            Action dict if tool is needed, None otherwise
        """
        tools = self.registry.get_tool_descriptions()
        tools_list = "\n".join([f"- {n}: {d}" for n, d in tools.items()])
        
        # Combine thoughts into context
        reasoning = "\n".join([f"Step {i+1}: {t}" for i, t in enumerate(thought_chain)])
        
        prompt = f"""Question: {query}

My reasoning:
{reasoning}

Available tools:
{tools_list}

Based on my reasoning, do I need to use a tool to answer this question?

CRITICAL RULES:
- If I need current information, facts, or data I don't have → USE web_search
- If my reasoning shows I need to look something up → USE web_search
- If I can answer from pure logic/reasoning alone → NO tool needed

Examples:
- "What is 2+2?" → NO tool (pure logic)
- "What are the best Python tutorials?" → USE web_search (need current data)
- "If A>B and B>C, is A>C?" → NO tool (logical deduction)

Respond with ONLY valid JSON (no explanation, no markdown):
{{"needs_tool": true, "tool_name": "web_search", "parameters": {{"query": "search terms", "max_results": 5}}}}

OR if no tool needed:
{{"needs_tool": false}}

JSON:"""
        
        response = self.model.generate(prompt, max_tokens=200, temperature=0.1)
        
        try:
            # Clean response
            response = response.strip()
            if "```" in response:
                parts = response.split("```")
                for part in parts:
                    if "{" in part and "}" in part:
                        response = part
                        if response.startswith("json"):
                            response = response[4:].strip()
                        break
            
            # Parse JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                decision = json.loads(response[start:end])
                
                if decision.get("needs_tool"):
                    logger.info(f"✓ CoT agent decided to use tool: {decision.get('tool_name')}")
                    logger.info(f"  Parameters: {decision.get('parameters')}")
                    return decision
                else:
                    logger.info("✓ CoT agent decided no tool needed (pure reasoning)")
                    return None
        except Exception as e:
            logger.warning(f"✗ Could not parse decision: {e}")
        
        return None
    
    def _execute_action(self, action: Dict) -> str:
        """
        Execute a tool and return observation
        
        Args:
            action: Action dictionary with tool_name and parameters
            
        Returns:
            Observation from tool execution
        """
        tool_name = action["tool_name"]
        parameters = action.get("parameters", {})
        
        logger.info(f"Executing tool: {tool_name}")
        result = self.registry.execute_tool(tool_name, **parameters)
        
        if result.success:
            # Format observation
            if isinstance(result.data, list):
                # Format search results
                formatted = []
                for i, item in enumerate(result.data[:5], 1):
                    if isinstance(item, dict):
                        title = item.get('title', 'No title')
                        snippet = item.get('snippet', item.get('body', ''))[:150]
                        formatted.append(f"{i}. {title}: {snippet}...")
                observation = "\n".join(formatted)
            else:
                observation = str(result.data)
            
            logger.info(f"Tool succeeded: {len(observation)} chars")
            return observation
        else:
            logger.error(f"Tool failed: {result.error}")
            return f"Error: {result.error}"
    
    def _final_answer(self, query: str, thought_chain: List[str], observation: Optional[str]) -> str:
        """
        Generate final answer based on reasoning and observations
        
        Args:
            query: Original query
            thought_chain: Chain of reasoning steps
            observation: Optional tool observation
            
        Returns:
            Final answer
        """
        reasoning = "\n".join([f"Step {i+1}: {t}" for i, t in enumerate(thought_chain)])
        
        if observation:
            prompt = f"""Question: {query}

My reasoning:
{reasoning}

Information found:
{observation}

Based on my reasoning and the information found, provide a clear, comprehensive final answer:

Answer:"""
        else:
            prompt = f"""Question: {query}

My reasoning:
{reasoning}

Based on my reasoning alone, provide a clear, comprehensive final answer:

Answer:"""
        
        response = self.model.generate(prompt, max_tokens=500, temperature=0.5)
        logger.info(f"Generated final answer: {len(response)} characters")
        
        return response.strip()


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    print_section("CoT Agent Demo")

    # Setup model and registry; fall back to a MockModel if real model unavailable
    try:
        from models.ollama import OllamaModel
        model = OllamaModel()
        from infra.tool_registry import ToolRegistry
        registry = ToolRegistry()
        print("Setting up real OllamaModel and ToolRegistry...")
    except Exception:
        # Minimal MockModel that returns predictable outputs for the demo
        class MockModel:
            def generate(self, prompt: str, max_tokens: int = None, temperature: float = 0.5) -> str:
                p = prompt.lower()
                # Thought-chain generation
                if "step 1:" in prompt or "let's think" in p:
                    return (
                        "Step 1: Consider the core aspects.\n"
                        "Step 2: Check relevant facts and constraints.\n"
                        "Step 3: Draw a concise conclusion."
                    )
                # Decision JSON expected
                if "respond with only valid json" in p or '"needs_tool"' in p or 'needs_tool' in p:
                    return '{"needs_tool": false}'
                # Final answer
                return "Python is a high-level programming language commonly used for automation, web development, and data science."

        model = MockModel()

        # lightweight registry with required methods
        class _EmptyRegistry:
            def __init__(self):
                self._tools = {}
            def get_tool_descriptions(self):
                return {}
            def execute_tool(self, name: str, **kwargs):
                from tools.base import ToolResult
                return ToolResult(success=False, data=None, error="No tools available")
            def clear(self):
                self._tools.clear()
            def __len__(self):
                return 0

        registry = _EmptyRegistry()
        print("Using MockModel and empty registry for demo (no external services required)")

    # Instantiate agent
    agent = CoTAgent(model=model, registry=registry, num_thoughts=3)
    print(f"✓ Agent ready with {len(registry)} tools")

    # Demo queries
    queries = [
        "What is the weather today in beirut do i wear a jacket?",
        "If A > B and B > C, is A > C? Explain your reasoning.",
        "Find a brief summary of Python's strengths for data science."
    ]

    for i, q in enumerate(queries, 1):
        print_section(f"Query {i}: {q}")
        print("Agent is reasoning...\n")
        try:
            response = agent.run(q)
        except Exception as e:
            response = f"Error running agent: {e}"

        print("\n" + "─"*60)
        print("FINAL ANSWER:")
        print("─"*60)
        print(response)
        print()

        try:
            input("Press Enter for next query...")
        except Exception:
            # In non-interactive environments, just continue
            pass

    print_section("Demo Complete!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()