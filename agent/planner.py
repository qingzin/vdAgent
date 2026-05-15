"""
LLM-driven chassis planning and tuning suggestions.

The old keyword-matching rule engine has been replaced with prompt
construction helpers.  The actual LLM call happens in the action callbacks
(planning_actions.py / knowledge_actions.py) so they can access the llm_client
and live UI context without circular imports.
"""


PLAN_SYSTEM_PROMPT = """你是资深底盘调校工程师。根据用户目标和当前系统状态给出专业分析和建议。

输出格式（中文 Markdown）：
### 诊断分析
### 建议步骤
### 参数方向
### 风险提示
### 验证指标

原则：优先分析、单变量小步迭代（5%-10%）、结合状态和知识库、信息不足时指出。
"""


def build_planning_prompt(goal: str,
                          complaint: str = None,
                          condition_name: str = None,
                          objective: str = None,
                          current_state: str = "",
                          knowledge: str = "",
                          experiences: str = "") -> str:
    """Build a complete user prompt for the LLM to reason about chassis work."""

    parts = [f"用户目标: {goal}"]
    if complaint:
        parts.append(f"主观抱怨: {complaint}")
    if objective:
        parts.append(f"优化目标: {objective}")
    if condition_name:
        parts.append(f"指定工况: {condition_name}")

    if current_state:
        parts.append(f"\n当前系统状态:\n{current_state}")
    if knowledge:
        parts.append(f"\n相关领域知识:\n{knowledge}")
    if experiences:
        parts.append(f"\n近期操作经验:\n{experiences}")

    parts.append("\n请根据以上信息给出分析和建议。")
    return "\n".join(parts)


def build_chassis_plan_prompt(goal: str,
                              complaint: str = None,
                              condition_name: str = None,
                              current_state: str = "",
                              knowledge: str = "",
                              experiences: str = "") -> str:
    """Build a prompt specifically for chassis task planning."""
    return build_planning_prompt(
        goal=goal,
        complaint=complaint,
        condition_name=condition_name,
        current_state=current_state,
        knowledge=knowledge,
        experiences=experiences,
    )


def build_tuning_suggestion_prompt(complaint: str,
                                   objective: str = None,
                                   condition_name: str = None,
                                   current_state: str = "",
                                   knowledge: str = "",
                                   experiences: str = "") -> str:
    """Build a prompt specifically for tuning suggestions."""
    return build_planning_prompt(
        goal=f"改善: {complaint}",
        complaint=complaint,
        objective=objective,
        condition_name=condition_name,
        current_state=current_state,
        knowledge=knowledge,
        experiences=experiences,
    )
