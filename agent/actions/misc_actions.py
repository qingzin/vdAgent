"""杂项 action — 通过 MetadataService 操作。"""


def register(registry, ctx):
    svc = ctx.service('metadata')

    def prepare_evaluation_metadata(mode: str = "set", car_model: str = None,
                                    tuning_parts: str = None, evaluator: str = None,
                                    condition: str = None) -> str:
        mode = (mode or "set").lower().strip()
        if mode == "get":
            data = svc.get_all()
            parts = [f"{k}={v or '(未设置)'}" for k, v in data.items()]
            return "当前预定义: " + ", ".join(parts)

        if mode != "set":
            return "mode 仅支持 get 或 set。"

        changed = svc.set_fields(
            car_model=car_model, tuning_parts=tuning_parts,
            evaluator=evaluator, condition=condition,
        )
        if not changed:
            return "未指定任何参数。可用: car_model, tuning_parts, evaluator, condition"
        return "已更新预定义: " + ", ".join(f"{k}='{v}'" for k, v in changed.items())

    registry.register(
        name="prepare_evaluation_metadata",
        description="设置或查询评价记录对话框的预定义元数据。",
        params_schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["get", "set"]},
                "car_model": {"type": "string"},
                "tuning_parts": {"type": "string"},
                "evaluator": {"type": "string"},
                "condition": {"type": "string"},
            },
            "required": []
        },
        callback=prepare_evaluation_metadata,
        category="misc",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
