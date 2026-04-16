"""
Bridge - 胶水层
将 Agent 的 action 注册到 Registry，每个 action 通过胶水函数绕过按钮直接操作

重要：所有胶水函数在主线程（通过 signal/slot）中执行，确保 Qt UI 安全更新

对 main.py 的改动：仅在 SimulatorUI.__init__ 末尾加 2 行：
    from agent.bootstrap import attach_agent
    attach_agent(self)
"""

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


def register_actions(registry, ui):
    """
    将所有 Agent 可控操作注册到 registry

    Args:
        registry: ActionRegistry 实例
        ui: SimulatorUI 实例（主窗口）
    """

    # =========================================================================
    # 1. 选择车型
    # =========================================================================
    def select_vehicle(vehicle_name: str) -> str:
        """选择车型并更新 CarSim 和 UI"""
        import re
        # 导入全局变量（在 main.py 模块级定义）
        import __main__ as main_module
        carsim = main_module.carsim
        vehicleInfoDic = main_module.vehicleInfoDic
        vehicleImagePath = main_module.vehicleImagePath

        if vehicle_name not in vehicleInfoDic:
            available = list(vehicleInfoDic.keys())
            # 模糊匹配：找包含关键词的车型
            matches = [n for n in available if vehicle_name in n]
            if len(matches) == 1:
                vehicle_name = matches[0]
            elif len(matches) > 1:
                return f"找到多个匹配车型：{matches}，请指定更精确的名称。"
            else:
                return f"未找到车型 '{vehicle_name}'。可用车型示例：{available[:5]}..."

        # 更新 CarSim
        vehicleInfo = vehicleInfoDic[vehicle_name]
        pattern = r"(.*):<(.*?)>(.*)"
        match = re.search(pattern, vehicleInfo)
        group = match.group(2)
        carsim.GoHome()
        carsim.BlueLink('#BlueLink2', 'Vehicle: Assembly', vehicle_name, group)

        # 更新 UI
        ui.carName = vehicle_name
        ui.select_car_button.setText(vehicle_name)
        if vehicle_name in vehicleImagePath and vehicleImagePath[vehicle_name]:
            image = QImage(vehicleImagePath[vehicle_name])
            pixmap = QPixmap.fromImage(image).scaled(
                200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            ui.carImage.setPixmap(pixmap)

        # 刷新调校参数面板
        ui.UpdateTuningParam()

        return f"已切换到车型：{vehicle_name}"

    registry.register(
        name="select_vehicle",
        description="选择/切换车型。更改当前 CarSim 仿真使用的车辆模型。",
        params_schema={
            "type": "object",
            "properties": {
                "vehicle_name": {
                    "type": "string",
                    "description": "车型名称，例如 'SUV_baseline' 或包含关键词的部分名称"
                }
            },
            "required": ["vehicle_name"]
        },
        callback=select_vehicle,
    )

    # =========================================================================
    # 2. 选择前弹簧
    # =========================================================================
    def select_front_spring(spring_name: str) -> str:
        """选择前轮弹簧"""
        import __main__ as main_module
        carsim = main_module.carsim
        springInfoDic = main_module.springInfoDic

        # 先检查是否是数值输入模式（常数弹簧刚度）
        try:
            value = float(spring_name)
            # 数值模式：直接设置弹簧刚度
            ui.CurrentVehicleSpringPage(1)
            carsim.Yellow('*KSPRING_L', str(value))
            carsim.GoHome()
            if hasattr(ui, 'frontSpringEditText'):
                ui.frontSpringEditText.setValue(value)
            ui.frontSpringName = str(value)
            return f"已设置前轮弹簧刚度为 {value}"
        except ValueError:
            pass  # 不是数值，按名称处理

        if spring_name not in springInfoDic:
            available = list(springInfoDic.keys())
            matches = [n for n in available if spring_name in n]
            if len(matches) == 1:
                spring_name = matches[0]
            elif len(matches) > 1:
                return f"找到多个匹配：{matches}，请指定更精确的名称。"
            else:
                return f"未找到前弹簧 '{spring_name}'。"

        ui.CurrentVehicleSpringPage(1)
        group = carsim.GetBlueLink('#BlueLink0')[2]
        carsim.BlueLink('#BlueLink0', 'Suspension: Spring', spring_name, group)
        carsim.GoHome()

        # 更新 UI
        ui.frontSpringName = spring_name
        if hasattr(ui, 'select_frontSpring_button'):
            ui.select_frontSpring_button.setText(spring_name)

        return f"已选择前轮弹簧：{spring_name}"

    registry.register(
        name="select_front_spring",
        description="选择前轮弹簧。可以输入弹簧样件名称，或直接输入弹簧刚度数值。",
        params_schema={
            "type": "object",
            "properties": {
                "spring_name": {
                    "type": "string",
                    "description": "弹簧名称或刚度数值（如 '25.5'）"
                }
            },
            "required": ["spring_name"]
        },
        callback=select_front_spring,
    )

    # =========================================================================
    # 3. 选择后弹簧
    # =========================================================================
    def select_rear_spring(spring_name: str) -> str:
        """选择后轮弹簧"""
        import __main__ as main_module
        carsim = main_module.carsim
        springInfoDic = main_module.springInfoDic

        try:
            value = float(spring_name)
            ui.CurrentVehicleSpringPage(2)
            carsim.Yellow('*KSPRING_L', str(value))
            carsim.GoHome()
            if hasattr(ui, 'rearSpringEditText'):
                ui.rearSpringEditText.setValue(value)
            ui.rearSpringName = str(value)
            return f"已设置后轮弹簧刚度为 {value}"
        except ValueError:
            pass

        if spring_name not in springInfoDic:
            available = list(springInfoDic.keys())
            matches = [n for n in available if spring_name in n]
            if len(matches) == 1:
                spring_name = matches[0]
            elif len(matches) > 1:
                return f"找到多个匹配：{matches}，请指定更精确的名称。"
            else:
                return f"未找到后弹簧 '{spring_name}'。"

        ui.CurrentVehicleSpringPage(2)
        group = carsim.GetBlueLink('#BlueLink0')[2]
        carsim.BlueLink('#BlueLink0', 'Suspension: Spring', spring_name, group)
        carsim.GoHome()

        ui.rearSpringName = spring_name
        if hasattr(ui, 'select_rearSpring_button'):
            ui.select_rearSpring_button.setText(spring_name)

        return f"已选择后轮弹簧：{spring_name}"

    registry.register(
        name="select_rear_spring",
        description="选择后轮弹簧。可以输入弹簧样件名称，或直接输入弹簧刚度数值。",
        params_schema={
            "type": "object",
            "properties": {
                "spring_name": {
                    "type": "string",
                    "description": "弹簧名称或刚度数值"
                }
            },
            "required": ["spring_name"]
        },
        callback=select_rear_spring,
    )

    # =========================================================================
    # 4. 选择前稳定杆
    # =========================================================================
    def select_front_antiroll(antiroll_name: str) -> str:
        """选择前轮稳定杆"""
        import __main__ as main_module
        carsim = main_module.carsim
        AuxMInfoDic = main_module.AuxMInfoDic
        MxTotInfoDic = main_module.MxTotInfoDic

        # 合并两个字典查找
        all_names = {**AuxMInfoDic, **MxTotInfoDic}

        if antiroll_name not in all_names:
            available = list(all_names.keys())
            matches = [n for n in available if antiroll_name in n]
            if len(matches) == 1:
                antiroll_name = matches[0]
            elif len(matches) > 1:
                return f"找到多个匹配：{matches}，请指定更精确的名称。"
            else:
                return f"未找到前稳定杆 '{antiroll_name}'。"

        ui.CurrentVehicleSpringPage(1)
        current_library = carsim.GetBlueLink('#BlueLink2')[0]

        if current_library == 'Suspension: Auxiliary Roll Moment':
            group = carsim.GetBlueLink('#BlueLink2')[2]
            carsim.BlueLink('#BlueLink2', 'Suspension: Auxiliary Roll Moment',
                           antiroll_name, group)
            # 如果是常数模式，同步 DAUX
            lib, ds, cat, _ = carsim.GetBlueLink('#BlueLink2')
            carsim.Gotolibrary(lib, ds, cat)
            ring = carsim.GetRing('#RingCtrl0')
            if ring in ('CONSTANT', 'COEFFICIENT'):
                val = float(carsim.GetYellow('*SCALAR'))
                ui.CurrentVehicleSpringPage(1)
                carsim.Yellow('DAUX', val * 0.01)
        elif current_library == 'Suspension: Measured Total Roll Stiffness':
            group = carsim.GetBlueLink('#BlueLink2')[2]
            carsim.BlueLink('#BlueLink2',
                           'Suspension: Measured Total Roll Stiffness',
                           antiroll_name, group)

        carsim.GoHome()

        ui.frontAuxMName = antiroll_name
        if hasattr(ui, 'select_frontAuxM_button'):
            ui.select_frontAuxM_button.setText(antiroll_name)

        return f"已选择前轮稳定杆：{antiroll_name}"

    registry.register(
        name="select_front_antiroll",
        description="选择前轮稳定杆（防倾杆）。更改前轴的辅助侧倾力矩配置。",
        params_schema={
            "type": "object",
            "properties": {
                "antiroll_name": {
                    "type": "string",
                    "description": "稳定杆名称"
                }
            },
            "required": ["antiroll_name"]
        },
        callback=select_front_antiroll,
    )

    # =========================================================================
    # 5. 选择后稳定杆
    # =========================================================================
    def select_rear_antiroll(antiroll_name: str) -> str:
        """选择后轮稳定杆"""
        import __main__ as main_module
        carsim = main_module.carsim
        AuxMInfoDic = main_module.AuxMInfoDic
        MxTotInfoDic = main_module.MxTotInfoDic

        all_names = {**AuxMInfoDic, **MxTotInfoDic}

        if antiroll_name not in all_names:
            available = list(all_names.keys())
            matches = [n for n in available if antiroll_name in n]
            if len(matches) == 1:
                antiroll_name = matches[0]
            elif len(matches) > 1:
                return f"找到多个匹配：{matches}，请指定更精确的名称。"
            else:
                return f"未找到后稳定杆 '{antiroll_name}'。"

        ui.CurrentVehicleSpringPage(2)
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
                ui.CurrentVehicleSpringPage(2)
                carsim.Yellow('DAUX', val * 0.01)
        elif current_library == 'Suspension: Measured Total Roll Stiffness':
            group = carsim.GetBlueLink('#BlueLink2')[2]
            carsim.BlueLink('#BlueLink2',
                           'Suspension: Measured Total Roll Stiffness',
                           antiroll_name, group)

        carsim.GoHome()

        ui.rearAuxMName = antiroll_name
        if hasattr(ui, 'select_rearAuxM_button'):
            ui.select_rearAuxM_button.setText(antiroll_name)

        return f"已选择后轮稳定杆：{antiroll_name}"

    registry.register(
        name="select_rear_antiroll",
        description="选择后轮稳定杆（防倾杆）。更改后轴的辅助侧倾力矩配置。",
        params_schema={
            "type": "object",
            "properties": {
                "antiroll_name": {
                    "type": "string",
                    "description": "稳定杆名称"
                }
            },
            "required": ["antiroll_name"]
        },
        callback=select_rear_antiroll,
    )

    # =========================================================================
    # 6. 设置触感增益
    # =========================================================================
    def set_haptic_gains(friction: float = None, damping: float = None,
                         feedback: float = None, saturation: float = None,
                         overall: float = None, steer_rate: float = None) -> str:
        """设置力反馈触感参数"""
        changes = []

        if friction is not None:
            ui.gain_fri = friction
            ui.gain_fri_spinbox.setValue(friction)
            changes.append(f"摩擦增益={friction}")

        if damping is not None:
            ui.gain_dam = damping
            ui.gain_dam_spinbox.setValue(damping)
            changes.append(f"阻尼增益={damping}")

        if feedback is not None:
            ui.gain_feedback = feedback
            ui.gain_feedback_spinbox.setValue(feedback)
            changes.append(f"回正增益={feedback}")

        if saturation is not None:
            ui.gain_sa = saturation
            ui.gain_sa_spinbox.setValue(saturation)
            changes.append(f"限位增益={saturation}")

        if overall is not None:
            ui.gain_all = overall
            ui.gain_all_spinbox.setValue(overall)
            changes.append(f"手感轻重={overall}")

        if steer_rate is not None:
            ui.sw_rate = steer_rate
            ui.sw_rate_spinbox.setValue(steer_rate)
            changes.append(f"力矩转角曲线转速={steer_rate}")

        if not changes:
            return "未指定任何参数。可设置：friction, damping, feedback, saturation, overall, steer_rate"

        # 保存到配置文件
        ui.save_haptic_gain()

        return f"已更新触感参数：{', '.join(changes)}"

    registry.register(
        name="set_haptic_gains",
        description="设置转向力反馈触感参数。可以一次设置多个参数，未指定的参数保持不变。"
                    "包括：摩擦增益(friction)、阻尼增益(damping)、回正增益(feedback)、"
                    "限位增益(saturation)、手感轻重(overall)、力矩转角曲线转速(steer_rate)。",
        params_schema={
            "type": "object",
            "properties": {
                "friction": {
                    "type": "number",
                    "description": "摩擦增益，范围 -10 到 10"
                },
                "damping": {
                    "type": "number",
                    "description": "阻尼增益，范围 -10 到 10"
                },
                "feedback": {
                    "type": "number",
                    "description": "回正增益，范围 -10 到 10"
                },
                "saturation": {
                    "type": "number",
                    "description": "限位增益，范围 -10 到 10"
                },
                "overall": {
                    "type": "number",
                    "description": "手感轻重（整体增益），范围 -1 到 10"
                },
                "steer_rate": {
                    "type": "number",
                    "description": "力矩转角曲线自定义转速，范围 0 到 100"
                },
            },
            "required": []
        },
        callback=set_haptic_gains,
    )

    # =========================================================================
    # 7. 平台控制指令
    # =========================================================================
    def platform_control(command: int) -> str:
        """发送平台控制指令"""
        command_names = {
            0: "Off（关闭）",
            1: "Disengage（脱开）",
            2: "Consent（同意）",
            3: "ReadyForTraining（准备训练）",
            4: "Engage（接合）",
            5: "Hold（保持）",
            6: "Reset（重置）",
        }

        if command not in command_names:
            return f"无效指令：{command}。有效范围 0-6。"

        ui.sendData2PlatformControl(0, command)
        ui.control_command_input.setText(str(command))

        return f"已发送平台指令：{command} - {command_names[command]}"

    registry.register(
        name="platform_control",
        description="发送运动平台控制指令。"
                    "0=Off关闭, 1=Disengage脱开, 2=Consent同意, "
                    "3=ReadyForTraining准备训练, 4=Engage接合, "
                    "5=Hold保持, 6=Reset重置。",
        params_schema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "integer",
                    "description": "平台控制指令编号（0-6）",
                    "enum": [0, 1, 2, 3, 4, 5, 6]
                }
            },
            "required": ["command"]
        },
        callback=platform_control,
    )

    # =========================================================================
    # 8. 运行 CarSim
    # =========================================================================
    def run_carsim() -> str:
        """运行 CarSim 仿真"""
        try:
            ui.RunDspace()
            return f"CarSim 仿真已执行完成（第 {ui.run_scheme} 组方案）"
        except Exception as e:
            return f"CarSim 运行失败：{e}"

    registry.register(
        name="run_carsim",
        description="运行 CarSim 仿真。执行当前配置的车辆模型仿真计算。",
        params_schema={
            "type": "object",
            "properties": {},
            "required": []
        },
        callback=run_carsim,
    )
