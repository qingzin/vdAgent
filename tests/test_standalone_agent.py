from agent.standalone_service import StandaloneAgentService


def test_standalone_service_reuses_actions_and_records_state_changes(tmp_path):
    service = StandaloneAgentService(memory_store=None)

    result = service.registry.execute(
        "tune_haptic_feedback",
        {"mode": "set", "friction": 1.5, "overall": 2.0},
    )

    assert "1.5" in result
    assert service.state.executions[-1].action_name == "tune_haptic_feedback"
    changed_targets = {change.target for change in service.state.executions[-1].changes}
    assert "ui.gain_fri" in changed_targets
    assert "ui.gain_all" in changed_targets
    assert service.snapshot()["haptic"]["friction"] == 1.5


def test_standalone_service_tracks_scene_and_simulation_changes():
    service = StandaloneAgentService(memory_store=None)

    service.registry.execute(
        "prepare_test_scene",
        {
            "condition_name": "double_lane_change",
            "map_name": "city_loop",
            "start_point_name": "start_b",
            "confirm": True,
        },
    )
    service.registry.execute("run_carsim", {})

    snapshot = service.snapshot()
    assert snapshot["scene"]["condition"] == "double_lane_change"
    assert snapshot["scene"]["map"] == "city_loop"
    assert snapshot["scene"]["start_point"] == "start_b"
    assert [record.action_name for record in service.state.executions] == [
        "prepare_test_scene",
        "run_carsim",
    ]


def test_standalone_service_covers_plotting_actions():
    service = StandaloneAgentService(memory_store=None)

    assert service.registry.has_action("set_plot_visibility")
    result = service.registry.execute(
        "set_plot_visibility",
        {"channels": ["roll", "pitch"], "visible": True},
    )
    service.registry.execute("set_alarm", {"enabled": True, "scenario": "cornering"})

    snapshot = service.snapshot()
    assert "roll" in snapshot["plotting"]["visible_channels"]
    assert "pitch" in snapshot["plotting"]["visible_channels"]
    assert snapshot["plotting"]["alarm_enabled"] is True
    assert snapshot["plotting"]["alarm_scenario"] == "cornering"
    assert "roll" in result or "Roll" in result
