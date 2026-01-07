"""
Web Search Tool

Provides web search capability using DuckDuckGo (no API key required).
Returns structured search results that the agent can use to answer questions.

Features:
- No API key needed (uses duckduckgo-search library)
- Returns top N results
- Extracts title, snippet, and URL
- Handles errors gracefully
"""

from typing import List, Dict, Any
from tools.base import BaseTool, ToolParameter, ToolResult
from infra.logging import logger

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False
    logger.warning(
        "duckduckgo-search not installed. "
        "Install with: pip install duckduckgo-search"
    )


class WebSearchTool(BaseTool):
    """
    Web Search Tool using DuckDuckGo
    
    Searches the web and returns structured results including titles,
    snippets, and URLs. No API key required.
    
    Example:
        >>> tool = WebSearchTool()
        >>> result = tool.execute(query="Python programming", max_results=5)
        >>> for item in result.data:
        ...     print(item['title'], item['url'])
    """
    
    def __init__(self, default_max_results: int = 5):
        """
        Initialize web search tool
        
        Args:
            default_max_results: Default number of results to return
        """
        self._default_max_results = default_max_results
        
        if not HAS_DDGS:
            logger.warning(
                "WebSearchTool initialized but duckduckgo-search is not available"
            )
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return (
            "Search the web using DuckDuckGo. Returns titles, snippets, and URLs "
            "of relevant web pages. Use this to find current information, "
            "answer questions, or research topics."
        )
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="The search query to execute",
                required=True
            ),
            ToolParameter(
                name="max_results",
                type="int",
                description=f"Maximum number of results to return (default: {self._default_max_results})",
                required=False,
                default=self._default_max_results
            )
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute web search
        
        Args:
            query: Search query string
            max_results: Maximum number of results (optional)
        
        Returns:
            ToolResult with list of search results
        """
        # Validate parameters
        self.validate(**kwargs)
        
        query = kwargs.get("query")
        max_results = kwargs.get("max_results", self._default_max_results)
        
        logger.info(f"Web search: '{query}' (max_results={max_results})")
        
        # Check if library is available
        if not HAS_DDGS:
            error_msg = (
                "duckduckgo-search library not installed. "
                "Install with: pip install duckduckgo-search"
            )
            logger.error(error_msg)
            return ToolResult(
                success=False,
                data=[],
                error=error_msg
            )
        
        try:
            # Perform search
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    max_results=max_results
                ))
            
            # Format results
            formatted_results = []
            for idx, result in enumerate(results, 1):
                formatted_results.append({
                    "position": idx,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", ""),
                })
            
            logger.info(f"Found {len(formatted_results)} results")
            logger.debug(f"First result: {formatted_results[0] if formatted_results else 'none'}")
            
            return ToolResult(
                success=True,
                data=formatted_results,
                metadata={
                    "query": query,
                    "result_count": len(formatted_results),
                    "max_results": max_results
                }
            )
        
        except Exception as e:
            error_msg = f"Web search failed: {str(e)}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                data=[],
                error=error_msg
            )
    
    def validate(self, **kwargs) -> bool:
        """
        Validate search parameters
        
        Extends base validation with search-specific checks
        """
        # Use base class parameter validation
        validated = self.validate_parameters(**kwargs)
        
        # Additional validation
        query = kwargs.get("query", "")
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        max_results = kwargs.get("max_results", self._default_max_results)
        if not isinstance(max_results, int) or max_results < 1:
            raise ValueError("max_results must be a positive integer")
        
        if max_results > 20:
            raise ValueError("max_results cannot exceed 20")
        
        return True