"""OpenAI SDK client wrapper - works with OpenAI, OpenRouter, and compatible APIs."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

from openai import AsyncOpenAI, OpenAI

from .types import Message, ToolCall, ToolDefinition, StreamChunk


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-4o"
    max_tokens: int = 512  # reduced for free tier limits
    temperature: float = 0.7


class LLMClient:
    """LLM client using OpenAI SDK - works with OpenRouter and other compatible APIs."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        self._async_client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)

    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        **kwargs: Any
    ) -> tuple[Message, Optional[list[ToolCall]]]:
        """Synchronous chat completion."""
        openai_messages = [m.to_dict() for m in messages]
        openai_tools = [t.to_openai_tool() for t in tools] if tools else None

        max_tokens = kwargs.pop("max_tokens", self.config.max_tokens)
        temperature = kwargs.pop("temperature", self.config.temperature)

        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=openai_messages,
            tools=openai_tools,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = None

        if choice.message.tool_calls:
            tool_calls = [ToolCall.from_openai(tc) for tc in choice.message.tool_calls]

        return Message.assistant(content, tool_calls), tool_calls

    async def chat_async(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        **kwargs: Any
    ) -> tuple[Message, Optional[list[ToolCall]]]:
        """Asynchronous chat completion."""
        openai_messages = [m.to_dict() for m in messages]
        openai_tools = [t.to_openai_tool() for t in tools] if tools else None

        max_tokens = kwargs.pop("max_tokens", self.config.max_tokens)
        temperature = kwargs.pop("temperature", self.config.temperature)

        response = await self._async_client.chat.completions.create(
            model=self.config.model,
            messages=openai_messages,
            tools=openai_tools,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = None

        if choice.message.tool_calls:
            tool_calls = [ToolCall.from_openai(tc) for tc in choice.message.tool_calls]

        return Message.assistant(content, tool_calls), tool_calls

    async def stream_async(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        include_reasoning: bool = False,
        **kwargs: Any
    ) -> AsyncIterator[StreamChunk]:
        """Asynchronous streaming chat completion."""
        openai_messages = [m.to_dict() for m in messages]
        openai_tools = [t.to_openai_tool() for t in tools] if tools else None

        # Build extra body for OpenRouter reasoning support
        # Skip for Ollama/local providers that don't support it
        extra_body = kwargs.pop("extra_body", {})
        is_local = "localhost" in (self.config.base_url or "") or "host.docker.internal" in (self.config.base_url or "")
        if include_reasoning and not is_local:
            # OpenRouter / compatible providers use include_reasoning
            extra_body["include_reasoning"] = True
            # Nudge toward concise but meaningful scratchpad (effort only; max_tokens not allowed together)
            extra_body.setdefault("reasoning", {"effort": "medium"})

        stream = await self._async_client.chat.completions.create(
            model=self.config.model,
            messages=openai_messages,
            tools=openai_tools,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            stream=True,
            extra_body=extra_body if extra_body else None,
            **kwargs
        )

        async for chunk in stream:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            # Extract reasoning if available (OpenRouter)
            reasoning = None
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                reasoning = delta.reasoning_content
            elif hasattr(delta, "model_extra") and delta.model_extra:
                reasoning = delta.model_extra.get("reasoning_content")

            # Extract content
            content = delta.content if delta.content else None

            # Handle structured content (list format from some providers)
            if isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        texts.append(block)
                content = "".join(texts) if texts else None

            yield StreamChunk(
                content=content,
                reasoning=reasoning,
                finish_reason=choice.finish_reason
            )


def create_client(
    provider: str = "openrouter",
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> LLMClient:
    """Create an LLM client for the specified provider.
    
    Providers:
    - openrouter: Uses OpenRouter API (default)
    - openai: Uses OpenAI API directly
    - gemini: Uses Google Gemini API (free tier available)
    - ollama: Uses local Ollama server
    """
    if provider == "openrouter":
        key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY not set")
        return LLMClient(LLMConfig(
            api_key=key,
            base_url="https://openrouter.ai/api/v1",
            model=model or os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free"),
            max_tokens=512  # keep low for free tier
        ))
    elif provider == "openai":
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not set")
        return LLMClient(LLMConfig(
            api_key=key,
            model=model or "gpt-4o"
        ))
    elif provider == "gemini":
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY not set")
        return LLMClient(LLMConfig(
            api_key=key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            model=model or "gemini-2.0-flash",
            max_tokens=1024
        ))
    elif provider == "ollama":
        return LLMClient(LLMConfig(
            api_key="ollama",
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            model=model or os.environ.get("OLLAMA_MODEL", "qwen2.5:14b"),
            max_tokens=2048
        ))
    else:
        raise ValueError(f"Unknown provider: {provider}")
