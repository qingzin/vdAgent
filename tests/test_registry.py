from agent.registry import ActionRegistry


def test_get_tools_schema_filters_unexposed_actions():
    registry = ActionRegistry()
    registry.register(
        name="visible_action",
        description="visible",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda: "ok",
        category="test",
        risk_level="low",
        exposed=True,
    )
    registry.register(
        name="hidden_action",
        description="hidden",
        params_schema={"type": "object", "properties": {}, "required": []},
        callback=lambda: "ok",
        category="test",
        risk_level="low",
        exposed=False,
    )

    names = [tool["function"]["name"] for tool in registry.get_tools_schema()]

    assert names == ["visible_action"]
    assert registry.has_action("hidden_action")
    assert registry.get_metadata("hidden_action")["exposed"] is False

