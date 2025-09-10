from __future__ import annotations


def test_guidelines_default_dynamic_mode(monkeypatch):
    # Ensure default (no env) yields dynamic mode and avoids loader usage
    import os
    os.environ.pop('ARM_GUIDELINES_MODE', None)

    from academic_research_mentor.guidelines_engine import create_guidelines_injector
    inj = create_guidelines_injector()

    # Dynamic mode should not crash without JSON and should not inject a large section
    base = "You are a mentor."
    out = inj.inject_guidelines(base)
    assert "You are a mentor." in out
    # Should contain the small hint to prefer the tool
    assert "research_guidelines tool" in out
