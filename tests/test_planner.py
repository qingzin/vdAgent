from unittest.mock import patch

from agent.actions import knowledge_actions, planning_actions
from agent.planner import format_chassis_plan, plan_chassis_task, suggest_chassis_tuning
from agent.registry import ActionRegistry


def test_plan_schema_includes_next_action_and_allowed_actions():
    plan = plan_chassis_task(goal="prepare record data", condition_name="recording")
    next_action = plan["next_action"]

    assert plan["current_step_id"] == next_action["step_id"]
    assert {
        "action_name",
        "step_id",
        "description",
        "params_needed",
        "risk_level",
        "validation",
    }.issubset(next_action)
    assert next_action["action_name"] == "prepare_test_scene"
    assert "prepare_test_scene" in plan["allowed_actions"]
    assert "prepare_recording_session" in plan["allowed_actions"]
    assert "start_recording" in plan["allowed_actions"]
    assert {"prepare_recording_session", "start_recording"}.issubset(
        plan["steps"][1]["allowed_actions"]
    )


def test_plan_chassis_task_for_lane_change_roll():
    plan = plan_chassis_task(goal="单移线侧倾大，需要改善", condition_name="单移线")

    assert plan["kind"] == "chassis_task_plan"
    assert plan["plan_id"].startswith("plan_")
    assert plan["goal"]
    assert plan["condition_name"]
    assert plan["steps"]
    assert plan["validation_metrics"]
    assert plan["required_confirmation"]
    assert {
        "action_name",
        "description",
        "params_needed",
        "risk_level",
        "preconditions",
        "validation",
    }.issubset(plan["steps"][0])
    assert any("稳定杆" in item for item in plan["parameter_direction"])
    assert any("侧倾角" in item for item in plan["validation_metrics"])


def test_suggest_chassis_tuning_for_steering_center_heavy():
    suggestion = suggest_chassis_tuning(
        complaint="方向盘中心区重",
        objective="减轻中心区手感",
        condition_name="中心区",
    )

    assert suggestion["kind"] == "chassis_tuning_suggestion"
    assert any("friction" in item or "overall" in item for item in suggestion["parameter_direction"])
    assert any("方向盘" in item for item in suggestion["validation_metrics"])


def test_format_chassis_plan_returns_readable_markdown():
    plan = plan_chassis_task(goal="单移线侧倾大，需要改善", condition_name="单移线")

    text = format_chassis_plan(plan)

    assert text.startswith("## 底盘任务规划")
    assert "### 建议步骤" in text
    assert "1. " in text
    assert "{'" not in text


def test_format_chassis_plan_includes_recent_experience_reference():
    plan = plan_chassis_task(goal="单移线侧倾大，需要改善", condition_name="单移线")
    plan["recent_experiences"] = [{
        "action_name": "set_antiroll_bar",
        "condition_name": "单移线",
        "result": "已选择后轮稳定杆: demo_bar",
    }]

    text = format_chassis_plan(plan)

    assert "### 近期经验参考" in text
    assert "set_antiroll_bar" in text
    assert "demo_bar" in text


def test_planning_and_knowledge_actions_return_readable_text():
    registry = ActionRegistry()
    planning_actions.register(registry, ctx=None)
    knowledge_actions.register(registry, ctx=None)

    plan_text = registry.execute(
        "plan_chassis_task",
        {"goal": "单移线侧倾大，需要改善", "condition_name": "单移线"},
    )
    suggestion_text = registry.execute(
        "suggest_chassis_tuning",
        {"complaint": "方向盘中心区重", "condition_name": "中心区"},
    )

    assert plan_text.startswith("## 底盘任务规划")
    assert suggestion_text.startswith("## 底盘调校建议")
    assert "{'" not in plan_text
    assert "{'" not in suggestion_text
    assert registry.get_metadata("plan_chassis_task")["side_effects"] is False


def test_planning_and_knowledge_actions_work_with_empty_memory():
    class EmptyMemoryStore:
        def rank_experience_seeds(self, **kwargs):
            return []

    registry = ActionRegistry()
    planning_actions.register(registry, ctx=None)
    knowledge_actions.register(registry, ctx=None)

    with patch.object(planning_actions, "AgentMemoryStore", EmptyMemoryStore):
        plan_text = registry.execute(
            "plan_chassis_task",
            {"goal": "lane change roll tuning"},
        )
    with patch.object(knowledge_actions, "AgentMemoryStore", EmptyMemoryStore):
        suggestion_text = registry.execute(
            "suggest_chassis_tuning",
            {"complaint": "center steering heavy"},
        )

    assert plan_text.startswith("## ")
    assert suggestion_text.startswith("## ")


def test_planning_and_knowledge_actions_work_when_memory_unavailable():
    registry = ActionRegistry()
    planning_actions.register(registry, ctx=None)
    knowledge_actions.register(registry, ctx=None)

    with patch.object(planning_actions, "AgentMemoryStore", side_effect=OSError("readonly")):
        plan_text = registry.execute(
            "plan_chassis_task",
            {"goal": "lane change roll tuning"},
        )
    with patch.object(knowledge_actions, "AgentMemoryStore", side_effect=OSError("readonly")):
        suggestion_text = registry.execute(
            "suggest_chassis_tuning",
            {"complaint": "center steering heavy"},
        )

    assert plan_text.startswith("## ")
    assert suggestion_text.startswith("## ")
