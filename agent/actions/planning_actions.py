"""Planning actions exposed to the LLM."""

from agent.planner import format_chassis_plan, plan_chassis_task
from agent.memory.store import AgentMemoryStore


def _relevant_experience_seeds(condition_name: str = None,
                               keyword: str = None,
                               limit: int = 3) -> list:
    try:
        store = AgentMemoryStore()
    except Exception:
        return []
    if hasattr(store, "rank_experience_seeds"):
        try:
            return store.rank_experience_seeds(
                condition_name=condition_name,
                keyword=keyword,
                limit=limit,
            )
        except Exception:
            pass
    if hasattr(store, "query_experience_seeds"):
        try:
            return store.query_experience_seeds(
                condition_name=condition_name,
                keyword=keyword,
                limit=limit,
            )
        except Exception:
            pass
    if hasattr(store, "recent_experience_seeds"):
        try:
            return store.recent_experience_seeds(limit=limit)
        except Exception:
            pass
    return []

def _plan_chassis_task_text(**kwargs) -> str:
    result = plan_chassis_task(**kwargs)
    result["recent_experiences"] = _relevant_experience_seeds(
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
