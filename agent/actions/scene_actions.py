"""
场景设置相关 action

- prepare_test_scene          切换工况/地图/起点并确认生效
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

    def prepare_test_scene(condition_name: str = None,
                           map_name: str = None,
                           start_point_name: str = None,
                           confirm: bool = True) -> str:
        ui = ctx.ui
        msgs = []

        if condition_name is not None:
            if not hasattr(ui, 'condition_combo'):
                return "condition_combo 未就绪。"
            names = [ui.condition_combo.itemText(i)
                     for i in range(ui.condition_combo.count())]
            resolved, err = fuzzy_resolve(condition_name, names)
            if err:
                return err + f" 可用工况: {names}"
            ui.condition_combo.setCurrentText(resolved)
            msgs.append(f"工况切换为: {resolved}")

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
            return "请至少指定 condition_name、map_name 或 start_point_name 中的一项。"

        if confirm:
            try:
                ui.confirm_scenario_settings()
                msgs.append("场景已确认并下发到平台")
            except Exception as e:
                msgs.append(f"场景确认失败: {e}")
        else:
            msgs.append("当前仅更新选择,尚未确认生效")

        return "；".join(msgs)

    registry.register(
        name="prepare_test_scene",
        description="准备试验场景。可统一设置工况、地图和起点,"
                    "并默认自动确认生效、下发起点坐标和 cueing 配置。",
        params_schema={
            "type": "object",
            "properties": {
                "condition_name":    {"type": "string", "description": "工况名称"},
                "map_name":          {"type": "string", "description": "地图名称"},
                "start_point_name":  {"type": "string", "description": "起点名称"},
                "confirm":           {"type": "boolean", "description": "是否立即确认生效,默认 true"},
            },
            "required": []
        },
        callback=prepare_test_scene,
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
