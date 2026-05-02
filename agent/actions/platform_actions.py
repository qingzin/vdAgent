"""平台控制 action — 通过 PlatformService 操作。"""

from ._helpers import require_not_recording


def register(registry, ctx):
    svc = ctx.service('platform')

    def one_click_platform_start() -> str:
        guard = require_not_recording(ctx, "一键启动平台")
        if guard:
            return guard
        try:
            return svc.one_click_start()
        except Exception as e:
            return f"一键启动失败: {e}"

    registry.register(
        name="one_click_platform_start",
        description="平台一键启动,自动按顺序发送 Reset → Consent → Engage。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=one_click_platform_start,
        category="platform",
        risk_level="high",
        exposed=True,
    )

    def one_click_platform_stop() -> str:
        guard = require_not_recording(ctx, "一键关闭平台")
        if guard:
            return guard
        try:
            return svc.one_click_stop()
        except Exception as e:
            return f"一键关闭失败: {e}"

    registry.register(
        name="one_click_platform_stop",
        description="平台一键关闭,自动按顺序发送 Disengage → Off。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=one_click_platform_stop,
        category="platform",
        risk_level="medium",
        exposed=True,
    )

    def prepare_platform(x: float = None, y: float = None, z: float = None) -> str:
        guard = require_not_recording(ctx, "设置平台偏置")
        if guard:
            return guard
        if x is None and y is None and z is None:
            return "未指定任何偏置,请提供 x / y / z (至少一项)。"
        try:
            return svc.set_offset(x=x, y=y, z=z)
        except Exception as e:
            return f"设置失败: {e}"

    registry.register(
        name="prepare_platform",
        description="设置运动平台位置偏置 X/Y/Z (米),未指定的轴保持当前值。",
        params_schema={
            "type": "object",
            "properties": {
                "x": {"type": "number"}, "y": {"type": "number"}, "z": {"type": "number"},
            },
            "required": []
        },
        callback=prepare_platform,
        category="platform",
        risk_level="medium",
        exposed=True,
    )
