from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    function: Callable


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        function: Callable,
    ):
        self._tools[name] = Tool(
            name=name,
            description=description,
            parameters=parameters,
            function=function,
        )

    def get_all(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)

    async def execute(self, name: str, arguments: dict) -> str:
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found"
        try:
            result = await tool.function(**arguments)
            return str(result)
        except Exception as e:
            return f"Error executing tool '{name}': {e}"


def tool(name: str, description: str, parameters: dict):
    """Decorator to register a function as a tool in the global registry."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        global_registry.register(name, description, parameters, wrapper)
        return wrapper
    return decorator


global_registry = ToolRegistry()
