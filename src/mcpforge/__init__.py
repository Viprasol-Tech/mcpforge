"""mcpforge — generate a runnable MCP server from an OpenAPI spec.

Public API::

    from mcpforge import parse_openapi, parse_spec_file, render_server
    from mcpforge import ParsedAPI, ToolSpec, SAMPLE_OPENAPI
"""

from __future__ import annotations

from .codegen import render_server
from .models import ParsedAPI, ToolSpec
from .openapi import OpenAPIError, load_spec, parse_openapi, parse_spec_file
from .sample import SAMPLE_OPENAPI
from .tools import build_input_schema, map_operation_to_tool, sanitize_identifier

__version__ = "0.1.0"

__all__ = [
    "SAMPLE_OPENAPI",
    "OpenAPIError",
    "ParsedAPI",
    "ToolSpec",
    "__version__",
    "build_input_schema",
    "load_spec",
    "map_operation_to_tool",
    "parse_openapi",
    "parse_spec_file",
    "render_server",
    "sanitize_identifier",
]
