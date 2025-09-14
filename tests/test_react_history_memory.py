from __future__ import annotations

import types
import sys


class _StubMsg:
    def __init__(self, content: str) -> None:
        self.content = content
        self.text = content


class _DummyExecutor:
    def __init__(self) -> None:
        self.last_messages = []

    def invoke(self, payload: dict) -> dict:
        self.last_messages = payload.get("messages", [])
        msgs = list(self.last_messages) + [_StubMsg(content="AI reply")]
        return {"messages": msgs}


def _install_langchain_core_stubs(monkeypatch) -> None:
    lc = types.ModuleType("langchain_core")
    messages = types.ModuleType("langchain_core.messages")
    messages.SystemMessage = _StubMsg
    messages.HumanMessage = _StubMsg
    messages.AIMessage = _StubMsg
    lc.messages = messages
    monkeypatch.setitem(sys.modules, "langchain_core", lc)
    monkeypatch.setitem(sys.modules, "langchain_core.messages", messages)


def _install_langgraph_prebuilt_stub(monkeypatch, executor: _DummyExecutor) -> None:
    lg = types.ModuleType("langgraph")
    prebuilt = types.ModuleType("langgraph.prebuilt")

    def create_react_agent(llm, tools):  # noqa: ARG001
        return executor

    prebuilt.create_react_agent = create_react_agent
    lg.prebuilt = prebuilt
    monkeypatch.setitem(sys.modules, "langgraph", lg)
    monkeypatch.setitem(sys.modules, "langgraph.prebuilt", prebuilt)


def test_react_history_includes_prior_turn(monkeypatch):
    from importlib import reload

    exec_stub = _DummyExecutor()
    _install_langchain_core_stubs(monkeypatch)
    _install_langgraph_prebuilt_stub(monkeypatch, exec_stub)
    monkeypatch.setenv("ARM_HISTORY_ENABLED", "true")
    monkeypatch.setenv("ARM_MAX_HISTORY_MESSAGES", "10")

    # Import after stubs installed
    from academic_research_mentor.runtime.agents import react_agent as react_mod
    reload(react_mod)
    Agent = react_mod.LangChainReActAgentWrapper

    agent = Agent(llm=object(), system_instructions="SYS", tools=[])

    # First turn
    agent.print_response("First")
    assert hasattr(agent, "_history")
    assert len(agent._history) == 2  # Human, AI

    # Second turn should include prior Human/AI in messages passed to executor
    agent.print_response("Second")
    msgs = exec_stub.last_messages
    # Expect: System + (Human, AI) + Human
    assert len(msgs) == 4
    assert isinstance(msgs[0], _StubMsg) and msgs[0].content == "SYS"
    assert isinstance(msgs[1], _StubMsg) and msgs[1].content == "First"
    assert isinstance(msgs[2], _StubMsg) and isinstance(msgs[2].content, str)
    assert isinstance(msgs[3], _StubMsg) and msgs[3].content == "Second"


def test_react_history_respects_window_limit(monkeypatch):
    from importlib import reload

    exec_stub = _DummyExecutor()
    _install_langchain_core_stubs(monkeypatch)
    _install_langgraph_prebuilt_stub(monkeypatch, exec_stub)
    monkeypatch.setenv("ARM_HISTORY_ENABLED", "true")
    monkeypatch.setenv("ARM_MAX_HISTORY_MESSAGES", "2")

    from academic_research_mentor.runtime.agents import react_agent as react_mod
    reload(react_mod)
    Agent = react_mod.LangChainReActAgentWrapper

    agent = Agent(llm=object(), system_instructions="SYS", tools=[])

    # Create three turns; window is 2 messages (1 Human + 1 AI)
    agent.print_response("T1")
    agent.print_response("T2")
    agent.print_response("T3")

    # On the last call, messages should be: System + last 2 from history + current Human
    msgs = exec_stub.last_messages
    assert len(msgs) == 1 + 2 + 1
    # The 2 history messages should correspond to T2 Human/AI, not T1
    contents = [m.content for m in msgs]
    assert "T1" not in contents
    assert "T2" in contents
    assert contents[-1] == "T3"


