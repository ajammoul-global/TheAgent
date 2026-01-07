

import pytest
from tools.web_search import WebSearchTool
from infra.config import settings

def test_mock_search(monkeypatch):
    monkeypatch.setattr(settings, "SEARCH_REAL", False)
    tool = WebSearchTool()
    query = "Python AI"
    result = tool.execute(query)
    assert "Result 1 for 'Python AI'" in result
