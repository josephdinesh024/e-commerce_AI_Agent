"""
Tool registry for storing and retrieving Agent tools.
"""

from typing import Dict, List, Union, Callable
from ai_agent_core.tools.base_tool import BaseTool, FunctionTool

class ToolRegistry:
    """
    Manages the registration, storage, and retrieval of agent tools.
    """
    _tools: Dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: Union[BaseTool, Callable]) -> None:
        """
        Registers a given tool instance or wraps a plain callable into a FunctionTool.
        """
        if callable(tool) and not isinstance(tool, BaseTool):
            tool = FunctionTool(tool)
        if not getattr(tool, "name", None):
            raise ValueError(f"Tool of type {type(tool).__name__} must define a 'name'")
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, tool_name: str) -> BaseTool:
        """Retrieves a registered tool by its name."""
        if tool_name not in cls._tools:
            raise KeyError(f"Tool '{tool_name}' not found in registry")
        return cls._tools[tool_name]

    @classmethod
    def get_all(cls) -> List[BaseTool]:
        """Provides a list of all currently registered tools."""
        return list(cls._tools.values())

    @classmethod
    def clear(cls) -> None:
        """Clears all registered tools (mostly used for testing)."""
        cls._tools.clear()
