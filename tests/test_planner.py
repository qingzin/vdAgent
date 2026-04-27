from agent.actions import knowledge_actions, planning_actions
from agent.planner import format_chassis_plan, plan_chassis_task, suggest_chassis_tuning
from agent.registry import ActionRegistry


def test_plan_chassis_task_for_lane_change_roll():
    plan = plan_chassis_task(goal="单移线侧倾大，需要改善", condition_name="单移线")

    assert plan["kind"] == "chassis_task_plan"
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
