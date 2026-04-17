"""
杂项 action

- set_preset               设置预定义的评价字段 (车型/调校件/评价人/工况)
- get_preset               查询当前预定义
- toggle_all_signals       全部启动/停止信号发送 (PVA 控制)
"""


def register(registry, ctx):

    # ---------- 预定义 ----------
    def set_preset(car_model: str = None, tuning_parts: str = None,
                   evaluator: str = None, condition: str = None) -> str:
        ui = ctx.ui
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
        name="set_preset",
        description="设置评价记录对话框的预定义默认字段。未指定的字段保持不变。",
        params_schema={
            "type": "object",
            "properties": {
                "car_model":    {"type": "string", "description": "车型预定义"},
                "tuning_parts": {"type": "string", "description": "调校件预定义"},
                "evaluator":    {"type": "string", "description": "评价人预定义"},
                "condition":    {"type": "string", "description": "工况预定义"},
            },
            "required": []
        },
        callback=set_preset,
    )

    def get_preset() -> str:
        ui = ctx.ui
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

    registry.register(
        name="get_preset",
        description="查询评价记录对话框的当前预定义字段。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=get_preset,
    )

    # ---------- 信号发送总开关 ----------
    def toggle_all_signals(enabled: bool) -> str:
        """对应信号输入配置页的'全部启动'按钮"""
        ui = ctx.ui
        if not hasattr(ui, 'signal_toggle_button'):
            return "signal_toggle_button 未就绪, 可能当前不在 PVA 控制模式。"

        try:
            # 该按钮是 checkable, 我们先设状态再调回调
            ui.signal_toggle_button.setChecked(bool(enabled))
            ui.toggle_all_signal()
            return f"所有信号已{'启动' if enabled else '停止'}。"
        except Exception as e:
            return f"操作失败: {e}"

    registry.register(
        name="toggle_all_signals",
        description="一键启动或停止所有已配置的信号发送 (PVA 控制模式下的 '全部启动/全部停止' 按钮)。",
        params_schema={
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "description": "true 启动, false 停止"}
            },
            "required": ["enabled"]
        },
        callback=toggle_all_signals,
    )
