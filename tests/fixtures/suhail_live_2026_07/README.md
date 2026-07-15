# Suhail live-source fixtures (captured 2026-07-15)

Real payloads captured from the live Suhail platform, used as regression / contract-test
inputs and as evidence for [`docs/SUHAIL_SOURCE_AUDIT_2026-07.md`](../../../docs/SUHAIL_SOURCE_AUDIT_2026-07.md).

## `tiles/` — MVT vector tiles (gzip-compressed, as served)
- `riyadh_15_20636_14069.vector.pbf.gz` — downtown Riyadh; contains all 17 tile layers
  (parcels, parcels-base, parcels-centroids, neighborhoods(+centroids), subdivisions,
  provinces, dimensions, streets, metro_lines, bus_lines, metro_stations,
  riyadh_bus_stations, qi_population_metrics, qi_stripes, building_detection,
  non_saudi_ownership_zones).
- `riyadh_15_20640_14060.vector.pbf.gz` — residential Riyadh; parcels with recent transactions.

Tiles are served with `Content-Encoding: gzip` (always on). `aiohttp` auto-decompresses in
the pipeline; test helpers `gzip.decompress()` first.

## `api/` — api2.suhail.ai JSON payloads
- `regions.json`, `settings_app.json`, `tiles_modes.json`, `gl_style_ksa.sources_and_layers.json`
  — platform/config surface.
- `transactions__9941681.json` — 6 real transaction records (39 fields each).
- `buildingRules__9858274.json`, `priceOfMeter__9858274.json` — enrichment payloads.
- `parcel_detail__9858274.json` — consolidated `parcel/{id}` endpoint (new).
- `landMetrics_list__region10.json`, `landMetrics__neighborhood1002969.json`,
  `landZoningGroups.json` — new neighbourhood market-intelligence endpoints (not yet ingested).

Consumed by `tests/unit/test_live_tile_schema.py` and
`tests/unit/test_enrichment_parsers_contract.py`.
