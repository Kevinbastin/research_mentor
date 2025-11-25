"""Tool definitions and registry for the agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from academic_research_mentor.llm.types import ToolDefinition, ToolResult


class Tool(ABC):
    """Base class for tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for the LLM."""
        pass
    
    @property
    def parameters(self) -> dict[str, Any]:
        """JSON schema for tool parameters."""
        return {"type": "object", "properties": {}}
    
    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """Execute the tool and return result as string."""
        pass
    
    def to_definition(self) -> ToolDefinition:
        """Convert to ToolDefinition."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters
        )


@dataclass
class FunctionTool(Tool):
    """A tool backed by a simple function."""
    _name: str
    _description: str
    _function: Callable[..., str]
    _parameters: dict[str, Any] = field(default_factory=dict)
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters
    
    def execute(self, **kwargs: Any) -> str:
        return self._function(**kwargs)


class ToolRegistry:
    """Registry of available tools."""
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def register_function(
        self,
        name: str,
        description: str,
        function: Callable[..., str],
        parameters: Optional[dict[str, Any]] = None
    ) -> None:
        """Register a function as a tool."""
        self._tools[name] = FunctionTool(
            _name=name,
            _description=description,
            _function=function,
            _parameters=parameters or {"type": "object", "properties": {}}
        )
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_definitions(self) -> list[ToolDefinition]:
        """Get all tool definitions."""
        return [tool.to_definition() for tool in self._tools.values()]
    
    def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool and return the result."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                tool_call_id="",
                name=name,
                content=f"Error: Unknown tool '{name}'",
                success=False
            )
        
        try:
            result = tool.execute(**kwargs)
            return ToolResult(
                tool_call_id="",
                name=name,
                content=result,
                success=True
            )
        except Exception as e:
            return ToolResult(
                tool_call_id="",
                name=name,
                content=f"Error executing tool: {e}",
                success=False
            )
    
    @property
    def tools(self) -> list[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def __len__(self) -> int:
        return len(self._tools)
