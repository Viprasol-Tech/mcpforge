"""$ref resolution, operationId fallback, and identifier sanitization."""

from __future__ import annotations

import pytest

from mcpforge import parse_openapi, sanitize_identifier
from mcpforge.openapi import OpenAPIError, resolve_refs
from mcpforge.tools import fallback_tool_name


def test_resolve_simple_ref() -> None:
    root = {"components": {"schemas": {"Pet": {"type": "object"}}}}
    out = resolve_refs({"$ref": "#/components/schemas/Pet"}, root)
    assert out == {"type": "object"}


def test_resolve_nested_ref() -> None:
    root = {
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {"tag": {"$ref": "#/components/schemas/Tag"}},
                },
                "Tag": {"type": "string"},
            }
        }
    }
    out = resolve_refs({"$ref": "#/components/schemas/Pet"}, root)
    assert out["properties"]["tag"] == {"type": "string"}


def test_resolve_ref_in_list() -> None:
    root = {"components": {"schemas": {"A": {"type": "integer"}}}}
    out = resolve_refs([{"$ref": "#/components/schemas/A"}], root)
    assert out == [{"type": "integer"}]


def test_resolve_ref_with_sibling_keys() -> None:
    root = {"components": {"schemas": {"A": {"type": "string"}}}}
    out = resolve_refs({"$ref": "#/components/schemas/A", "description": "extra"}, root)
    assert out == {"type": "string", "description": "extra"}


def test_external_ref_rejected() -> None:
    with pytest.raises(OpenAPIError):
        resolve_refs({"$ref": "other.yaml#/X"}, {})


def test_missing_ref_target_raises() -> None:
    with pytest.raises(OpenAPIError):
        resolve_refs({"$ref": "#/components/schemas/Missing"}, {"components": {"schemas": {}}})


def test_ref_in_request_body_resolved() -> None:
    doc = {
        "info": {"title": "T", "version": "1"},
        "paths": {
            "/x": {
                "post": {
                    "operationId": "mk",
                    "requestBody": {
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Body"}}
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "Body": {
                    "type": "object",
                    "required": ["a"],
                    "properties": {"a": {"type": "string"}},
                }
            }
        },
    }
    parsed = parse_openapi(doc)
    tool = parsed.tools[0]
    assert "a" in tool.input_schema["properties"]
    assert tool.input_schema["required"] == ["a"]


def test_fallback_name_for_missing_operation_id() -> None:
    doc = {
        "info": {"title": "T", "version": "1"},
        "paths": {"/pets/{petId}": {"get": {"summary": "x"}}},
    }
    parsed = parse_openapi(doc)
    assert parsed.tools[0].name == "get_pets_petId"
    assert parsed.tools[0].operation_id is None


def test_fallback_root_path() -> None:
    assert fallback_tool_name("get", "/") == "get_root"


def test_fallback_strips_braces() -> None:
    assert (
        fallback_tool_name("delete", "/users/{id}/posts/{postId}") == "delete_users_id_posts_postId"
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("getPet", "getPet"),
        ("get pet/by-id!", "get_pet_by_id"),
        ("123abc", "_123abc"),
        ("  spaced  ", "spaced"),
        ("a..b__c", "a_b__c"),
    ],
)
def test_sanitize_identifier(raw: str, expected: str) -> None:
    assert sanitize_identifier(raw) == expected


def test_sanitize_keyword_gets_suffix() -> None:
    assert sanitize_identifier("class") == "class_"


def test_sanitize_empty_uses_fallback() -> None:
    assert sanitize_identifier("!!!", fallback="tool") == "tool"


def test_sanitized_names_are_valid_identifiers() -> None:
    for raw in ["get pet", "9lives", "delete/all", "import", "résumé"]:
        assert sanitize_identifier(raw).isidentifier()


def test_duplicate_operation_ids_made_unique() -> None:
    doc = {
        "info": {"title": "T", "version": "1"},
        "paths": {
            "/a": {"get": {"operationId": "dup"}},
            "/b": {"get": {"operationId": "dup"}},
        },
    }
    parsed = parse_openapi(doc)
    names = parsed.tool_names()
    assert len(set(names)) == len(names)
    assert "dup" in names and "dup_2" in names
