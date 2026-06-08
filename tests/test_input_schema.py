"""Input-schema construction: parameters, request bodies, required flags, types."""

from __future__ import annotations

from mcpforge import SAMPLE_OPENAPI, build_input_schema, parse_openapi


def _tool(name: str):  # type: ignore[no-untyped-def]
    parsed = parse_openapi(SAMPLE_OPENAPI)
    return next(t for t in parsed.tools if t.name == name)


def test_schema_is_object_with_properties() -> None:
    schema = build_input_schema([], None)
    assert schema == {"type": "object", "properties": {}}


def test_no_params_no_body_has_no_required() -> None:
    schema = build_input_schema([], None)
    assert "required" not in schema


def test_query_param_optional_not_required() -> None:
    params = [{"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}}]
    schema = build_input_schema(params, None)
    assert "limit" in schema["properties"]
    assert "required" not in schema


def test_query_param_required() -> None:
    params = [{"name": "q", "in": "query", "required": True, "schema": {"type": "string"}}]
    schema = build_input_schema(params, None)
    assert schema["required"] == ["q"]


def test_path_param_always_required() -> None:
    params = [{"name": "petId", "in": "path", "schema": {"type": "integer"}}]
    schema = build_input_schema(params, None)
    assert schema["required"] == ["petId"]


def test_param_type_preserved() -> None:
    params = [{"name": "limit", "in": "query", "schema": {"type": "integer", "maximum": 100}}]
    schema = build_input_schema(params, None)
    assert schema["properties"]["limit"]["type"] == "integer"
    assert schema["properties"]["limit"]["maximum"] == 100


def test_param_description_carried_into_schema() -> None:
    params = [
        {
            "name": "tag",
            "in": "query",
            "description": "Filter by tag.",
            "schema": {"type": "string"},
        }
    ]
    schema = build_input_schema(params, None)
    assert schema["properties"]["tag"]["description"] == "Filter by tag."


def test_param_without_schema_defaults_to_string() -> None:
    params = [{"name": "x", "in": "query"}]
    schema = build_input_schema(params, None)
    assert schema["properties"]["x"]["type"] == "string"


def test_header_param_supported() -> None:
    params = [{"name": "X-Trace", "in": "header", "required": True, "schema": {"type": "string"}}]
    schema = build_input_schema(params, None)
    assert "X-Trace" in schema["properties"]
    assert "X-Trace" in schema["required"]


def test_request_body_fields_merged() -> None:
    body = {
        "type": "object",
        "required": ["name"],
        "properties": {"name": {"type": "string"}, "tag": {"type": "string"}},
    }
    schema = build_input_schema([], body)
    assert "name" in schema["properties"]
    assert "tag" in schema["properties"]
    assert schema["required"] == ["name"]


def test_request_body_exposes_full_body_property() -> None:
    body = {"type": "object", "properties": {"name": {"type": "string"}}}
    schema = build_input_schema([], body)
    assert schema["properties"]["body"] == body


def test_param_and_body_merged_together() -> None:
    params = [{"name": "petId", "in": "path", "schema": {"type": "integer"}}]
    body = {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}
    schema = build_input_schema(params, body)
    assert "petId" in schema["properties"]
    assert "name" in schema["properties"]
    assert "petId" in schema["required"]
    assert "name" in schema["required"]


def test_param_not_clobbered_by_body_field() -> None:
    params = [{"name": "id", "in": "path", "schema": {"type": "integer"}}]
    body = {"type": "object", "properties": {"id": {"type": "string"}}}
    schema = build_input_schema(params, body)
    # The path parameter's integer type must win.
    assert schema["properties"]["id"]["type"] == "integer"


def test_sample_list_pets_two_optional_inputs() -> None:
    tool = _tool("listPets")
    assert tool.input_count == 2
    assert tool.required_inputs == []


def test_sample_get_pet_by_id_required_path() -> None:
    tool = _tool("getPetById")
    assert tool.input_schema["required"] == ["petId"]
    assert tool.input_schema["properties"]["petId"]["type"] == "integer"


def test_sample_create_pet_merges_body() -> None:
    tool = _tool("createPet")
    props = tool.input_schema["properties"]
    assert "name" in props
    assert "tag" in props
    assert tool.input_schema["required"] == ["name"]
