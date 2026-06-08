"""ToolSpec and ParsedAPI model behaviour."""

from __future__ import annotations

from mcpforge.models import ParsedAPI, ToolSpec


def test_toolspec_defaults() -> None:
    tool = ToolSpec(name="t", method="get", path="/t")
    assert tool.description == ""
    assert tool.input_schema == {"type": "object", "properties": {}}
    assert tool.operation_id is None


def test_toolspec_input_count() -> None:
    tool = ToolSpec(
        name="t",
        method="get",
        path="/t",
        input_schema={"type": "object", "properties": {"a": {}, "b": {}}},
    )
    assert tool.input_count == 2


def test_toolspec_required_inputs() -> None:
    tool = ToolSpec(
        name="t",
        method="get",
        path="/t",
        input_schema={"type": "object", "properties": {"a": {}}, "required": ["a"]},
    )
    assert tool.required_inputs == ["a"]


def test_toolspec_required_inputs_empty_default() -> None:
    tool = ToolSpec(name="t", method="get", path="/t")
    assert tool.required_inputs == []


def test_parsed_api_defaults() -> None:
    parsed = ParsedAPI()
    assert parsed.title == "API"
    assert parsed.version == "0.0.0"
    assert parsed.tool_count == 0


def test_parsed_api_tool_names() -> None:
    parsed = ParsedAPI(
        tools=[
            ToolSpec(name="a", method="get", path="/a"),
            ToolSpec(name="b", method="post", path="/b"),
        ]
    )
    assert parsed.tool_names() == ["a", "b"]


def test_models_roundtrip_json() -> None:
    parsed = ParsedAPI(title="X", version="1", tools=[ToolSpec(name="a", method="get", path="/a")])
    restored = ParsedAPI.model_validate_json(parsed.model_dump_json())
    assert restored == parsed
