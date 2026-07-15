"""The decoder must skip non-MVT payloads (e.g. an HTML error page the tile server
returns instead of a vector tile) cleanly, rather than raising a protobuf DecodeError.
Salvaged idea from the abandoned fix-mvt-decoder-str-bug branch, cleaned up.
"""
from suhail_pipeline.decoder.mvt_decoder import MVTDecoder


def test_html_payload_is_skipped_not_decoded():
    dec = MVTDecoder()
    html = b"<!DOCTYPE html><html><body>503 Service Unavailable</body></html>"
    assert dec.decode_bytes(html, 15, 20636, 14069) == {}


def test_leading_whitespace_html_is_skipped():
    dec = MVTDecoder()
    assert dec.decode_bytes(b"\n   <html>error</html>", 15, 1, 1) == {}


def test_empty_payload_is_skipped():
    dec = MVTDecoder()
    assert dec.decode_bytes(b"", 15, 1, 1) == {}
