"""Pydantic models describing a parsed OpenAPI document and its MCP tools.

These models are the stable, serialisable core of mcpforge. The whole pipeline
is the pure transformation::

    OpenAPI dict  ->  ParsedAPI (list[ToolSpec])  ->  generated server source

so everything here is plain data with no dependency on the ``mcp`` SDK.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# HTTP methods that OpenAPI treats as operations (in canonical emit order).
HTTP_METHODS: tuple[str, ...] = ("get", "post", "put", "patch", "delete")


class ToolSpec(BaseModel):
    """A single MCP tool derived from one OpenAPI operation.

    Attributes:
        name: A valid Python/MCP identifier, unique within a :class:`ParsedAPI`.
        description: Human-readable summary shown to the LLM.
        input_schema: A JSON-Schema object (``type: object``) for the tool input.
        method: The HTTP method in lowercase (e.g. ``get``).
        path: The original templated path (e.g. ``/pets/{petId}``).
        operation_id: The raw ``operationId`` if the spec provided one.
    """

    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}}
    )
    method: str
    path: str
    operation_id: str | None = None

    @property
    def input_count(self) -> int:
        """Number of top-level input properties on this tool."""
        props = self.input_schema.get("properties", {})
        return len(props) if isinstance(props, dict) else 0

    @property
    def required_inputs(self) -> list[str]:
        """Names of the required input properties, in declared order."""
        req = self.input_schema.get("required", [])
        return list(req) if isinstance(req, list) else []


class ParsedAPI(BaseModel):
    """A fully parsed OpenAPI document ready for code generation.

    Attributes:
        title: The ``info.title`` of the source document.
        version: The ``info.version`` of the source document.
        tools: The tools, one per operation, in document order.
    """

    title: str = "API"
    version: str = "0.0.0"
    tools: list[ToolSpec] = Field(default_factory=list)

    @property
    def tool_count(self) -> int:
        """Number of generated tools."""
        return len(self.tools)

    def tool_names(self) -> list[str]:
        """All tool names in order."""
        return [t.name for t in self.tools]
