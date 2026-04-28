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


def test_memory_store_filters_experience_seeds(tmp_path):
    store = AgentMemoryStore(base_dir=str(tmp_path))
    store.append_experience_seed(EngineeringExperienceSeed(
        action_name="set_antiroll_bar",
        params={"position": "rear"},
        result="roll improved",
        lesson="lane change rear bar helped",
        goal="reduce roll",
        condition_name="lane_change",
        metrics={"roll_peak": 3.2},
        user_feedback="better support",
        outcome="improved",
        confidence=0.8,
    ))
    store.append_experience_seed(EngineeringExperienceSeed(
        action_name="set_spring",
        params={"position": "front"},
        result="ride harsh",
        condition_name="bump",
    ))

    by_condition = store.query_experience_seeds(condition_name="lane_change")
    by_action = store.query_experience_seeds(action_name="set_spring")
    by_keyword = store.query_experience_seeds(keyword="rear bar")

    assert [seed["action_name"] for seed in by_condition] == ["set_antiroll_bar"]
    assert [seed["condition_name"] for seed in by_action] == ["bump"]
    assert [seed["goal"] for seed in by_keyword] == ["reduce roll"]
