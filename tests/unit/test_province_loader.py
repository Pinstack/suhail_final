from meshic_pipeline.config import settings
from meshic_pipeline.utils.tile_list_generator import tiles_from_bbox_z


def test_provinces_loaded(monkeypatch):
    mock_provinces = {
        'riyadh': {
            'display_name': 'Riyadh',
            'bbox_latlon': {
                'southwest': [24.0, 46.0],
                'northeast': [25.0, 47.0],
            },
            'tile_url_template': 'https://tiles.example.com/riyadh/{z}/{x}/{y}.pbf',
        }
    }
    monkeypatch.setattr(settings, 'provinces', mock_provinces)
    assert 'riyadh' in settings.provinces
    meta = settings.get_province_meta('riyadh')
    assert 'display_name' in meta
    assert 'bbox_latlon' in meta
    assert 'tile_url_template' in meta
    # Optionally, check bbox_latlon structure
    assert 'southwest' in meta['bbox_latlon']
    assert 'northeast' in meta['bbox_latlon']
