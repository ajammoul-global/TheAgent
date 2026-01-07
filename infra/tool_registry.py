# infra/tool_registry.py

import importlib
import inspect
import sys
from pathlib import Path
from typing import Dict

from tools.base import BaseTool, ToolResult
from infra.logging import logger


class ToolRegistry:
    """
    Dynamically loads all BaseTool subclasses from tools/ folder (recursively)
    and provides access to them by name.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tools_path = Path(__file__).parent.parent / "tools"
        self._load_tools()

    def _load_tools(self):
        logger.info(f"Scanning tools directory recursively: {self._tools_path}")
        # Add tools folder to sys.path for dynamic import
        sys.path.insert(0, str(self._tools_path))

        # Recursively iterate over all .py files, ignoring __init__.py
        for py_file in self._tools_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            # Compute module name relative to tools folder
            module_path = py_file.relative_to(self._tools_path).with_suffix("")
            module_name = ".".join(module_path.parts)

            try:
                module = importlib.import_module(module_name)
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseTool) and obj is not BaseTool:
                        tool_instance = obj()
                        if tool_instance.name in self._tools:
                            logger.warning(f"Duplicate tool name '{tool_instance.name}' skipped")
                            continue
                        self._tools[tool_instance.name] = tool_instance
                        logger.info(f"Registered tool: {tool_instance.name}")
            except Exception as e:
                logger.error(f"Failed to import tool module {module_name}: {e}")

        sys.path.pop(0)

    def get_tool(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all registered tools"""
        return {
            name: tool.description 
            for name, tool in self._tools.items()
        }

    def register(self, tool: BaseTool) -> None:
        """Manually register a tool in the registry"""
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered, overwriting")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def clear(self) -> None:
        """Clear all registered tools"""
        self._tools.clear()
        logger.info("Tool registry cleared")

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered"""
        return name in self._tools

    def __len__(self) -> int:
        """Get number of registered tools"""
        return len(self._tools)

    def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with given parameters
        
        Args:
            name: Name of the tool to execute
            **kwargs: Parameters to pass to the tool
        
        Returns:
            ToolResult from tool execution
        """
        tool = self.get_tool(name)
        return tool.execute(**kwargs)
