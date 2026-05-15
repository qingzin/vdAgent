"""Tests for LLM-driven planner prompt builders and action registration."""

from unittest.mock import patch, MagicMock

from agent.planner import (
    PLAN_SYSTEM_PROMPT,
    build_chassis_plan_prompt,
    build_tuning_suggestion_prompt,
    build_planning_prompt,
)
from agent.actions import knowledge_actions, planning_actions
from agent.registry import ActionRegistry


# -- prompt builders ---------------------------------------------------

def test_build_planning_prompt_includes_all_sections():
    prompt = build_planning_prompt(
        goal="单移线侧倾大，需要改善",
        complaint="侧倾明显",
        condition_name="单移线",
        current_state="- 当前车型: CarA\n- 前稳定杆: BAR_F1",
        knowledge="【稳定杆调校基本原则】分类:chassis_tuning\n稳定杆通过扭杆的扭转刚度...",
        experiences="- set_antiroll_bar: 已选择后轮稳定杆",
    )

    assert "单移线侧倾大" in prompt
    assert "侧倾明显" in prompt
    assert "单移线" in prompt
    assert "CarA" in prompt
    assert "稳定杆调校基本原则" in prompt
    assert "set_antiroll_bar" in prompt


def test_build_chassis_plan_prompt():
    prompt = build_chassis_plan_prompt(
        goal="侧倾大",
        current_state="- 前稳定杆: BAR_F1",
    )
    assert "侧倾大" in prompt
    assert "BAR_F1" in prompt


def test_build_tuning_suggestion_prompt():
    prompt = build_tuning_suggestion_prompt(
        complaint="方向盘中心区重",
        current_state="- 摩擦增益=2",
    )
    assert "方向盘中心区重" in prompt
    assert "摩擦增益=2" in prompt


def test_plan_system_prompt_is_chinese():
    assert "底盘调校" in PLAN_SYSTEM_PROMPT
    assert "诊断分析" in PLAN_SYSTEM_PROMPT
    assert "建议步骤" in PLAN_SYSTEM_PROMPT


# -- action registration (without LLM) ---------------------------------

class FakeContext:
    llm_client = None  # no LLM, actions should return error gracefully


def test_planning_action_returns_error_without_llm():
    registry = ActionRegistry()
    ctx = FakeContext()
    planning_actions.register(registry, ctx)

    result = registry.execute(
        "plan_chassis_task",
        {"goal": "单移线侧倾大"},
    )
    assert "未就绪" in result


def test_knowledge_action_returns_error_without_llm():
    registry = ActionRegistry()
    ctx = FakeContext()
    knowledge_actions.register(registry, ctx)

    result = registry.execute(
        "suggest_chassis_tuning",
        {"complaint": "方向盘重"},
    )
    assert "未就绪" in result


def test_planning_action_metadata():
    registry = ActionRegistry()
    planning_actions.register(registry, None)
    meta = registry.get_metadata("plan_chassis_task")
    assert meta["side_effects"] is False
    assert meta["risk_level"] == "low"


def test_knowledge_action_metadata():
    registry = ActionRegistry()
    knowledge_actions.register(registry, None)
    meta = registry.get_metadata("suggest_chassis_tuning")
    assert meta["side_effects"] is False
    assert meta["risk_level"] == "low"
