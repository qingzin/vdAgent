"""
仿真相关 action

- run_carsim           运行 CarSim 仿真
- open_simulink        打开 Simulink (对应"打开simulink"按钮)
- build_dspace         编译 (对应"编译"按钮)
- clear_offline_data   清空离线仿真数据缓存
- view_offline_data    查看并对比离线仿真数据
"""

from ._helpers import require_not_recording


def register(registry, ctx):

    def run_carsim() -> str:
        guard = require_not_recording(ctx, "运行 CarSim 仿真")
        if guard:
            return guard
        try:
            ctx.ui.RunDspace()
            return f"CarSim 仿真已执行完成 (第 {ctx.ui.run_scheme} 组方案)"
        except Exception as e:
            return f"CarSim 运行失败: {e}"

    registry.register(
        name="run_carsim",
        description="运行 CarSim 仿真。执行当前配置的车辆模型仿真计算,"
                    "结果保存到离线仿真目录,并更新最优方案。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=run_carsim,
    )

    def open_simulink() -> str:
        try:
            ctx.ui.OpenSimulink()
            return "已请求打开 Simulink。"
        except Exception as e:
            return f"打开 Simulink 失败: {e}"

    registry.register(
        name="open_simulink",
        description="打开 Simulink 模型(对应 GUI 的'打开simulink'按钮)。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=open_simulink,
    )

    def build_dspace() -> str:
        try:
            ctx.ui.BuildDspace()
            return "已请求编译 DSpace。"
        except Exception as e:
            return f"编译失败: {e}"

    registry.register(
        name="build_dspace",
        description="编译 DSpace 模型(对应 GUI 的'编译'按钮)。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=build_dspace,
    )

    def clear_offline_data() -> str:
        """清除 E:\\01_TestData\\01_DCH_Data\\DCH\\离线仿真 目录的所有数据"""
        try:
            result = ctx.ui.clear()
            if result is False:
                return "清理缓存失败,请查看控制台日志。"
            return "离线仿真数据缓存已清理。"
        except Exception as e:
            return f"清理失败: {e}"

    registry.register(
        name="clear_offline_data",
        description="清除所有离线仿真数据缓存(删除 离线仿真 目录下所有文件)。"
                    "危险操作,确认后执行。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=clear_offline_data,
    )

    def view_offline_data() -> str:
        try:
            ctx.ui.viewOfflineData()
            return "已跳转到离线数据查看页,正在加载对比结果。"
        except Exception as e:
            return f"查看离线数据失败: {e}"

    registry.register(
        name="view_offline_data",
        description="跳转到数据处理-一阶起伏页面查看离线仿真数据,"
                    "并自动找出最优方案。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=view_offline_data,
    )
