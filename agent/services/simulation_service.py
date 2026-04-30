"""仿真与工作区管理 service。"""


class SimulationService:
    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def _ui(self):
        return self._ctx.ui

    def run_carsim(self) -> str:
        self._ui.RunDspace()
        return f"CarSim 仿真已执行完成 (第 {self._ui.run_scheme} 组方案)"

    def open_simulink(self) -> str:
        self._ui.OpenSimulink()
        return "已请求打开 Simulink。"

    def build_dspace(self) -> str:
        self._ui.BuildDspace()
        return "已请求编译 DSpace。"

    def clear_cache(self):
        self._ui.clear()

    def view_offline_data(self):
        self._ui.viewOfflineData()
