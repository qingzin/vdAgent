"""
Agent Executor - Agent 调度核心
负责:接收用户输入 → 调用 LLM → 解析意图 → 请求确认 → 执行操作
"""

try:
    from PyQt5.QtCore import QObject, pyqtSignal, QThread
except ImportError:  # pragma: no cover - used by non-GUI tests.
    class _BoundSignal:
        def __init__(self):
            self._slots = []

        def connect(self, slot):
            self._slots.append(slot)

        def emit(self, *args, **kwargs):
            for slot in list(self._slots):
                slot(*args, **kwargs)

    class pyqtSignal:
        def __init__(self, *args, **kwargs):
            self.name = None

        def __set_name__(self, owner, name):
            self.name = name

        def __get__(self, instance, owner):
            if instance is None:
                return self
            return instance.__dict__.setdefault(self.name, _BoundSignal())

    class QObject:
        def __init__(self, *args, **kwargs):
            super().__init__()

        def moveToThread(self, thread):
            return None

        def deleteLater(self):
            return None

    class QThread:
        def __init__(self):
            self.started = _BoundSignal()
            self.finished = _BoundSignal()

        def start(self):
            self.started.emit()

        def quit(self):
            self.finished.emit()

        def deleteLater(self):
            return None

from agent.memory.models import EngineeringExperienceSeed, ProcessTrace
from agent.memory.store import AgentMemoryStore, NullAgentMemoryStore


SYSTEM_PROMPT = """你是一个驾驶模拟器控制系统的智能助手。用户会用中文自然语言描述想要进行的操作,你需要调用合适的工具来完成。

重要规则:
1. 仔细理解用户意图,选择最匹配的工具
2. 如果用户的描述不够明确,回复文字询问更多信息,不要猜测调用工具
3. 参数值必须严格匹配工具定义中的可选值(如果有 enum 限制)
4. 一次只调用一个工具
5. 用中文回复
6. 遇到复杂底盘目标或主观反馈(例如侧倾大、单移线表现差、方向盘中心区重、起伏舒适性差、修改悬架并验证),优先调用 plan_chassis_task 或 suggest_chassis_tuning 形成方案/建议,不要直接修改弹簧、稳定杆或触感参数
7. 只有当用户明确确认了具体参数修改或准备动作时,才调用 set_spring、set_antiroll_bar、tune_haptic_feedback、prepare_test_scene、run_carsim、start_recording、stop_recording 等操作型工具

当前系统支持的操作领域:
- 车型选择与切换
- 悬架参数调整(弹簧、稳定杆)
- 转向触感/力反馈调节
- 运动平台控制
- CarSim 仿真运行
- 底盘任务规划与调校建议
"""

# 对话历史最多保留多少条消息(user + assistant 共同计数)
# 每轮对话通常 2-3 条(user / assistant / optional tool-confirm user)
# 保留 20 条大约能覆盖最近 7-10 轮
MAX_HISTORY_MESSAGES = 20
AUTO_EXECUTE_CATEGORIES = {"planning", "knowledge"}


