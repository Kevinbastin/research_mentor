"""LLM module - Direct OpenAI SDK integration."""

from .client import LLMClient, create_client
from .types import Message, ToolCall, ToolResult, Role

__all__ = ["LLMClient", "create_client", "Message", "ToolCall", "ToolResult", "Role"]
