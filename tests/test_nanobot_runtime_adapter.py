from agent.memory.store import AgentMemoryStore
from agent.planner import format_chassis_plan, plan_chassis_task
from agent.registry import ActionRegistry
from agent.runtime import NanobotMemoryBridge, NanobotRuntimeAdapter


def _build_runtime(tmp_path, counters=None):
    counters = counters if counters is not None else {}
    registry = ActionRegistry()
    registry.register(
        name="get_current_setup",
        description="query setup",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda: "current setup: demo",
        category="query",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
    registry.register(
        name="plan_chassis_task",
        description="plan chassis task",
        params_schema={
            "type": "object",
            "properties": {"goal": {"type": "string"}},
            "required": ["goal"],
        },
        callback=lambda goal, condition_name=None: format_chassis_plan(
            plan_chassis_task(goal=goal, condition_name=condition_name)
        ),
        category="planning",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )

    def set_spring(position, spring_name, condition_name=None):
        counters["set_spring"] = counters.get("set_spring", 0) + 1
        return f"spring {position}={spring_name}"

    registry.register(
        name="set_spring",
        description="set spring",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=set_spring,
        category="tuning",
        risk_level="high",
        exposed=True,
        side_effects=True,
    )
    registry.register(
        name="hidden_internal_action",
        description="hidden",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda: "hidden",
        category="internal",
        risk_level="low",
        exposed=False,
        side_effects=False,
    )
    memory = NanobotMemoryBridge(AgentMemoryStore(base_dir=str(tmp_path)))
    return NanobotRuntimeAdapter(registry, memory), counters


def test_runtime_exports_registry_tools_with_metadata(tmp_path):
    runtime, _ = _build_runtime(tmp_path)

    tools = runtime.export_nanobot_tools()
    names = [tool["name"] for tool in tools]
    spring_tool = next(tool for tool in tools if tool["name"] == "set_spring")

    assert names == ["get_current_setup", "plan_chassis_task", "set_spring"]
    assert spring_tool["metadata"]["risk_level"] == "high"
    assert spring_tool["metadata"]["side_effects"] is True
    assert "input_schema" in spring_tool


def test_runtime_executes_readonly_query_and_records_history(tmp_path):
    runtime, _ = _build_runtime(tmp_path)

    result = runtime.call_tool("get_current_setup")
    layers = runtime.memory.export_layers()

    assert result.status == "executed"
    assert result.output == "current setup: demo"
    assert any(item["event_type"] == "runtime_tool_call" for item in layers["history"])
    assert any(item["event_type"] == "runtime_tool_result" for item in layers["history"])


def test_runtime_requires_confirmation_for_high_risk_action(tmp_path):
    runtime, counters = _build_runtime(tmp_path)

    result = runtime.call_tool(
        "set_spring",
        {"position": "front", "spring_name": "K1"},
    )

    assert result.status == "requires_confirmation"
    assert result.requires_confirmation is True
    assert "Action is not matched to the latest plan" in result.confirmation_summary
    assert counters.get("set_spring", 0) == 0


def test_runtime_confirmed_high_risk_action_writes_experience(tmp_path):
    runtime, counters = _build_runtime(tmp_path)

    result = runtime.call_tool(
        "set_spring",
        {"position": "front", "spring_name": "K1", "condition_name": "lane_change"},
        confirmed=True,
    )
    seeds = runtime.memory.recall_experiences(action_name="set_spring")

    assert result.status == "executed"
    assert counters["set_spring"] == 1
    assert seeds[-1]["condition_name"] == "lane_change"
    assert seeds[-1]["risk_level"] == "high"


def test_runtime_routes_complex_goal_to_planning_before_write_action(tmp_path):
    runtime, counters = _build_runtime(tmp_path)

    turn = runtime.handle_user_goal("lane change roll tuning", condition_name="lane_change")
    layers = runtime.memory.export_layers()

    assert turn.selected_tool == "plan_chassis_task"
    assert turn.tool_result.status == "executed"
    assert runtime.recent_plan_context["plan_id"].startswith("plan_")
    assert counters.get("set_spring", 0) == 0
    assert any(item["event_type"] == "runtime_session_message" for item in layers["session"])
    assert any(
        item["event_type"] == "runtime_plan_context_saved"
        for item in layers["history"]
    )
