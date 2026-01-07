# agents/react_agent.py
from typing import List, Tuple, Dict, Optional
from models.base import BaseModel
from infra.tool_registry import ToolRegistry
from infra.logging import logger
import json

class ReActAgent:
    """ReAct Agent - Reason + Act in a loop"""
    
    def __init__(self, model: BaseModel, registry: ToolRegistry, max_steps: int = 5):
        self.model = model
        self.registry = registry
        self.max_steps = max_steps
        logger.info(f"ReActAgent initialized with {len(registry)} tools")
    
    def run(self, query: str) -> str:
        """Execute the ReAct loop"""
        logger.info(f"ReAct agent starting: {query}")
        history: List[Tuple[str, str]] = []
        
        for step in range(1, self.max_steps + 1):
            logger.info(f"ReAct step {step}/{self.max_steps}")
            
            # 1. THOUGHT
            thought = self._generate_thought(query, history, step)
            history.append(("Thought", thought))
            
            # Check if done
            if self._is_complete(thought):
                return self._final_answer(query, history)
            
            # 2. ACTION
            action = self._decide_action(thought)
            if not action:
                return self._final_answer(query, history)
            
            history.append(("Action", str(action)))
            
            # 3. OBSERVATION
            observation = self._execute_action(action)
            history.append(("Observation", observation))
        
        return self._final_answer(query, history)
    
    def _generate_thought(self, query: str, history: List[Tuple[str, str]], step: int) -> str:
        """Generate reasoning"""
        context = "\n\n".join([f"{k}: {v}" for k, v in history]) if history else "Starting fresh."
        
        prompt = f"""Task: {query}

Previous steps:
{context}

Step {step}: What should I think about next? What do I need to know?

Thought:"""
        
        return self.model.generate(prompt, max_tokens=150).strip()
    
    def _is_complete(self, thought: str) -> bool:
        """Check if task is done"""
        done_phrases = ["have enough", "can now answer", "task complete", "have the answer"]
        return any(p in thought.lower() for p in done_phrases)
    
    def _decide_action(self, thought: str) -> Optional[Dict]:
        """Decide what tool to use"""
        tools = self.registry.get_tool_descriptions()
        tools_list = "\n".join([f"- {n}: {d}" for n, d in tools.items()])
        
        prompt = f"""Thought: {thought}

Available tools:
{tools_list}

CRITICAL: If the thought mentions needing to "search", "find", "look up", or get current information, you MUST use web_search.

Examples:
- Thought: "I need to find Python tutorials" → USE web_search
- Thought: "I should search for AI news" → USE web_search  
- Thought: "I already know what Python is" → NO tool needed

Respond with ONLY valid JSON (no explanation, no markdown):
{{"needs_tool": true, "tool_name": "web_search", "parameters": {{"query": "search terms here", "max_results": 5}}}}

OR if no tool needed:
{{"needs_tool": false}}

JSON:"""
        
        response = self.model.generate(prompt, max_tokens=200, temperature=0.1)
        
        try:
            # Clean response - remove markdown if present
            response = response.strip()
            if "```" in response:
                # Extract content between code blocks
                parts = response.split("```")
                for part in parts:
                    if "{" in part and "}" in part:
                        response = part
                        if response.startswith("json"):
                            response = response[4:].strip()
                        break
            
            # Find and parse JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                decision = json.loads(response[start:end])
                
                if decision.get("needs_tool"):
                    logger.info(f"✓ Agent decided to use tool: {decision.get('tool_name')}")
                    logger.info(f"  Parameters: {decision.get('parameters')}")
                    return decision
                else:
                    logger.info("✓ Agent decided no tool needed")
                    return None
        except Exception as e:
            logger.warning(f"✗ Could not parse decision from: {response[:150]}...")
            logger.warning(f"  Error: {e}")
        
        return None
    
    def _execute_action(self, action: Dict) -> str:
        """Run a tool"""
        try:
            result = self.registry.execute_tool(action["tool_name"], **action.get("parameters", {}))
            
            if result.success:
                if isinstance(result.data, list):
                    # Format search results
                    obs = "Found:\n"
                    for item in result.data[:3]:
                        obs += f"- {item.get('title', 'N/A')}: {item.get('snippet', 'N/A')}\n"
                    return obs
                return str(result.data)
            else:
                return f"Error: {result.error}"
        except Exception as e:
            return f"Failed: {str(e)}"
    
    def _final_answer(self, query: str, history: List[Tuple[str, str]]) -> str:
        """Generate final answer"""
        context = "\n\n".join([f"{k}: {v}" for k, v in history])
        
        prompt = f"""Original question: {query}

My reasoning process:
{context}

Based on everything above, provide a clear final answer:

Answer:"""
        
        return self.model.generate(prompt, max_tokens=300).strip()