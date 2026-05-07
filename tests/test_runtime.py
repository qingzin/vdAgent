from agent.runtime import AgentCommandQueue
from agent.runtime_events import AgentEvent
from agent.memory.store import AgentMemoryStore


def test_command_queue_serializes_per_session():
    queue = AgentCommandQueue()
    queue.mark_active("s1")
    first = queue.enqueue("s1", "first")
    second = queue.enqueue("s1", "second")

    assert queue.is_active("s1") is True
    assert queue.pending_count("s1") == 2
    assert queue.dequeue("s1") == first
    assert queue.dequeue("s1") == second
    assert queue.dequeue("s1") is None

    queue.mark_idle("s1")
    assert queue.is_active("s1") is False


def test_memory_store_appends_structured_agent_event(tmp_path):
    store = AgentMemoryStore(base_dir=str(tmp_path))
    event = AgentEvent(
        stream="approval",
        event_type="approval_requested",
        message="confirm",
        payload={"approval_id": "a1"},
        session_id="s1",
        run_id="r1",
    )

    record = store.append_event(event)

    assert record["stream"] == "approval"
    assert record["event_type"] == "approval_requested"
    assert record["payload"] == {"approval_id": "a1"}
    assert (tmp_path / "events.jsonl").exists()
