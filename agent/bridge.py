"""
Bridge - Action 汇总入口

每个领域的 action 定义在 agent/actions/ 下独立文件,
每个文件暴露一个 register(registry, ctx) 函数, 本文件把它们都调一遍。

新增 action 的两种方式:
  (1) 在已有的 actions/xxx.py 里加函数 + registry.register
  (2) 新建 actions/new_domain.py, 在本文件 ACTION_MODULES 中加一行

main.py 永远不需要修改。
"""

from agent.actions import (
    tuning_actions,
    simulation_actions,
    recording_actions,
    haptic_actions,
    platform_actions,
    scene_actions,
    visual_actions,
    misc_actions,
)


ACTION_MODULES = [
    tuning_actions,      # 车型/弹簧/稳定杆
    simulation_actions,  # CarSim 运行/Simulink/编译/缓存/查看
    recording_actions,   # 数据记录
    haptic_actions,      # 触感力反馈
    platform_actions,    # 平台准备/一键启停
    scene_actions,       # 工况/地图/起点/确认
    visual_actions,      # 视觉补偿
    misc_actions,        # 评价元数据
]


def register_actions(registry, ctx):
    """注册所有 action 到 registry"""
    for module in ACTION_MODULES:
        module.register(registry, ctx)
