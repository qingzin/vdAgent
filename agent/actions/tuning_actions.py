"""
车型与悬架调校相关 action

包含:
- select_vehicle            切换车型
- select_front_spring       选择前左/整体弹簧
- select_rear_spring        选择后左/整体弹簧
- select_front_right_spring 选择前右弹簧(仅左右独立车型)
- select_rear_right_spring  选择后右弹簧(仅左右独立车型)
- select_front_antiroll     选择前稳定杆
- select_rear_antiroll      选择后稳定杆
- refresh_tuning_params     重新读取样件列表
- get_current_setup         查询当前调校状态
"""

import re
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

from ._helpers import require_not_recording, fuzzy_resolve


def register(registry, ctx):
    _register_select_vehicle(registry, ctx)
    _register_spring_actions(registry, ctx)
    _register_antiroll_actions(registry, ctx)
    _register_misc(registry, ctx)


# ---------------------------------------------------------------------------
# 车型
# ---------------------------------------------------------------------------

def _register_select_vehicle(registry, ctx):

    def select_vehicle(vehicle_name: str) -> str:
        guard = require_not_recording(ctx, "切换车型")
        if guard:
            return guard

        vehicle_info_dic = ctx.mod('vehicleInfoDic', {})
        vehicle_image_path = ctx.mod('vehicleImagePath', {})
        carsim = ctx.require('carsim')
        ui = ctx.ui

        resolved, err = fuzzy_resolve(vehicle_name, list(vehicle_info_dic.keys()))
        if err:
            return err + f" 可用车型示例: {list(vehicle_info_dic.keys())[:5]}"
        vehicle_name = resolved

        info = vehicle_info_dic[vehicle_name]
        match = re.search(r"(.*):<(.*?)>(.*)", info)
        group = match.group(2)
        carsim.GoHome()
        carsim.BlueLink('#BlueLink2', 'Vehicle: Assembly', vehicle_name, group)

        ui.carName = vehicle_name
        ui.select_car_button.setText(vehicle_name)
        img_path = vehicle_image_path.get(vehicle_name, '')
        if img_path:
            image = QImage(img_path)
            pixmap = QPixmap.fromImage(image).scaled(
                200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            ui.carImage.setPixmap(pixmap)
        ui.UpdateTuningParam()

        return f"已切换到车型: {vehicle_name}"

    registry.register(
        name="select_vehicle",
        description="选择/切换车型,更改当前 CarSim 仿真使用的车辆模型。",
        params_schema={
            "type": "object",
            "properties": {
                "vehicle_name": {"type": "string", "description": "车型名称或部分关键词"}
            },
            "required": ["vehicle_name"]
        },
        callback=select_vehicle,
    )


# ---------------------------------------------------------------------------
# 弹簧 (4 个 action: 前/后 x 左-整体/右)
# ---------------------------------------------------------------------------

def _register_spring_actions(registry, ctx):

    def _select_spring_generic(page: int, blue_link: str, ui_name_attr: str,
                               ui_button_attr: str, ui_spin_attr: str,
                               side_label: str, spring_name: str) -> str:
        """
        通用弹簧选择逻辑。
        Args:
            page: 1 或 2, 对应 CurrentVehicleSpringPage
            blue_link: '#BlueLink0' (左/整体) 或 '#BlueLink3' (右)
            side_label: 显示给用户的标签如 "前左" / "前右"
        """
        guard = require_not_recording(ctx, f"修改{side_label}弹簧")
        if guard:
            return guard

        carsim = ctx.require('carsim')
        spring_info_dic = ctx.mod('springInfoDic', {})
        ui = ctx.ui

        # 数值模式 (只对 #BlueLink0 即左/整体 有效,
        # 因为数值模式 KSPRING_L 只设主侧)
        if blue_link == '#BlueLink0':
            try:
                value = float(spring_name)
                ui.CurrentVehicleSpringPage(page)
                carsim.Yellow('*KSPRING_L', value)
                carsim.GoHome()
                if hasattr(ui, ui_spin_attr):
                    getattr(ui, ui_spin_attr).setValue(value)
                setattr(ui, ui_name_attr, str(value))
                return f"已设置{side_label}弹簧刚度为 {value}"
            except ValueError:
                pass

        resolved, err = fuzzy_resolve(spring_name, list(spring_info_dic.keys()))
        if err:
            return f"{side_label}弹簧: {err}"
        spring_name = resolved

        ui.CurrentVehicleSpringPage(page)
        group = carsim.GetBlueLink(blue_link)[2]
        carsim.BlueLink(blue_link, 'Suspension: Spring', spring_name, group)
        carsim.GoHome()

        setattr(ui, ui_name_attr, spring_name)
        if hasattr(ui, ui_button_attr):
            getattr(ui, ui_button_attr).setText(spring_name)

        return f"已选择{side_label}弹簧: {spring_name}"

    # 前左/整体
    registry.register(
        name="select_front_spring",
        description="选择前轮(左侧或整体,取决于车型)弹簧。可输入名称或刚度数值。",
        params_schema={
            "type": "object",
            "properties": {
                "spring_name": {"type": "string", "description": "弹簧名称或刚度数值"}
            },
            "required": ["spring_name"]
        },
        callback=lambda spring_name: _select_spring_generic(
            page=1, blue_link='#BlueLink0',
            ui_name_attr='frontSpringName',
            ui_button_attr='select_frontSpring_button',
            ui_spin_attr='frontSpringEditText',
            side_label='前', spring_name=spring_name
        ),
    )

    # 后左/整体
    registry.register(
        name="select_rear_spring",
        description="选择后轮(左侧或整体,取决于车型)弹簧。可输入名称或刚度数值。",
        params_schema={
            "type": "object",
            "properties": {
                "spring_name": {"type": "string", "description": "弹簧名称或刚度数值"}
            },
            "required": ["spring_name"]
        },
        callback=lambda spring_name: _select_spring_generic(
            page=2, blue_link='#BlueLink0',
            ui_name_attr='rearSpringName',
            ui_button_attr='select_rearSpring_button',
            ui_spin_attr='rearSpringEditText',
            side_label='后', spring_name=spring_name
        ),
    )

    # 前右
    registry.register(
        name="select_front_right_spring",
        description="选择前右弹簧(仅左右独立车型可用;不分左右的车型会报错)。",
        params_schema={
            "type": "object",
            "properties": {
                "spring_name": {"type": "string", "description": "弹簧名称"}
            },
            "required": ["spring_name"]
        },
        callback=lambda spring_name: _select_spring_generic(
            page=1, blue_link='#BlueLink3',
            ui_name_attr='frontRightSpringName',
            ui_button_attr='select_frontRightSpring_button',
            ui_spin_attr='_noop',
            side_label='前右', spring_name=spring_name
        ),
    )

    # 后右
    registry.register(
        name="select_rear_right_spring",
        description="选择后右弹簧(仅左右独立车型可用;不分左右的车型会报错)。",
        params_schema={
            "type": "object",
            "properties": {
                "spring_name": {"type": "string", "description": "弹簧名称"}
            },
            "required": ["spring_name"]
        },
        callback=lambda spring_name: _select_spring_generic(
            page=2, blue_link='#BlueLink3',
            ui_name_attr='rearRightSpringName',
            ui_button_attr='select_rearRightSpring_button',
            ui_spin_attr='_noop',
            side_label='后右', spring_name=spring_name
        ),
    )


# ---------------------------------------------------------------------------
# 稳定杆
# ---------------------------------------------------------------------------

def _register_antiroll_actions(registry, ctx):

    def _select_antiroll(is_front: bool, antiroll_name: str) -> str:
        side = "前" if is_front else "后"
        page = 1 if is_front else 2
        ui_name_attr = 'frontAuxMName' if is_front else 'rearAuxMName'
        ui_button_attr = 'select_frontAuxM_button' if is_front else 'select_rearAuxM_button'

        guard = require_not_recording(ctx, f"修改{side}稳定杆")
        if guard:
            return guard

        carsim = ctx.require('carsim')
        aux_m = ctx.mod('AuxMInfoDic', {})
        mx_tot = ctx.mod('MxTotInfoDic', {})
        all_names = {**aux_m, **mx_tot}
        ui = ctx.ui

        resolved, err = fuzzy_resolve(antiroll_name, list(all_names.keys()))
        if err:
            return f"{side}稳定杆: {err}"
        antiroll_name = resolved

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

        setattr(ui, ui_name_attr, antiroll_name)
        if hasattr(ui, ui_button_attr):
            getattr(ui, ui_button_attr).setText(antiroll_name)

        return f"已选择{side}轮稳定杆: {antiroll_name}"

    registry.register(
        name="select_front_antiroll",
        description="选择前轮稳定杆(防倾杆)。",
        params_schema={
            "type": "object",
            "properties": {
                "antiroll_name": {"type": "string", "description": "稳定杆名称"}
            },
            "required": ["antiroll_name"]
        },
        callback=lambda antiroll_name: _select_antiroll(True, antiroll_name),
    )

    registry.register(
        name="select_rear_antiroll",
        description="选择后轮稳定杆(防倾杆)。",
        params_schema={
            "type": "object",
            "properties": {
                "antiroll_name": {"type": "string", "description": "稳定杆名称"}
            },
            "required": ["antiroll_name"]
        },
        callback=lambda antiroll_name: _select_antiroll(False, antiroll_name),
    )


# ---------------------------------------------------------------------------
# 其他
# ---------------------------------------------------------------------------

def _register_misc(registry, ctx):

    def refresh_tuning_params() -> str:
        """重新读取当前车型的调校样件列表(刷新 UI)"""
        try:
            ctx.ui.UpdateTuningParam()
            return "已重新读取样件列表。"
        except Exception as e:
            return f"刷新失败: {e}"

    registry.register(
        name="refresh_tuning_params",
        description="重新读取当前车型的调校样件列表(弹簧、稳定杆等)。"
                    "当 CarSim 数据库有外部修改时使用。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=refresh_tuning_params,
    )

    def get_current_setup() -> str:
        """查询当前车型和悬架配置"""
        ui = ctx.ui
        parts = [f"当前车型: {getattr(ui, 'carName', '未知')}"]
        for label, attr in [
            ("前弹簧",   'frontSpringName'),
            ("后弹簧",   'rearSpringName'),
            ("前右弹簧", 'frontRightSpringName'),
            ("后右弹簧", 'rearRightSpringName'),
            ("前稳定杆", 'frontAuxMName'),
            ("后稳定杆", 'rearAuxMName'),
        ]:
            val = getattr(ui, attr, None)
            if val:
                parts.append(f"{label}: {val}")
        return "; ".join(parts)

    registry.register(
        name="get_current_setup",
        description="查询并返回当前车型及其悬架配置(弹簧、稳定杆名称)。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=get_current_setup,
    )
