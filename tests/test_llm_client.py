from agent.llm_client import LLMClient


def test_parse_standard_multiple_tool_calls_preserves_all_calls():
    client = LLMClient()
    response = client._parse_response({
        "choices": [{
            "message": {
                "tool_calls": [
                    {
                        "function": {
                            "name": "prepare_platform",
                            "arguments": '{"x": 1, "y": 1, "z": 1}',
                        }
                    },
                    {
                        "function": {
                            "name": "set_antiroll_bar",
                            "arguments": '{"position": "front", "antiroll_name": "1150"}',
                        }
                    },
                ]
            }
        }]
    })

    assert response.has_tool_call is True
    assert response.tool_name == "prepare_platform"
    assert response.tool_params == {"x": 1, "y": 1, "z": 1}
    assert response.tool_calls == [
        {"name": "prepare_platform", "arguments": {"x": 1, "y": 1, "z": 1}},
        {
            "name": "set_antiroll_bar",
            "arguments": {"position": "front", "antiroll_name": "1150"},
        },
    ]


def test_parse_single_tool_call_keeps_legacy_fields():
    client = LLMClient()
    response = client._parse_response({
        "choices": [{
            "message": {
                "tool_calls": [{
                    "function": {
                        "name": "get_system_status",
                        "arguments": "{}",
                    }
                }]
            }
        }]
    })

    assert response.has_tool_call is True
    assert response.tool_name == "get_system_status"
    assert response.tool_params == {}
    assert response.tool_calls == [{"name": "get_system_status", "arguments": {}}]


def test_parse_tool_call_from_text_keeps_fallback_behavior():
    client = LLMClient()
    response = client._parse_response({
        "choices": [{
            "message": {
                "content": (
                    '<tool_call>{"name":"get_system_status",'
                    '"arguments":{}}</tool_call>'
                )
            }
        }]
    })

    assert response.has_tool_call is True
    assert response.tool_name == "get_system_status"
    assert response.tool_params == {}
    assert response.tool_calls == [{"name": "get_system_status", "arguments": {}}]
