"""
Simple Agent

A basic agentic AI that can:
1. Understand user queries
2. Decide which tools to use
3. Execute tools
4. Generate responses

This is a foundational agent that will be enhanced in Phase 2 with
ReAct, Chain of Thought, and other advanced reasoning patterns.

Architecture:
- Uses Ollama for language understanding and generation
- Accesses tools via ToolRegistry
- Simple prompt-based tool selection
- Single-step reasoning (multi-step in Phase 2)
"""

import json
from typing import Dict, Any, List, Optional
from models.base import BaseModel
from infra.tool_registry import ToolRegistry
from tools.base import ToolResult
from infra.logging import logger


class AgentError(Exception):
    """Base exception for agent errors"""
    pass


class SimpleAgent:
    """
    Simple Agent with tool use capability
    
    This agent can understand user queries, select appropriate tools,
    execute them, and generate responses. It uses a straightforward
    prompt-based approach for tool selection.
    
    Features:
    - Tool-aware: Can use any registered tool
    - LLM-powered: Uses language model for understanding and generation
    - Single-step: Executes one tool per query (multi-step in Phase 2)
    - Error handling: Gracefully handles failures
    
    Example:
        >>> agent = SimpleAgent(model=OllamaModel(), registry=tool_registry)
        >>> response = agent.run("What is the weather in Paris?")
        >>> print(response)
    """
    
    def __init__(
        self,
        model: BaseModel,
        registry: ToolRegistry,
        temperature: float = 0.3  # Lower for more focused reasoning
    ):
        """
        Initialize the agent
        
        Args:
            model: Language model for understanding and generation
            registry: Tool registry for accessing tools
            temperature: Sampling temperature for LLM
        """
        self.model = model
        self.registry = registry
        self.temperature = temperature
        
        logger.info(f"SimpleAgent initialized with {len(registry)} tools")
        logger.debug(f"Available tools: {', '.join(registry.list_tools())}")
    
    def run(self, query: str) -> str:
        """
        Run the agent on a user query
        
        This is the main entry point. The agent will:
        1. Analyze the query
        2. Decide if tools are needed
        3. Select and execute appropriate tool
        4. Generate final response
        
        Args:
            query: User's question or request
        
        Returns:
            Agent's response as a string
        """
        logger.info(f"Agent running query: '{query}'")
        
        try:
            # Step 1: Decide if we need tools
            needs_tool, tool_name, tool_params = self._plan_action(query)
            
            # Step 2: Execute tool if needed
            if needs_tool and tool_name:
                logger.info(f"Agent decided to use tool: {tool_name}")
                tool_result = self._execute_tool(tool_name, tool_params)
                
                # Step 3: Generate response with tool results
                response = self._generate_response_with_tool(
                    query, tool_name, tool_result
                )
            else:
                # Step 3: Generate direct response (no tools needed)
                logger.info("Agent decided no tools needed")
                response = self._generate_direct_response(query)
            
            logger.info("Agent completed successfully")
            return response
        
        except Exception as e:
            error_msg = f"Agent error: {str(e)}"
            logger.error(error_msg)
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _plan_action(self, query: str) -> tuple[bool, Optional[str], Optional[Dict]]:
        """
        Decide if tools are needed and which one to use
        
        Uses LLM to analyze query and select appropriate tool.
        
        Args:
            query: User's query
        
        Returns:
            Tuple of (needs_tool, tool_name, tool_parameters)
        """
        # Get available tools
        tool_descriptions = self.registry.get_tool_descriptions()
        
        if not tool_descriptions:
            # No tools available
            return False, None, None
        
        # Build tool selection prompt
        tools_info = "\n".join([
            f"- {name}: {desc}"
            for name, desc in tool_descriptions.items()
        ])
        
        prompt = f"""You are an AI assistant with access to tools. Analyze this query and decide if you need to use a tool.

Available tools:
{tools_info}

User query: "{query}"

Think step by step:
1. Can I answer this directly from my knowledge?
2. Do I need current/real-time information?
3. Which tool (if any) would be most helpful?

Respond in JSON format:
{{
    "needs_tool": true/false,
    "reasoning": "why you made this decision",
    "tool_name": "tool_name or null",
    "tool_params": {{"param": "value"}} or null
}}

If the query asks about current events, news, real-time data, or requires web search, use web_search.
If you can answer from your training knowledge, set needs_tool to false."""

        # Get LLM decision
        logger.debug("Requesting tool selection from LLM")
        response = self.model.generate(
            prompt,
            temperature=self.temperature,
            max_tokens=300
        )
        
        logger.debug(f"LLM tool decision: {response[:200]}...")
        
        # Parse response
        try:
            # Try to extract JSON from response
            response_clean = response.strip()
            if "```json" in response_clean:
                response_clean = response_clean.split("```json")[1].split("```")[0]
            elif "```" in response_clean:
                response_clean = response_clean.split("```")[1].split("```")[0]
            
            decision = json.loads(response_clean)
            
            needs_tool = decision.get("needs_tool", False)
            tool_name = decision.get("tool_name")
            tool_params = decision.get("tool_params", {})
            
            logger.info(
                f"Tool decision: needs_tool={needs_tool}, "
                f"tool={tool_name}, reasoning='{decision.get('reasoning', 'N/A')}'"
            )
            
            return needs_tool, tool_name, tool_params
        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM decision as JSON: {e}")
            logger.debug(f"Raw response: {response}")
            # Default to no tool use if we can't parse
            return False, None, None
    
    def _execute_tool(
        self,
        tool_name: str,
        tool_params: Optional[Dict[str, Any]]
    ) -> ToolResult:
        """
        Execute a tool with given parameters
        
        Args:
            tool_name: Name of tool to execute
            tool_params: Parameters for the tool
        
        Returns:
            ToolResult from execution
        """
        if tool_params is None:
            tool_params = {}
        
        logger.debug(f"Executing {tool_name} with params: {tool_params}")
        
        result = self.registry.execute_tool(tool_name, **tool_params)
        
        logger.debug(
            f"Tool result: success={result.success}, "
            f"data_len={len(str(result.data))}"
        )
        
        return result
    
    def _generate_response_with_tool(
        self,
        query: str,
        tool_name: str,
        tool_result: ToolResult
    ) -> str:
        """
        Generate response incorporating tool results
        
        Args:
            query: Original user query
            tool_name: Name of tool that was used
            tool_result: Result from tool execution
        
        Returns:
            Natural language response
        """
        if not tool_result.success:
            return (
                f"I tried to use {tool_name} to help answer your question, "
                f"but encountered an error: {tool_result.error}"
            )
        
        # Format tool data for LLM
        if tool_name == "web_search" and isinstance(tool_result.data, list):
            # Format search results nicely
            results_text = "\n\n".join([
                f"Result {item['position']}: {item['title']}\n{item['snippet']}\nURL: {item['url']}"
                for item in tool_result.data[:5]  # Top 5 results
            ])
        else:
            # Generic formatting
            results_text = str(tool_result.data)
        
        # Generate response with tool results
        prompt = f"""You are a helpful AI assistant. Use the information from the tool to answer the user's question.

User question: "{query}"

Tool used: {tool_name}

Tool results:
{results_text}

Provide a clear, helpful answer based on the tool results. Be concise but informative. 
If appropriate, cite specific sources or URLs from the results."""

        response = self.model.generate(
            prompt,
            temperature=self.temperature + 0.2,  # Slightly higher for more natural response
            max_tokens=500
        )
        
        return response.strip()
    
    def _generate_direct_response(self, query: str) -> str:
        """
        Generate direct response without tools
        
        Args:
            query: User's query
        
        Returns:
            Natural language response
        """
        prompt = f"""You are a helpful AI assistant. Answer this question directly using your knowledge.

User question: "{query}"

Provide a clear, helpful answer. Be concise but informative."""

        response = self.model.generate(
            prompt,
            temperature=self.temperature + 0.2,
            max_tokens=500
        )
        
        return response.strip()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status information
        
        Returns:
            Dictionary containing agent metadata
        """
        return {
            "model": self.model.name,
            "model_provider": self.model.provider,
            "available_tools": self.registry.list_tools(),
            "tool_count": len(self.registry),
            "temperature": self.temperature
        }
    
    def __repr__(self) -> str:
        """Developer representation"""
        return f"<SimpleAgent(model={self.model.name}, tools={len(self.registry)})>"
    
    def __str__(self) -> str:
        """String representation"""
        tools = ", ".join(self.registry.list_tools()) if len(self.registry) > 0 else "none"
        return f"SimpleAgent with {len(self.registry)} tools: {tools}"