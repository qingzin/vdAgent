"""
运动平台控制 Service

封装 UI 层的一键启停和平台偏置操作。
底层 UDP 通信由 SimulatorUI 内部处理。
"""


from agent.services._base import BaseService

class PlatformService(BaseService):


    def one_click_start(self) -> str:
        self._ui.one_click_start()
        return "已触发平台一键启动流程 (Reset → Consent → Engage)。"

    def one_click_stop(self) -> str:
        self._ui.one_click_stop()
        return "已触发平台一键关闭流程 (Disengage → Off)。"

    def set_offset(self, x=None, y=None, z=None) -> str:
        ui = self._ui
        cur_x = float(ui.offset_x.text()) if hasattr(ui, 'offset_x') and x is None else 0.0
        cur_y = float(ui.offset_y.text()) if hasattr(ui, 'offset_y') and y is None else 0.0
        cur_z = float(ui.offset_z.text()) if hasattr(ui, 'offset_z') and z is None else 0.0

        nx = cur_x if x is None else float(x)
        ny = cur_y if y is None else float(y)
        nz = cur_z if z is None else float(z)

        if hasattr(ui, 'offset_x'): ui.offset_x.setText(str(nx))
        if hasattr(ui, 'offset_y'): ui.offset_y.setText(str(ny))
        if hasattr(ui, 'offset_z'): ui.offset_z.setText(str(nz))

        ui.sendDataPlatformOffset2(nx, ny, nz)
        return f"已设置平台位置偏置: X={nx}, Y={ny}, Z={nz} (米)"
