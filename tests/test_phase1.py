"""
Phase 1 Integration Tests

End-to-end tests that verify all Phase 1 components work together:
- Models (Ollama)
- Tools (WebSearch)
- Tool Registry
- Simple Agent

These tests verify the complete agent workflow from query to response.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from models.ollama import OllamaModel
from infra.tool_registry import ToolRegistry
from tools.base import ToolResult
from tools.web_search import WebSearchTool
from agents.simple_agent import SimpleAgent


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_ollama():
    """Mock Ollama model for testing"""
    with patch('models.ollama.requests') as mock_requests:
        # Mock connection validation
        tags_response = Mock()
        tags_response.json.return_value = {
            "models": [{"name": "llama3.1:8b"}]
        }
        tags_response.raise_for_status = Mock()
        mock_requests.get.return_value = tags_response
        
        # Create model
        model = OllamaModel()
        yield model, mock_requests


@pytest.fixture
def clean_registry():
    """Provide a clean tool registry for each test"""
    registry = ToolRegistry()
    registry.clear()  # Clear auto-loaded tools
    yield registry
    registry.clear()


@pytest.fixture
def mock_web_search_tool():
    """Mock web search tool for testing"""
    tool = Mock(spec=WebSearchTool)
    tool.name = "web_search"
    tool.description = "Search the web"
    tool.parameters = []
    tool.validate = Mock(return_value=True)
    tool.get_schema = Mock(return_value={
        "name": "web_search",
        "description": "Search the web",
        "parameters": []
    })
    return tool


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhase1Integration:
    """Test complete Phase 1 workflow"""
    
    def test_tool_registration(self, clean_registry, mock_web_search_tool):
        """Test tool can be registered and retrieved"""
        # Register tool
        clean_registry.register(mock_web_search_tool)
        
        # Verify registration
        assert "web_search" in clean_registry
        assert len(clean_registry) == 1
        
        # Retrieve tool
        tool = clean_registry.get_tool("web_search")
        assert tool.name == "web_search"
    
    def test_agent_initialization(self, mock_ollama, clean_registry):
        """Test agent can be initialized with model and registry"""
        model, _ = mock_ollama
        
        # Create agent
        agent = SimpleAgent(model=model, registry=clean_registry)
        
        # Verify initialization
        assert agent.model == model
        assert agent.registry == clean_registry
        status = agent.get_status()
        assert status["model"] == "llama3.1:8b"
        assert status["tool_count"] == 0
    
    def test_agent_with_registered_tool(self, mock_ollama, clean_registry, mock_web_search_tool):
        """Test agent can access registered tools"""
        model, _ = mock_ollama
        clean_registry.register(mock_web_search_tool)
        
        # Create agent
        agent = SimpleAgent(model=model, registry=clean_registry)
        
        # Verify tool access
        status = agent.get_status()
        assert "web_search" in status["available_tools"]
        assert status["tool_count"] == 1
    
    def test_agent_direct_response(self, mock_ollama, clean_registry):
        """Test agent can generate direct responses without tools"""
        model, mock_requests = mock_ollama
        
        # Mock LLM responses
        # Single response: actual answer (no tool planning when registry is empty)
        answer_response = Mock()
        answer_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "Python is a high-level programming language."
            }
        }
        answer_response.raise_for_status = Mock()
        
        mock_requests.post.side_effect = [answer_response]
        
        # Create agent and run
        agent = SimpleAgent(model=model, registry=clean_registry)
        response = agent.run("What is Python?")
        
        # Verify response
        assert isinstance(response, str)
        assert len(response) > 0
        assert "Python" in response or "python" in response
    
    def test_agent_with_tool_use(self, mock_ollama, clean_registry):
        """Test agent can use tools to answer questions"""
        model, mock_requests = mock_ollama
        
        # Create and register mock tool
        mock_tool = Mock(spec=WebSearchTool)
        mock_tool.name = "web_search"
        mock_tool.description = "Search the web"
        mock_tool.parameters = []
        mock_tool.validate = Mock(return_value=True)
        mock_tool.get_schema = Mock(return_value={
            "name": "web_search",
            "description": "Search the web",
            "parameters": []
        })
        
        # Mock tool execution
        mock_tool.execute = Mock(return_value=ToolResult(
            success=True,
            data=[
                {
                    "position": 1,
                    "title": "Weather in Paris",
                    "snippet": "Current weather in Paris is sunny, 20°C",
                    "url": "https://weather.example.com/paris"
                }
            ]
        ))
        
        clean_registry.register(mock_tool)
        
        # Mock LLM responses
        # First: tool selection (use web_search)
        selection_response = Mock()
        selection_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": '{"needs_tool": true, "reasoning": "Need current weather", "tool_name": "web_search", "tool_params": {"query": "weather in Paris"}}'
            }
        }
        selection_response.raise_for_status = Mock()
        
        # Second: response with tool results
        answer_response = Mock()
        answer_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "Based on current data, the weather in Paris is sunny with a temperature of 20°C."
            }
        }
        answer_response.raise_for_status = Mock()
        
        mock_requests.post.side_effect = [selection_response, answer_response]
        
        # Create agent and run
        agent = SimpleAgent(model=model, registry=clean_registry)
        response = agent.run("What's the weather in Paris?")
        
        # Verify tool was called
        assert mock_tool.execute.called
        
        # Verify response
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_agent_tool_error_handling(self, mock_ollama, clean_registry):
        """Test agent handles tool errors gracefully"""
        model, mock_requests = mock_ollama
        
        # Create mock tool that fails
        mock_tool = Mock(spec=WebSearchTool)
        mock_tool.name = "web_search"
        mock_tool.description = "Search the web"
        mock_tool.parameters = []
        mock_tool.validate = Mock(return_value=True)
        mock_tool.get_schema = Mock(return_value={
            "name": "web_search",
            "description": "Search the web",
            "parameters": []
        })
        
        # Mock tool execution to fail
        mock_tool.execute = Mock(return_value=ToolResult(
            success=False,
            data=[],
            error="Network error"
        ))
        
        clean_registry.register(mock_tool)
        
        # Mock LLM to select tool
        selection_response = Mock()
        selection_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": '{"needs_tool": true, "tool_name": "web_search", "tool_params": {"query": "test"}}'
            }
        }
        selection_response.raise_for_status = Mock()
        mock_requests.post.return_value = selection_response
        
        # Create agent and run
        agent = SimpleAgent(model=model, registry=clean_registry)
        response = agent.run("Test query")
        
        # Verify error is handled gracefully
        assert isinstance(response, str)
        assert "error" in response.lower() or "encountered" in response.lower()


# ============================================================================
# REAL INTEGRATION TESTS (require Ollama and internet)
# ============================================================================

class TestRealIntegration:
    """
    Real integration tests with actual Ollama and web search
    
    These tests require:
    - Ollama running locally
    - Internet connection for web search
    - duckduckgo-search installed
    """
    
    @pytest.fixture
    def real_setup(self):
        """Setup real components"""
        try:
            from models.ollama import OllamaModel
            from tools import WebSearchTool
            
            model = OllamaModel()
            registry = ToolRegistry()
            
            # Try to create web search tool
            try:
                web_tool = WebSearchTool()
                registry.register(web_tool)
            except Exception as e:
                pytest.skip(f"Web search tool not available: {e}")
            
            agent = SimpleAgent(model=model, registry=registry)
            
            yield agent, registry
            
            registry.clear()
            
        except Exception as e:
            pytest.skip(f"Real integration setup failed: {e}")
    
    def test_real_agent_query(self, real_setup):
        """Test real agent with actual Ollama and tools"""
        agent, registry = real_setup
        
        # Run a simple query
        response = agent.run("What is Python programming?")
        
        # Verify we got a response
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"\nAgent response: {response[:200]}...")
    
    def test_real_web_search(self, real_setup):
        """Test real web search integration"""
        agent, registry = real_setup
        
        # Query that should trigger web search
        response = agent.run("What are the latest Python 3.12 features?")
        
        # Verify response
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"\nAgent response with web search: {response[:200]}...")


# ============================================================================
# RUN INSTRUCTIONS
# ============================================================================

if __name__ == "__main__":
    """
    Run tests with: python tests/test_integration.py
    Or with pytest: pytest tests/test_integration.py -v
    
    To run only mock tests (no Ollama needed):
    pytest tests/test_integration.py::TestPhase1Integration -v
    
    To run real integration tests:
    pytest tests/test_integration.py::TestRealIntegration -v -s
    """
    pytest.main([__file__, "-v", "-s"])