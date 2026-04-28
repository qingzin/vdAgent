"""Knowledge suggestion actions exposed to the LLM."""

from agent.planner import format_chassis_plan, suggest_chassis_tuning
from agent.memory.store import AgentMemoryStore


def _relevant_experience_seeds(condition_name: str = None,
                               keyword: str = None,
                               limit: int = 3) -> list:
    try:
        return AgentMemoryStore().query_experience_seeds(
            condition_name=condition_name,
            keyword=keyword,
            limit=limit,
        )
    except Exception:
        return []


def _suggest_chassis_tuning_text(**kwargs) -> str:
    result = suggest_chassis_tuning(**kwargs)
    result["recent_experiences"] = _relevant_experience_seeds(
        condition_name=kwargs.get("condition_name"),
        keyword=(
            None if kwargs.get("condition_name")
            else kwargs.get("complaint") or kwargs.get("objective")
        ),
    )
    return format_chassis_plan(result)


def register(registry, ctx):
    registry.register(
        name="suggest_chassis_tuning",
        description=(
            "根据主观抱怨和目标输出底盘/触感调校建议。只给建议和验证指标，"
            "不会直接修改车辆、硬件或仿真参数。"
        ),
        params_schema={
            "type": "object",
            "properties": {
                "complaint": {"type": "string", "description": "主观抱怨，例如侧倾大、中心区重、起伏不舒适"},
                "objective": {"type": "string", "description": "希望优化的目标，可选"},
                "condition_name": {"type": "string", "description": "工况名称，可选"},
            },
            "required": ["complaint"],
        },
        callback=_suggest_chassis_tuning_text,
        category="knowledge",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
