"""LLM-driven planning action exposed to the agent."""

from agent.planner import PLAN_SYSTEM_PROMPT, build_chassis_plan_prompt
from agent.knowledge.store import KnowledgeStore
from agent.executor import _build_context_snapshot
from ._helpers import relevant_experience_seeds


def register(registry, ctx):

    def plan_chassis_task(goal: str, complaint: str = None,
                          condition_name: str = None) -> str:
        """LLM 驱动的底盘任务规划。"""
        llm = getattr(ctx, 'llm_client', None) if ctx is not None else None
        if llm is None:
            return "LLM 客户端未就绪，无法生成计划。请检查 llama-server 连接。"
        ui = ctx.ui

        current_state = _build_context_snapshot(ui)
        knowledge = KnowledgeStore().search_for_context(
            keyword=goal or complaint or "",
            limit=4,
        )
        experiences_list = relevant_experience_seeds(
            condition_name=condition_name,
            keyword=goal or complaint,
            limit=3,
        )
        exp_text = ""
        if experiences_list:
            exp_lines = []
            for e in experiences_list:
                a = e.get("action_name", "?")
                r = str(e.get("result", ""))[:100]
                exp_lines.append(f"- {a}: {r}")
            exp_text = "\n".join(exp_lines)

        prompt = build_chassis_plan_prompt(
            goal=goal,
            complaint=complaint,
            condition_name=condition_name,
            current_state=current_state,
            knowledge=knowledge,
            experiences=exp_text,
        )

        try:
            response = llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system=PLAN_SYSTEM_PROMPT,
                temperature=0.3,
            )
            return response.text or "(LLM 返回空响应)"
        except Exception as e:
            return f"LLM 规划调用失败: {e}"

    registry.register(
        name="plan_chassis_task",
        description=(
            "针对复杂底盘目标生成执行计划和分析。适用于侧倾、单移线、中心区手感、"
            "起伏舒适性、准备工况记录、修改悬架并仿真验证等需求。"
            "调用此工具会触发一次专门的 LLM 推理，请耐心等待响应。"
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
        callback=plan_chassis_task,
        category="planning",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
