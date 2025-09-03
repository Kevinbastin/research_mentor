from __future__ import annotations

"""
Tool registry scaffolding.

WS1 goal: provide a minimal API for registering and fetching tools without
altering existing code paths. Auto-discovery will be added later.
"""

from typing import Dict, Optional


class ToolBase:
    """Minimal base class placeholder (WS2 will expand)."""

    name: str = "tool"

    def execute(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise NotImplementedError


_registry: Dict[str, ToolBase] = {}


def register_tool(tool: ToolBase) -> None:
    _registry[tool.name] = tool


def get_tool(name: str) -> Optional[ToolBase]:
    return _registry.get(name)


def list_tools() -> Dict[str, ToolBase]:
    return dict(_registry)
