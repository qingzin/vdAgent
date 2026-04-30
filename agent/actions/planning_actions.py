"""LLM-driven planning action exposed to the agent."""

from agent.planner import PLAN_SYSTEM_PROMPT, build_chassis_plan_prompt
from agent.knowledge.store import KnowledgeStore
from ._helpers import relevant_experience_seeds


def _get_current_state_snapshot(ui) -> str:
    """Build a text snapshot of the current system state for the LLM."""
    lines = []
    car = getattr(ui, 'carName', None)
    if car:
        lines.append(f"当前车型: {car}")

    setup = []
    for attr, label in [
        ('frontSpringName', '前弹簧'), ('rearSpringName', '后弹簧'),
        ('frontRightSpringName', '前右弹簧'), ('rearRightSpringName', '后右弹簧'),
        ('frontAuxMName', '前稳定杆'), ('rearAuxMName', '后稳定杆'),
    ]:
        val = getattr(ui, attr, None)
        if val:
            setup.append(f"{label}={val}")
    if setup:
        lines.append("悬架配置: " + ", ".join(setup))

    scene = []
    if hasattr(ui, 'condition_combo') and ui.condition_combo.count() > 0:
        scene.append(f"工况={ui.condition_combo.currentText()}")
    if hasattr(ui, 'map_combo') and ui.map_combo.count() > 0:
        scene.append(f"地图={ui.map_combo.currentText()}")
    if scene:
        lines.append("场景: " + ", ".join(scene))

    haptic = []
    for attr, label in [
        ('gain_fri', '摩擦增益'), ('gain_dam', '阻尼增益'),
        ('gain_feedback', '回正增益'), ('gain_sa', '限位增益'),
        ('gain_all', '手感轻重'),
    ]:
        val = getattr(ui, attr, None)
        if val is not None:
            haptic.append(f"{label}={val}")
    if haptic:
        lines.append("触感参数: " + ", ".join(haptic))

    return "\n".join(f"- {l}" for l in lines)


def register(registry, ctx):

    def plan_chassis_task(goal: str, complaint: str = None,
                          condition_name: str = None) -> str:
        """LLM 驱动的底盘任务规划。"""
        llm = getattr(ctx, 'llm_client', None) if ctx is not None else None
        if llm is None:
            return "LLM 客户端未就绪，无法生成计划。请检查 llama-server 连接。"
        ui = ctx.ui

        current_state = _get_current_state_snapshot(ui)
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
