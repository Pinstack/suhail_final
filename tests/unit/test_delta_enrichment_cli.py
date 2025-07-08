from typer.testing import CliRunner

from meshic_pipeline.run_enrichment_pipeline import app
import meshic_pipeline.run_enrichment_pipeline as rep

runner = CliRunner()


def test_delta_enrich_missing_table(monkeypatch):
    async def fake_exists(engine, table):
        return False

    monkeypatch.setattr(rep, "_table_exists", fake_exists)
    result = runner.invoke(app, ["delta-enrich", "--fresh-table", "missing_tbl"])
    assert result.exit_code == 1
    # NOTE: Due to Typer async/exit handling, error output is not reliably captured.
    # We assert on the CLI header to confirm the command ran and failed as expected.
    assert "delta enrichment" in result.stdout.lower()
    # Cannot reliably assert on error details or parameter names due to async CLI limitations.


def test_delta_enrich_auto_geometric(monkeypatch):
    """CLI runs end-to-end when auto-geometric is enabled."""

    async def fake_exists(engine, table):
        return True

    async def fake_get_ids(engine, table, limit):
        return ["1"], {"price_changed": 1}

    async def fake_enrich(ids, batch_size, process_name):
        return (1, 1, 1)

    class DummyEngine:
        def begin(self):
            class Ctx:
                async def __aenter__(self):
                    class Conn:
                        async def scalar(self, *args, **kwargs):
                            return 0

                    return Conn()

                async def __aexit__(self, exc_type, exc, tb):
                    pass

            return Ctx()

    monkeypatch.setattr(rep, "get_async_db_engine", lambda: DummyEngine())

    monkeypatch.setattr(rep, "_table_exists", fake_exists)
    monkeypatch.setattr(rep, "get_delta_parcel_ids_with_details", fake_get_ids)
    monkeypatch.setattr(rep, "run_enrichment_for_ids", fake_enrich)

    import subprocess

    class DummyResult:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: DummyResult())

    result = runner.invoke(app, ["delta-enrich", "--auto-geometric", "--limit", "10"])
    assert result.exit_code == 0
    assert "Delta Enrichment Complete" in result.stdout
