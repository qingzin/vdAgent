"""
Agent Executor - Agent 调度核心
负责:接收用户输入 → 调用 LLM → 解析意图 → 请求确认 → 执行操作
"""

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
- 每个工具执行后，结果会自动反馈给你，你可以继续调用下一个工具
- 当任务完成时，直接回复文字总结（不要再调用工具）
- 如果上一步失败，分析原因并决定是否重试或调整方案
- 最多可连续执行 10 步

重要规则:
1. 仔细理解用户意图,选择最匹配的工具
2. 如果用户的描述不够明确,回复文字询问更多信息,不要猜测调用工具
3. 参数值必须严格匹配工具定义中的可选值(如果有 enum 限制)
4. 用中文回复
5. 遇到复杂底盘目标或主观反馈(例如侧倾大、单移线表现差、方向盘中心区重、起伏舒适性差、修改悬架并验证),优先调用 plan_chassis_task 或 suggest_chassis_tuning 形成方案/建议,不要直接修改弹簧、稳定杆或触感参数
6. 只有当用户明确确认了具体参数修改或准备动作时,才调用 set_spring、set_antiroll_bar、tune_haptic_feedback、prepare_test_scene、run_carsim、start_recording、stop_recording 等操作型工具
7. 当用户询问"为什么"、寻求原理解释或需要分析时,优先调用 search_knowledge 检索领域知识库,结合当前系统状态给出有依据的回答
8. 如果用户描述了一个有价值的调校经验或规律,主动调用 save_knowledge 将其保存

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
AUTO_EXECUTE_CATEGORIES = {"planning", "knowledge"}


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


