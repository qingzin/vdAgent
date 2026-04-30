"""
知识库与调校建议 action

- suggest_chassis_tuning   LLM 驱动的底盘/触感调校建议
- search_knowledge         检索领域知识库
- save_knowledge           保存新的领域知识条目
"""

from agent.planner import PLAN_SYSTEM_PROMPT, build_tuning_suggestion_prompt
from agent.knowledge.store import KnowledgeStore
from agent.executor import _build_context_snapshot
from ._helpers import relevant_experience_seeds


def register(registry, ctx):

    # ---------- LLM 驱动的调校建议 ----------
    def suggest_chassis_tuning(complaint: str, objective: str = None,
                               condition_name: str = None) -> str:
        """LLM 驱动的底盘调校建议。"""
        llm = getattr(ctx, 'llm_client', None) if ctx is not None else None
        if llm is None:
            return "LLM 客户端未就绪，无法生成建议。请检查 llama-server 连接。"
        ui = ctx.ui

        current_state = _build_context_snapshot(ui)
        knowledge = KnowledgeStore().search_for_context(
            keyword=complaint or objective or "",
            limit=4,
        )
        experiences_list = relevant_experience_seeds(
            condition_name=condition_name,
            keyword=complaint or objective,
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

        prompt = build_tuning_suggestion_prompt(
            complaint=complaint,
            objective=objective,
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
            return f"LLM 建议调用失败: {e}"

    registry.register(
        name="suggest_chassis_tuning",
        description=(
            "根据主观抱怨和目标输出底盘/触感调校建议。调用此工具会触发一次专门的"
            "LLM 推理来分析当前配置、知识库和历史经验，只给建议和验证指标，"
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
        callback=suggest_chassis_tuning,
        category="knowledge",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )

    # ---------- 知识库检索 ----------
    def search_knowledge(keyword: str = None, category: str = None, limit: int = 5) -> str:
        store = KnowledgeStore()
        result = store.search_for_context(keyword=keyword, category=category, limit=limit)
        if not result or result.startswith("（未找到"):
            return "未找到匹配的领域知识条目。"
        return result

    registry.register(
        name="search_knowledge",
        description="检索底盘调校领域知识库。可按关键词、分类查找历史积累的调校经验和原理。",
        params_schema={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "检索关键词,如'侧倾'、'弹簧刚度'"},
                "category": {"type": "string", "description": "知识分类,如 chassis_tuning / haptic / scene"},
                "limit": {"type": "integer", "description": "返回条数上限,默认5"},
            },
            "required": []
        },
        callback=search_knowledge,
        category="knowledge",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )

    # ---------- 知识库写入 ----------
    def save_knowledge(title: str, category: str, body: str, tags: str = "") -> str:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        store = KnowledgeStore()
        filepath = store.save_from_llm(
            title=title,
            category=category,
            body=body,
            tags=tag_list,
            source="agent",
        )
        return f"已保存知识条目「{title}」到 {filepath}"

    registry.register(
        name="save_knowledge",
        description="保存一条新的底盘调校领域知识。适用于将在交互中获得的经验、原理或规律沉淀为可检索的知识。",
        params_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "知识标题"},
                "category": {"type": "string", "description": "分类: chassis_tuning / haptic / scene / simulation / recording"},
                "body": {"type": "string", "description": "知识正文 (Markdown 格式,中文)"},
                "tags": {"type": "string", "description": "标签,逗号分隔,如 '稳定杆,侧倾,操稳'"},
            },
            "required": ["title", "category", "body"]
        },
        callback=save_knowledge,
        category="knowledge",
        risk_level="low",
        exposed=True,
    )
