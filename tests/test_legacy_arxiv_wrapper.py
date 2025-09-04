from __future__ import annotations

from academic_research_mentor.tools import auto_discover, get_tool


def test_legacy_arxiv_tool_discovered_and_runs() -> None:
    auto_discover()
    t = get_tool("legacy_arxiv_search")
    assert t is not None
    out = t.execute({"query": "diffusion models", "limit": 1})
    assert isinstance(out, dict)
    assert "papers" in out
