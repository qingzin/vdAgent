from agent.memory.models import EngineeringExperienceSeed, ProcessTrace
from agent.memory.store import AgentMemoryStore


def test_memory_store_appends_and_reads_jsonl(tmp_path):
    store = AgentMemoryStore(base_dir=str(tmp_path))

    store.append_trace(ProcessTrace(event_type="user_input", message="hello"))
    store.append_experience_seed(EngineeringExperienceSeed(
        action_name="run_carsim",
        params={},
        result="ok",
        lesson="baseline run",
    ))

    traces = store.recent_traces()
    seeds = store.recent_experience_seeds()

    assert traces[-1]["event_type"] == "user_input"
    assert seeds[-1]["action_name"] == "run_carsim"
    assert (tmp_path / "run_logs.jsonl").exists()
    assert (tmp_path / "experience_seeds.jsonl").exists()

