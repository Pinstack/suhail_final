import asyncio
from meshic_pipeline import run_enrichment_pipeline as rep


def test_delta_enrich_no_parcels(monkeypatch, capsys):
    async def fake_get_delta_ids_with_details(engine, table, limit):
        return [], {}

    monkeypatch.setattr(rep, "get_async_db_engine", lambda: None)
    monkeypatch.setattr(rep, "get_delta_parcel_ids_with_details", fake_get_delta_ids_with_details)

    logged = {}

    def fake_info(msg, *args, **kwargs):
        logged["msg"] = msg
        logged["extra"] = kwargs.get("extra")

    monkeypatch.setattr(rep.logger, "info", fake_info)

    rep.delta_enrich(batch_size=10, limit=None, fresh_mvt_table="tmp_table", show_details=True, auto_run_geometric=False)

    out = capsys.readouterr().out
    assert "No transaction price changes detected" in out
    assert "0 parcels" in out
    assert logged.get("extra") is not None
    assert logged["extra"]["metrics"]["parcels_identified_for_enrichment"] == 0
