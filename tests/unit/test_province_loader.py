from meshic_pipeline.config import settings
from meshic_pipeline.utils.tile_list_generator import tiles_from_bbox_z


def test_provinces_loaded():
    assert 'riyadh' in settings.provinces
    meta = settings.get_province_meta('riyadh')
    assert 'bbox_z15' in meta
    tiles = tiles_from_bbox_z(meta['bbox_z15'])
    assert len(tiles) > 0
