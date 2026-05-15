"""报警监控 action — 通过 MonitoringService 操作。"""


def register(registry, ctx):
    svc = ctx.service('monitoring')

    def toggle_alarm(enable: bool = True) -> str:
        svc.toggle_alarm(bool(enable))
        state = "已开启" if enable else "已关闭"
        return f"实时报警监控{state}。"

    registry.register(
        name="toggle_alarm",
        description="启用或关闭驾驶模拟器实时报警监控。",
        params_schema={
            "type": "object",
            "properties": {
                "enable": {"type": "boolean", "description": "true 开启, false 关闭"}
            },
            "required": ["enable"]
        },
        callback=toggle_alarm,
        category="monitoring",
        risk_level="low",
        exposed=True,
    )
