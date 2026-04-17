"""
场景设置相关 action

- select_map_and_start_point  切换地图和起点 (可单独切起点)
- confirm_scene               确认场景设置, 发起点坐标给平台
- set_condition               切换工况 (下拉框)
- get_current_scene           查询当前场景设置
"""

from ._helpers import fuzzy_resolve


def register(registry, ctx):

    # -----------------------------------------------------------------------

    def _find_map(ui, map_name):
        """根据名称在 map_combo 里找对应索引"""
        if not hasattr(ui, 'map_combo'):
            return -1, None
        for i in range(ui.map_combo.count()):
            if ui.map_combo.itemText(i) == map_name:
                return i, ui.map_combo.itemData(i)
        # 模糊
        names = [ui.map_combo.itemText(i) for i in range(ui.map_combo.count())]
        resolved, _err = fuzzy_resolve(map_name, names)
        if resolved is None:
            return -1, None
        for i in range(ui.map_combo.count()):
            if ui.map_combo.itemText(i) == resolved:
                return i, ui.map_combo.itemData(i)
        return -1, None

    def _find_point(ui, point_name):
        if not hasattr(ui, 'start_point_combo'):
            return -1
        for i in range(ui.start_point_combo.count()):
            if ui.start_point_combo.itemText(i) == point_name:
                return i
        names = [ui.start_point_combo.itemText(i) for i in range(ui.start_point_combo.count())]
        resolved, _ = fuzzy_resolve(point_name, names)
        if resolved is None:
            return -1
        for i in range(ui.start_point_combo.count()):
            if ui.start_point_combo.itemText(i) == resolved:
                return i
        return -1

    def select_map_and_start_point(map_name: str = None,
                                   start_point_name: str = None) -> str:
        ui = ctx.ui
        msgs = []

        if map_name is not None:
            idx, _data = _find_map(ui, map_name)
            if idx < 0:
                return f"未找到地图: {map_name}"
            ui.map_combo.setCurrentIndex(idx)
            msgs.append(f"地图切换为: {ui.map_combo.currentText()}")
            # 切换地图会触发 update_start_points, 此时起点已经是第一个

        if start_point_name is not None:
            idx = _find_point(ui, start_point_name)
            if idx < 0:
                return "; ".join(msgs) + f"; 未找到起点: {start_point_name}"
            ui.start_point_combo.setCurrentIndex(idx)
            msgs.append(f"起点切换为: {ui.start_point_combo.currentText()}")

        if not msgs:
            return "请至少指定 map_name 或 start_point_name。"
        return "; ".join(msgs) + " (未发送,需要调用 confirm_scene 才会生效)"

    registry.register(
        name="select_map_and_start_point",
        description="在场景设置中选择地图和/或起点。只是改动选项,不发送任何指令。"
                    "要让更改生效,需要再调用 confirm_scene。",
        params_schema={
            "type": "object",
            "properties": {
                "map_name":          {"type": "string", "description": "地图名称"},
                "start_point_name":  {"type": "string", "description": "起点名称"},
            },
            "required": []
        },
        callback=select_map_and_start_point,
    )

    # -----------------------------------------------------------------------

    def confirm_scene() -> str:
        try:
            ctx.ui.confirm_scenario_settings()
            return "已确认场景设置,起点坐标已发送到平台,体感方案已按工况更新。"
        except Exception as e:
            return f"确认场景设置失败: {e}"

    registry.register(
        name="confirm_scene",
        description="确认当前选择的地图和起点,把起点坐标发送给平台,"
                    "并根据选择的起点自动更新体感(cueing)方案。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=confirm_scene,
    )

    # -----------------------------------------------------------------------

    def set_condition(condition_name: str) -> str:
        ui = ctx.ui
        if not hasattr(ui, 'condition_combo'):
            return "condition_combo 未就绪。"
        names = [ui.condition_combo.itemText(i)
                 for i in range(ui.condition_combo.count())]
        resolved, err = fuzzy_resolve(condition_name, names)
        if err:
            return err + f" 可用工况: {names}"
        ui.condition_combo.setCurrentText(resolved)
        return f"工况已切换为: {resolved}"

    registry.register(
        name="set_condition",
        description="切换 CarSim 仿真工况(condition_combo 下拉框)。",
        params_schema={
            "type": "object",
            "properties": {
                "condition_name": {"type": "string", "description": "工况名称"}
            },
            "required": ["condition_name"]
        },
        callback=set_condition,
    )

    # -----------------------------------------------------------------------

    def get_current_scene() -> str:
        ui = ctx.ui
        parts = []
        if hasattr(ui, 'map_combo'):
            parts.append(f"地图: {ui.map_combo.currentText()}")
        if hasattr(ui, 'start_point_combo'):
            parts.append(f"起点: {ui.start_point_combo.currentText()}")
        if hasattr(ui, 'condition_combo'):
            parts.append(f"工况: {ui.condition_combo.currentText()}")
        return "; ".join(parts) if parts else "场景信息不可用。"

    registry.register(
        name="get_current_scene",
        description="查询当前场景设置(地图、起点、工况)。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=get_current_scene,
    )
