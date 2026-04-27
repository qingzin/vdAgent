"""
车型与悬架调校相关 action

包含:
- select_vehicle            切换车型
- set_spring                统一设置前/后/左/右弹簧
- set_antiroll_bar          统一设置前/后稳定杆
- get_current_setup         查询当前调校状态
"""

import re
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

from ._helpers import require_not_recording, fuzzy_resolve


def register(registry, ctx):
    _register_select_vehicle(registry, ctx)
    _register_spring_action(registry, ctx)
    _register_antiroll_action(registry, ctx)
    _register_get_current_setup(registry, ctx)


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
        category="vehicle",
        risk_level="medium",
        exposed=True,
    )


# ---------------------------------------------------------------------------
# 弹簧
# ---------------------------------------------------------------------------

def _register_spring_action(registry, ctx):

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

    registry.register(
        name="set_spring",
        description="统一设置弹簧。支持 position=front/rear, "
                    "side=left/right/both。可输入弹簧名称或刚度数值。"
                    "对于不分左右的车型, side 默认使用 both。"
                    "对于左右独立车型, side=left/right 用于单侧设置, side=both 会同时设置左右。",
        params_schema={
            "type": "object",
            "properties": {
                "position": {"type": "string", "enum": ["front", "rear"],
                             "description": "前轴或后轴"},
                "side": {"type": "string", "enum": ["left", "right", "both"],
                         "description": "左/右/双侧, 默认 both"},
                "spring_name": {"type": "string", "description": "弹簧名称或刚度数值"}
            },
            "required": ["position", "spring_name"]
        },
        callback=lambda position, spring_name, side="both": _set_spring(
            ctx,
            _select_spring_generic,
            position=position,
            side=side,
            spring_name=spring_name,
        ),
        category="tuning",
        risk_level="high",
        exposed=True,
    )


# ---------------------------------------------------------------------------
# 稳定杆
# ---------------------------------------------------------------------------

def _register_antiroll_action(registry, ctx):

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
        name="set_antiroll_bar",
        description="统一设置前/后防倾杆(稳定杆)或滚转刚度相关数据集。"
                    "通过 position=front/rear 指定前后轴。",
        params_schema={
            "type": "object",
            "properties": {
                "position": {"type": "string", "enum": ["front", "rear"],
                             "description": "前轴或后轴"},
                "antiroll_name": {"type": "string", "description": "稳定杆名称"}
            },
            "required": ["position", "antiroll_name"]
        },
        callback=lambda position, antiroll_name: _select_antiroll(
            position == "front", antiroll_name
        ),
        category="tuning",
        risk_level="high",
        exposed=True,
    )


# ---------------------------------------------------------------------------
# 其他
# ---------------------------------------------------------------------------

def _register_get_current_setup(registry, ctx):

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
        category="query",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )


def _set_spring(ctx, selector, position: str, side: str, spring_name: str) -> str:
    position = position.lower().strip()
    side = (side or "both").lower().strip()

    if position not in ("front", "rear"):
        return "position 仅支持 front 或 rear。"
    if side not in ("left", "right", "both"):
        return "side 仅支持 left、right 或 both。"

    page = 1 if position == "front" else 2
    if position == "front":
        left_cfg = ('#BlueLink0', 'frontSpringName', 'select_frontSpring_button',
                    'frontSpringEditText', '前')
        right_cfg = ('#BlueLink3', 'frontRightSpringName', 'select_frontRightSpring_button',
                     '_noop', '前右')
    else:
        left_cfg = ('#BlueLink0', 'rearSpringName', 'select_rearSpring_button',
                    'rearSpringEditText', '后')
        right_cfg = ('#BlueLink3', 'rearRightSpringName', 'select_rearRightSpring_button',
                     '_noop', '后右')

    messages = []
    numeric_value = None
    try:
        numeric_value = float(spring_name)
    except ValueError:
        numeric_value = None

    if side in ("left", "both"):
        blue_link, name_attr, button_attr, spin_attr, label = left_cfg
        messages.append(selector(page, blue_link, name_attr, button_attr, spin_attr, label, spring_name))

    if side in ("right", "both"):
        blue_link, name_attr, button_attr, spin_attr, label = right_cfg
        # 数值模式目前仅支持主侧, 右侧遇到纯数值时给出更友好的提示
        if numeric_value is not None:
            if side == "right":
                return "右侧弹簧当前仅支持按名称切换,暂不支持直接输入数值刚度。"
            messages.append("右侧弹簧未更新: 当前仅支持按名称切换,暂不支持直接输入数值刚度")
            return "；".join(messages)
        messages.append(selector(page, blue_link, name_attr, button_attr, spin_attr, label, spring_name))

    return "；".join(messages)
