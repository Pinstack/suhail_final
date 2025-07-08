import pytest
from typer.testing import CliRunner
from meshic_pipeline.cli import app
import asyncio
from unittest.mock import AsyncMock

runner = CliRunner()

@pytest.mark.parametrize("command", [
    ["geometric", "--help"],
    ["fast-enrich", "--help"],
    ["incremental-enrich", "--help"],
    ["full-refresh", "--help"],
    ["delta-enrich", "--help"],
    ["smart-pipeline", "--help"],
    ["monitor", "--help"],
    ["province-geometric", "--help"],
    ["saudi-arabia-geometric", "--help"],
    ["discovery-summary", "--help"],
    ["province-pipeline", "--help"],
    ["saudi-pipeline", "--help"],
])
def test_cli_command_help(command):
    result = runner.invoke(app, command)
    assert result.exit_code == 0
    assert "--help" in result.stdout or "Usage" in result.stdout or "usage" in result.stdout

# Expanded CLI tests for 'geometric' command
@pytest.mark.parametrize("args,expected", [
    ([], "Run the geometric pipeline"),
    (["--bbox", "46.0", "24.0", "47.0", "25.0"], "Run the geometric pipeline"),
    (["--recreate-db"], "Run the geometric pipeline"),
])
def test_geometric_command_runs(monkeypatch, args, expected):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: type("DummyResult", (), {"returncode": 0, "stdout": "", "stderr": ""})())
    result = runner.invoke(app, ["geometric"] + args)
    assert result.exit_code == 0

# Expanded CLI tests for 'delta-enrich' command
@pytest.mark.parametrize("args,expected", [
    (["--auto-geometric"], "delta enrichment"),
    (["--limit", "10"], "delta enrichment"),
])
def test_delta_enrich_command_runs(monkeypatch, args, expected):
    import meshic_pipeline.run_enrichment_pipeline as rep
    monkeypatch.setattr(rep, "get_async_db_engine", lambda: None)
    monkeypatch.setattr(rep, "_table_exists", AsyncMock(return_value=True))
    monkeypatch.setattr(rep, "get_delta_parcel_ids_with_details", AsyncMock(return_value=([], {})))
    monkeypatch.setattr(rep, "run_enrichment_for_ids", AsyncMock(return_value=(0, 0, 0)))
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: type("DummyResult", (), {"returncode": 0, "stdout": "", "stderr": ""})())
    result = runner.invoke(app, ["delta-enrich"] + args)
    assert result.exit_code == 0
    assert "delta enrichment" in result.stdout.lower()

# Template for further expansion:
# def test_command_with_invalid_args(monkeypatch):
#     result = runner.invoke(app, ["geometric", "--bbox", "bad", "args"])
#     assert result.exit_code != 0
#     assert "error" in result.stdout.lower() or result.stderr.lower()

@pytest.mark.parametrize("args,should_succeed,expected", [
    (["riyadh"], True, None),
    ([], False, "Error"),
    (["riyadh", "--strategy", "invalid"], True, None),  # Should succeed, but strategy may be ignored or defaulted
])
def test_province_geometric_command(monkeypatch, args, should_succeed, expected):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: None)
    result = runner.invoke(app, ["province-geometric"] + args)
    if should_succeed:
        assert result.exit_code == 0
    else:
        assert result.exit_code != 0
        if expected:
            assert expected.lower() in result.stdout.lower() or result.stderr.lower()

@pytest.mark.parametrize("action,should_succeed", [
    ("status", True),
    ("recommend", True),
    ("schedule-info", True),
    ("invalid-action", False),
])
def test_monitor_command(monkeypatch, action, should_succeed):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: type("DummyResult", (), {"returncode": 0, "stdout": "", "stderr": ""})())
    result = runner.invoke(app, ["monitor", action])
    if should_succeed:
        assert result.exit_code == 0
    else:
        assert result.exit_code != 0 or "error" in result.stdout.lower() or result.stderr.lower()

@pytest.mark.parametrize("args", [
    [],
    ["--batch-size", "100"],
    ["--limit", "10"],
])
def test_fast_enrich_command(monkeypatch, args):
    # Mock enrichment function
    import meshic_pipeline.run_enrichment_pipeline as rep
    monkeypatch.setattr(rep, "fast_enrich", lambda *a, **k: None)
    result = runner.invoke(app, ["fast-enrich"] + args)
    assert result.exit_code == 0

