"""
Base class for all agent tools.
"""

from typing import Any, Callable, Optional

class BaseTool:
    """
    Interface for tools that the agent can use.
    Subclasses must define 'name', 'description', and implement 'run()'.
    """
    name: str = ""
    description: str = ""

    async def run(self, input: Any) -> Any:
        """
        Execute the tool's core logic with the given input.
        """
        raise NotImplementedError("Subclasses must implement the run method")

    def to_langchain_tool(self):
        """Convert this BaseTool to a LangChain StructuredTool for native function calling."""
        from langchain_core.tools import StructuredTool
        # We use from_function on the run method, ensuring it's bound.
        # This will create a tool that takes an 'input' argument by default.
        return StructuredTool.from_function(
            func=self.run,
            name=self.name,
            description=self.description
        )


class FunctionTool(BaseTool):
    """
    Wraps a plain function (or @tool decorated function) into a BaseTool.
    Uses func.__name__ as name and func.__doc__ as description.
    
    Usage:
        def search_products(query: str) -> str:
            '''Search for products in the catalog.'''
            return "..."
        
        tool = FunctionTool(search_products)
        # or just pass search_products to AgentCore(tools=[search_products])
    """
    def __init__(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None):
        self.func = func
        self.name = name or getattr(func, "__name__", "name")
        self.description = description or (func.__doc__ or "No description provided.").strip()

    async def run(self, input: Any) -> Any:
        import inspect
        if isinstance(input, dict):
            # Many models (Gemini, Ollama/Qwen) wrap arguments in a 'kwargs' object
            # or 'parameters' object. We unwrap it here for direct function application.
            if "kwargs" in input and len(input) == 1:
                input = input["kwargs"]
            elif "parameters" in input and len(input) == 1:
                input = input["parameters"]
                
            res = self.func(**input)
        else:
            res = self.func(input)
            
        if inspect.iscoroutine(res):
            return await res
        return res

    def to_langchain_tool(self):
        """Convert this FunctionTool to a LangChain StructuredTool for native function calling."""
        from langchain_core.tools import StructuredTool
        return StructuredTool.from_function(
            func=self.func,
            name=self.name,
            description=self.description
        )
