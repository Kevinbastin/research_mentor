from __future__ import annotations

from typing import Any, Dict, Optional

from ...base_tool import BaseTool
from ....mentor_tools import arxiv_search as legacy_arxiv_search


class ArxivSearchTool(BaseTool):
    name = "legacy_arxiv_search"
    version = "0.1"

    def can_handle(self, task_context: Optional[Dict[str, Any]] = None) -> bool:  # type: ignore[override]
        tc = (task_context or {}).get("goal", "")
        return any(k in str(tc).lower() for k in ("arxiv", "paper", "literature"))

    def get_metadata(self) -> Dict[str, Any]:  # type: ignore[override]
        meta = super().get_metadata()
        meta["identity"]["owner"] = "legacy"
        meta["capabilities"] = {"task_types": ["literature_search"], "domains": ["cs", "ml"]}
        meta["io"] = {
            "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            "output_schema": {"type": "object", "properties": {"papers": {"type": "array"}}},
        }
        meta["operational"] = {"cost_estimate": "low", "latency_profile": "low", "rate_limits": None}
        meta["usage"] = {"ideal_inputs": ["concise topic"], "anti_patterns": [], "prerequisites": []}
        return meta

    def execute(self, inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:  # type: ignore[override]
        q = str(inputs.get("query", "")).strip()
        if not q:
            return {"papers": [], "note": "empty query"}
        return legacy_arxiv_search(query=q, from_year=None, limit=int(inputs.get("limit", 10)))