@pytest.mark.parametrize("args", [
    [],
    ["--batch-size", "50"],
    ["--days-old", "7"],
    ["--limit", "5"],
])
def test_incremental_enrich_command(monkeypatch, args):
    import meshic_pipeline.run_enrichment_pipeline as rep
    monkeypatch.setattr(rep, "incremental_enrich", lambda *a, **k: None)
    result = runner.invoke(app, ["incremental-enrich"] + args)
    assert result.exit_code == 0

@pytest.mark.parametrize("args", [
    [],
    ["--batch-size", "25"],
    ["--limit", "2"],
])
def test_full_refresh_command(monkeypatch, args):
    import meshic_pipeline.run_enrichment_pipeline as rep
    monkeypatch.setattr(rep, "full_refresh", lambda *a, **k: None)
    result = runner.invoke(app, ["full-refresh"] + args)
    assert result.exit_code == 0

@pytest.mark.parametrize("args", [
    [],
    ["--geometric-first"],
    ["--batch-size", "300"],
    ["--bbox", "46.0", "24.0", "47.0", "25.0"],
])
def test_smart_pipeline_command(monkeypatch, args):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: type("DummyResult", (), {"returncode": 0, "stdout": "", "stderr": ""})())
    result = runner.invoke(app, ["smart-pipeline"] + args)
    assert result.exit_code == 0

@pytest.mark.parametrize("args,should_succeed", [
    ([], True),
    (["--strategy", "efficient"], True),
    (["--recreate-db"], True),
    (["--save-as-temp", "temp_table"], True),
])
def test_saudi_arabia_geometric_command(monkeypatch, args, should_succeed):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: None)
    result = runner.invoke(app, ["saudi-arabia-geometric"] + args)
    if should_succeed:
        assert result.exit_code == 0
    else:
        assert result.exit_code != 0

# discovery-summary: no args, just test it runs

def test_discovery_summary_command(monkeypatch):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: None)
    result = runner.invoke(app, ["discovery-summary"])
    assert result.exit_code == 0

@pytest.mark.parametrize("args,should_succeed", [
    (["riyadh"], True),
    (["riyadh", "--strategy", "optimal", "--batch-size", "300", "--geometric-first"], True),
    ([], False),  # Missing required province
])
def test_province_pipeline_command(monkeypatch, args, should_succeed):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: None)
    result = runner.invoke(app, ["province-pipeline"] + args)
    if should_succeed:
        assert result.exit_code == 0
    else:
        assert result.exit_code != 0

@pytest.mark.parametrize("args,should_succeed", [
    ([], True),
    (["--strategy", "efficient", "--batch-size", "500", "--geometric-first"], True),
])
def test_saudi_pipeline_command(monkeypatch, args, should_succeed):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: None)
    result = runner.invoke(app, ["saudi-pipeline"] + args)
    if should_succeed:
        assert result.exit_code == 0
    else:
        assert result.exit_code != 0

def test_geometric_help_output():
    result = runner.invoke(app, ["geometric", "--help"])
    assert result.exit_code == 0
    assert "Run the geometric pipeline" in result.stdout or "Bounding box" in result.stdout

# Enhance delta-enrich output assertion

def test_delta_enrich_auto_geometric_output(monkeypatch):
    import meshic_pipeline.run_enrichment_pipeline as rep
    monkeypatch.setattr(rep, "get_async_db_engine", lambda: None)
    monkeypatch.setattr(rep, "_table_exists", AsyncMock(return_value=True))
    monkeypatch.setattr(rep, "get_delta_parcel_ids_with_details", AsyncMock(return_value=([], {})))
    monkeypatch.setattr(rep, "run_enrichment_for_ids", AsyncMock(return_value=(0, 0, 0)))
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: type("DummyResult", (), {"returncode": 0, "stdout": "", "stderr": ""})())
    result = runner.invoke(app, ["delta-enrich", "--auto-geometric"])
    assert result.exit_code == 0
    assert "delta enrichment" in result.stdout.lower()
    assert "auto-running geometric pipeline" in result.stdout.lower() or "fresh mvt data" in result.stdout.lower()

# Enhance monitor invalid-action output assertion

def test_monitor_invalid_action(monkeypatch):
    monkeypatch.setattr("subprocess.run", lambda *a, **k: type("DummyResult", (), {"returncode": 1, "stdout": "", "stderr": "Invalid action"})())
    result = runner.invoke(app, ["monitor", "not-a-real-action"])
    assert result.exit_code != 0
    assert "error" in result.stdout.lower() or result.stderr.lower()

# Add similar output assertions for other commands as needed. 