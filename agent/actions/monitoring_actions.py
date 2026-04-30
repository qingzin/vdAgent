"""
监控与报警相关 action

- toggle_alarm             启用或关闭实时驾驶报警监控
"""


def register(registry, ctx):

    def toggle_alarm(enable: bool = True) -> str:
        ui = ctx.ui
        enable = bool(enable)
        ui.toggle_alarm(enable)
        if hasattr(ui, 'alarm_toggle'):
            ui.alarm_toggle.setChecked(enable)
        state = "已开启" if enable else "已关闭"
        return f"实时报警监控{state}。"

    registry.register(
        name="toggle_alarm",
        description="启用或关闭驾驶模拟器实时报警监控。"
                    "开启后,当车速、方向盘转角、方向盘转速超过当前工况阈值时将显示报警。",
        params_schema={
            "type": "object",
            "properties": {
                "enable": {"type": "boolean", "description": "true 开启报警, false 关闭报警"}
            },
            "required": ["enable"]
        },
        callback=toggle_alarm,
        category="monitoring",
        risk_level="low",
        exposed=True,
    )
