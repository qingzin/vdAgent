"""车型与悬架调校 service: 封装 CarSim 与 UI widget 操作。"""

from agent.services._base import BaseService


class TuningService(BaseService):
    @property
    def _carsim(self):
        return self._ctx.main_module.carsim

    @property
    def _vehicle_info(self):
        return self._ctx.main_module.vehicleInfoDic

    @property
    def _spring_info(self):
        return self._ctx.main_module.springInfoDic

    @property
    def _aux_m_info(self):
        return self._ctx.main_module.AuxMInfoDic

    @property
    def _mx_tot_info(self):
        return self._ctx.main_module.MxTotInfoDic

    def _set_button_text_via_ui_handler(self, button_attr: str,
                                        handler_attr: str,
                                        value: str) -> None:
        """Use the same callback path as a manual GUI menu selection."""
        ui = self._ui
        button = getattr(ui, button_attr, None)
        handler = getattr(ui, handler_attr, None)
        if button is None or handler is None:
            raise AttributeError(f"missing UI path: {button_attr}/{handler_attr}")
        button.setText(value)
        handler(value)

    # -- vehicle -------------------------------------------------------

    def select_vehicle(self, vehicle_name: str) -> str:
        """切换车型。返回解析后的车型名称。"""
        self._set_button_text_via_ui_handler(
            "select_car_button", "onCarChange", vehicle_name)
        return vehicle_name

    def get_vehicle_name(self) -> str:
        return getattr(self._ui, "carName", "")

    # -- spring --------------------------------------------------------

    def _select_spring_generic(self, page, blue_link, name_attr,
                               button_attr, spin_attr, handler_attr,
                               edit_handler_attr, label, spring_name):
        """通用弹簧选择: 支持按名称查找或直接输入刚度数值。"""
        import re

        carsim = self._carsim
        ui = self._ui
        spring_dic = self._spring_info

        if blue_link == "#BlueLink0":
            try:
                value = float(spring_name)
                if hasattr(ui, spin_attr):
                    getattr(ui, spin_attr).setValue(value)
                edit_handler = getattr(ui, edit_handler_attr, None)
                if edit_handler is not None:
                    edit_handler()
                else:
                    ui.CurrentVehicleSpringPage(page)
                    carsim.Yellow("*KSPRING_L", value)
                    carsim.GoHome()
                setattr(ui, name_attr, str(value))
                return f"已设置{label}弹簧刚度为 {value}"
            except ValueError:
                pass

        if spring_name not in spring_dic:
            return None  # caller handles fuzzy resolve

        if hasattr(ui, button_attr):
            self._set_button_text_via_ui_handler(
                button_attr, handler_attr, spring_name)
        else:
            ui.CurrentVehicleSpringPage(page)
            info = spring_dic[spring_name]
            match = re.search(r"(.*):<(.*?)>(.*)", info)
            if match is None:
                return f"无法解析弹簧信息: {info[:80]}"
            group = match.group(2)
            carsim.BlueLink(blue_link, "Suspension: Spring", spring_name, group)
            carsim.GoHome()
            setattr(ui, name_attr, spring_name)
        return f"已选择{label}弹簧: {spring_name}"

    def set_front_left_spring(self, spring_name: str) -> str:
        return self._select_spring_generic(
            1, "#BlueLink0", "frontSpringName",
            "select_frontSpring_button", "frontSpringEditText",
            "onFrontSpringChange", "OnFrontSpringTextChanged",
            "前", spring_name)

    def set_rear_left_spring(self, spring_name: str) -> str:
        return self._select_spring_generic(
            2, "#BlueLink0", "rearSpringName",
            "select_rearSpring_button", "rearSpringEditText",
            "onRearSpringChange", "OnRearSpringTextChanged",
            "后", spring_name)

    def set_front_right_spring(self, spring_name: str) -> str:
        return self._select_spring_generic(
            1, "#BlueLink3", "frontRightSpringName",
            "select_frontRightSpring_button", "_noop",
            "onFrontRightSpringChange", "_noop",
            "前右", spring_name)

    def set_rear_right_spring(self, spring_name: str) -> str:
        return self._select_spring_generic(
            2, "#BlueLink3", "rearRightSpringName",
            "select_rearRightSpring_button", "_noop",
            "onRearRightSpringChange", "_noop",
            "后右", spring_name)

    # -- antiroll bar --------------------------------------------------

    def set_antiroll_bar(self, is_front: bool, antiroll_name: str) -> str:
        side = "前" if is_front else "后"
        button_attr = (
            "select_frontAuxM_button" if is_front else "select_rearAuxM_button"
        )
        handler_attr = "onFrontAuxMChange" if is_front else "onRearAuxMChange"
        all_names = {**self._aux_m_info, **self._mx_tot_info}

        if antiroll_name not in all_names:
            return None  # caller handles fuzzy resolve

        if not hasattr(self._ui, button_attr):
            return f"无法找到{side}稳定杆按钮，请先重新读取样件列表"

        self._set_button_text_via_ui_handler(
            button_attr, handler_attr, antiroll_name)
        return f"已选择{side}轮稳定杆: {antiroll_name}"

    # -- query ---------------------------------------------------------

    def get_current_setup(self) -> str:
        ui = self._ui
        parts = [f"当前车型: {getattr(ui, 'carName', '未知')}"]
        for label, attr in [
            ("前弹簧", "frontSpringName"),
            ("后弹簧", "rearSpringName"),
            ("前右弹簧", "frontRightSpringName"),
            ("后右弹簧", "rearRightSpringName"),
            ("前稳定杆", "frontAuxMName"),
            ("后稳定杆", "rearAuxMName"),
        ]:
            val = getattr(ui, attr, None)
            if val:
                parts.append(f"{label}: {val}")
        return "; ".join(parts)