class AgentWorker(QObject):
    """在子线程中运行 LLM 调用,避免阻塞 UI"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, llm_client, messages, tools):
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages
        self.tools = tools

    def run(self):
        try:
            response = self.llm_client.chat(
                messages=self.messages,
                tools=self.tools,
                system=SYSTEM_PROMPT,
                temperature=0.3,
            )
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


class AgentExecutor(QObject):
    """
    Agent 执行器

    Signals:
        response_ready: Agent 产生了文本回复 (str)
        confirm_request: Agent 需要用户确认操作 (action_name, params, summary)
        action_done: 操作执行完成 (result_str)
        thinking: Agent 正在思考 (bool)
    """
    response_ready = pyqtSignal(str)
    confirm_request = pyqtSignal(str, dict, str)
    action_done = pyqtSignal(str)
    thinking = pyqtSignal(bool)

    def __init__(self, registry, llm_client, max_history=MAX_HISTORY_MESSAGES,
                 memory_store=None):
        super().__init__()
        self.registry = registry
        self.llm_client = llm_client
        self.memory_store = memory_store or self._build_memory_store()
        self.history = []
        self.max_history = max_history
        self._pending_action = None
        self._worker_thread = None
        self._worker = None
        self._is_busy = False  # 防止并发 LLM 请求

    def process_user_input(self, user_message: str):
        """处理用户输入的自然语言"""
        if self._is_busy:
            self.response_ready.emit("AI 正在处理上一条消息,请稍候...")
            self._write_trace("user_input_rejected", user_message,
                              status="busy")
            return
        self._write_trace("user_input", user_message)
        self._append_history({"role": "user", "content": user_message})
        self._call_llm()

    def _append_history(self, message: dict):
        """追加一条消息到历史,并应用滑动窗口"""
        self.history.append(message)
        self._trim_history()

    def _trim_history(self):
        """
        保留最近 max_history 条消息。
        尽量避免在 user->assistant 配对中间切断(虽然当前实现是简单截断,
        LLM 通常能容忍历史开头是 assistant 消息)
        """
        if len(self.history) > self.max_history:
            # 从头部丢弃,保留最近的
            drop_count = len(self.history) - self.max_history
            self.history = self.history[drop_count:]

    def _call_llm(self):
        """在子线程中调用 LLM"""
        self._is_busy = True
        self.thinking.emit(True)

        tools = self.registry.get_tools_schema()
        self._write_trace("llm_request", payload={"tool_count": len(tools)})

        self._worker_thread = QThread()
        self._worker = AgentWorker(self.llm_client, list(self.history), tools)
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_llm_response)
        self._worker.error.connect(self._on_llm_error)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.error.connect(self._worker_thread.quit)
        # 确保 thread 和 worker 对象在线程结束后被清理
        self._worker_thread.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)

        self._worker_thread.start()

    def _on_llm_response(self, response):
        """处理 LLM 响应"""
        self._is_busy = False
        self.thinking.emit(False)

        if response.has_tool_call:
            name = response.tool_name
            params = response.tool_params or {}
            self._write_trace(
                "llm_tool_call",
                message=f"LLM requested action {name}",
                payload={"params": params},
                action_name=name,
            )

            if not self.registry.has_action(name):
                msg = f"未知操作:{name},请重新描述您的需求。"
                self._write_trace("unknown_action", msg, status="error",
                                  action_name=name,
                                  payload={"params": params})
                self._append_history({"role": "assistant", "content": msg})
                self.response_ready.emit(msg)
                return

            if self._should_auto_execute_action(name):
                self._auto_execute_action(name, params)
                return

            summary = self.registry.format_action_summary(name, params)
            self._pending_action = (name, params)

            self._append_history({
                "role": "assistant",
                "content": f"我将执行以下操作:\n{summary}\n请确认是否执行。"
            })

            self.confirm_request.emit(name, params, summary)
        else:
            text = response.text or "(无响应)"
            self._write_trace("llm_text_response", text)
            self._append_history({"role": "assistant", "content": text})
            self.response_ready.emit(text)

    def _on_llm_error(self, error_msg):
        """处理 LLM 错误"""
        self._is_busy = False
        self.thinking.emit(False)
        msg = f"AI 助手出错:{error_msg}"
        self._write_trace("llm_error", msg, status="error")
        self.response_ready.emit(msg)

    def confirm_action(self):
        """用户确认执行操作"""
        if self._pending_action is None:
            return

        name, params = self._pending_action
        self._pending_action = None
        self._write_trace("confirm_action", "User confirmed action",
                          payload={"params": params}, action_name=name)

        result = self.registry.execute(name, params)
        status = "error" if str(result).startswith(("执行失败", "错误")) else "ok"
        self._write_trace("action_result", result, status=status,
                          payload={"params": params}, action_name=name)
        if status == "ok":
            self._write_experience_seed(name, params, result)

        self._append_history({"role": "user", "content": "确认执行"})
        self._append_history({
            "role": "assistant",
            "content": f"已执行。结果:{result}"
        })

        self.action_done.emit(result)

    def cancel_action(self):
        """用户取消操作"""
        if self._pending_action is None:
            return

        name, params = self._pending_action
        self._pending_action = None
        self._write_trace("cancel_action", "User cancelled action",
                          payload={"params": params}, action_name=name)

        self._append_history({"role": "user", "content": "取消执行"})
        self._append_history({
            "role": "assistant",
            "content": "好的,已取消。请问还有其他需要吗?"
        })

        self.response_ready.emit("操作已取消。")

    def clear_history(self):
        """清空对话历史"""
        self.history.clear()
        self._pending_action = None
        self._write_trace("clear_history", "Conversation history cleared")

    @staticmethod
    def _build_memory_store():
        try:
            return AgentMemoryStore()
        except Exception as exc:
            return NullAgentMemoryStore(reason=str(exc))

    def _should_auto_execute_action(self, action_name: str) -> bool:
        metadata = {}
        if hasattr(self.registry, "get_metadata"):
            metadata = self.registry.get_metadata(action_name)
        category = metadata.get("category")
        risk_level = metadata.get("risk_level", "medium")
        side_effects = metadata.get("side_effects", True)
        if risk_level != "low" or side_effects is not False:
            return False
        return category in AUTO_EXECUTE_CATEGORIES or side_effects is False

    def _auto_execute_action(self, name: str, params: dict):
        self._pending_action = None
        self._write_trace("auto_execute_action", "Auto-executing read-only action",
                          payload={"params": params}, action_name=name)
        result = self.registry.execute(name, params)
        status = "error" if str(result).startswith(("执行失败", "错误")) else "ok"
        self._write_trace("action_result", result, status=status,
                          payload={"params": params}, action_name=name)
        self._append_history({"role": "assistant", "content": result})
        self.response_ready.emit(result)

    def _write_trace(self, event_type: str, message: str = "",
                     payload: dict = None, status: str = "ok",
                     action_name: str = None):
        try:
            self.memory_store.append_trace(ProcessTrace(
                event_type=event_type,
                message=message,
                payload=payload or {},
                status=status,
                action_name=action_name,
            ))
        except Exception:
            # Memory must never block simulator control.
            pass

    def _write_experience_seed(self, action_name: str, params: dict, result: str):
        key_actions = {
            "set_spring",
            "set_antiroll_bar",
            "prepare_test_scene",
            "run_carsim",
            "start_recording",
            "stop_recording",
        }
        if action_name not in key_actions:
            return
        metadata = {}
        if hasattr(self.registry, "get_metadata"):
            metadata = self.registry.get_metadata(action_name)
        lesson = f"Confirmed {action_name} with params={params}; result={result}"
        try:
            self.memory_store.append_experience_seed(EngineeringExperienceSeed(
                action_name=action_name,
                params=params,
                result=result,
                lesson=lesson,
                condition_name=params.get("condition_name") if isinstance(params, dict) else None,
                risk_level=metadata.get("risk_level", "medium"),
            ))
        except Exception:
            pass
