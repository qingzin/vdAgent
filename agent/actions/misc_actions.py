"""
杂项 action

- prepare_evaluation_metadata  设置或查询预定义的评价字段
"""


def register(registry, ctx):

    # ---------- 预定义 ----------
    def prepare_evaluation_metadata(mode: str = "set", car_model: str = None, tuning_parts: str = None,
                                    evaluator: str = None, condition: str = None) -> str:
        ui = ctx.ui
        mode = (mode or "set").lower().strip()
        if mode == "get":
            parts = []
            for label, attr in [
                ('车型', 'preset_car_model'),
                ('调校件', 'preset_tuning_parts'),
                ('评价人', 'preset_evaluator'),
                ('工况', 'preset_condition'),
            ]:
                val = getattr(ui, attr, '') or '(未设置)'
                parts.append(f"{label}={val}")
            return "当前预定义: " + ", ".join(parts)

        if mode != "set":
            return "mode 仅支持 get 或 set。"

        changes = []

        if car_model is not None:
            ui.preset_car_model = str(car_model)
            changes.append(f"车型预定义='{car_model}'")
        if tuning_parts is not None:
            ui.preset_tuning_parts = str(tuning_parts)
            changes.append(f"调校件预定义='{tuning_parts}'")
        if evaluator is not None:
            ui.preset_evaluator = str(evaluator)
            changes.append(f"评价人预定义='{evaluator}'")
        if condition is not None:
            ui.preset_condition = str(condition)
            changes.append(f"工况预定义='{condition}'")

        if not changes:
            return "未指定任何参数。可用: car_model, tuning_parts, evaluator, condition"
        return "已更新预定义: " + ", ".join(changes)

    registry.register(
        name="prepare_evaluation_metadata",
        description="设置或查询评价记录对话框的预定义元数据。"
                    "mode=get 时查询当前预定义, mode=set 时更新默认字段。",
        params_schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["get", "set"],
                         "description": "get 查询; set 更新"},
                "car_model":    {"type": "string", "description": "车型预定义"},
                "tuning_parts": {"type": "string", "description": "调校件预定义"},
                "evaluator":    {"type": "string", "description": "评价人预定义"},
                "condition":    {"type": "string", "description": "工况预定义"},
            },
            "required": []
        },
        callback=prepare_evaluation_metadata,
    )
