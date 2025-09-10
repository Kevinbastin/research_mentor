from __future__ import annotations

from typing import Any, Dict, Optional


def test_execute_task_records_transparency_run(monkeypatch):
    from academic_research_mentor.tools.base_tool import BaseTool
    from academic_research_mentor.core.transparency import get_transparency_store
    import academic_research_mentor.core.orchestrator as orch_mod

    store = get_transparency_store()
    before = len(store.list_runs())

    class FakeTool(BaseTool):
        name = "fake_tool"
        version = "0.1"

        def can_handle(self, task_context: Optional[Dict[str, Any]] = None) -> bool:  # type: ignore[override]
            return True

        def execute(self, inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:  # type: ignore[override]
            return {"results": [{"title": "ok", "url": "http://example.com/ok"}]}

    orch_mod.list_tools = lambda: {"fake_tool": FakeTool()}  # type: ignore[assignment]

    orch = orch_mod.Orchestrator()
    out = orch.execute_task("literature_search", inputs={"query": "test"}, context={"goal": "test"})
    assert out["execution"]["executed"] is True

    after = len(store.list_runs())
    assert after >= before + 1
    assert any(r.tool_name == "fake_tool" for r in store.list_runs())
