"""
仿真相关 action

- run_carsim           运行 CarSim 仿真
- manage_simulation_workspace  管理仿真工作区
- analyze_offline_result       查看并对比离线仿真数据
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
        category="simulation",
        risk_level="medium",
        exposed=True,
    )

    def manage_simulation_workspace(operation: str) -> str:
        op = operation.lower().strip()
        try:
            if op in ("open_simulink", "simulink", "open"):
                ctx.ui.OpenSimulink()
                return "已请求打开 Simulink。"
            if op in ("build_dspace", "build", "compile"):
                ctx.ui.BuildDspace()
                return "已请求编译 DSpace。"
            return "未知 operation。支持: open_simulink / build_dspace"
        except Exception as e:
            return f"仿真工作区操作失败: {e}"

    registry.register(
        name="manage_simulation_workspace",
        description="管理仿真工作区准备动作。当前支持打开 Simulink 和编译 DSpace。",
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

    def analyze_offline_result() -> str:
        try:
            ctx.ui.viewOfflineData()
            return "已跳转到离线数据查看页,正在加载对比结果。"
        except Exception as e:
            return f"查看离线数据失败: {e}"

    registry.register(
        name="analyze_offline_result",
        description="分析离线仿真结果并跳转到结果对比页面。"
                    "用于查看已跑完方案的离线对比和最优方案。",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=analyze_offline_result,
        category="analysis",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
