from typer.testing import CliRunner
from meshic_pipeline.run_geometric_pipeline import app

runner = CliRunner()

def test_geometric_cli_invalid_bbox():
    # Should fail with invalid bbox length
    result = runner.invoke(app, ["--bbox", "1", "2", "3"])  # Only 3 values
    assert result.exit_code != 0
    # Check both stdout and stderr for the error message
    output = result.stdout + getattr(result, 'stderr', '')
    assert ("Bounding box must be 4 floats" in output) or ("Usage:" in output)

def test_geometric_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--bbox" in result.stdout
    assert "--province" in result.stdout
    assert "--saudi-arabia" in result.stdout 