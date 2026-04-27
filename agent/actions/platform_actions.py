"""
运动平台控制相关 action

- one_click_platform_start      一键启动
- one_click_platform_stop       一键关闭
- prepare_platform             设置平台位置偏置 X/Y/Z
"""


COMMAND_NAMES = {
    0: "Off(关闭)", 1: "Disengage(脱开)", 2: "Consent(同意)",
    3: "ReadyForTraining(准备训练)", 4: "Engage(接合)",
    5: "Hold(保持)", 6: "Reset(重置)",
}


def register(registry, ctx):

    def one_click_platform_start() -> str:
        try:
            ctx.ui.one_click_start()
            return "已触发平台一键启动流程 (Reset → Consent → Engage)。"
        except Exception as e:
            return f"一键启动失败: {e}"

    registry.register(
        name="one_click_platform_start",
        description="平台一键启动,自动按顺序发送 Reset(6) → Consent(2) → Engage(4) 三个指令。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=one_click_platform_start,
        category="platform",
        risk_level="high",
        exposed=True,
    )

    def one_click_platform_stop() -> str:
        try:
            ctx.ui.one_click_stop()
            return "已触发平台一键关闭流程 (Disengage → Off)。"
        except Exception as e:
            return f"一键关闭失败: {e}"

    registry.register(
        name="one_click_platform_stop",
        description="平台一键关闭,自动按顺序发送 Disengage(1) → Off(0) 两个指令。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=one_click_platform_stop,
        category="platform",
        risk_level="medium",
        exposed=True,
    )

    def prepare_platform(x: float = None, y: float = None, z: float = None) -> str:
        ui = ctx.ui

        if x is None and y is None and z is None:
            return "未指定任何偏置,请提供 x / y / z (至少一项)。"

        # 读取 UI 上的当前值作为默认
        def _get(attr, default=0.0):
            w = getattr(ui, attr, None)
            if w is None:
                return default
            try:
                return float(w.text())
            except Exception:
                return default

        cur_x = _get('offset_x')
        cur_y = _get('offset_y')
        cur_z = _get('offset_z')

        nx = cur_x if x is None else float(x)
        ny = cur_y if y is None else float(y)
        nz = cur_z if z is None else float(z)

        # 同步到 UI 输入框
        if hasattr(ui, 'offset_x'): ui.offset_x.setText(str(nx))
        if hasattr(ui, 'offset_y'): ui.offset_y.setText(str(ny))
        if hasattr(ui, 'offset_z'): ui.offset_z.setText(str(nz))

        try:
            ui.sendDataPlatformOffset2(nx, ny, nz)
            return f"已设置平台位置偏置: X={nx}, Y={ny}, Z={nz} (米)"
        except Exception as e:
            return f"设置失败: {e}"

    registry.register(
        name="prepare_platform",
        description="准备运动平台配置。当前支持设置平台位置偏置,"
                    "未指定的轴保持当前值。单位:米。",
        params_schema={
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "X 方向偏置 (米)"},
                "y": {"type": "number", "description": "Y 方向偏置 (米)"},
                "z": {"type": "number", "description": "Z 方向偏置 (米)"},
            },
            "required": []
        },
        callback=prepare_platform,
        category="platform",
        risk_level="medium",
        exposed=True,
    )
