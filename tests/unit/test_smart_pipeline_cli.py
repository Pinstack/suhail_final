import types
from typer.testing import CliRunner

from meshic_pipeline.run_enrichment_pipeline import app
import meshic_pipeline.run_enrichment_pipeline as rep
import meshic_pipeline.run_geometric_pipeline as rgp

runner = CliRunner()


def test_smart_pipeline_enrich_runs_geometric(monkeypatch):
    called = False

    def fake_main():
        nonlocal called
        called = True

    monkeypatch.setattr(rgp, "main", fake_main)
    monkeypatch.setattr(
        rep.fast_enrich,
        "callback",
        lambda **kw: None,
        raising=False,
    )

    result = runner.invoke(app, ["smart-pipeline-enrich"])
    assert result.exit_code == 0
    assert called
