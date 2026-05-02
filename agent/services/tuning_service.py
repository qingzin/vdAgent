"""车型与悬架调校 service — 封装所有 CarSim COM 和 UI widget 操作。"""


from agent.services._base import BaseService

class TuningService(BaseService):


    @property
    def _carsim(self):
        return self._ctx.main_module.carsim

    @property
    def _vehicle_info(self):
        return self._ctx.main_module.vehicleInfoDic

    @property
    def _vehicle_images(self):
        return self._ctx.main_module.vehicleImagePath

    @property
    def _spring_info(self):
        return self._ctx.main_module.springInfoDic

    @property
    def _aux_m_info(self):
        return self._ctx.main_module.AuxMInfoDic

    @property
    def _mx_tot_info(self):
        return self._ctx.main_module.MxTotInfoDic

    # -- vehicle -------------------------------------------------------

    def select_vehicle(self, vehicle_name: str) -> str:
        """切换车型。返回解析后的车型名称。"""
        from PyQt5.QtGui import QImage, QPixmap
        from PyQt5.QtCore import Qt
        import re

        info = self._vehicle_info[vehicle_name]
        match = re.search(r"(.*):<(.*?)>(.*)", info)
        if match is None:
            return f"无法解析车型信息: {info[:80]}"
        group = match.group(2)

        self._carsim.GoHome()
        self._carsim.BlueLink('#BlueLink2', 'Vehicle: Assembly', vehicle_name, group)

        ui = self._ui
        ui.carName = vehicle_name
        ui.select_car_button.setText(vehicle_name)
        img_path = self._vehicle_images.get(vehicle_name, '')
        if img_path:
            image = QImage(img_path)
            pixmap = QPixmap.fromImage(image).scaled(
                200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            ui.carImage.setPixmap(pixmap)
        ui.UpdateTuningParam()
        return vehicle_name

    def get_vehicle_name(self) -> str:
        return getattr(self._ui, 'carName', '')

    # -- spring --------------------------------------------------------

    def _select_spring_generic(self, page, blue_link, name_attr,
                               button_attr, spin_attr, label, spring_name):
        """通用弹簧选择：支持按名称查找或直接输入刚度数值。"""
        import re

        carsim = self._carsim
        ui = self._ui
        spring_dic = self._spring_info

        if blue_link == '#BlueLink0':
            try:
                value = float(spring_name)
                ui.CurrentVehicleSpringPage(page)
                carsim.Yellow('*KSPRING_L', value)
                carsim.GoHome()
                if hasattr(ui, spin_attr):
                    getattr(ui, spin_attr).setValue(value)
                setattr(ui, name_attr, str(value))
                return f"已设置{label}弹簧刚度为 {value}"
            except ValueError:
                pass

        if spring_name not in spring_dic:
            return None  # caller handles fuzzy resolve
        ui.CurrentVehicleSpringPage(page)
        info = spring_dic[spring_name]
        m = re.search(r"(.*):<(.*?)>(.*)", info)
        if m is None:
            return f"无法解析弹簧信息: {info[:80]}"
        group = m.group(2)
        carsim.BlueLink(blue_link, 'Suspension: Spring', spring_name, group)
        carsim.GoHome()
        setattr(ui, name_attr, spring_name)
        if hasattr(ui, button_attr):
            getattr(ui, button_attr).setText(spring_name)
        return f"已选择{label}弹簧: {spring_name}"

    def set_front_left_spring(self, spring_name: str) -> str:
        return self._select_spring_generic(
            1, '#BlueLink0', 'frontSpringName',
            'select_frontSpring_button', 'frontSpringEditText', '前', spring_name)

    def set_rear_left_spring(self, spring_name: str) -> str:
        return self._select_spring_generic(
            2, '#BlueLink0', 'rearSpringName',
            'select_rearSpring_button', 'rearSpringEditText', '后', spring_name)

    def set_front_right_spring(self, spring_name: str) -> str:
        return self._select_spring_generic(
            1, '#BlueLink3', 'frontRightSpringName',
            'select_frontRightSpring_button', '_noop', '前右', spring_name)

    def set_rear_right_spring(self, spring_name: str) -> str:
        return self._select_spring_generic(
            2, '#BlueLink3', 'rearRightSpringName',
            'select_rearRightSpring_button', '_noop', '后右', spring_name)

    # -- antiroll bar --------------------------------------------------

    def set_antiroll_bar(self, is_front: bool, antiroll_name: str) -> str:
        side = "前" if is_front else "后"
        page = 1 if is_front else 2
        name_attr = 'frontAuxMName' if is_front else 'rearAuxMName'
        button_attr = 'select_frontAuxM_button' if is_front else 'select_rearAuxM_button'

        carsim = self._carsim
        ui = self._ui
        all_names = {**self._aux_m_info, **self._mx_tot_info}

        if antiroll_name not in all_names:
            return None  # caller handles fuzzy resolve

        ui.CurrentVehicleSpringPage(page)
        current_library = carsim.GetBlueLink('#BlueLink2')[0]

        if current_library == 'Suspension: Auxiliary Roll Moment':
            group = carsim.GetBlueLink('#BlueLink2')[2]
            carsim.BlueLink('#BlueLink2', 'Suspension: Auxiliary Roll Moment',
                            antiroll_name, group)
            lib, ds, cat, _ = carsim.GetBlueLink('#BlueLink2')
            carsim.Gotolibrary(lib, ds, cat)
            ring = carsim.GetRing('#RingCtrl0')
            if ring in ('CONSTANT', 'COEFFICIENT'):
                val = float(carsim.GetYellow('*SCALAR'))
                ui.CurrentVehicleSpringPage(page)
                carsim.Yellow('DAUX', val * 0.01)
        elif current_library == 'Suspension: Measured Total Roll Stiffness':
            group = carsim.GetBlueLink('#BlueLink2')[2]
            carsim.BlueLink('#BlueLink2',
                            'Suspension: Measured Total Roll Stiffness',
                            antiroll_name, group)

        carsim.GoHome()
        setattr(ui, name_attr, antiroll_name)
        if hasattr(ui, button_attr):
            getattr(ui, button_attr).setText(antiroll_name)
        return f"已选择{side}轮稳定杆: {antiroll_name}"

    # -- query ---------------------------------------------------------

    def get_current_setup(self) -> str:
        ui = self._ui
        parts = [f"当前车型: {getattr(ui, 'carName', '未知')}"]
        for label, attr in [
            ("前弹簧", 'frontSpringName'), ("后弹簧", 'rearSpringName'),
            ("前右弹簧", 'frontRightSpringName'), ("后右弹簧", 'rearRightSpringName'),
            ("前稳定杆", 'frontAuxMName'), ("后稳定杆", 'rearAuxMName'),
        ]:
            val = getattr(ui, attr, None)
            if val:
                parts.append(f"{label}: {val}")
        return "; ".join(parts)
