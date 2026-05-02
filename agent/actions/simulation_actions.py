"""
仿真相关 action — 通过 SimulationService 操作。
"""

from ._helpers import require_not_recording


def register(registry, ctx):
    svc = ctx.service('simulation')

    def run_carsim() -> str:
        guard = require_not_recording(ctx, "运行 CarSim 仿真")
        if guard:
            return guard
        try:
            return svc.run_carsim()
        except Exception as e:
            return f"CarSim 运行失败: {e}"

    registry.register(
        name="run_carsim",
        description="运行 CarSim 仿真。执行当前配置的车辆模型仿真计算。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=run_carsim,
        category="simulation",
        risk_level="medium",
        exposed=True,
    )

    def manage_simulation_workspace(operation: str) -> str:
        guard = require_not_recording(ctx, "管理仿真工作区")
        if guard:
            return guard
        op = operation.lower().strip()
        try:
            if op in ("open_simulink", "simulink", "open"):
                return svc.open_simulink()
            if op in ("build_dspace", "build", "compile"):
                return svc.build_dspace()
            return "未知 operation。支持: open_simulink / build_dspace"
        except Exception as e:
            return f"仿真工作区操作失败: {e}"

    registry.register(
        name="manage_simulation_workspace",
        description="管理仿真工作区准备动作。支持打开 Simulink 和编译 DSpace。",
        params_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["open_simulink", "build_dspace"],
                    "description": "仿真工作区操作类型"
                }
            },
            "required": ["operation"]
        },
        callback=manage_simulation_workspace,
        category="simulation",
        risk_level="medium",
        exposed=True,
    )

    def clear_simulation_cache() -> str:
        guard = require_not_recording(ctx, "清除仿真缓存")
        if guard:
            return guard
        try:
            svc.clear_cache()
            return "已清除离线仿真缓存数据,方案计数器已归零。"
        except Exception as e:
            return f"清除缓存失败: {e}"

    registry.register(
        name="clear_simulation_cache",
        description="清除 CarSim 离线仿真缓存目录下所有文件。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=clear_simulation_cache,
        category="simulation",
        risk_level="high",
        exposed=True,
    )

    def analyze_offline_result() -> str:
        try:
            svc.view_offline_data()
            return "已跳转到离线数据查看页,正在加载对比结果。"
        except Exception as e:
            return f"查看离线数据失败: {e}"

    registry.register(
        name="analyze_offline_result",
        description="分析离线仿真结果并跳转到结果对比页面。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=analyze_offline_result,
        category="analysis",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
