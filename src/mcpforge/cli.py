"""Typer CLI for mcpforge.

Commands:
    inspect SPEC        Parse a spec file and print the generated tools table.
    gen SPEC -o OUT.py  Write a runnable MCP server to OUT.py.
    demo                Run against the bundled sample spec.
    version             Print the installed version.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.syntax import Syntax

from . import __version__
from .codegen import render_server
from .dashboard import render_dashboard
from .models import ParsedAPI
from .openapi import OpenAPIError, parse_openapi, parse_spec_file
from .sample import SAMPLE_OPENAPI

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Generate a runnable MCP server from an OpenAPI spec.",
)
console = Console()


def _print_code_preview(source: str, *, lines: int = 24) -> None:
    """Print the first ``lines`` lines of generated source with highlighting."""

    snippet = "\n".join(source.splitlines()[:lines])
    console.print(Syntax(snippet, "python", theme="ansi_dark", line_numbers=False))


@app.command()
def inspect(
    spec: Path = typer.Argument(..., help="Path to an OpenAPI .json/.yaml/.yml file."),
) -> None:
    """Parse SPEC and print the table of tools that would be generated."""

    try:
        parsed = parse_spec_file(spec)
    except (OpenAPIError, FileNotFoundError, ValueError) as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    render_dashboard(parsed, console=console)


@app.command()
def gen(
    spec: Path = typer.Argument(..., help="Path to an OpenAPI .json/.yaml/.yml file."),
    out: Path = typer.Option(
        Path("server.py"), "--out", "-o", help="Where to write the generated server."
    ),
) -> None:
    """Generate an MCP server from SPEC and write it to OUT."""

    try:
        parsed = parse_spec_file(spec)
    except (OpenAPIError, FileNotFoundError, ValueError) as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    source = render_server(parsed, module_name=out.stem)
    out.write_text(source, encoding="utf-8")
    console.print(
        f"[green]wrote[/green] {out} "
        f"([bold]{parsed.tool_count}[/bold] tools from {parsed.title} v{parsed.version})"
    )


@app.command()
def demo() -> None:
    """Run mcpforge against the bundled sample spec and show the output."""

    parsed: ParsedAPI = parse_openapi(SAMPLE_OPENAPI)
    render_dashboard(parsed, console=console)
    console.print("\n[bold]Generated server (first lines):[/bold]\n")
    source = render_server(parsed)
    _print_code_preview(source, lines=22)


@app.command()
def version() -> None:
    """Print the installed mcpforge version."""

    console.print(f"mcpforge {__version__}")


if __name__ == "__main__":
    app()
