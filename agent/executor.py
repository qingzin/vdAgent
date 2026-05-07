"""
Agent Executor - Agent 调度核心
负责:接收用户输入 → 调用 LLM → 解析意图 → 请求确认 → 执行操作
"""

from dataclasses import dataclass
import re
from uuid import uuid4

try:
    from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer
except ImportError:  # pragma: no cover - used by non-GUI tests.
    class QTimer:
        def __init__(self, parent=None):
            self.timeout = _BoundSignal()

        def setSingleShot(self, v):
            pass

        def start(self, ms=None):
            pass

        def stop(self):
            pass

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
from agent.knowledge.store import KnowledgeStore
from agent.session_store import SessionStore


SYSTEM_PROMPT = """你是一个驾驶模拟器控制系统的智能助手。用户会用中文自然语言描述想要进行的操作,你需要调用合适的工具来完成。

多步执行规则:
- 用户可能一次要求多个操作（如"改弹簧和稳定杆"），你需要依次调用所有必要工具
- 用户一次提出多个明确操作时，必须调用 submit_action_plan 提交完整步骤队列，不要只调用第一步工具
- submit_action_plan 只用于提交计划，steps 中的每一步仍会由程序逐步确认和执行
- 每步执行后，系统会询问"任务是否已全部完成"——已完成则回复"完成"，否则继续
- 如果上一步失败，分析原因并决定是否重试或调整方案
- 最多可连续执行 5 步

重要规则:
1. 仔细理解用户意图,选择最匹配的工具
2. 如果用户的描述不够明确,回复文字询问更多信息,不要猜测调用工具
3. 参数值必须严格匹配工具定义中的可选值(如果有 enum 限制)
4. 用中文回复
5. 遇到复杂底盘目标或主观反馈(例如侧倾大、单移线表现差、方向盘中心区重、起伏舒适性差、修改悬架并验证),优先调用 plan_chassis_task 或 suggest_chassis_tuning 形成方案/建议,不要直接修改弹簧、稳定杆或触感参数
6. 只有当用户明确确认了具体参数修改或准备动作时,才调用 set_spring、set_antiroll_bar、tune_haptic_feedback、prepare_test_scene、run_carsim、start_recording、stop_recording 等操作型工具
7. 不要用普通文本输出"我将执行以下操作...请确认是否执行"；需要确认时必须返回结构化工具调用，由程序生成确认界面
8. 当用户询问"为什么"、寻求原理解释或需要分析时,优先调用 search_knowledge 检索领域知识库,结合当前系统状态给出有依据的回答
9. 如果用户描述了一个有价值的调校经验或规律,主动调用 save_knowledge 将其保存

当前系统支持的操作领域:
- 车型选择与切换
- 悬架参数调整(弹簧、稳定杆)
- 转向触感/力反馈调节
- 运动平台控制
- CarSim 仿真运行
- 底盘任务规划与调校建议
- 领域知识库检索与积累
- 历史数据加载与分析
- 实时报警监控
"""

SYSTEM_PROMPT_WITH_CONTEXT = SYSTEM_PROMPT + """

=== 当前系统状态 ===
{context}
"""


def _build_context_snapshot(ui) -> str:
    """构建当前系统状态的文本快照,供 LLM 推理使用。"""
    parts = []

    # 车型与悬架
    car = getattr(ui, 'carName', None)
    if car:
        parts.append(f"当前车型: {car}")

    setup_fields = [
        ('frontSpringName', '前弹簧'),
        ('rearSpringName', '后弹簧'),
        ('frontRightSpringName', '前右弹簧'),
        ('rearRightSpringName', '后右弹簧'),
        ('frontAuxMName', '前稳定杆'),
        ('rearAuxMName', '后稳定杆'),
    ]
    current_setup = []
    for attr, label in setup_fields:
        val = getattr(ui, attr, None)
        if val:
            current_setup.append(f"{label}={val}")
    if current_setup:
        parts.append("悬架配置: " + ", ".join(current_setup))

    # 场景
    scene_parts = []
    if hasattr(ui, 'map_combo') and ui.map_combo.count() > 0:
        scene_parts.append(f"地图={ui.map_combo.currentText()}")
    if hasattr(ui, 'start_point_combo') and ui.start_point_combo.count() > 0:
        scene_parts.append(f"起点={ui.start_point_combo.currentText()}")
    if hasattr(ui, 'condition_combo') and ui.condition_combo.count() > 0:
        scene_parts.append(f"工况={ui.condition_combo.currentText()}")
    if scene_parts:
        parts.append("当前场景: " + ", ".join(scene_parts))

    # 触感参数
    haptic_fields = [
        ('gain_fri', '摩擦增益'),
        ('gain_dam', '阻尼增益'),
        ('gain_feedback', '回正增益'),
        ('gain_sa', '限位增益'),
        ('gain_all', '手感轻重'),
    ]
    haptic_parts = []
    for attr, label in haptic_fields:
        val = getattr(ui, attr, None)
        if val is not None:
            haptic_parts.append(f"{label}={val}")
    if haptic_parts:
        parts.append("触感参数: " + ", ".join(haptic_parts))

    # 记录状态
    rec_flags = []
    for label, attr in [
        ('IMU', 'is_recording_imu'),
        ('CarSim', 'is_recording_carsim'),
        ('MOOG', 'is_recording_moog'),
    ]:
        if getattr(ui, attr, False):
            rec_flags.append(label)
    parts.append("记录状态: " + ("记录中(" + ",".join(rec_flags) + ")" if rec_flags else "未记录"))

    # 平台/仿真
    parts.append(f"方案计数: 第{getattr(ui, 'run_scheme', 0)}组")
    parts.append(f"报警监控: {'开启' if getattr(ui, 'alarm_enabled', False) else '关闭'}")

    return "\n".join(f"- {p}" for p in parts)

