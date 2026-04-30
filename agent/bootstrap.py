"""
Bootstrap - Agent 模块的唯一入口

使用方法 (main.py 里只需要这一行, 永远不变):
    from agent.bootstrap import attach_agent
    attach_agent(self)

以后新增 action 时不需要修改 main.py, 也不需要修改 attach_agent 的签名。
新增 action 在 bridge.py / service/ 目录下完成。
"""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QPushButton

from agent.registry import ActionRegistry
from agent.llm_client import LLMClient
from agent.executor import AgentExecutor
from agent.chat_widget import ChatWidget
from agent.bridge import register_actions
from agent.context import AgentContext
from agent.services.tuning_service import TuningService
from agent.services.simulation_service import SimulationService
from agent.services.recording_service import RecordingService
from agent.services.haptic_service import HapticService
from agent.services.platform_service import PlatformService
from agent.services.scene_service import SceneService
from agent.services.visual_service import VisualService
from agent.services.monitoring_service import MonitoringService
from agent.services.metadata_service import MetadataService
from agent.services.analysis_service import AnalysisService


def attach_agent(main_window, llm_url: str = "http://127.0.0.1:8080"):
    """
    将 Agent 系统挂载到主窗口。

    Args:
        main_window: SimulatorUI 实例
        llm_url: llama-server 地址

    注意签名只有 main_window 一个必需参数, 以后永远不会增加。
    依赖通过 AgentContext 从 main_window 所在模块自动定位。
    """

    # 1. 构造 context, 自动定位 main.py 模块
    ctx = AgentContext(ui=main_window)

    # 2. 注册 service 层
    ctx.register_service('tuning', TuningService(ctx))
    ctx.register_service('simulation', SimulationService(ctx))
    ctx.register_service('recording', RecordingService(ctx))
    ctx.register_service('haptic', HapticService(ctx))
    ctx.register_service('platform', PlatformService(ctx))
    ctx.register_service('scene', SceneService(ctx))
    ctx.register_service('visual', VisualService(ctx))
    ctx.register_service('monitoring', MonitoringService(ctx))
    ctx.register_service('metadata', MetadataService(ctx))
    ctx.register_service('analysis', AnalysisService(ctx))

    # 3. 创建核心组件
    registry = ActionRegistry()
    llm_client = LLMClient(base_url=llm_url)
    executor = AgentExecutor(registry, llm_client, ctx=ctx)
    ctx.llm_client = llm_client  # 供 planning/knowledge action 调用 LLM

    # 4. 注册所有 action
    register_actions(registry, ctx)
    print(f"[Agent] 已注册 {len(registry.get_action_names())} 个操作:")
    for name in registry.get_action_names():
        print(f"  - {name}: {registry.get_description(name)}")

    # 4. 聊天面板
    chat_dock = ChatWidget(executor, parent=main_window)
    main_window.addDockWidget(Qt.RightDockWidgetArea, chat_dock)

    # 5. statusBar 上加 toggle 按钮
    toggle_ai_btn = QPushButton("Toggle AI Assistant")
    toggle_ai_btn.clicked.connect(
        lambda: chat_dock.setVisible(not chat_dock.isVisible())
    )
    main_window.statusBar().addPermanentWidget(toggle_ai_btn)

    # 6. LLM 连接检测
    def check_llm_connection():
        connected = llm_client.check_connection()
        chat_dock.update_connection_status(connected)

    connection_timer = QTimer(main_window)
    connection_timer.timeout.connect(check_llm_connection)
    connection_timer.start(10000)
    QTimer.singleShot(1000, check_llm_connection)

    # 7. 保存引用到 main_window 防 GC
    main_window._agent_context = ctx
    main_window._agent_registry = registry
    main_window._agent_llm_client = llm_client
    main_window._agent_executor = executor
    main_window._agent_chat_dock = chat_dock
    main_window._agent_connection_timer = connection_timer
    main_window._agent_toggle_btn = toggle_ai_btn

    print("[Agent] AI 助手已加载完成")
