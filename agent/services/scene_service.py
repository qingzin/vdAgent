"""场景设置 service。"""


from agent.services._base import BaseService

class SceneService(BaseService):


    # -- condition -----------------------------------------------------

    def set_condition(self, condition_name: str) -> str:
        ui = self._ui
        names = [ui.condition_combo.itemText(i)
                 for i in range(ui.condition_combo.count())]
        if condition_name in names:
            ui.condition_combo.setCurrentText(condition_name)
            return condition_name
        return None  # caller does fuzzy resolve

    def get_condition(self) -> str:
        if hasattr(self._ui, 'condition_combo'):
            return self._ui.condition_combo.currentText()
        return ""

    # -- map -----------------------------------------------------------

    def _find_combo_item(self, combo_attr: str, name: str):
        combo = getattr(self._ui, combo_attr, None)
        if combo is None:
            return -1, None
        for i in range(combo.count()):
            if combo.itemText(i) == name:
                return i, combo.itemData(i)
        return -1, None

    def set_map(self, map_name: str) -> str:
        idx, _data = self._find_combo_item('map_combo', map_name)
        if idx < 0:
            return None
        self._ui.map_combo.setCurrentIndex(idx)
        return self._ui.map_combo.currentText()

    def get_map(self) -> str:
        if hasattr(self._ui, 'map_combo') and self._ui.map_combo.count() > 0:
            return self._ui.map_combo.currentText()
        return ""

    # -- start point ---------------------------------------------------

    def set_start_point(self, point_name: str) -> str:
        idx, _data = self._find_combo_item('start_point_combo', point_name)
        if idx < 0:
            return None
        self._ui.start_point_combo.setCurrentIndex(idx)
        return self._ui.start_point_combo.currentText()

    def get_start_point(self) -> str:
        if hasattr(self._ui, 'start_point_combo') and self._ui.start_point_combo.count() > 0:
            return self._ui.start_point_combo.currentText()
        return ""

    # -- road segment --------------------------------------------------

    def set_road_segment(self, segment_name: str) -> str:
        idx, _data = self._find_combo_item('road_segment_combo', segment_name)
        if idx < 0:
            return None
        self._ui.road_segment_combo.setCurrentIndex(idx)
        if hasattr(self._ui, 'update_coordinates'):
            self._ui.update_coordinates(idx)
        return self._ui.road_segment_combo.currentText()

    def get_road_segment(self) -> str:
        if hasattr(self._ui, 'road_segment_combo') and self._ui.road_segment_combo.count() > 0:
            return self._ui.road_segment_combo.currentText()
        return ""

    # -- confirm -------------------------------------------------------

    def confirm_scene(self):
        self._ui.confirm_scenario_settings()

    def list_conditions(self) -> list:
        ui = self._ui
        if hasattr(ui, 'condition_combo'):
            return [ui.condition_combo.itemText(i) for i in range(ui.condition_combo.count())]
        return []

    def list_maps(self) -> list:
        ui = self._ui
        if hasattr(ui, 'map_combo'):
            return [ui.map_combo.itemText(i) for i in range(ui.map_combo.count())]
        return []

    def list_start_points(self) -> list:
        ui = self._ui
        if hasattr(ui, 'start_point_combo'):
            return [ui.start_point_combo.itemText(i) for i in range(ui.start_point_combo.count())]
        return []

    def list_road_segments(self) -> list:
        ui = self._ui
        if hasattr(ui, 'road_segment_combo'):
            return [ui.road_segment_combo.itemText(i) for i in range(ui.road_segment_combo.count())]
        return []
