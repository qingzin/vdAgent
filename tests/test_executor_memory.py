from unittest.mock import patch

from agent.executor import (
    HISTORY_TRUNCATION_SUFFIX,
    MAX_HISTORY_MESSAGE_CHARS,
    MAX_HISTORY_RETRY_MESSAGE_CHARS,
    MAX_HISTORY_RETRY_MESSAGES,
    MAX_HISTORY_TOKENS_EST,
    AgentExecutor,
    ConfirmationStatus,
    ExecutorState,
)
from agent.memory.store import AgentMemoryStore, NullAgentMemoryStore
from agent.registry import ActionRegistry


class FakeLLMResponse:
    def __init__(self, tool_name=None, tool_params=None, text=None):
        self.has_tool_call = tool_name is not None
        self.tool_name = tool_name
        self.tool_params = tool_params or {}
        self.text = text


def test_confirm_action_writes_trace_and_experience_seed(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="set_spring",
        description="set spring",
        params_schema={
            "type": "object",
            "properties": {
                "position": {"type": "string"},
                "spring_name": {"type": "string"},
            },
            "required": ["position", "spring_name"],
        },
        callback=lambda position, spring_name: f"spring {position}={spring_name}",
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    store = AgentMemoryStore(base_dir=str(tmp_path))
    executor = AgentExecutor(registry, llm_client=None, memory_store=store)
    confirmation = executor._create_confirmation(
        "set_spring",
        {"position": "front", "spring_name": "K1"},
        "set spring",
    )

    executor.confirm_action(confirmation.confirmation_id)

    traces = store.query_traces(action_name="set_spring")
    seeds = store.query_experience_seeds(action_name="set_spring")

    assert [t["event_type"] for t in traces] == [
        "confirmation_created",
        "confirm_action",
        "action_result",
    ]
    assert confirmation.status == ConfirmationStatus.COMPLETED
    assert seeds[-1]["risk_level"] == "high"
    assert seeds[-1]["params"]["spring_name"] == "K1"


def test_planning_action_auto_executes_without_pending_confirm(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="plan_chassis_task",
        description="plan",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda goal: "## 底盘任务规划\n\n### 建议步骤\n1. 先建立基线",
        category="planning",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
    store = AgentMemoryStore(base_dir=str(tmp_path))
    executor = AgentExecutor(registry, llm_client=None, memory_store=store)
    confirmations = []
    responses = []
    executor.confirm_request.connect(lambda cid, name, params, summary: confirmations.append(name))
    executor.response_ready.connect(responses.append)

    executor._on_llm_response(FakeLLMResponse(
        tool_name="plan_chassis_task",
        tool_params={"goal": "单移线侧倾大"},
    ))

    assert executor._pending_action is None
    assert confirmations == []
    assert responses[-1].startswith("## 底盘任务规划")
    assert executor.history[-1]["content"] == responses[-1]
    assert executor.recent_plan_context["goal"] == "单移线侧倾大"
    assert executor._session_id is not None
    assert [t["event_type"] for t in store.query_traces(action_name="plan_chassis_task")] == [
        "llm_tool_call",
        "auto_execute_action",
        "action_result",
        "plan_context_saved",
    ]


def test_knowledge_action_auto_executes_without_pending_confirm(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="suggest_chassis_tuning",
        description="suggest",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda complaint: "## 底盘调校建议\n\n### 参数方向\n- 先小步调整",
        category="knowledge",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    confirmations = []
    responses = []
    executor.confirm_request.connect(lambda cid, name, params, summary: confirmations.append(name))
    executor.response_ready.connect(responses.append)

    executor._on_llm_response(FakeLLMResponse(
        tool_name="suggest_chassis_tuning",
        tool_params={"complaint": "方向盘中心区重"},
    ))

    assert executor._pending_action is None
    assert confirmations == []
    assert responses[-1].startswith("## 底盘调校建议")


def test_planning_category_with_side_effects_still_requires_confirmation(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="bad_planning_action",
        description="bad",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda goal: "should require confirmation",
        category="planning",
        risk_level="low",
        exposed=True,
        side_effects=True,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    confirmations = []
    executor.confirm_request.connect(lambda cid, name, params, summary: confirmations.append(name))

    executor._on_llm_response(FakeLLMResponse(
        tool_name="bad_planning_action",
        tool_params={"goal": "unsafe"},
    ))

    assert executor._pending_action == ("bad_planning_action", {"goal": "unsafe"})
    assert confirmations == ["bad_planning_action"]


def test_low_risk_readonly_query_auto_executes(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="get_current_setup",
        description="query setup",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda: "当前车型: demo",
        category="query",
        risk_level="low",
        exposed=True,
        side_effects=False,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    confirmations = []
    responses = []
    executor.confirm_request.connect(lambda cid, name, params, summary: confirmations.append(name))
    executor.response_ready.connect(responses.append)

    executor._on_llm_response(FakeLLMResponse(tool_name="get_current_setup"))

    assert executor._pending_action is None
    assert confirmations == []
    assert responses[-1] == "当前车型: demo"


def test_operational_action_still_requests_confirmation(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="set_spring",
        description="set spring",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda position, spring_name: "ok",
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    confirmations = []
    executor.confirm_request.connect(
        lambda cid, name, params, summary: confirmations.append((cid, name))
    )

    executor._on_llm_response(FakeLLMResponse(
        tool_name="set_spring",
        tool_params={"position": "front", "spring_name": "K1"},
    ))

    assert executor._pending_action == ("set_spring", {"position": "front", "spring_name": "K1"})
    assert confirmations[0][1] == "set_spring"
    assert confirmations[0][0] == executor._pending_confirmation.confirmation_id
    assert executor.state == ExecutorState.WAITING_CONFIRMATION
    assert executor.has_pending_confirmation(confirmations[0][0]) is True


def test_stale_confirmation_id_is_rejected(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="set_spring",
        description="set spring",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda position, spring_name: "ok",
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    executor._create_confirmation(
        "set_spring",
        {"position": "front", "spring_name": "K1"},
        "set spring",
    )
    action_results = []
    executor.action_done.connect(action_results.append)

    executor.confirm_action("stale-id")

    assert action_results == []
    assert executor._pending_action == ("set_spring", {"position": "front", "spring_name": "K1"})
    assert executor.state == ExecutorState.WAITING_CONFIRMATION


def test_cancel_uses_confirmation_id_and_expires_pending(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="set_spring",
        description="set spring",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda position, spring_name: "ok",
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    confirmation = executor._create_confirmation(
        "set_spring",
        {"position": "front", "spring_name": "K1"},
        "set spring",
    )

    executor.cancel_action(confirmation.confirmation_id)

    assert confirmation.status == ConfirmationStatus.CANCELED
    assert executor._pending_action is None
    assert executor._pending_confirmation is None
    assert executor.state == ExecutorState.IDLE


def test_unmatched_high_risk_action_warns_in_confirmation_summary(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="set_spring",
        description="set spring",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda position, spring_name: "ok",
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    summaries = []
    executor.confirm_request.connect(
        lambda cid, name, params, summary: summaries.append(summary)
    )

    executor._on_llm_response(FakeLLMResponse(
        tool_name="set_spring",
        tool_params={"position": "front", "spring_name": "K1"},
    ))

    assert "当前操作未经过规划分析" in summaries[-1]


def test_matched_plan_action_still_requires_confirmation_without_warning(tmp_path):
    registry = ActionRegistry()
    registry.register(
        name="set_antiroll_bar",
        description="set antiroll bar",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda position, bar_name: "ok",
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=AgentMemoryStore(base_dir=str(tmp_path)),
    )
    executor.recent_plan_context = {
        "action": "plan_chassis_task",
        "goal": "lane change roll improvement",
        "condition_name": "lane change",
    }
    summaries = []
    executor.confirm_request.connect(
        lambda cid, name, params, summary: summaries.append(summary)
    )

    executor._on_llm_response(FakeLLMResponse(
        tool_name="set_antiroll_bar",
        tool_params={"position": "rear", "bar_name": "bar_a"},
    ))

    assert executor._pending_action == (
        "set_antiroll_bar",
        {"position": "rear", "bar_name": "bar_a"},
    )
    assert "未匹配近期计划" not in summaries[-1]


def test_memory_initialization_failure_does_not_block_executor():
    registry = ActionRegistry()

    with patch("agent.executor.AgentMemoryStore", side_effect=OSError("readonly")):
        executor = AgentExecutor(registry, llm_client=None)

    assert getattr(executor.memory_store, "disabled", False) is True
    executor._write_trace("smoke", "memory disabled")


def test_history_is_bounded_by_message_size_and_total_tokens():
    executor = AgentExecutor(
        ActionRegistry(),
        llm_client=None,
        memory_store=NullAgentMemoryStore("test"),
    )

    for i in range(12):
        executor._append_history({
            "role": "user",
            "content": f"{i}-" + ("x" * (MAX_HISTORY_MESSAGE_CHARS + 100)),
        })

    assert len(executor.history) <= executor.max_history
    assert sum(len(m["content"]) for m in executor.history) <= MAX_HISTORY_TOKENS_EST
    assert all(len(m["content"]) <= MAX_HISTORY_MESSAGE_CHARS + len(HISTORY_TRUNCATION_SUFFIX)
               for m in executor.history)
    assert executor.history[-1]["content"].endswith(HISTORY_TRUNCATION_SUFFIX)


def test_long_user_input_is_truncated_before_llm_history():
    executor = AgentExecutor(
        ActionRegistry(),
        llm_client=None,
        memory_store=NullAgentMemoryStore("test"),
    )
    calls = []
    executor._call_llm = lambda: calls.append(list(executor.history))

    executor.process_user_input("u" * (MAX_HISTORY_MESSAGE_CHARS + 500))

    assert len(calls) == 1
    assert len(executor.history) == 1
    assert executor.history[0]["content"].endswith(HISTORY_TRUNCATION_SUFFIX)
    assert len(executor.history[0]["content"]) < MAX_HISTORY_MESSAGE_CHARS + 500


def test_long_action_result_keeps_ui_result_but_truncates_history():
    registry = ActionRegistry()
    long_result = "r" * (MAX_HISTORY_MESSAGE_CHARS + 500)
    registry.register(
        name="set_spring",
        description="set spring",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda position, spring_name: long_result,
        category="tuning",
        risk_level="high",
        exposed=True,
    )
    executor = AgentExecutor(
        registry,
        llm_client=None,
        memory_store=NullAgentMemoryStore("test"),
    )
    confirmation = executor._create_confirmation(
        "set_spring",
        {"position": "front", "spring_name": "K1"},
        "set spring",
    )
    action_results = []
    executor.action_done.connect(action_results.append)

    executor.confirm_action(confirmation.confirmation_id)

    assert action_results == [long_result]
    assert any(m["content"].endswith(HISTORY_TRUNCATION_SUFFIX)
               for m in executor.history)
    assert all(len(m["content"]) <= MAX_HISTORY_MESSAGE_CHARS + len(HISTORY_TRUNCATION_SUFFIX)
               for m in executor.history)


def test_llm_400_context_error_compacts_history_and_retries():
    executor = AgentExecutor(
        ActionRegistry(),
        llm_client=None,
        memory_store=NullAgentMemoryStore("test"),
    )
    for i in range(8):
        executor._append_history({
            "role": "user",
            "content": f"{i}-" + ("x" * MAX_HISTORY_MESSAGE_CHARS),
        })
    calls = []
    executor._call_llm = lambda: calls.append(list(executor.history))
    executor._is_busy = True

    executor._on_llm_error("400 Bad Request: context length exceeded")

    assert len(calls) == 1
    assert len(executor.history) <= MAX_HISTORY_RETRY_MESSAGES
    assert all(len(m["content"]) <= MAX_HISTORY_RETRY_MESSAGE_CHARS + len(HISTORY_TRUNCATION_SUFFIX)
               for m in executor.history)


def test_busy_timeout_resets_state_and_emits_fallback():
    executor = AgentExecutor(
        ActionRegistry(),
        llm_client=None,
        memory_store=NullAgentMemoryStore("test"),
    )
    responses = []
    executor.response_ready.connect(responses.append)
    executor._is_busy = True
    executor._multi_step_active = True
    executor._auto_step_count = 3

    executor._on_busy_timeout()

    assert executor._is_busy is False
    assert executor._multi_step_active is False
    assert executor._auto_step_count == 0
    assert responses[-1] == "AI 响应超时，请重试。"


def test_call_llm_recovers_when_previous_qthread_wrapper_was_deleted():
    class FakeSignal:
        def __init__(self):
            self.slots = []

        def connect(self, slot):
            self.slots.append(slot)

        def disconnect(self):
            self.slots.clear()

    class DeletedThread:
        finished = FakeSignal()

        def isRunning(self):
            raise RuntimeError("wrapped C/C++ object of type QThread has been deleted")

    class FakeThread:
        def __init__(self):
            self.started = FakeSignal()
            self.finished = FakeSignal()
            self.started_ok = False

        def isRunning(self):
            return False

        def quit(self):
            pass

        def wait(self, timeout):
            pass

        def deleteLater(self):
            pass

        def start(self):
            self.started_ok = True

    class FakeWorker:
        def __init__(self, *args, **kwargs):
            self.finished = FakeSignal()
            self.error = FakeSignal()

        def moveToThread(self, thread):
            self.thread = thread

        def run(self):
            pass

        def deleteLater(self):
            pass

    executor = AgentExecutor(
        ActionRegistry(),
        llm_client=object(),
        memory_store=NullAgentMemoryStore("test"),
    )
    executor._worker_thread = DeletedThread()
    new_thread = FakeThread()

    with patch("agent.executor.QThread", return_value=new_thread), \
            patch("agent.executor.AgentWorker", FakeWorker):
        executor._call_llm()

    assert executor._worker_thread is new_thread
    assert new_thread.started_ok is True
