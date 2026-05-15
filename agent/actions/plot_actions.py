"""
绘图和报警相关 action

- control_plotting      控制绘图运行/暂停/清空
- set_plot_visibility   显示/隐藏单个或多个信号的图表
- set_all_plots         全开/全关所有图表
- set_plot_time_range   设置 X 轴时间范围
- set_alarm             切换报警开关 / 切换报警工况
"""

from ._helpers import fuzzy_resolve


# 把 plot_switches 里的 key 和中文名都列出来, 让 LLM 和用户都能用
PLOT_CHANNELS = {
    'pos_x': '位移X', 'pos_y': '位移Y', 'pos_z': '位移Z',
    'vel_x': '速度X', 'vel_y': '速度Y', 'vel_z': '速度Z',
    'acc_x': '加速度X', 'acc_y': '加速度Y', 'acc_z': '加速度Z',
    'ang_x': '角速度X', 'ang_y': '角速度Y', 'ang_z': '角速度Z',
    'roll': 'Roll', 'pitch': 'Pitch', 'yaw': 'Yaw',
    'ang_acc_x': '角加速度X', 'ang_acc_y': '角加速度Y', 'ang_acc_z': '角加速度Z',
    'steering_angle': '方向盘转角',
    'throttle': '油门开度',
    'pbk_con': '制动主缸压力',
    'steering_speed': '方向盘转速',
    'CmpRD_L1': '运行速度L1', 'CmpRD_L2': '运行速度L2',
    'CmpRD_R1': '运行速度R1', 'CmpRD_R2': '运行速度R2',
}


