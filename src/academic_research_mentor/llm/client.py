"""LLM client — talks directly to the Ollama Docker container (ollama/ollama:latest).

No external SDK needed. Uses Ollama's native /api/chat REST endpoint via urllib.
Model: qwen2.5:14b  |  100% FREE, 100% local.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

from .types import Message, ToolCall, ToolDefinition, StreamChunk


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:14b"
    max_tokens: int = 4096
    temperature: float = 0.7
    # kept for backward compat — ignored for Ollama
    api_key: str = "ollama"


# ---------------------------------------------------------------------------
# Auto-detect Ollama URL
# ---------------------------------------------------------------------------

def _detect_ollama_url() -> str:
    """Find the first reachable Ollama instance (Docker container or local)."""
    candidates = [
        "http://localhost:11434",
        "http://172.17.0.3:11434",
        "http://host.docker.internal:11434",
    ]
    for url in candidates:
        try:
            req = urllib.request.urlopen(f"{url}/api/tags", timeout=2)
            if req.status == 200:
                return url
        except Exception:
            continue
    return "http://localhost:11434"


# ---------------------------------------------------------------------------
# LLMClient — pure urllib, no SDK
# ---------------------------------------------------------------------------

class LLMClient:
    """LLM client that talks to Ollama native /api/chat endpoint.

    Uses only stdlib urllib — no openai SDK, no pip installs needed.
    """

    def __init__(self, config: LLMConfig | None = None):
        if config is None:
            config = LLMConfig(base_url=_detect_ollama_url())
        self.config = config

    # ---- synchronous chat -------------------------------------------------

    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        **kwargs: Any,
    ) -> tuple[Message, Optional[list[ToolCall]]]:
        """Synchronous chat completion via Ollama /api/chat."""
        ollama_messages = []
        for m in messages:
            content = m.content if isinstance(m.content, str) else str(m.content)
            ollama_messages.append({"role": m.role.value, "content": content})

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.config.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot reach Ollama at {self.config.base_url}. "
                f"Make sure the ollama/ollama Docker container is running.\n{e}"
            )

        content = body.get("message", {}).get("content", "")
        return Message.assistant(content), None

    # ---- async chat (thin wrapper) ----------------------------------------

    async def chat_async(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        **kwargs: Any,
    ) -> tuple[Message, Optional[list[ToolCall]]]:
        """Async chat — delegates to sync (Ollama is local, fast enough)."""
        return self.chat(messages, tools, **kwargs)

    # ---- streaming --------------------------------------------------------

    async def stream_async(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        include_reasoning: bool = False,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Streaming chat via Ollama /api/chat with stream=true."""
        ollama_messages = []
        for m in messages:
            content = m.content if isinstance(m.content, str) else str(m.content)
            ollama_messages.append({"role": m.role.value, "content": content})

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.config.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
        )

        try:
            resp = urllib.request.urlopen(req, timeout=120)
        except urllib.error.URLError as e:
            yield StreamChunk(content=f"[Ollama connection error: {e}]", finish_reason="error")
            return

        for raw_line in resp:
            try:
                chunk = json.loads(raw_line.decode())
            except json.JSONDecodeError:
                continue

            text = chunk.get("message", {}).get("content")
            done = chunk.get("done", False)

            if text:
                yield StreamChunk(content=text, finish_reason="stop" if done else None)

            if done:
                return


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> LLMClient:
    """Create an LLM client.

    Always uses the local Ollama Docker container (ollama/ollama:latest)
    with qwen2.5:14b.  No API keys, no .env, no external SDKs.
    """
    ollama_url = _detect_ollama_url()
    return LLMClient(LLMConfig(
        base_url=ollama_url,
        model=model or "qwen2.5:14b",
        max_tokens=4096,
        temperature=0.7,
    ))
