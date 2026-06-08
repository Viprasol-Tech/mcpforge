"""Code generation: output must compile() and contain an entry per operation."""

from __future__ import annotations

from mcpforge import SAMPLE_OPENAPI, parse_openapi, render_server
from mcpforge.models import ParsedAPI, ToolSpec


def _render_sample() -> str:
    return render_server(parse_openapi(SAMPLE_OPENAPI))


def test_output_compiles() -> None:
    source = _render_sample()
    compile(source, "server.py", "exec")


def test_output_is_str() -> None:
    assert isinstance(_render_sample(), str)


def test_output_imports_mcp() -> None:
    source = _render_sample()
    assert "from mcp.server import Server" in source
    assert "from mcp.server.stdio import stdio_server" in source


def test_has_list_tools_handler() -> None:
    source = _render_sample()
    assert "@app.list_tools()" in source
    assert "async def list_tools(" in source


def test_has_call_tool_handler() -> None:
    source = _render_sample()
    assert "@app.call_tool()" in source
    assert "async def call_tool(" in source


def test_one_tool_entry_per_operation() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    source = render_server(parsed)
    for tool in parsed.tools:
        assert f"name={tool.name!r}" in source


def test_routes_present_for_each_tool() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    source = render_server(parsed)
    for tool in parsed.tools:
        assert tool.path in source
        assert f'"method": "{tool.method}"' in source


def test_server_name_slug_in_output() -> None:
    source = _render_sample()
    assert "Server('petstore')" in source


def test_title_and_version_in_docstring() -> None:
    source = _render_sample()
    assert "Petstore" in source
    assert "1.2.0" in source


def test_module_name_threaded_into_docstring() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    source = render_server(parsed, module_name="petstore_server")
    assert "python petstore_server.py" in source


def test_empty_api_still_compiles() -> None:
    parsed = ParsedAPI(title="Empty", version="0.1", tools=[])
    source = render_server(parsed)
    compile(source, "empty.py", "exec")
    assert "_TOOLS: list[types.Tool] = [" in source


def test_tool_with_special_chars_in_description_compiles() -> None:
    tool = ToolSpec(
        name="weird",
        description="Has 'quotes', \"double\", and \n newlines \\ backslashes.",
        input_schema={"type": "object", "properties": {}},
        method="get",
        path="/weird",
    )
    parsed = ParsedAPI(title="W", version="1", tools=[tool])
    source = render_server(parsed)
    compile(source, "weird.py", "exec")


def test_schema_embedded_as_valid_literal() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    source = render_server(parsed)
    # The integer type from getPetById's path param must survive into the source.
    assert '"type": "integer"' in source


def test_main_entrypoint_present() -> None:
    source = _render_sample()
    assert 'if __name__ == "__main__":' in source
    assert "asyncio.run(_main())" in source


def test_complex_spec_compiles() -> None:
    doc = {
        "info": {"title": "Complex API", "version": "2.0"},
        "paths": {
            "/a/{x}": {
                "get": {
                    "operationId": "getA",
                    "parameters": [
                        {"name": "x", "in": "path", "schema": {"type": "string"}},
                        {"name": "q", "in": "query", "schema": {"type": "integer"}},
                    ],
                },
                "post": {
                    "operationId": "postA",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["v"],
                                    "properties": {"v": {"type": "boolean"}},
                                }
                            }
                        }
                    },
                },
            },
            "/b": {"delete": {"summary": "no opid"}},
        },
    }
    source = render_server(parse_openapi(doc))
    compile(source, "complex.py", "exec")
