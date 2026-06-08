"""CLI smoke tests via typer's CliRunner and spec-file loading."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from mcpforge import SAMPLE_OPENAPI
from mcpforge.cli import app
from mcpforge.openapi import load_spec, parse_spec_file

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "mcpforge" in result.stdout


def test_demo_command_runs() -> None:
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0
    assert "Petstore" in result.stdout
    assert "listPets" in result.stdout


def test_demo_shows_generated_code() -> None:
    result = runner.invoke(app, ["demo"])
    assert "Generated server" in result.stdout


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code != 0 or "Usage" in result.stdout


def test_inspect_json_spec(tmp_path: Path) -> None:
    spec = tmp_path / "api.json"
    spec.write_text(json.dumps(SAMPLE_OPENAPI), encoding="utf-8")
    result = runner.invoke(app, ["inspect", str(spec)])
    assert result.exit_code == 0
    assert "getPetById" in result.stdout


def test_inspect_yaml_spec(tmp_path: Path) -> None:
    spec = tmp_path / "api.yaml"
    spec.write_text(yaml.safe_dump(SAMPLE_OPENAPI), encoding="utf-8")
    result = runner.invoke(app, ["inspect", str(spec)])
    assert result.exit_code == 0
    assert "createPet" in result.stdout


def test_inspect_missing_file_errors() -> None:
    result = runner.invoke(app, ["inspect", "does-not-exist.yaml"])
    assert result.exit_code == 1


def test_gen_writes_compilable_server(tmp_path: Path) -> None:
    spec = tmp_path / "api.json"
    spec.write_text(json.dumps(SAMPLE_OPENAPI), encoding="utf-8")
    out = tmp_path / "server.py"
    result = runner.invoke(app, ["gen", str(spec), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    compile(out.read_text(encoding="utf-8"), str(out), "exec")


def test_gen_reports_tool_count(tmp_path: Path) -> None:
    spec = tmp_path / "api.yaml"
    spec.write_text(yaml.safe_dump(SAMPLE_OPENAPI), encoding="utf-8")
    out = tmp_path / "s.py"
    result = runner.invoke(app, ["gen", str(spec), "--out", str(out)])
    assert result.exit_code == 0
    assert "3" in result.stdout


def test_load_spec_json_roundtrip(tmp_path: Path) -> None:
    spec = tmp_path / "api.json"
    spec.write_text(json.dumps(SAMPLE_OPENAPI), encoding="utf-8")
    assert load_spec(spec)["info"]["title"] == "Petstore"


def test_load_spec_yaml_roundtrip(tmp_path: Path) -> None:
    spec = tmp_path / "api.yml"
    spec.write_text(yaml.safe_dump(SAMPLE_OPENAPI), encoding="utf-8")
    assert load_spec(spec)["info"]["title"] == "Petstore"


def test_parse_spec_file_yaml(tmp_path: Path) -> None:
    spec = tmp_path / "api.yaml"
    spec.write_text(yaml.safe_dump(SAMPLE_OPENAPI), encoding="utf-8")
    parsed = parse_spec_file(spec)
    assert parsed.tool_count == 3
