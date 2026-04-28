from unittest.mock import patch

from agent.executor import AgentExecutor
from agent.memory.store import AgentMemoryStore
from agent.planner import plan_chassis_task
from agent.registry import ActionRegistry


class FakeLLMResponse:
    def __init__(self, tool_name=None, tool_params=None, text=None):
        self.has_tool_call = tool_name is not None
        self.tool_name = tool_name
        self.tool_params = tool_params or {}
        self.text = text


def test_confirm_action_writes_trace_and_experience_seed(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="set_spring",
        description="set spring",
        params_schema={
            "type": "object",
            "properties": {
                "position": {"type": "string"},
                "spring_name": {"type": "string"},
            },
            "required": ["position", "spring_name"],
        },
        callback=lambda position, spring_name: f"spring {position}={spring_name}",
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    store = AgentMemoryStore(base_dir=str(tmp_path))
    executor = AgentExecutor(registry, llm_client=None, memory_store=store)
    executor._pending_action = (
        "set_spring",
        {"position": "front", "spring_name": "K1"},
    )

    executor.confirm_action()

    traces = store.query_traces(action_name="set_spring")
    seeds = store.query_experience_seeds(action_name="set_spring")

    assert [t["event_type"] for t in traces] == ["confirm_action", "action_result"]
    assert seeds[-1]["risk_level"] == "high"
    assert seeds[-1]["params"]["spring_name"] == "K1"


def test_confirm_action_experience_seed_includes_plan_context(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="set_spring",
        description="set spring",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda position, spring_name: "ok",
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    store = AgentMemoryStore(base_dir=str(tmp_path))
    executor = AgentExecutor(registry, llm_client=None, memory_store=store)
    executor.recent_plan_context = plan_chassis_task(
        goal="lane change roll tuning",
        condition_name="lane_change",
    )
    executor._pending_action = (
        "set_spring",
        {"position": "front", "spring_name": "K1"},
    )

    executor.confirm_action()

    seed = store.query_experience_seeds(action_name="set_spring")[-1]
    assert seed["plan_id"] == executor.recent_plan_context["plan_id"]
    assert seed["step_id"] == executor.recent_plan_context["current_step_id"]
    assert seed["plan_goal"] == "lane change roll tuning"
    assert seed["next_action"]["step_id"] == executor.recent_plan_context["current_step_id"]


def test_planning_action_auto_executes_without_pending_confirm(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="plan_chassis_task",
        description="plan",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda goal: "## 底盘任务规划\n\n### 建议步骤\n1. 先建立基线",
        category="planning",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
    store = AgentMemoryStore(base_dir=str(tmp_path))
    executor = AgentExecutor(registry, llm_client=None, memory_store=store)
    confirmations = []
    responses = []
    executor.confirm_request.connect(lambda name, params, summary: confirmations.append(name))
    executor.response_ready.connect(responses.append)

    executor._on_llm_response(FakeLLMResponse(
        tool_name="plan_chassis_task",
        tool_params={"goal": "单移线侧倾大"},
    ))

    assert executor._pending_action is None
    assert confirmations == []
    assert responses[-1].startswith("## 底盘任务规划")
    assert executor.history[-1]["content"] == responses[-1]
    assert executor.recent_plan_context["plan_id"].startswith("plan_")
    assert [t["event_type"] for t in store.query_traces(action_name="plan_chassis_task")] == [
        "llm_tool_call",
        "auto_execute_action",
        "action_result",
        "plan_context_saved",
    ]


def test_knowledge_action_auto_executes_without_pending_confirm(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="suggest_chassis_tuning",
        description="suggest",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda complaint: "## 底盘调校建议\n\n### 参数方向\n- 先小步调整",
        category="knowledge",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    confirmations = []
    responses = []
    executor.confirm_request.connect(lambda name, params, summary: confirmations.append(name))
    executor.response_ready.connect(responses.append)

    executor._on_llm_response(FakeLLMResponse(
        tool_name="suggest_chassis_tuning",
        tool_params={"complaint": "方向盘中心区重"},
    ))

    assert executor._pending_action is None
    assert confirmations == []
    assert responses[-1].startswith("## 底盘调校建议")


def test_planning_category_with_side_effects_still_requires_confirmation(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="bad_planning_action",
        description="bad",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda goal: "should require confirmation",
        category="planning",
        risk_level="low",
        exposed=True,
        side_effects=True,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    confirmations = []
    executor.confirm_request.connect(lambda name, params, summary: confirmations.append(name))

    executor._on_llm_response(FakeLLMResponse(
        tool_name="bad_planning_action",
        tool_params={"goal": "unsafe"},
    ))

    assert executor._pending_action == ("bad_planning_action", {"goal": "unsafe"})
    assert confirmations == ["bad_planning_action"]


def test_low_risk_readonly_query_auto_executes(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="get_current_setup",
        description="query setup",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda: "当前车型: demo",
        category="query",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    confirmations = []
    responses = []
    executor.confirm_request.connect(lambda name, params, summary: confirmations.append(name))
    executor.response_ready.connect(responses.append)

    executor._on_llm_response(FakeLLMResponse(tool_name="get_current_setup"))

    assert executor._pending_action is None
    assert confirmations == []
    assert responses[-1] == "当前车型: demo"


def test_operational_action_still_requests_confirmation(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="set_spring",
        description="set spring",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda position, spring_name: "ok",
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    confirmations = []
    executor.confirm_request.connect(lambda name, params, summary: confirmations.append(name))

    executor._on_llm_response(FakeLLMResponse(
        tool_name="set_spring",
        tool_params={"position": "front", "spring_name": "K1"},
    ))

    assert executor._pending_action == ("set_spring", {"position": "front", "spring_name": "K1"})
    assert confirmations == ["set_spring"]


def test_unmatched_high_risk_action_warns_in_confirmation_summary(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="set_spring",
        description="set spring",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda position, spring_name: "ok",
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    summaries = []
    executor.confirm_request.connect(
        lambda name, params, summary: summaries.append(summary)
    )

    executor._on_llm_response(FakeLLMResponse(
        tool_name="set_spring",
        tool_params={"position": "front", "spring_name": "K1"},
    ))

    assert "未匹配近期计划" in summaries[-1]


def test_matched_plan_action_still_requires_confirmation_without_warning(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="set_antiroll_bar",
        description="set antiroll bar",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda position, bar_name: "ok",
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    executor.recent_plan_context = plan_chassis_task(
        goal="lane change roll improvement",
        condition_name="lane change",
    )
    summaries = []
    executor.confirm_request.connect(
        lambda name, params, summary: summaries.append(summary)
    )

    executor._on_llm_response(FakeLLMResponse(
        tool_name="set_antiroll_bar",
        tool_params={"position": "rear", "bar_name": "bar_a"},
    ))

    assert executor._pending_action == (
        "set_antiroll_bar",
        {"position": "rear", "bar_name": "bar_a"},
    )
    assert "未匹配近期计划" not in summaries[-1]


def test_memory_initialization_failure_does_not_block_executor():
    registry = ActionRegistry()

    with patch("agent.executor.AgentMemoryStore", side_effect=OSError("readonly")):
        executor = AgentExecutor(registry, llm_client=None)

    assert getattr(executor.memory_store, "disabled", False) is True
    executor._write_trace("smoke", "memory disabled")
