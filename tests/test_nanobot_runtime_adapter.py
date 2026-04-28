from agent.memory.models import EngineeringExperienceSeed
from agent.memory.store import AgentMemoryStore
from agent.planner import format_chassis_plan, plan_chassis_task, suggest_chassis_tuning
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
    registry.register(
        name="suggest_chassis_tuning",
        description="suggest chassis tuning",
        params_schema={
            "type": "object",
            "properties": {"complaint": {"type": "string"}},
            "required": ["complaint"],
        },
        callback=lambda complaint, objective=None, condition_name=None: format_chassis_plan(
            suggest_chassis_tuning(
                complaint=complaint,
                objective=objective,
                condition_name=condition_name,
            )
        ),
        category="knowledge",
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
    def hidden_internal_action():
        counters["hidden_internal_action"] = (
            counters.get("hidden_internal_action", 0) + 1
        )
        return "hidden"

    registry.register(
        name="hidden_internal_action",
        description="hidden",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=hidden_internal_action,
        category="internal",
        risk_level="low",
        exposed=False,
        side_effects=False,
    )

    def medium_action():
        counters["medium_action"] = counters.get("medium_action", 0) + 1
        return "medium action executed"

    registry.register(
        name="medium_action",
        description="medium",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=medium_action,
        category="test",
        risk_level="medium",
        exposed=True,
        side_effects=False,
    )

    def low_side_effect():
        counters["low_side_effect"] = counters.get("low_side_effect", 0) + 1
        return "low side effect executed"

    registry.register(
        name="low_side_effect",
        description="low side effect",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=low_side_effect,
        category="test",
        risk_level="low",
        exposed=True,
        side_effects=True,
    )
    memory = NanobotMemoryBridge(AgentMemoryStore(base_dir=str(tmp_path)))
    return NanobotRuntimeAdapter(registry, memory), counters


def test_runtime_exports_registry_tools_with_metadata(tmp_path):
    runtime, _ = _build_runtime(tmp_path)

    tools = runtime.export_nanobot_tools()
    names = [tool["name"] for tool in tools]
    spring_tool = next(tool for tool in tools if tool["name"] == "set_spring")

    assert names == [
        "get_current_setup",
        "plan_chassis_task",
        "suggest_chassis_tuning",
        "set_spring",
        "medium_action",
        "low_side_effect",
    ]
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
    decision = result.metadata["policy_decision"]
    assert decision["confirmation_id"]
    assert decision["params_digest"]
    assert decision["plan_match"]["matched"] is False
    assert counters.get("set_spring", 0) == 0


def test_runtime_rejects_hidden_action_even_when_named_directly(tmp_path):
    runtime, counters = _build_runtime(tmp_path)

    result = runtime.call_tool("hidden_internal_action")

    assert result.status == "error"
    assert result.metadata["policy_decision"]["reason"] == "action_not_exposed"
    assert counters.get("hidden_internal_action", 0) == 0


def test_runtime_rejects_confirmed_high_risk_action_without_confirmation_id(tmp_path):
    runtime, counters = _build_runtime(tmp_path)

    result = runtime.call_tool(
        "set_spring",
        {"position": "front", "spring_name": "K1"},
        confirmed=True,
    )

    assert result.status == "error"
    assert result.metadata["policy_decision"]["reason"] == "missing_confirmation_id"
    assert counters.get("set_spring", 0) == 0


def test_runtime_rejects_wrong_confirmation_id(tmp_path):
    runtime, counters = _build_runtime(tmp_path)

    runtime.call_tool("set_spring", {"position": "front", "spring_name": "K1"})
    result = runtime.call_tool(
        "set_spring",
        {"position": "front", "spring_name": "K1"},
        confirmed=True,
        confirmation_id="wrong-id",
    )

    assert result.status == "error"
    assert result.metadata["policy_decision"]["reason"] == "invalid_confirmation_id"
    assert counters.get("set_spring", 0) == 0


def test_runtime_rejects_confirmation_when_params_change(tmp_path):
    runtime, counters = _build_runtime(tmp_path)

    requested = runtime.call_tool(
        "set_spring",
        {"position": "front", "spring_name": "K1"},
    )
    confirmation_id = requested.metadata["policy_decision"]["confirmation_id"]
    result = runtime.call_tool(
        "set_spring",
        {"position": "front", "spring_name": "K2"},
        confirmed=True,
        confirmation_id=confirmation_id,
    )

    assert result.status == "error"
    assert result.metadata["policy_decision"]["reason"] == "params_digest_mismatch"
    assert counters.get("set_spring", 0) == 0


def test_runtime_confirmed_high_risk_action_with_matching_id_writes_experience(tmp_path):
    runtime, counters = _build_runtime(tmp_path)

    requested = runtime.call_tool(
        "set_spring",
        {"position": "front", "spring_name": "K1", "condition_name": "lane_change"},
    )
    confirmation_id = requested.metadata["policy_decision"]["confirmation_id"]
    result = runtime.call_tool(
        "set_spring",
        {"position": "front", "spring_name": "K1", "condition_name": "lane_change"},
        confirmed=True,
        confirmation_id=confirmation_id,
    )
    seeds = runtime.memory.recall_experiences(action_name="set_spring")

    assert result.status == "executed"
    assert counters["set_spring"] == 1
    assert seeds[-1]["condition_name"] == "lane_change"
    assert seeds[-1]["risk_level"] == "high"


def test_runtime_requires_confirmation_for_medium_and_low_side_effect_actions(tmp_path):
    runtime, counters = _build_runtime(tmp_path)

    medium_result = runtime.call_tool("medium_action")
    low_side_effect_result = runtime.call_tool("low_side_effect")

    assert medium_result.status == "requires_confirmation"
    assert low_side_effect_result.status == "requires_confirmation"
    assert counters.get("medium_action", 0) == 0
    assert counters.get("low_side_effect", 0) == 0


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


def test_runtime_routes_suggest_goal_to_knowledge_tool(tmp_path):
    runtime, counters = _build_runtime(tmp_path)

    turn = runtime.handle_user_goal("suggest a fix for lane change roll")

    assert turn.selected_tool == "suggest_chassis_tuning"
    assert turn.tool_result.status == "executed"
    assert runtime.recent_plan_context["kind"] == "chassis_tuning_suggestion"
    assert counters.get("set_spring", 0) == 0


def test_runtime_exports_knowledge_layer(tmp_path):
    runtime, _ = _build_runtime(tmp_path)
    runtime.memory.store.append_experience_seed(EngineeringExperienceSeed(
        action_name="set_antiroll_bar",
        params={"position": "rear"},
        result="roll improved",
        lesson="rear bar helped lane change",
        condition_name="lane_change",
    ))

    layers = runtime.memory.export_layers()

    assert layers["knowledge"][-1]["action_name"] == "set_antiroll_bar"
    assert layers["knowledge"][-1]["condition_name"] == "lane_change"
