import meshic_pipeline.run_enrichment_pipeline as rep


def test_smart_pipeline_import(monkeypatch):
    called = {}
    def fake_main():
        called['ok'] = True
    monkeypatch.setattr('meshic_pipeline.run_geometric_pipeline.main', fake_main)
    # Call the command function directly to ensure import works
    rep.smart_pipeline_enrich(geometric_first=True, trigger_after=False, batch_size=300, bbox=None)
    assert called.get('ok')
