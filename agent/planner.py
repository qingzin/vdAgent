"""
LLM-driven chassis planning and tuning suggestions.

The old keyword-matching rule engine has been replaced with prompt
construction helpers.  The actual LLM call happens in the action callbacks
(planning_actions.py / knowledge_actions.py) so they can access the llm_client
and live UI context without circular imports.
"""


PLAN_SYSTEM_PROMPT = """你是一位资深的底盘调校工程师。你需要根据用户的目标、抱怨和当前系统状态，给出专业的分析和建议。

输出格式要求（用中文，Markdown）：
## 底盘任务规划（或：底盘调校建议）
- 目标: ...
- 现象/抱怨: ...（如有）
- 工况: ...（如有）

### 诊断分析
（简要分析当前配置和抱怨之间的关联，引用知识库原理）

### 建议步骤
（具体的、可执行的操作步骤，按顺序排列，每步说明要调什么工具、什么参数）

### 参数方向
（具体建议的调整方向和幅度，如"前稳定杆加硬5%"）

### 风险提示
（可能的副作用和需要注意的问题）

### 验证指标
（如何判断改善是否有效）

重要原则：
1. 优先给分析，不要直接建议大幅修改硬件参数
2. 建议单变量、小步迭代（每次5%-10%）
3. 结合当前系统状态和知识库原理给出有依据的建议
4. 如果信息不足，明确指出还需要什么信息
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
