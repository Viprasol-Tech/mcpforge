"""Render a :class:`ParsedAPI` as a colourful rich table of generated tools."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from .models import ParsedAPI

_METHOD_STYLE = {
    "get": "green",
    "post": "cyan",
    "put": "yellow",
    "patch": "magenta",
    "delete": "red",
}


def build_tools_table(parsed: ParsedAPI) -> Table:
    """Build a rich :class:`Table` listing every generated tool."""

    table = Table(
        title=f"mcpforge :: {parsed.title} v{parsed.version}  ({parsed.tool_count} tools)",
        title_style="bold white",
        header_style="bold",
        expand=False,
    )
    table.add_column("#", justify="right", style="dim")
    table.add_column("Tool", style="bold")
    table.add_column("Method", justify="center")
    table.add_column("Path")
    table.add_column("Inputs", justify="right")
    table.add_column("Required", justify="right")

    for index, tool in enumerate(parsed.tools, start=1):
        style = _METHOD_STYLE.get(tool.method, "white")
        table.add_row(
            str(index),
            tool.name,
            f"[{style}]{tool.method.upper()}[/{style}]",
            tool.path,
            str(tool.input_count),
            str(len(tool.required_inputs)),
        )

    return table


def render_dashboard(parsed: ParsedAPI, *, console: Console | None = None) -> None:
    """Print the tools table to ``console`` (or a fresh stdout console)."""

    (console or Console()).print(build_tools_table(parsed))
