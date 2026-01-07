# tests/test_react.py
import pytest
from agents.react_agent import ReActAgent
from models.ollama import OllamaModel
from infra.tool_registry import ToolRegistry

def test_react_initialization():
    """Test ReAct agent can be created"""
    model = OllamaModel()
    registry = ToolRegistry()
    agent = ReActAgent(model, registry)
    
    assert agent.max_steps == 5
    assert agent.model is not None
    assert agent.registry is not None

def test_react_simple_query():
    """Test with simple query (should not need multiple steps)"""
    model = OllamaModel()
    registry = ToolRegistry()
    agent = ReActAgent(model, registry, max_steps=3)
    
    response = agent.run("What is Python?")
    
    assert len(response) > 0
    assert "python" in response.lower()

@pytest.mark.skipif(not pytest.config.getoption("--real", default=False), 
                    reason="Real integration test")
def test_react_multi_step():
    """Test with complex query requiring multiple steps"""
    model = OllamaModel()
    registry = ToolRegistry()
    agent = ReActAgent(model, registry, max_steps=5)
    
    response = agent.run(
        "Search for the latest Python version and tell me what's new"
    )
    
    assert len(response) > 50
    # Should have used reasoning and search