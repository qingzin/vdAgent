"""
Bootstrap - Agent 模块的唯一入口
在 SimulatorUI.__init__ 末尾调用此模块即可完成全部初始化

使用方法（在 main.py 的 SimulatorUI.__init__ 末尾加 2 行）：
    from agent.bootstrap import attach_agent
    attach_agent(self)
"""

from PyQt5.QtCore import Qt, QTimer

from agent.registry import ActionRegistry
from agent.llm_client import LLMClient
from agent.executor import AgentExecutor
from agent.chat_widget import ChatWidget
from agent.bridge import register_actions


def attach_agent(main_window, llm_url: str = "http://127.0.0.1:8080"):
    """
    将 Agent 系统挂载到主窗口

    Args:
        main_window: SimulatorUI 实例
        llm_url: llama-server 的地址
    """

    # 1. 创建核心组件
    registry = ActionRegistry()
    llm_client = LLMClient(base_url=llm_url)
    executor = AgentExecutor(registry, llm_client)

    # 2. 注册所有 action（通过胶水层）
    register_actions(registry, main_window)
    print(f"[Agent] 已注册 {len(registry.get_action_names())} 个操作：")
    for name in registry.get_action_names():
        print(f"  - {name}: {registry.get_description(name)}")

    # 3. 创建聊天面板并挂载到主窗口右侧
    chat_dock = ChatWidget(executor, parent=main_window)
    main_window.addDockWidget(Qt.RightDockWidgetArea, chat_dock)

    # 4. 在 statusBar 添加 AI 面板切换按钮
    toggle_ai_btn = main_window.toggle_button.__class__("Toggle AI Assistant")
    toggle_ai_btn.clicked.connect(
        lambda: chat_dock.setVisible(not chat_dock.isVisible())
    )
    main_window.statusBar().addPermanentWidget(toggle_ai_btn)

    # 5. 定时检查 LLM 连接状态
    def check_llm_connection():
        connected = llm_client.check_connection()
        chat_dock.update_connection_status(connected)

    connection_timer = QTimer(main_window)
    connection_timer.timeout.connect(check_llm_connection)
    connection_timer.start(10000)  # 每 10 秒检查一次

    # 首次检查
    QTimer.singleShot(1000, check_llm_connection)

    # 6. 保存引用到主窗口（防止被 GC 回收）
    main_window._agent_registry = registry
    main_window._agent_llm_client = llm_client
    main_window._agent_executor = executor
    main_window._agent_chat_dock = chat_dock
    main_window._agent_connection_timer = connection_timer

    print("[Agent] AI 助手已加载完成")
