from meshic_pipeline.decoder.mvt_decoder import MVTDecoder


def test_decode_empty_bytes():
    decoder = MVTDecoder()
    assert decoder.decode_bytes(b"", 15, 0, 0) == {}


def test_cast_property_types_basic():
    decoder = MVTDecoder()
    result = decoder._cast_property_types({"parcel_id": "1", "other": "abc"})
    assert result["parcel_id"] == 1
    assert result["other"] == "abc"
