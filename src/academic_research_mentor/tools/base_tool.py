from __future__ import annotations

"""
Base tool interface scaffolding (kept very small for WS1).

WS2 will extend with metadata, can_handle, initialize, cleanup, etc.
"""

from typing import Any, Dict, Optional


class BaseTool:
    name: str = "tool"

    def execute(self, inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError
