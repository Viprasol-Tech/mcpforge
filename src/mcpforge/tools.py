"""Map a single OpenAPI operation to an MCP :class:`ToolSpec`.

The two public helpers are pure functions over plain dicts:

* :func:`build_input_schema` merges path/query/header/cookie parameters and a JSON
  request body into one JSON-Schema ``object``.
* :func:`map_operation_to_tool` wraps that into a complete :class:`ToolSpec`,
  deriving a safe tool name when no ``operationId`` is present.
"""

from __future__ import annotations

import keyword
import re
from typing import Any

from .models import ToolSpec

# Characters that are not legal in a Python identifier become underscores.
_INVALID_IDENT = re.compile(r"[^0-9a-zA-Z_]+")


def sanitize_identifier(raw: str, *, fallback: str = "tool") -> str:
    """Turn an arbitrary string into a valid, lowercase-ish Python identifier.

    Collapses runs of invalid characters to single underscores, strips leading
    digits, lowercases nothing (operationIds keep their case), and avoids Python
    keywords. Always returns a non-empty identifier.
    """

    cleaned = _INVALID_IDENT.sub("_", raw).strip("_")
    if not cleaned:
        cleaned = fallback
    if cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    if keyword.iskeyword(cleaned) or keyword.issoftkeyword(cleaned):
        cleaned = f"{cleaned}_"
    return cleaned


def fallback_tool_name(method: str, path: str) -> str:
    """Build a deterministic tool name from a method + path.

    ``GET /pets/{petId}`` -> ``get_pets_petId``. Path templating braces are
    dropped so the segment name survives intact.
    """

    segments = [seg for seg in path.split("/") if seg]
    stripped = [seg.replace("{", "").replace("}", "") for seg in segments]
    base = "_".join([method.lower(), *stripped]) if stripped else f"{method.lower()}_root"
    return sanitize_identifier(base, fallback=f"{method.lower()}_root")


def _schema_for_parameter(param: dict[str, Any]) -> dict[str, Any]:
    """Extract a JSON-Schema fragment for one parameter, with its description."""

    schema = dict(param.get("schema") or {})
    if not schema:
        # OpenAPI 2-style inline type, defensively supported.
        schema["type"] = param.get("type", "string")
    if "description" in param and "description" not in schema:
        schema["description"] = param["description"]
    return schema


def build_input_schema(
    parameters: list[dict[str, Any]],
    request_body_schema: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge parameters and a JSON request body into one JSON-Schema object.

    Path/query/header/cookie parameters each become a top-level property (required iff
    the parameter is ``required`` or sits in the path). An ``application/json``
    request body, if present, contributes its own object properties merged at the
    top level, plus a structured ``body`` property carrying the whole payload
    schema so callers can pass either flattened fields or a nested object.
    """

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in parameters:
        name = param.get("name")
        if not name:
            continue
        properties[name] = _schema_for_parameter(param)
        in_path = param.get("in") == "path"
        if (param.get("required", False) or in_path) and name not in required:
            required.append(name)

    if request_body_schema:
        body_props = request_body_schema.get("properties")
        body_required = request_body_schema.get("required", [])
        if isinstance(body_props, dict):
            for field_name, field_schema in body_props.items():
                # Do not let a body field silently clobber a path/query param.
                if field_name not in properties:
                    properties[field_name] = field_schema
            for field_name in body_required:
                if field_name not in required:
                    required.append(field_name)
        # Always expose the full body object too, for non-object payloads.
        properties.setdefault("body", request_body_schema)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _operation_description(operation: dict[str, Any], method: str, path: str) -> str:
    summary = operation.get("summary")
    description = operation.get("description")
    text = summary or description or f"{method.upper()} {path}"
    return str(text).strip()


def map_operation_to_tool(
    method: str,
    path: str,
    operation: dict[str, Any],
    request_body_schema: dict[str, Any] | None,
    *,
    taken_names: set[str] | None = None,
) -> ToolSpec:
    """Build a :class:`ToolSpec` for one ``(method, path, operation)`` triple.

    ``taken_names`` lets the caller guarantee uniqueness across a whole document;
    a numeric suffix is appended on collision.
    """

    method = method.lower()
    operation_id = operation.get("operationId")
    if operation_id:
        name = sanitize_identifier(str(operation_id), fallback=fallback_tool_name(method, path))
    else:
        name = fallback_tool_name(method, path)

    if taken_names is not None:
        unique = name
        counter = 2
        while unique in taken_names:
            unique = f"{name}_{counter}"
            counter += 1
        name = unique
        taken_names.add(name)

    parameters = [p for p in operation.get("parameters", []) if isinstance(p, dict)]
    input_schema = build_input_schema(parameters, request_body_schema)

    return ToolSpec(
        name=name,
        description=_operation_description(operation, method, path),
        input_schema=input_schema,
        method=method,
        path=path,
        operation_id=str(operation_id) if operation_id else None,
    )
