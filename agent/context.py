"""
AgentContext - 承载 Agent 执行 action 所需的所有外部依赖

设计原则:
1. main.py 只需要一行 `attach_agent(self)`, 签名永远不变
2. bridge 通过 ctx 访问 ui、ui 所在模块的全局变量、以及逐步建立的 service 层
3. 随着 service 层成熟, bridge 逐步从直接访问模块全局 → 调用 service,
   但 ctx 接口保持稳定
"""

import sys


class AgentContext:
    """
    Agent 的运行时上下文。

    核心字段:
        ui            - SimulatorUI 实例
        main_module   - ui 所在的 Python 模块对象 (通常是 main.py)
                        bridge 通过 ctx.main_module.xxx 访问 main.py 模块级变量,
                        例如 ctx.main_module.vehicleInfoDic, ctx.main_module.carsim
        services      - dict[str, object], 逐步建立的 service 层,
                        由 bridge 在注册 action 时按需注入

    为什么用 main_module 而不是 import __main__:
        __main__ 只在 main.py 作为入口脚本时有效;
        如果 main.py 被其他脚本 import (比如做测试、打包后入口变了),
        __main__ 就不指向它了。
        通过 ui.__class__.__module__ 查 sys.modules 是健壮的——
        无论 main.py 是不是入口, 只要 SimulatorUI 能实例化,
        它所在的模块就能被找到。
    """

    def __init__(self, ui):
        self.ui = ui
        self.main_module = self._locate_module_of(ui)
        self.services = {}  # service 层逐步填充

    @staticmethod
    def _locate_module_of(obj):
        """找到 obj 的类所在的模块对象"""
        module_name = obj.__class__.__module__
        module = sys.modules.get(module_name)
        if module is None:
            raise RuntimeError(
                f"无法定位 {obj.__class__.__name__} 所在模块 '{module_name}'。"
                f"这通常不该发生——请检查 SimulatorUI 的定义位置。"
            )
        return module

    # ---------- 便利访问方法 ----------

    def mod(self, attr_name, default=None):
        """
        从 main 模块取全局变量, 不存在时返回 default。
        用法: ctx.mod('vehicleInfoDic', {})
        """
        return getattr(self.main_module, attr_name, default)

    def require(self, attr_name):
        """
        从 main 模块取全局变量, 不存在则抛错。
        用法: carsim = ctx.require('carsim')
        """
        if not hasattr(self.main_module, attr_name):
            raise AttributeError(
                f"main 模块 '{self.main_module.__name__}' "
                f"没有定义 '{attr_name}'。"
                f"请检查 main.py 是否定义了该全局变量。"
            )
        return getattr(self.main_module, attr_name)

    # ---------- service 层管理 ----------

    def register_service(self, name, service):
        """注册一个 service 到 ctx (由 bridge 或 bootstrap 调用)"""
        self.services[name] = service

    def service(self, name):
        """获取已注册的 service, 未注册时返回 None"""
        return self.services.get(name)

    # ---------- UI 状态检查 ----------

    def is_recording(self) -> bool:
        """检查当前是否处于数据记录状态"""
        ui = self.ui
        return any([
            getattr(ui, 'is_recording_imu', False),
            getattr(ui, 'is_recording_carsim', False),
            getattr(ui, 'is_recording_moog', False),
            getattr(ui, 'is_recording_disusx', False),
            getattr(ui, 'is_recording_visual_compensator', False),
        ])
