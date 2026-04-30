"""
知识库与调校建议 action

- suggest_chassis_tuning   根据主观抱怨和目标输出底盘/触感调校建议
- search_knowledge         检索领域知识库
- save_knowledge           保存新的领域知识条目
"""

from agent.planner import format_chassis_plan, suggest_chassis_tuning
from agent.memory.store import AgentMemoryStore
from agent.knowledge.store import KnowledgeStore


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
    # 附加知识库检索
    kw = kwargs.get("complaint") or kwargs.get("objective") or ""
    result["knowledge_refs"] = KnowledgeStore().search(keyword=kw, limit=3)
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

    # ---------- 知识库检索 ----------
    def search_knowledge(keyword: str = None, category: str = None, limit: int = 5) -> str:
        store = KnowledgeStore()
        entries = store.search(keyword=keyword, category=category, limit=limit)
        if not entries:
            return "未找到匹配的领域知识条目。"
        parts = []
        for e in entries:
            meta = e["meta"]
            title = meta.get("title", e["filename"])
            cat = meta.get("category", "")
            tags = meta.get("tags", [])
            tag_str = "、".join(tags) if tags else "无"
            parts.append(f"【{title}】分类:{cat} 标签:{tag_str}\n{e['summary']}...")
        return "\n\n---\n\n".join(parts)

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
