"""Render the mcpforge demo output to an SVG for the README hero.

Runs the real library pipeline on the bundled sample spec
(``OpenAPI dict -> ParsedAPI -> rich table``) into a recording console, then
exports ``docs/assets/demo.svg``. Regenerate with::

    PYTHONPATH=src python docs/make_demo.py
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mcpforge.codegen import render_server
from mcpforge.dashboard import render_dashboard
from mcpforge.openapi import parse_openapi
from mcpforge.sample import SAMPLE_OPENAPI

_OUT = Path(__file__).resolve().parent / "assets" / "demo.svg"


def main() -> None:
    """Render the sample tools table + code caption and save the SVG."""

    parsed = parse_openapi(SAMPLE_OPENAPI)

    console = Console(record=True, width=100)
    render_dashboard(parsed, console=console)

    # A short caption echoing the first lines of the generated server, exactly
    # as the `mcpforge demo` command prints them.
    source = render_server(parsed)
    console.print("\n[bold]Generated server (first lines):[/bold]\n")
    for line in source.splitlines()[:6]:
        console.print(f"[grey70]{line}[/grey70]")

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    console.save_svg(str(_OUT), title="mcpforge")
    print(f"wrote {_OUT} ({_OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
