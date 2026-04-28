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


def test_memory_store_ranks_experience_seeds_by_relevance(tmp_path):
    store = AgentMemoryStore(base_dir=str(tmp_path))
    store.append_experience_seed(EngineeringExperienceSeed(
        action_name="set_antiroll_bar",
        params={"position": "rear"},
        result="roll improved",
        lesson="rear bar helped roll response",
        condition_name="lane_change",
        outcome="improved",
        confidence=0.6,
    ))
    store.append_experience_seed(EngineeringExperienceSeed(
        action_name="set_spring",
        params={"position": "front"},
        result="roll response success",
        lesson="spring change improved roll control",
        condition_name="lane_change",
        outcome="success",
        confidence=0.9,
    ))
    store.append_experience_seed(EngineeringExperienceSeed(
        action_name="set_spring",
        params={"position": "rear"},
        result="ride comfort improved",
        lesson="bump ride stayed controlled",
        condition_name="bump",
        outcome="improved",
        confidence=1.0,
    ))

    ranked = store.rank_experience_seeds(
        action_name="set_spring",
        condition_name="lane_change",
        keyword="roll",
        limit=3,
    )

    assert [seed["condition_name"] for seed in ranked] == [
        "lane_change",
        "lane_change",
        "bump",
    ]
    assert ranked[0]["action_name"] == "set_spring"
    assert ranked[0]["match_score"] > ranked[1]["match_score"]
    assert ranked[1]["match_score"] > ranked[2]["match_score"]
    assert "match_score" not in store.query_experience_seeds(keyword="roll")[0]


def test_memory_store_rank_reasons_explain_matches(tmp_path):
    store = AgentMemoryStore(base_dir=str(tmp_path))
    store.append_experience_seed(EngineeringExperienceSeed(
        action_name="set_spring",
        params={"position": "front", "note": "roll support"},
        result="roll improved",
        lesson="front spring helped roll",
        condition_name="lane_change",
        outcome="improved",
        confidence=0.75,
    ))

    ranked = store.rank_experience_seeds(
        action_name="set_spring",
        condition_name="lane_change",
        keyword="roll",
    )
    reasons = ranked[0]["match_reasons"]

    assert any("action_name match" in reason for reason in reasons)
    assert any("condition exact match" in reason for reason in reasons)
    assert any("keyword match in lesson" in reason for reason in reasons)
    assert any("positive outcome" in reason for reason in reasons)
    assert any("confidence bonus" in reason for reason in reasons)
