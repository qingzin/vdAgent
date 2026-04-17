"""
Service 层 - 业务能力抽象

每个 service 是纯 Python 类, 不依赖 PyQt, 不直接操作 UI widget。
通过构造函数注入 carsim 和需要的数据。

设计目标:
- bridge action 从直接操作 main 模块/UI, 逐步演化为调用 service
- main.py 业务逻辑也可以逐步迁移到 service (但这个迁移由你手工推进,
  agent 模块不强制 main.py 改)
- 一旦 service 建立, agent 和 main.py 都能共用它
"""
