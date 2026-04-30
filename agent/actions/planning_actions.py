"""Planning actions exposed to the LLM."""

from agent.planner import format_chassis_plan, plan_chassis_task
from ._helpers import relevant_experience_seeds


def _plan_chassis_task_text(**kwargs) -> str:
    result = plan_chassis_task(**kwargs)
    result["recent_experiences"] = relevant_experience_seeds(
        condition_name=kwargs.get("condition_name"),
        keyword=(
            None if kwargs.get("condition_name")
            else kwargs.get("goal") or kwargs.get("complaint")
        ),
    )
    return format_chassis_plan(result)


def register(registry, ctx):
    registry.register(
        name="plan_chassis_task",
        description=(
            "针对复杂底盘目标生成保守执行计划。适用于侧倾、单移线、中心区手感、"
            "起伏舒适性、准备工况记录、修改悬架并仿真验证等需求。"
        ),
        params_schema={
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "用户目标或任务描述"},
                "complaint": {"type": "string", "description": "主观抱怨或现象，可选"},
                "condition_name": {"type": "string", "description": "工况名称，可选"},
            },
            "required": ["goal"],
        },
        callback=_plan_chassis_task_text,
        category="planning",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