def register(registry, ctx):

    # --------- 运行/暂停/清空 ---------
    def control_plotting(action: str) -> str:
        ui = ctx.ui
        action = action.lower().strip()
        if action in ('run', 'start', 'resume', '开始', '运行'):
            if hasattr(ui, 'run_button'):
                ui.run_button.setChecked(True)
            ui.toggle_plotting(True)
            return "绘图已开始/恢复。"
        if action in ('pause', 'stop', '暂停', '停止'):
            ui.stop_plotting()
            return "绘图已暂停。"
        if action in ('clear', '清空'):
            ui.clear_plots()
            return "绘图已清空。"
        return f"未知操作: {action}。支持: run / pause / clear"

    registry.register(
        name="control_plotting",
        description="控制实时绘图的运行状态。action 可选: "
                    "run(开始/恢复)、pause(暂停)、clear(清空数据并重置)。",
        params_schema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["run", "pause", "clear"],
                           "description": "操作类型"}
            },
            "required": ["action"]
        },
        callback=control_plotting,
    )

    # --------- 全开/全关 ---------
    def set_all_plots(visible: bool) -> str:
        ui = ctx.ui
        if visible:
            ui.toggle_all_plots_on()
            return "所有图表已开启显示。"
        else:
            ui.toggle_all_plots_off()
            return "所有图表已关闭显示。"

    registry.register(
        name="set_all_plots",
        description="一键显示或隐藏所有通道的实时图表。",
        params_schema={
            "type": "object",
            "properties": {
                "visible": {"type": "boolean", "description": "true 全开, false 全关"}
            },
            "required": ["visible"]
        },
        callback=set_all_plots,
    )

    # --------- 单个/多个图表显隐 ---------
    def set_plot_visibility(channels, visible: bool) -> str:
        """
        Args:
            channels: 单个字符串(可为 key 如 'roll' 或中文名 '方向盘转角')
                      或字符串列表。
            visible: True 显示, False 隐藏
        """
        ui = ctx.ui
        if isinstance(channels, str):
            channels = [channels]

        # 反向映射: 中文名 -> key
        zh_to_key = {v: k for k, v in PLOT_CHANNELS.items()}

        ok, not_found = [], []
        for ch in channels:
            key = ch
            if ch not in PLOT_CHANNELS and ch in zh_to_key:
                key = zh_to_key[ch]
            if key not in ui.plot_switches:
                # 尝试模糊匹配中文名
                resolved, _ = fuzzy_resolve(ch, list(zh_to_key.keys()))
                if resolved:
                    key = zh_to_key[resolved]
                else:
                    not_found.append(ch)
                    continue
            ui.plot_switches[key].setChecked(visible)
            ok.append(f"{PLOT_CHANNELS.get(key, key)}")

        if ok:
            ui.update_plot_layout()
        msg = f"已{'显示' if visible else '隐藏'}: {', '.join(ok)}" if ok else ""
        if not_found:
            msg += f" 未找到的通道: {not_found}"
        return msg or "未操作任何通道。"

    registry.register(
        name="set_plot_visibility",
        description="显示或隐藏特定通道的实时图表。"
                    "channels 参数可以是单个通道或列表。"
                    "通道名可以是代号(如 'roll'、'vel_x'、'steering_angle')"
                    "或中文名(如 'Roll'、'速度X'、'方向盘转角')。",
        params_schema={
            "type": "object",
            "properties": {
                "channels": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}}
                    ],
                    "description": "通道名称,单个字符串或字符串数组"
                },
                "visible": {"type": "boolean", "description": "true 显示, false 隐藏"}
            },
            "required": ["channels", "visible"]
        },
        callback=set_plot_visibility,
    )

    # --------- X 轴范围 ---------
    def set_plot_time_range(x_min: float, x_max: float) -> str:
        ui = ctx.ui
        if x_min >= x_max:
            return f"x_min ({x_min}) 必须小于 x_max ({x_max})"
        try:
            for plot in ui.plots.values():
                plot.setXRange(x_min, x_max)
            return f"已设置所有图表 X 轴范围: [{x_min}, {x_max}] 秒"
        except Exception as e:
            return f"设置失败: {e}"

    registry.register(
        name="set_plot_time_range",
        description="设置所有实时图表的 X 轴(时间轴)显示范围。单位: 秒。",
        params_schema={
            "type": "object",
            "properties": {
                "x_min": {"type": "number", "description": "X 轴最小值 (秒)"},
                "x_max": {"type": "number", "description": "X 轴最大值 (秒)"},
            },
            "required": ["x_min", "x_max"]
        },
        callback=set_plot_time_range,
    )

    # --------- 报警 ---------
    def set_alarm(enabled: bool = None, scenario: str = None) -> str:
        ui = ctx.ui
        msgs = []

        if enabled is not None:
            try:
                ui.toggle_alarm(bool(enabled))
                if hasattr(ui, 'alarm_toggle'):
                    ui.alarm_toggle.setChecked(bool(enabled))
                msgs.append(f"报警{'开启' if enabled else '关闭'}")
            except Exception as e:
                msgs.append(f"报警开关设置失败: {e}")

        if scenario is not None:
            if not hasattr(ui, 'scenario_combo'):
                msgs.append("scenario_combo 未就绪")
            else:
                names = [ui.scenario_combo.itemText(i)
                         for i in range(ui.scenario_combo.count())]
                resolved, err = fuzzy_resolve(scenario, names)
                if err:
                    msgs.append(f"工况: {err} (可选: {names})")
                else:
                    ui.scenario_combo.setCurrentText(resolved)
                    msgs.append(f"报警工况切换为: {resolved}")

        if not msgs:
            return "未指定任何参数。可用: enabled (布尔), scenario (工况名)"
        return "; ".join(msgs)

    registry.register(
        name="set_alarm",
        description="配置报警系统。可单独切换报警开关,或切换报警工况。"
                    "工况决定阈值(单移线/转弯/中心区/一阶起伏/自定义)。",
        params_schema={
            "type": "object",
            "properties": {
                "enabled":  {"type": "boolean", "description": "报警开关"},
                "scenario": {"type": "string",
                             "description": "报警工况: 单移线/转弯/中心区/一阶起伏/自定义"},
            },
            "required": []
        },
        callback=set_alarm,
    )