class StreamingAgentWorker(QObject):
    """在子线程中流式调用 LLM，逐 token 发送"""
    finished = pyqtSignal(object)
    chunk = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, llm_client, messages, tools, system_prompt):
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages
        self.tools = tools
        self.system_prompt = system_prompt

    def run(self):
        try:
            full_text = ""
            for token in self.llm_client.chat_stream(
                messages=self.messages,
                tools=self.tools,
                system=self.system_prompt,
                temperature=0.3,
            ):
                full_text += token
                self.chunk.emit(token)

            # 对完整文本做 tool call 检测
            response = self.llm_client._parse_response_from_text(full_text, self.tools)
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
    chunk_received = pyqtSignal(str)

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
        self.recent_plan_context = None
        self._worker_thread = None
        self._worker = None
        self._is_busy = False
        self._auto_step_count = 0
        self._auto_step_max = 10
        self._multi_step_active = False
        self._session_store = SessionStore()
        self._session_id = None
        from collections import deque
        self._message_queue = deque(maxlen=20)
        self._busy_watchdog = QTimer()
        self._busy_watchdog.setSingleShot(True)
        self._busy_watchdog.timeout.connect(self._on_busy_timeout)

    def process_user_input(self, user_message: str):
        """处理用户输入的自然语言，忙碌时排队"""
        if self._is_busy:
            self._message_queue.append(user_message)
            self._write_trace("user_input_queued", user_message,
                              status="busy", payload={"queue_len": len(self._message_queue)})
            return
        self._write_trace("user_input", user_message)
        self._auto_step_count = 0
        self._multi_step_active = True
        self._append_history({"role": "user", "content": user_message})
        self._call_llm()

    def _drain_queue(self):
        """处理消息队列中的下一条消息"""
        if self._message_queue:
            next_msg = self._message_queue.popleft()
            self._write_trace("user_input_dequeued", next_msg,
                              payload={"remaining": len(self._message_queue)})
            self._auto_step_count = 0
            self._multi_step_active = True
            self._append_history({"role": "user", "content": next_msg})
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
        """在子线程中流式调用 LLM,注入当前系统上下文"""
        self._is_busy = True
        self.thinking.emit(True)
        self._busy_watchdog.start(60000)

        tools = self.registry.get_tools_schema()
        self._write_trace("llm_request", payload={"tool_count": len(tools)})

        context_text = self._build_full_context()

        self._worker_thread = QThread()
        self._worker = StreamingAgentWorker(self.llm_client, list(self.history),
                                            tools, system_prompt=context_text)
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.chunk.connect(self._on_stream_chunk)
        self._worker.finished.connect(self._on_llm_response)
        self._worker.error.connect(self._on_llm_error)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.error.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)

        self._worker_thread.start()

    def _on_stream_chunk(self, token: str):
        """流式输出的 token 回调 — 转发给 UI"""
        self.chunk_received.emit(token)

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
            entries = store.search(limit=4)
            if not entries:
                return ""
            lines = []
            for e in entries:
                title = e["meta"].get("title", e["filename"])
                lines.append(f"- {title}: {e['summary'][:120]}")
            return "\n".join(lines) if lines else ""
        except Exception:
            return ""

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

    def _on_llm_response(self, response):
        """处理 LLM 响应"""
        self._stop_busy_watchdog()

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
                self._stop_multi_step()
                return

            if self._should_auto_execute_action(name):
                self._auto_execute_action(name, params)
                return

            self._multi_step_active = True
            summary = self._build_confirmation_summary(name, params)
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
            self._auto_step_count = 0
            self._multi_step_active = False
            self.response_ready.emit(text)
            self._drain_queue()

    def _stop_busy_watchdog(self):
        self._busy_watchdog.stop()
        self._is_busy = False
        self.thinking.emit(False)

    def _on_busy_timeout(self):
        """看门狗超时：强制重置 _is_busy，防止 agent 永久卡死。"""
        self._is_busy = False
        self.thinking.emit(False)
        self._auto_step_count = 0
        self._multi_step_active = False
        self._stop_multi_step()
        self.response_ready.emit("AI 响应超时，请重试。")
        self._drain_queue()

    def _on_llm_error(self, error_msg):
        """处理 LLM 错误"""
        self._stop_busy_watchdog()
        self._auto_step_count = 0
        self._multi_step_active = False
        msg = f"AI 助手出错:{error_msg}"
        self._write_trace("llm_error", msg, status="error")
        self.response_ready.emit(msg)
        self._drain_queue()

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
        self._record_step(name, result)

        self._append_history({"role": "user", "content": "确认执行"})
        self._append_history({
            "role": "assistant",
            "content": f"已执行。结果:{result}"
        })

        self.action_done.emit(result)
        self._continue_or_finish(result)

    def cancel_action(self):
        """用户取消操作"""
        if self._pending_action is None:
            return

        name, params = self._pending_action
        self._pending_action = None
        self._write_trace("cancel_action", "User cancelled action",
                          payload={"params": params}, action_name=name)

        self._auto_step_count = 0
        self._multi_step_active = False

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
        self.complete_session()
        self._auto_step_count = 0
        self._multi_step_active = False
        self._write_trace("clear_history", "Conversation history cleared")

    def _stop_multi_step(self):
        self._auto_step_count = 0
        self._multi_step_active = False

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
        self._continue_or_finish(result)

    def _continue_or_finish(self, result: str):
        """多步执行循环：结果喂回 LLM，让 LLM 决定下一步。"""
        if not self._multi_step_active:
            self.response_ready.emit(result)
            return

        self._auto_step_count += 1
        if self._auto_step_count >= self._auto_step_max:
            self._auto_step_count = 0
            self._multi_step_active = False
            self.response_ready.emit(f"{result}\n\n(已达到最大执行步数 {self._auto_step_max}，自动停止)")
            self._drain_queue()
            return

        self._append_history({
            "role": "user",
            "content": f"上一步执行结果: {result}\n请继续执行下一步，或回复'完成'结束。"
        })
        self._call_llm()

    def _build_confirmation_summary(self, action_name: str, params: dict) -> str:
        summary = self.registry.format_action_summary(action_name, params)
        if self._requires_confirmation_warning(action_name):
            if not self._action_matches_recent_plan(action_name):
                warning = "未匹配近期计划，建议先规划/重新确认。"
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
