import re

from typer.testing import CliRunner
from suhail_pipeline.run_geometric_pipeline import app

runner = CliRunner()

# Typer/Rich colourises option names in help output (e.g. in CI, FORCE_COLOR),
# rendering "--bbox" as "\x1b[..m-\x1b[0m\x1b[..m-bbox\x1b[0m" so a literal
# substring check fails even though the option is present. Strip ANSI first.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    return _ANSI_RE.sub("", text)


def test_geometric_cli_invalid_bbox():
    # Should fail with invalid bbox length
    result = runner.invoke(app, ["--bbox", "1", "2", "3"])  # Only 3 values
    assert result.exit_code != 0
    # Check both stdout and stderr for the error message
    output = _plain(result.stdout + getattr(result, "stderr", ""))
    assert ("Bounding box must be 4 floats" in output) or ("Usage:" in output)


def test_geometric_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    out = _plain(result.stdout)
    assert "--bbox" in out
    assert "--province" in out
    assert "--saudi-arabia" in out
