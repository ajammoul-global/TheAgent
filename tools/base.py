from abc import ABC, abstractmethod
from typing import Any, List, Optional
from dataclasses import dataclass, field


# ==============================================================================
# HELPER CLASSES - Used to define tool schemas
# ==============================================================================

@dataclass
class ToolParameter:
    """
    Defines a single parameter for a tool.
    
    Uses Python dataclasses for simplicity (no external dependencies).
    
    Example:
        ToolParameter(
            name="query",
            type="string",
            description="Search query",
            required=True
        )
    """
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


@dataclass
class ToolResult:
    """
    Standardized result from tool execution.
    
    Every tool returns this structure, making results predictable.
    
    Example Success:
        ToolResult(
            success=True,
            data={"results": [...]},
            metadata={"source": "duckduckgo"}
        )
    
    Example Failure:
        ToolResult(
            success=False,
            error="Network timeout",
            metadata={"tool": "web_search"}
        )
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


# ==============================================================================
# BASE TOOL - The interface all tools implement
# ==============================================================================

class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Every tool must implement:
    1. name - unique identifier
    2. description - what the tool does
    3. parameters - what inputs it needs
    4. execute - how to run it
    
    Example tool structure:
        class WebSearchTool(BaseTool):
            @property
            def name(self):
                return "web_search"
            
            @property
            def description(self):
                return "Search the web for information"
            
            @property
            def parameters(self):
                return [
                    ToolParameter(name="query", type="string", ...)
                ]
            
            def execute(self, query: str):
                # Do the search
                return ToolResult(success=True, data=results)
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique identifier for this tool.
        
        Must be lowercase with underscores (snake_case).
        This is what the LLM uses to call the tool.
        
        Example: "web_search", "create_task", "send_email"
        
        Returns:
            Tool name as string
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Clear description of what this tool does.
        
        This is shown to the LLM so it knows WHEN to use this tool.
        Be specific and clear!
        
        Good: "Search the web for current information on any topic"
        Bad: "Searches stuff"
        
        Returns:
            Tool description as string
        """
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """
        List of parameters this tool accepts.
        
        Defines the "schema" for calling this tool.
        The LLM needs to know what parameters to provide.
        
        Example:
            return [
                ToolParameter(
                    name="query",
                    type="string",
                    description="What to search for",
                    required=True
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="Max results to return",
                    required=False,
                    default=5
                )
            ]
        
        Returns:
            List of ToolParameter objects
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        This is where the actual work happens!
        
        Args:
            **kwargs: Tool parameters (matching self.parameters)
            
        Returns:
            ToolResult with execution outcome
            
        Example:
            def execute(self, query: str, max_results: int = 5):
                try:
                    results = do_search(query, max_results)
                    return ToolResult(success=True, data=results)
                except Exception as e:
                    return ToolResult(success=False, error=str(e))
        """
        pass
    
    # ==========================================================================
    # HELPER METHODS - Provided by BaseTool, don't need to override
    # ==========================================================================
    
    def to_schema(self) -> dict:
        """
        Convert tool to LLM-readable schema.
        
        This is called automatically to generate the tool description
        that gets sent to the LLM in the prompt.
        
        Returns:
            Dictionary with tool schema in standard format
            
        Example output:
            {
                "name": "web_search",
                "description": "Search the web...",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description,
                        **({"default": param.default} if param.default is not None else {})
                    }
                    for param in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required]
            }
        }
    
    def validate_parameters(self, **kwargs: Any) -> dict:
        """
        Validate parameters before execution.
        
        Checks:
        1. All required parameters are provided
        2. Uses defaults for missing optional parameters
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            Validated parameters dictionary
            
        Raises:
            ValueError: If validation fails
            
        Example:
            params = tool.validate_parameters(query="Python")
            # Returns: {"query": "Python", "max_results": 5}  # Used default
        """
        validated = {}
        
        for param in self.parameters:
            value = kwargs.get(param.name)
            
            # Check required parameters
            if param.required and value is None:
                raise ValueError(
                    f"Required parameter '{param.name}' is missing for tool '{self.name}'"
                )
            
            # Use default if not provided
            if value is None and param.default is not None:
                value = param.default
            
            validated[param.name] = value
        
        return validated
    
    def safe_execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute tool with automatic validation and error handling.
        
        This wraps execute() with:
        1. Parameter validation
        2. Error catching
        3. Consistent error reporting
        
        Use this instead of execute() for production!
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult (always returns, never throws)
            
        Example:
            result = tool.safe_execute(query="Python")
            if result.success:
                print(result.data)
            else:
                print(f"Error: {result.error}")
        """
        try:
            # Validate parameters first
            validated_params = self.validate_parameters(**kwargs)
            
            # Execute tool with validated params
            result = self.execute(**validated_params)
            
            return result
            
        except Exception as e:
            # Catch ANY error and return as ToolResult
            return ToolResult(
                success=False,
                error=f"Tool '{self.name}' failed: {str(e)}",
                metadata={
                    "tool": self.name,
                    "params": kwargs,
                    "error_type": type(e).__name__
                }
            )
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<Tool: {self.name}>"