# 对话历史最多保留多少条消息(user + assistant 共同计数)
# 每轮对话通常 2-3 条(user / assistant / optional tool-confirm user)
# 保留 20 条大约能覆盖最近 7-10 轮
MAX_HISTORY_MESSAGES = 20
MAX_HISTORY_TOKENS_EST = 6000
MAX_HISTORY_MESSAGE_CHARS = 1200
MAX_HISTORY_RETRY_MESSAGES = 4
MAX_HISTORY_RETRY_MESSAGE_CHARS = 500
HISTORY_TRUNCATION_SUFFIX = "\n...(history truncated)"
AUTO_EXECUTE_CATEGORIES = {"planning", "knowledge"}
ACTION_PLAN_TOOL_NAME = "submit_action_plan"
ACTION_PLAN_MAX_STEPS = 5
RECOVERABLE_LLM_ERROR_MARKERS = (
    "400",
    "bad request",
    "context",
    "context length",
    "maximum context",
    "too many tokens",
    "token",
)


class ExecutorState:
    IDLE = "idle"
    WAITING_LLM = "waiting_llm"
    WAITING_CONFIRMATION = "waiting_confirmation"
    EXECUTING_ACTION = "executing_action"
    FAILED = "failed"
    SHUTTING_DOWN = "shutting_down"


class ConfirmationStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionPlanStepStatus:
    PENDING = "pending"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ConfirmationRecord:
    confirmation_id: str
    action_name: str
    params: dict
    summary: str
    status: str = ConfirmationStatus.PENDING
    result: str = ""


@dataclass
class ActionPlanStep:
    action_name: str
    params: dict
    summary: str = ""
    reason: str = ""
    status: str = ActionPlanStepStatus.PENDING
    result: str = ""


