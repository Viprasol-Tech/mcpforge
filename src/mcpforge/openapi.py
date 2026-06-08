"""A minimal but correct OpenAPI 3 parser.

It walks ``paths`` -> operations, resolves local ``$ref`` pointers against the
document's ``components``, and delegates per-operation work to
:mod:`mcpforge.tools`. The result is a :class:`ParsedAPI` of :class:`ToolSpec`.

Only the subset needed to build MCP tool schemas is implemented: parameters
(path/query/header), an ``application/json`` request body, and local
``#/components/...`` references. External ``$ref`` URLs are intentionally not
followed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import HTTP_METHODS, ParsedAPI
from .tools import map_operation_to_tool

_MAX_REF_DEPTH = 50


class OpenAPIError(ValueError):
    """Raised when a document is not usable as an OpenAPI 3 spec."""


def _resolve_ref(ref: str, root: dict[str, Any]) -> Any:
    """Resolve a single local JSON pointer like ``#/components/schemas/Pet``."""

    if not ref.startswith("#/"):
        raise OpenAPIError(f"only local $ref is supported, got: {ref!r}")
    node: Any = root
    for part in ref[2:].split("/"):
        # JSON-pointer unescaping.
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise OpenAPIError(f"cannot resolve $ref: {ref!r}")
        node = node[part]
    return node


def resolve_refs(node: Any, root: dict[str, Any], _depth: int = 0) -> Any:
    """Recursively inline every local ``$ref`` found inside ``node``.

    Returns a new structure; the input is not mutated. Recursion is bounded to
    avoid infinite loops on self-referential schemas.
    """

    if _depth > _MAX_REF_DEPTH:
        return node
    if isinstance(node, dict):
        if "$ref" in node and isinstance(node["$ref"], str):
            target = _resolve_ref(node["$ref"], root)
            resolved = resolve_refs(target, root, _depth + 1)
            # Merge sibling keys (other than $ref) over the resolved target.
            if isinstance(resolved, dict):
                extra = {
                    k: resolve_refs(v, root, _depth + 1) for k, v in node.items() if k != "$ref"
                }
                return {**resolved, **extra}
            return resolved
        return {k: resolve_refs(v, root, _depth + 1) for k, v in node.items()}
    if isinstance(node, list):
        return [resolve_refs(item, root, _depth + 1) for item in node]
    return node


def _request_body_schema(operation: dict[str, Any], root: dict[str, Any]) -> dict[str, Any] | None:
    """Pull the ``application/json`` request-body schema for an operation."""

    body = operation.get("requestBody")
    if not isinstance(body, dict):
        return None
    body = resolve_refs(body, root)
    content = body.get("content")
    if not isinstance(content, dict):
        return None
    json_media = content.get("application/json")
    if not isinstance(json_media, dict):
        # Fall back to the first declared media type with a schema.
        json_media = next(
            (m for m in content.values() if isinstance(m, dict) and "schema" in m), None
        )
    if not isinstance(json_media, dict):
        return None
    schema = json_media.get("schema")
    return schema if isinstance(schema, dict) else None


def parse_openapi(document: dict[str, Any]) -> ParsedAPI:
    """Parse an in-memory OpenAPI 3 document into a :class:`ParsedAPI`.

    Args:
        document: The decoded OpenAPI document (from JSON or YAML).

    Returns:
        A :class:`ParsedAPI` with one :class:`ToolSpec` per operation, in the
        order operations appear in the document.

    Raises:
        OpenAPIError: If ``document`` has no ``paths`` mapping.
    """

    if not isinstance(document, dict):
        raise OpenAPIError("OpenAPI document must be a mapping")

    info = document.get("info", {}) if isinstance(document.get("info"), dict) else {}
    paths = document.get("paths")
    if not isinstance(paths, dict):
        raise OpenAPIError("OpenAPI document has no 'paths' object")

    parsed = ParsedAPI(
        title=str(info.get("title", "API")),
        version=str(info.get("version", "0.0.0")),
        tools=[],
    )

    taken_names: set[str] = set()
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        # Parameters declared at the path level apply to every operation.
        shared_params = path_item.get("parameters", [])
        shared_params = resolve_refs(shared_params, document) if shared_params else []
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
            op_params = resolve_refs(operation.get("parameters", []), document)
            merged = {**operation, "parameters": [*shared_params, *op_params]}
            body_schema = _request_body_schema(operation, document)
            tool = map_operation_to_tool(
                method,
                str(path),
                merged,
                body_schema,
                taken_names=taken_names,
            )
            parsed.tools.append(tool)

    return parsed


def load_spec(path: str | Path) -> dict[str, Any]:
    """Load an OpenAPI document from a ``.json``, ``.yaml`` or ``.yml`` file.

    JSON is parsed with the stdlib; YAML uses :mod:`yaml.safe_load`. The file
    extension selects the loader, defaulting to YAML (a superset of JSON).
    """

    p = Path(path)
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix == ".json":
        data = json.loads(text)
    else:
        import yaml

        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise OpenAPIError(f"{p} did not decode to an object")
    return data


def parse_spec_file(path: str | Path) -> ParsedAPI:
    """Convenience wrapper: load a spec file and parse it in one call."""

    return parse_openapi(load_spec(path))
