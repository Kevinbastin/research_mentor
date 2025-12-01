"""Type definitions for LLM interactions."""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Union, List, Dict
from enum import Enum


class Role(str, Enum):
    """Message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A chat message."""
    role: Role
    content: Union[str, List[Any]]
    name: Optional[str] = None  # For tool messages
    tool_call_id: Optional[str] = None  # For tool responses
    tool_calls: Optional[list["ToolCall"]] = None  # For assistant messages with tool calls

    def to_dict(self) -> dict:
        """Convert to OpenAI message format."""
        msg: dict[str, Any] = {"role": self.role.value, "content": self.content}
        if self.name:
            msg["name"] = self.name
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            msg["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        return msg

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(cls, content: str, tool_calls: Optional[list["ToolCall"]] = None) -> "Message":
        return cls(role=Role.ASSISTANT, content=content, tool_calls=tool_calls)

    @classmethod
    def tool(cls, content: str, tool_call_id: str, name: str) -> "Message":
        return cls(role=Role.TOOL, content=content, tool_call_id=tool_call_id, name=name)


@dataclass
class ToolCall:
    """A tool call from the assistant."""
    id: str
    name: str
    arguments: dict[str, Any]

    def to_dict(self) -> dict:
        """Convert to OpenAI tool call format."""
        import json
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments)
            }
        }

    @classmethod
    def from_openai(cls, tool_call: Any) -> "ToolCall":
        """Create from OpenAI response tool call."""
        import json
        return cls(
            id=tool_call.id,
            name=tool_call.function.name,
            arguments=json.loads(tool_call.function.arguments or "{}")
        )


@dataclass
class ToolResult:
    """Result of a tool execution."""
    tool_call_id: str
    name: str
    content: str
    success: bool = True

    def to_message(self) -> Message:
        """Convert to a tool message."""
        return Message.tool(content=self.content, tool_call_id=self.tool_call_id, name=self.name)


@dataclass
class ToolDefinition:
    """Definition of a tool for the LLM."""
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_openai_tool(self) -> dict:
        """Convert to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or {"type": "object", "properties": {}}
            }
        }


@dataclass
class StreamChunk:
    """A chunk from streaming response."""
    content: Optional[str] = None
    reasoning: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    finish_reason: Optional[str] = None
    # Tool execution status (for streaming with tools)
    tool_status: Optional[str] = None  # "calling", "executing", "completed"
    tool_name: Optional[str] = None
    tool_result: Optional[str] = None
