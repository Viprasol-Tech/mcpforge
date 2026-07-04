"""Security-scheme handling for generated MCP tool input schemas."""

from __future__ import annotations

from pathlib import Path

from mcpforge import parse_openapi, render_server
from mcpforge.openapi import load_spec


def _xquik_example() -> dict:
    return load_spec(Path("docs/examples/xquik-openapi.yaml"))


def test_api_key_security_scheme_becomes_required_input() -> None:
    parsed = parse_openapi(_xquik_example())
    tool = parsed.tools[0]

    assert tool.name == "listXquikEvents"
    assert tool.input_schema["properties"]["X-API-Key"]["type"] == "string"
    assert "X-API-Key" in tool.input_schema["required"]


def test_api_key_security_keeps_operation_inputs() -> None:
    parsed = parse_openapi(_xquik_example())
    list_events = parsed.tools[0]
    create_draft = parsed.tools[1]

    assert "limit" in list_events.input_schema["properties"]
    assert "text" in create_draft.input_schema["properties"]
    assert create_draft.input_schema["required"] == ["X-API-Key", "text"]


def test_xquik_example_generates_compilable_server() -> None:
    parsed = parse_openapi(_xquik_example())
    source = render_server(parsed, module_name="xquik_server")

    compile(source, "xquik_server.py", "exec")
    assert "listXquikEvents" in source
    assert "createXquikDraft" in source
