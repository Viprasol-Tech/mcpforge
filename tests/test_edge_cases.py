"""Edge cases: empty paths, no params/body, multi-method, malformed docs."""

from __future__ import annotations

import pytest

from mcpforge import parse_openapi
from mcpforge.openapi import OpenAPIError


def test_no_paths_raises() -> None:
    with pytest.raises(OpenAPIError):
        parse_openapi({"info": {"title": "T", "version": "1"}})


def test_non_dict_document_raises() -> None:
    with pytest.raises(OpenAPIError):
        parse_openapi([])  # type: ignore[arg-type]


def test_empty_paths_zero_tools() -> None:
    parsed = parse_openapi({"info": {"title": "T", "version": "1"}, "paths": {}})
    assert parsed.tool_count == 0


def test_missing_info_defaults() -> None:
    parsed = parse_openapi({"paths": {"/x": {"get": {"operationId": "x"}}}})
    assert parsed.title == "API"
    assert parsed.version == "0.0.0"


def test_operation_with_no_params_or_body() -> None:
    parsed = parse_openapi({"paths": {"/ping": {"get": {"operationId": "ping"}}}})
    tool = parsed.tools[0]
    assert tool.input_count == 0
    assert "required" not in tool.input_schema


def test_all_five_methods_on_one_path() -> None:
    doc = {
        "paths": {
            "/r": {
                "get": {"operationId": "g"},
                "post": {"operationId": "p"},
                "put": {"operationId": "u"},
                "patch": {"operationId": "pa"},
                "delete": {"operationId": "d"},
            }
        }
    }
    parsed = parse_openapi(doc)
    assert parsed.tool_count == 5
    assert {t.method for t in parsed.tools} == {"get", "post", "put", "patch", "delete"}


def test_non_operation_keys_ignored() -> None:
    doc = {
        "paths": {
            "/r": {
                "summary": "a path summary, not an operation",
                "get": {"operationId": "g"},
            }
        }
    }
    parsed = parse_openapi(doc)
    assert parsed.tool_count == 1


def test_path_level_parameters_applied_to_operations() -> None:
    doc = {
        "paths": {
            "/items/{id}": {
                "parameters": [{"name": "id", "in": "path", "schema": {"type": "integer"}}],
                "get": {"operationId": "getItem"},
                "delete": {"operationId": "delItem"},
            }
        }
    }
    parsed = parse_openapi(doc)
    for tool in parsed.tools:
        assert "id" in tool.input_schema["properties"]
        assert "id" in tool.input_schema["required"]


def test_non_dict_path_item_skipped() -> None:
    doc = {"paths": {"/x": {"get": {"operationId": "x"}}, "/bad": "nope"}}
    parsed = parse_openapi(doc)
    assert parsed.tool_count == 1


def test_description_fallback_when_no_summary() -> None:
    doc = {"paths": {"/x": {"get": {"operationId": "x"}}}}
    parsed = parse_openapi(doc)
    assert parsed.tools[0].description == "GET /x"


def test_description_uses_description_field() -> None:
    doc = {"paths": {"/x": {"get": {"operationId": "x", "description": "Does X."}}}}
    parsed = parse_openapi(doc)
    assert parsed.tools[0].description == "Does X."
