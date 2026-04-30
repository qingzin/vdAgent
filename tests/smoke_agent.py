"""Pytest-free smoke checks for agent planner, executor, and memory fallback."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.actions import knowledge_actions, planning_actions
from agent.executor import AgentExecutor
from agent.memory.store import AgentMemoryStore
from agent.registry import ActionRegistry


class FakeLLMResponse:
    def __init__(self, tool_name=None, tool_params=None, text=None):
        self.has_tool_call = tool_name is not None
        self.tool_name = tool_name
        self.tool_params = tool_params or {}
        self.text = text


class FakeLLMClient:
    """Returns canned text for planning/knowledge actions."""

    def chat(self, messages, system=None, tools=None, temperature=0.3):
        return FakeLLMResponse(text="## CHASSIS PLAN\n\n- goal: test\n\n### steps\n1. test")


class FakeCtx:
    def __init__(self):
        self.llm_client = FakeLLMClient()
        self.ui = None


def _capture(signal):
    values = []
    signal.connect(lambda *args: values.append(args))
    return values


def smoke_auto_execute_planning_action():
    registry = ActionRegistry()
    planning_actions.register(registry, ctx=FakeCtx())
    with tempfile.TemporaryDirectory() as tmp_dir:
        executor = AgentExecutor(
            registry,
            llm_client=None,
            memory_store=AgentMemoryStore(base_dir=tmp_dir),
        )
        confirmations = _capture(executor.confirm_request)
        responses = _capture(executor.response_ready)

        executor._on_llm_response(FakeLLMResponse(
            "plan_chassis_task",
            {"goal": "单移线侧倾大", "condition_name": "单移线"},
        ))

        assert executor._pending_action is None
        assert confirmations == []
        assert responses and responses[-1][0].startswith("## CHASSIS PLAN")


def smoke_auto_execute_knowledge_action():
    registry = ActionRegistry()
    knowledge_actions.register(registry, ctx=FakeCtx())
    with tempfile.TemporaryDirectory() as tmp_dir:
        executor = AgentExecutor(
            registry,
            llm_client=None,
            memory_store=AgentMemoryStore(base_dir=tmp_dir),
        )
        confirmations = _capture(executor.confirm_request)
        responses = _capture(executor.response_ready)

        executor._on_llm_response(FakeLLMResponse(
            "suggest_chassis_tuning",
            {"complaint": "方向盘中心区重", "condition_name": "中心区"},
        ))

        assert executor._pending_action is None
        assert confirmations == []
        assert responses and responses[-1][0].startswith("## CHASSIS PLAN")


def smoke_planning_with_side_effects_requires_confirmation():
    registry = ActionRegistry()
    registry.register(
        name="unsafe_plan",
        description="unsafe",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda goal: "unsafe",
        category="planning",
        risk_level="low",
        exposed=True,
        side_effects=True,
    )
    executor = AgentExecutor(registry, llm_client=None)
    confirmations = _capture(executor.confirm_request)

    executor._on_llm_response(FakeLLMResponse("unsafe_plan", {"goal": "x"}))

    assert executor._pending_action == ("unsafe_plan", {"goal": "x"})
    assert confirmations and confirmations[-1][0] == "unsafe_plan"


def smoke_memory_fallback():
    with patch("agent.executor.AgentMemoryStore", side_effect=OSError("readonly")):
        executor = AgentExecutor(ActionRegistry(), llm_client=None)
    assert getattr(executor.memory_store, "disabled", False) is True
    executor._write_trace("smoke", "memory disabled")


def smoke_planning_no_llm_graceful():
    """Planning action returns graceful error when LLM is unavailable."""
    registry = ActionRegistry()
    planning_actions.register(registry, ctx=FakeCtx())
    registry2 = ActionRegistry()
    planning_actions.register(registry2, ctx=None)
    result = registry2.execute("plan_chassis_task", {"goal": "test"})
    assert "LLM" in result


if __name__ == "__main__":
    smoke_auto_execute_planning_action()
    smoke_auto_execute_knowledge_action()
    smoke_planning_with_side_effects_requires_confirmation()
    smoke_memory_fallback()
    smoke_planning_no_llm_graceful()
    print("smoke_agent: ok")