class AgentWorker(QObject):
    """在子线程中运行 LLM 调用,避免阻塞 UI"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, llm_client, messages, tools, system_prompt=SYSTEM_PROMPT):
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages
        self.tools = tools
        self.system_prompt = system_prompt

    def run(self):
        try:
            response = self.llm_client.chat(
                messages=self.messages,
                tools=self.tools,
                system=self.system_prompt,
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
        confirm_request: Agent 需要用户确认操作 (confirmation_id, action_name, params, summary)
        action_done: 操作执行完成 (result_str)
        thinking: Agent 正在思考 (bool)
        state_changed: Agent 执行状态变化 (state)
    """
    response_ready = pyqtSignal(str)
    confirm_request = pyqtSignal(str, str, dict, str)
    action_done = pyqtSignal(str)
    thinking = pyqtSignal(bool)
    state_changed = pyqtSignal(str)

    def __init__(self, registry, llm_client, max_history=MAX_HISTORY_MESSAGES,
                 memory_store=None, ctx=None):
        super().__init__()
        self.registry = registry
        self.llm_client = llm_client
        self.memory_store = memory_store or self._build_memory_store()
        self._ctx = ctx  # AgentContext, 用于获取 UI 引用构建上下文
        self.history = []
        self.max_history = max_history
        self._pending_action = None
        self._pending_confirmation = None
        self.recent_plan_context = None
        self.state = ExecutorState.IDLE
        self._worker_thread = None
        self._worker = None
        self._is_busy = False
        self._call_generation = 0
        self._llm_recovery_attempted = False
        self._auto_step_count = 0
        self._auto_step_max = 5
        self._multi_step_active = False
        self._active_plan_id = None
        self._pending_plan_steps = []
        self._current_plan_step = None
        self._session_store = SessionStore()
        self._session_id = None
        from collections import deque
        self._message_queue = deque(maxlen=20)
        self._busy_watchdog = QTimer(self)
        self._busy_watchdog.setSingleShot(True)
        self._busy_watchdog.timeout.connect(self._on_busy_timeout)

    def process_user_input(self, user_message: str):
        """处理用户输入的自然语言，忙碌时排队"""
        if self._is_busy or self.state in {
            ExecutorState.WAITING_LLM,
            ExecutorState.WAITING_CONFIRMATION,
            ExecutorState.EXECUTING_ACTION,
        }:
            self._message_queue.append(user_message)
            self._write_trace("user_input_queued", user_message,
                              status="busy", payload={
                                  "queue_len": len(self._message_queue),
                                  "state": self.state,
                              })
            return
        self._write_trace("user_input", user_message)
        self._llm_recovery_attempted = False
        self._auto_step_count = 0
        self._multi_step_active = True
        self._clear_action_plan()
        self._append_history({"role": "user", "content": user_message})
        self._call_llm()

    def _drain_queue(self):
        """处理消息队列中的下一条消息"""
        if self._message_queue:
            next_msg = self._message_queue.popleft()
            self._write_trace("user_input_dequeued", next_msg,
                              payload={"remaining": len(self._message_queue)})
            self._llm_recovery_attempted = False
            self._auto_step_count = 0
            self._multi_step_active = True
            self._clear_action_plan()
            self._append_history({"role": "user", "content": next_msg})
            self._call_llm()

    def _set_state(self, state: str):
        """显式更新 executor 状态，并写入审计轨迹。"""
        if self.state == state:
            return
        previous = self.state
        self.state = state
        self._write_trace(
            "state_changed",
            f"{previous} -> {state}",
            payload={"from": previous, "to": state},
        )
        self.state_changed.emit(state)

    def _append_history(self, message: dict):
        """追加一条消息到历史,并应用滑动窗口。"""
        message = self._bounded_history_message(message, MAX_HISTORY_MESSAGE_CHARS)
        self.history.append(message)
        self._trim_history()

    def _trim_history(self):
        """按条数和估算 token 数双重截断对话历史。"""
        if len(self.history) > self.max_history:
            drop_count = len(self.history) - self.max_history
            self.history = self.history[drop_count:]

        total = sum(self._estimate_history_tokens(m.get("content", ""))
                    for m in self.history)
        while total > MAX_HISTORY_TOKENS_EST and len(self.history) > 1:
            removed = self.history.pop(0)
            total -= self._estimate_history_tokens(removed.get("content", ""))

    @staticmethod
    def _bounded_history_message(message: dict, max_chars: int) -> dict:
        content = message.get("content", "")
        if not isinstance(content, str):
            content = str(content)
        if len(content) <= max_chars:
            return message
        bounded = dict(message)
        bounded["content"] = content[:max_chars] + HISTORY_TRUNCATION_SUFFIX
        return bounded

    @staticmethod
    def _estimate_history_tokens(content: str) -> int:
        if not isinstance(content, str):
            content = str(content)
        return max(1, len(content))

    def _call_llm(self):
        """在子线程中调用 LLM,注入当前系统上下文"""
        self._set_state(ExecutorState.WAITING_LLM)
        self._is_busy = True
        self.thinking.emit(True)
        self._busy_watchdog.start(65000)

        self._discard_worker_thread()
        self._discard_worker()

        self._call_generation += 1
        generation = self._call_generation

        tools = self._tools_with_action_plan_schema()
        self._write_trace("llm_request", payload={"tool_count": len(tools)})

        context_text = self._build_full_context()

        self._worker_thread = QThread()
        self._worker = AgentWorker(self.llm_client, list(self.history), tools,
                                   system_prompt=context_text)
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)

        # 用 generation 守卫防止旧线程响应污染新流程状态
        def on_finished(response):
            if self._call_generation == generation:
                self._on_llm_response(response)

        def on_error(error_msg):
            if self._call_generation == generation:
                self._on_llm_error(error_msg)

        self._worker.finished.connect(on_finished)
        self._worker.error.connect(on_error)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.error.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)

        self._worker_thread.start()

    def _build_full_context(self) -> str:
        """构建包含当前系统状态、知识库和近期经验的完整上下文。"""
        snapshot = _build_context_snapshot(self._get_ui())
        experiences = self._format_recent_experiences()
        if experiences:
            snapshot += "\n\n近期操作经验:\n" + experiences
        knowledge = self._format_knowledge_context()
        if knowledge:
            snapshot += "\n\n相关领域知识:\n" + knowledge
        return SYSTEM_PROMPT_WITH_CONTEXT.replace("{context}", snapshot)

    def _format_knowledge_context(self) -> str:
        """从知识库检索与当前上下文相关的条目。"""
        try:
            store = KnowledgeStore()
            keyword = self._extract_recent_keywords()
            entries = store.search(keyword=keyword, limit=4)
            if not entries:
                return ""
            lines = []
            for e in entries:
                title = e["meta"].get("title", e["filename"])
                lines.append(f"- {title}: {e['summary'][:120]}")
            return "\n".join(lines) if lines else ""
        except Exception:
            return ""

    def _extract_recent_keywords(self) -> str:
        """从最近用户消息中提取中文关键词用于知识检索。"""
        user_msgs = [m.get("content", "") for m in self.history[-6:]
                     if m.get("role") == "user"]
        text = " ".join(user_msgs)
        # 取最近用户的自然语言输入作为搜索关键词
        if user_msgs:
            return user_msgs[-1][:80]
        return text[:80]

    def _get_ui(self):
        """获取 UI 引用。"""
        if self._ctx is not None:
            return self._ctx.ui
        return None

    def _format_recent_experiences(self) -> str:
        """格式化最近的经验种子为文本。"""
        try:
            seeds = self.memory_store.recent_experience_seeds(limit=5)
        except Exception:
            return ""
        if not seeds:
            return ""
        lines = []
        for s in seeds:
            if not isinstance(s, dict):
                continue
            action = s.get("action_name", "?")
            result = str(s.get("result", ""))[:100]
            condition = s.get("condition_name", "")
            ctx_str = f" (工况:{condition})" if condition else ""
            lines.append(f"- {action}{ctx_str}: {result}")
        return "\n".join(lines)

    def _tools_with_action_plan_schema(self) -> list:
        tools = list(self.registry.get_tools_schema())
        tools.append({
            "type": "function",
            "function": {
                "name": ACTION_PLAN_TOOL_NAME,
                "description": (
                    "提交一个多步操作计划。用户一次要求多个明确操作时必须使用。"
                    "该工具只提交步骤队列,每一步会由程序逐步确认后执行。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "steps": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": ACTION_PLAN_MAX_STEPS,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action_name": {
                                        "type": "string",
                                        "description": "已注册业务 action 名称",
                                    },
                                    "params": {
                                        "type": "object",
                                        "description": "传给 action 的参数对象",
                                    },
                                    "reason": {
                                        "type": "string",
                                        "description": "为什么需要这一步,可选",
                                    },
                                },
                                "required": ["action_name", "params"],
                            },
                        }
                    },
                    "required": ["steps"],
                },
            },
        })
        return tools

    def _on_llm_response(self, response):
        """处理 LLM 响应"""
        self._stop_busy_watchdog()

        tool_calls = self._iter_tool_calls(response)
        if tool_calls:
            if len(tool_calls) > 1:
                self._start_action_plan_from_calls(tool_calls)
                return
            name, params = tool_calls[0]
            self._handle_tool_call(name, params)
            return

        text = response.text or "(无响应)"
        self._handle_llm_text_response(text)

    def _iter_tool_calls(self, response) -> list:
        calls = []
        for call in getattr(response, "tool_calls", []) or []:
            name = call.get("name")
            params = call.get("arguments") or call.get("params") or {}
            if name:
                calls.append((name, params))
        if not calls and getattr(response, "has_tool_call", False):
            calls.append((response.tool_name, response.tool_params or {}))
        return calls

    def _handle_tool_call(self, name: str, params: dict):
        self._write_trace(
            "llm_tool_call",
            message=f"LLM requested action {name}",
            payload={"params": params},
            action_name=name,
        )

        if name == ACTION_PLAN_TOOL_NAME:
            self._start_action_plan(params.get("steps", []))
            return

        if not self.registry.has_action(name):
            msg = f"未知操作:{name},请重新描述您的需求。"
            self._write_trace("unknown_action", msg, status="error",
                              action_name=name,
                              payload={"params": params})
            self._append_history({"role": "assistant", "content": msg})
            self.response_ready.emit(msg)
            self._stop_multi_step()
            self._set_state(ExecutorState.IDLE)
            self._drain_queue()
            return

        if self._should_auto_execute_action(name):
            self._auto_execute_action(name, params)
            return

        self._multi_step_active = True
        self._request_action_confirmation(name, params)

    def _handle_llm_text_response(self, text: str):
        if self._is_recoverable_llm_error(text):
            self._retry_llm_with_compacted_history(text)
            return
        self._write_trace("llm_text_response", text)
        parsed = self._parse_pseudo_confirmation_text(text)
        if parsed:
            name, params = parsed
            self._write_trace(
                "pseudo_confirmation_converted",
                "Converted non-structured confirmation text to confirm_request",
                payload={"params": params},
                action_name=name,
            )
            self._request_action_confirmation(name, params)
            return
        if self._looks_like_pseudo_confirmation(text):
            msg = "模型返回了非结构化确认，请重新发起或简化指令。"
            self._write_trace("action_plan_invalid", msg, status="error",
                              payload={"text": text[:500]})
            self._append_history({"role": "assistant", "content": msg})
            self._stop_multi_step()
            self._clear_action_plan()
            self._set_state(ExecutorState.IDLE)
            self.response_ready.emit(msg)
            self._drain_queue()
            return
        self._append_history({"role": "assistant", "content": text})
        self._auto_step_count = 0
        self._multi_step_active = False
        self._clear_action_plan()
        self._set_state(ExecutorState.IDLE)
        self.response_ready.emit(text)
        self._drain_queue()

    def _stop_busy_watchdog(self):
        self._busy_watchdog.stop()
        self._is_busy = False
        self.thinking.emit(False)

    def _on_busy_timeout(self):
        """看门狗超时：强制重置 _is_busy，防止 agent 永久卡死。"""
        self._stop_busy_watchdog()
        self._stop_multi_step()
        self._set_state(ExecutorState.FAILED)
        self.response_ready.emit("AI 响应超时，请重试。")
        self._drain_queue()

    def _on_llm_error(self, error_msg):
        """处理 LLM 错误"""
        self._stop_busy_watchdog()
        if self._is_recoverable_llm_error(error_msg):
            self._retry_llm_with_compacted_history(error_msg)
            return
        self._auto_step_count = 0
        self._multi_step_active = False
        self._set_state(ExecutorState.FAILED)
        msg = f"AI 助手出错:{error_msg}"
        self._write_trace("llm_error", msg, status="error")
        self.response_ready.emit(msg)
        self._drain_queue()

    def _is_recoverable_llm_error(self, error_msg: str) -> bool:
        msg = str(error_msg).lower()
        return any(marker in msg for marker in RECOVERABLE_LLM_ERROR_MARKERS)

    def _retry_llm_with_compacted_history(self, error_msg: str):
        self._stop_busy_watchdog()
        if self._llm_recovery_attempted:
            self._auto_step_count = 0
            self._multi_step_active = False
            self._set_state(ExecutorState.FAILED)
            msg = f"AI 助手出错:{error_msg}"
            self._write_trace("llm_error", msg, status="error")
            self.response_ready.emit(msg)
            self._drain_queue()
            return

        self._llm_recovery_attempted = True
        self.history = [
            self._bounded_history_message(m, MAX_HISTORY_RETRY_MESSAGE_CHARS)
            for m in self.history[-MAX_HISTORY_RETRY_MESSAGES:]
        ]
        self._trim_history()
        self._write_trace(
            "llm_retry_compacted_history",
            str(error_msg),
            status="retry",
            payload={"history_len": len(self.history)},
        )
        self._call_llm()

    def _request_action_confirmation(self, action_name: str, params: dict,
                                     plan_step: ActionPlanStep = None):
        summary = self._build_confirmation_summary(action_name, params)
        if plan_step is not None:
            plan_step.summary = summary
            plan_step.status = ActionPlanStepStatus.CONFIRMING
            self._write_trace(
                "action_plan_step_confirming",
                f"Plan step waiting confirmation for {action_name}",
                payload={
                    "plan_id": self._active_plan_id,
                    "params": params,
                    "summary": summary,
                    "remaining": len(self._pending_plan_steps),
                },
                action_name=action_name,
            )
        confirmation = self._create_confirmation(action_name, params, summary)
        self._append_history({
            "role": "assistant",
            "content": f"待用户确认 {action_name}({params})"
        })
        self._set_state(ExecutorState.WAITING_CONFIRMATION)
        self.confirm_request.emit(
            confirmation.confirmation_id,
            action_name,
            params,
            summary,
        )

    def _start_action_plan_from_calls(self, tool_calls: list):
        steps = [
            {"action_name": name, "params": params, "reason": "LLM returned multiple tool calls"}
            for name, params in tool_calls
        ]
        self._start_action_plan(steps)

    def _start_action_plan(self, raw_steps):
        steps, error = self._validate_action_plan_steps(raw_steps)
        if error:
            self._write_trace("action_plan_invalid", error, status="error",
                              payload={"steps": raw_steps})
            self._append_history({"role": "assistant", "content": error})
            self._clear_action_plan()
            self._stop_multi_step()
            self._set_state(ExecutorState.IDLE)
            self.response_ready.emit(error)
            self._drain_queue()
            return

        self._active_plan_id = uuid4().hex
        self._pending_plan_steps = steps
        self._current_plan_step = None
        self._auto_step_count = 0
        self._multi_step_active = False
        self._write_trace(
            "action_plan_created",
            f"Action plan {self._active_plan_id} created",
            payload={
                "plan_id": self._active_plan_id,
                "steps": [
                    {"action_name": s.action_name, "params": s.params, "reason": s.reason}
                    for s in steps
                ],
            },
        )
        self._append_history({
            "role": "assistant",
            "content": "已创建执行计划: " + " -> ".join(s.action_name for s in steps),
        })
        self._emit_next_plan_confirmation()

    def _validate_action_plan_steps(self, raw_steps):
        if not isinstance(raw_steps, list) or not raw_steps:
            return [], "执行计划为空，请重新描述您的需求。"
        if len(raw_steps) > ACTION_PLAN_MAX_STEPS:
            return [], f"执行计划超过最大步骤数 {ACTION_PLAN_MAX_STEPS}，请拆分后重试。"

        steps = []
        for index, raw in enumerate(raw_steps, start=1):
            if not isinstance(raw, dict):
                return [], f"执行计划第 {index} 步格式错误。"
            action_name = raw.get("action_name")
            params = raw.get("params") or {}
            reason = raw.get("reason", "")
            if action_name == ACTION_PLAN_TOOL_NAME:
                return [], "执行计划不能嵌套 submit_action_plan。"
            if not action_name or not self.registry.has_action(action_name):
                return [], f"执行计划第 {index} 步包含未知操作: {action_name}"
            metadata = self.registry.get_metadata(action_name)
            if metadata.get("exposed") is False:
                return [], f"执行计划第 {index} 步包含未暴露操作: {action_name}"
            if not isinstance(params, dict):
                return [], f"执行计划第 {index} 步参数必须是对象。"
            steps.append(ActionPlanStep(
                action_name=action_name,
                params=dict(params),
                reason=str(reason) if reason else "",
            ))
        return steps, None

    def _emit_next_plan_confirmation(self):
        if not self._pending_plan_steps:
            completed_plan_id = self._active_plan_id
            self._clear_action_plan()
            self._stop_multi_step()
            self._set_state(ExecutorState.IDLE)
            self._write_trace(
                "action_plan_completed",
                f"Action plan {completed_plan_id} completed",
                payload={"plan_id": completed_plan_id},
            )
            self._append_history({"role": "assistant", "content": "执行计划已完成。"})
            self.response_ready.emit("完成")
            self._drain_queue()
            return

        step = self._pending_plan_steps.pop(0)
        self._current_plan_step = step
        self._request_action_confirmation(step.action_name, step.params, plan_step=step)

    def _clear_action_plan(self):
        self._active_plan_id = None
        self._pending_plan_steps = []
        self._current_plan_step = None

    def _looks_like_pseudo_confirmation(self, text: str) -> bool:
        return (
            "我将执行以下操作" in text
            and "请确认是否执行" in text
            and "参数" in text
        )

    def _parse_pseudo_confirmation_text(self, text: str):
        if not self._looks_like_pseudo_confirmation(text):
            return None
        action_name = None
        for name in self.registry.get_action_names():
            if name in text:
                action_name = name
                break
            desc = self.registry.get_description(name)
            if desc and desc in text:
                action_name = name
                break
        if not action_name:
            return None
        params = self._parse_pseudo_confirmation_params(text)
        return action_name, params

    def _parse_pseudo_confirmation_params(self, text: str) -> dict:
        match = re.search(r"参数[:：]\s*(.+)", text, re.DOTALL)
        if not match:
            return {}
        params_text = match.group(1).strip()
        params_text = params_text.split("\n", 1)[0]
        params = {}
        for item in re.split(r"[,，]\s*", params_text):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            params[key] = self._coerce_pseudo_param_value(value)
        return params

    @staticmethod
    def _coerce_pseudo_param_value(value: str):
        if value in {"True", "true", "是"}:
            return True
        if value in {"False", "false", "否"}:
            return False
        return value

    def _create_confirmation(self, action_name: str, params: dict, summary: str) -> ConfirmationRecord:
        if self._pending_confirmation is not None:
            self._pending_confirmation.status = ConfirmationStatus.EXPIRED
        confirmation = ConfirmationRecord(
            confirmation_id=uuid4().hex,
            action_name=action_name,
            params=dict(params),
            summary=summary,
        )
        self._pending_confirmation = confirmation
        self._pending_action = (action_name, params)
        self._set_state(ExecutorState.WAITING_CONFIRMATION)
        self._write_trace(
            "confirmation_created",
            f"Confirmation {confirmation.confirmation_id} for {action_name}",
            payload={
                "confirmation_id": confirmation.confirmation_id,
                "params": params,
                "summary": summary,
            },
            action_name=action_name,
        )
        return confirmation

    def has_pending_confirmation(self, confirmation_id: str = None) -> bool:
        confirmation = self._pending_confirmation
        if confirmation is None or confirmation.status != ConfirmationStatus.PENDING:
            return False
        if confirmation_id is not None and confirmation.confirmation_id != confirmation_id:
            return False
        return True

    def _reject_stale_confirmation(self, confirmation_id: str, operation: str) -> bool:
        if self.has_pending_confirmation(confirmation_id):
            return False
        self._write_trace(
            f"stale_{operation}",
            f"Stale {operation} ignored",
            status="stale",
            payload={
                "confirmation_id": confirmation_id,
                "pending_confirmation_id": (
                    self._pending_confirmation.confirmation_id
                    if self._pending_confirmation is not None else None
                ),
                "state": self.state,
            },
        )
        if self._pending_confirmation is None:
            self._pending_action = None
            self._set_state(ExecutorState.IDLE)
            self.response_ready.emit("确认已过期，请重新发起操作。")
            self._drain_queue()
        return True

    def confirm_action(self, confirmation_id: str = None):
        """用户确认执行操作"""
        if self._pending_action is None or self._pending_confirmation is None:
            self._reject_stale_confirmation(confirmation_id, "confirm_action")
            return
        if self._reject_stale_confirmation(confirmation_id, "confirm_action"):
            return

        confirmation = self._pending_confirmation
        confirmation.status = ConfirmationStatus.CONFIRMED
        name, params = confirmation.action_name, confirmation.params
        self._pending_action = None
        self._set_state(ExecutorState.EXECUTING_ACTION)
        self._write_trace("confirm_action", "User confirmed action",
                          payload={
                              "confirmation_id": confirmation.confirmation_id,
                              "params": params,
                              "plan_id": self._active_plan_id,
                          }, action_name=name)

        if self._current_plan_step is not None:
            self._current_plan_step.status = ActionPlanStepStatus.EXECUTING
        result = self.registry.execute(name, params)
        status = "error" if str(result).startswith(("执行失败", "错误")) else "ok"
        confirmation.result = result
        confirmation.status = (
            ConfirmationStatus.FAILED if status == "error"
            else ConfirmationStatus.COMPLETED
        )
        self._pending_confirmation = None
        if self._current_plan_step is not None:
            self._current_plan_step.result = result
            self._current_plan_step.status = (
                ActionPlanStepStatus.FAILED if status == "error"
                else ActionPlanStepStatus.COMPLETED
            )
        self._write_trace("action_result", result, status=status,
                          payload={
                              "confirmation_id": confirmation.confirmation_id,
                              "params": params,
                              "plan_id": self._active_plan_id,
                          }, action_name=name)
        if status == "ok":
            self._write_experience_seed(name, params, result)
        self._record_step(name, result)

        self._append_history({"role": "user", "content": f"用户确认 {name}"})
        self._append_history({
            "role": "assistant",
            "content": f"已执行 {name}，结果:{result}"
        })

        self.action_done.emit(result)
        if self._active_plan_id is not None:
            self._write_trace(
                "action_plan_step_done",
                f"Plan step done for {name}",
                status=status,
                payload={
                    "plan_id": self._active_plan_id,
                    "params": params,
                    "remaining": len(self._pending_plan_steps),
                },
                action_name=name,
            )
            if status != "ok":
                msg = f"{result}\n\n执行计划已停止。"
                self._clear_action_plan()
                self._stop_multi_step()
                self._set_state(ExecutorState.IDLE)
                self.response_ready.emit(msg)
                self._drain_queue()
                return
            self._current_plan_step = None
            self._emit_next_plan_confirmation()
            return

        # 兼容旧的单步 direct tool call 路径
        self._continue_or_finish(result)

    def cancel_action(self, confirmation_id: str = None):
        """用户取消操作"""
        if self._pending_action is None or self._pending_confirmation is None:
            self._reject_stale_confirmation(confirmation_id, "cancel_action")
            return
        if self._reject_stale_confirmation(confirmation_id, "cancel_action"):
            return

        confirmation = self._pending_confirmation
        confirmation.status = ConfirmationStatus.CANCELED
        name, params = confirmation.action_name, confirmation.params
        self._pending_action = None
        self._pending_confirmation = None
        self._clear_action_plan()
        self._write_trace("cancel_action", "User cancelled action",
                          payload={
                              "confirmation_id": confirmation.confirmation_id,
                              "params": params,
                          }, action_name=name)

        self._auto_step_count = 0
        self._multi_step_active = False
        self._set_state(ExecutorState.IDLE)

        self._append_history({"role": "user", "content": "取消执行"})
        self._append_history({
            "role": "assistant",
            "content": "好的,已取消。请问还有其他需要吗?"
        })

        self.response_ready.emit("操作已取消。")
        self._drain_queue()

    def clear_history(self):
        """清空对话历史"""
        self.history.clear()
        self._pending_action = None
        if self._pending_confirmation is not None:
            self._pending_confirmation.status = ConfirmationStatus.EXPIRED
        self._pending_confirmation = None
        self._clear_action_plan()
        self.complete_session()
        self._auto_step_count = 0
        self._multi_step_active = False
        self._set_state(ExecutorState.IDLE)
        self._write_trace("clear_history", "Conversation history cleared")

    def shutdown(self):
        """应用关闭时安全清理线程和定时器。"""
        self._set_state(ExecutorState.SHUTTING_DOWN)
        self._stop_busy_watchdog()
        self._discard_worker_thread()
        self._discard_worker(delete_later=False)
        self._busy_watchdog.stop()
        self._busy_watchdog.deleteLater()

    @staticmethod
    def _safe_disconnect(signal):
        try:
            signal.disconnect()
        except (TypeError, RuntimeError):
            pass

    def _discard_worker_thread(self):
        """Drop the previous QThread, tolerating wrappers already deleted by Qt."""
        thread = self._worker_thread
        self._worker_thread = None
        if thread is None:
            return

        try:
            self._safe_disconnect(thread.finished)
        except RuntimeError:
            return

        try:
            running = thread.isRunning()
        except RuntimeError:
            return

        if running:
            try:
                thread.quit()
                thread.wait(2000)
            except RuntimeError:
                return

    def _discard_worker(self, delete_later: bool = True):
        """Drop the previous worker, tolerating wrappers already deleted by Qt."""
        worker = self._worker
        self._worker = None
        if worker is None:
            return

        try:
            self._safe_disconnect(worker.finished)
            self._safe_disconnect(worker.error)
        except RuntimeError:
            return

        if delete_later:
            try:
                worker.deleteLater()
            except RuntimeError:
                pass

    def _stop_multi_step(self):
        self._auto_step_count = 0
        self._multi_step_active = False
        self._clear_action_plan()

    def _record_step(self, action_name: str, result: str):
        """跨会话持久化：记录每一步操作。"""
        if self._session_id:
            try:
                self._session_store.add_step(self._session_id, action_name, result)
            except Exception:
                pass

    def get_restore_context(self) -> str:
        """启动时返回上次未完成会话的恢复提示。"""
        try:
            return self._session_store.build_restore_prompt()
        except Exception:
            return ""

    def complete_session(self):
        """标记当前会话为已完成。"""
        if self._session_id:
            try:
                self._session_store.complete(self._session_id)
            except Exception:
                pass
        self._session_id = None
        self.recent_plan_context = None

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
        self._pending_confirmation = None
        self._clear_action_plan()
        self._set_state(ExecutorState.EXECUTING_ACTION)
        self._write_trace("auto_execute_action", "Auto-executing read-only action",
                          payload={"params": params}, action_name=name)
        result = self.registry.execute(name, params)
        status = "error" if str(result).startswith(("执行失败", "错误")) else "ok"
        self._write_trace("action_result", result, status=status,
                          payload={"params": params}, action_name=name)
        if status == "ok":
            self._capture_plan_context(name, params)
        self._record_step(name, result)
        self._append_history({"role": "assistant", "content": result})
        self._set_state(ExecutorState.IDLE)
        self.response_ready.emit(result)
        self._drain_queue()

    def _continue_or_finish(self, result: str):
        """多步执行循环：结果喂回 LLM，让 LLM 决定下一步。"""
        if not self._multi_step_active:
            self._set_state(ExecutorState.IDLE)
            self.response_ready.emit(result)
            self._drain_queue()
            return

        self._auto_step_count += 1
        if self._auto_step_count >= self._auto_step_max:
            self._auto_step_count = 0
            self._multi_step_active = False
            self._set_state(ExecutorState.IDLE)
            self.response_ready.emit(f"{result}\n\n(已达到最大执行步数 {self._auto_step_max}，自动停止)")
            self._drain_queue()
            return

        self._append_history({
            "role": "user",
            "content": f"操作结果: {result}\n原始任务是否已全部完成？已完成请回复'完成'；如果还有必要操作，继续调用工具。"
        })
        self._call_llm()

    def _build_confirmation_summary(self, action_name: str, params: dict) -> str:
        summary = self.registry.format_action_summary(action_name, params)
        if self._requires_confirmation_warning(action_name):
            if not self._action_matches_recent_plan(action_name):
                warning = "当前操作未经过规划分析，建议先让我分析问题再执行。"
                summary = f"{warning}\n{summary}"
        return summary

    def _requires_confirmation_warning(self, action_name: str) -> bool:
        metadata = {}
        if hasattr(self.registry, "get_metadata"):
            metadata = self.registry.get_metadata(action_name)
        risk_level = metadata.get("risk_level", "medium")
        side_effects = metadata.get("side_effects", True)
        return risk_level in {"medium", "high"} or side_effects is not False

    def _action_matches_recent_plan(self, action_name: str) -> bool:
        return bool(self.recent_plan_context)

    def _capture_plan_context(self, action_name: str, params: dict):
        if action_name not in {"plan_chassis_task", "suggest_chassis_tuning"}:
            return
        goal = params.get("goal") or params.get("complaint")
        condition = params.get("condition_name")
        self.recent_plan_context = {
            "action": action_name,
            "goal": goal,
            "condition_name": condition,
        }
        # 创建/更新跨会话持久化记录
        ui = self._get_ui()
        setup = _build_context_snapshot(ui) if ui else ""
        self._session_id = self._session_store.save(
            session_id=self._session_id,
            goal=goal,
            condition_name=condition,
            vehicle_setup_snapshot=setup,
            status="active",
        )
        self._write_trace(
            "plan_context_saved",
            f"Session {self._session_id} saved",
            payload=self.recent_plan_context,
            action_name=action_name,
        )

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
        plan = self.recent_plan_context or {}
        try:
            self.memory_store.append_experience_seed(EngineeringExperienceSeed(
                action_name=action_name,
                params=params,
                result=result,
                lesson=lesson,
                goal=plan.get("goal"),
                condition_name=(
                    params.get("condition_name") if isinstance(params, dict) else None
                ) or plan.get("condition_name"),
                risk_level=metadata.get("risk_level", "medium"),
            ))
        except Exception:
            pass
