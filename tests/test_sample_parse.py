"""Parsing the bundled sample spec end-to-end."""

from __future__ import annotations

from mcpforge import SAMPLE_OPENAPI, parse_openapi
from mcpforge.models import ParsedAPI


def test_parse_returns_parsed_api() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    assert isinstance(parsed, ParsedAPI)


def test_sample_title_and_version() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    assert parsed.title == "Petstore"
    assert parsed.version == "1.2.0"


def test_sample_tool_count() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    assert parsed.tool_count == 3


def test_sample_tool_names_in_order() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    assert parsed.tool_names() == ["listPets", "createPet", "getPetById"]


def test_sample_methods() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    methods = {t.name: t.method for t in parsed.tools}
    assert methods == {"listPets": "get", "createPet": "post", "getPetById": "get"}


def test_sample_paths() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    paths = {t.name: t.path for t in parsed.tools}
    assert paths["listPets"] == "/pets"
    assert paths["createPet"] == "/pets"
    assert paths["getPetById"] == "/pets/{petId}"


def test_sample_descriptions_from_summary() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    descriptions = {t.name: t.description for t in parsed.tools}
    assert descriptions["listPets"] == "List all pets"
    assert descriptions["getPetById"] == "Get a pet by its id"


def test_operation_ids_preserved() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    assert all(t.operation_id is not None for t in parsed.tools)
    assert parsed.tools[0].operation_id == "listPets"


def test_two_methods_on_one_path_both_present() -> None:
    parsed = parse_openapi(SAMPLE_OPENAPI)
    pets = [t for t in parsed.tools if t.path == "/pets"]
    assert {t.method for t in pets} == {"get", "post"}
