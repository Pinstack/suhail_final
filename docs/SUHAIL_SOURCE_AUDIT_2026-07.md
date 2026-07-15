# Suhail source audit & integration gap analysis (2026-07-15)

Forensic, evidence-led audit of the **current live Suhail site** against this
repository's scraper, decoder, parser, schema and ingestion pipeline. Every claim
below is backed by a captured payload or a source line. Captured evidence lives in
[`tests/fixtures/suhail_live_2026_07/`](../tests/fixtures/suhail_live_2026_07) and the
working capture set under the session scratchpad.

> TL;DR — The site was rebuilt on a new React/Vite front end backed by `api2.suhail.ai`.
> The tile schema is dramatically richer than when the scraper was written: the
> `parcels` MVT layer now carries **inline time-series market data** (1w/1m/6m/12m
> transaction price, price-of-meter, transaction count and date), and there are
> **five new tile layers** (`dimensions`, `streets`, `provinces`, `building_detection`,
> `non_saudi_ownership_zones`) plus a duplicate `parcels-base`. Several existing layers
> (`bus_lines`, `metro_stations`, `riyadh_bus_stations`, `qi_population_metrics`,
> `qi_stripes`) changed field names and now capture **nothing or only their key**.
> All three enrichment REST endpoints still work and are unauthenticated; a new
> consolidated `parcel/{id}` endpoint and a province-wide neighbourhood-metrics list
> endpoint are now available.

---

## 1. Method & evidence

Reconnaissance was done against transport, not the rendered UI:

- Loaded `https://www.suhail.ai` + `/Riyadh/metrics` in a headless browser and captured
  all network activity.
- Downloaded and decoded a live MVT tile (`tiles.suhail.ai/maps/riyadh/15/20636/14069.vector.pbf`,
  and a residential tile `.../20640/14060`) with `mapbox_vector_tile`.
- Pulled the authoritative Mapbox GL style (`tiles.suhail.ai/gl-styles/ksa.json`) — it
  declares every tile source, source-layer and tile URL template.
- Pulled `api2.suhail.ai/{regions,settings/app}` and `tiles.suhail.ai/modes/`.
- Mined the front-end JS bundles (`assets/index-*.js` etc.) for the complete axios API
  surface (base `https://api2.suhail.ai/`).
- Probed each REST endpoint directly with real parcel/neighbourhood/region IDs taken
  from the decoded tile.

Capture manifest: [`CAPTURE_MANIFEST.md`](../tests/fixtures/suhail_live_2026_07) equivalent
saved in scratchpad; representative payloads committed under `tests/fixtures/suhail_live_2026_07/`.

### Transport facts that matter

- **Tiles are always gzipped.** `tiles.suhail.ai` returns `Content-Encoding: gzip`
  even for `Accept-Encoding: identity`. `aiohttp` auto-decompresses this, so the
  downloader is unaffected — but any code that reads tile bytes *without* HTTP-layer
  decompression (raw `requests` without `--compressed`, reading a hand-saved `.pbf`) will
  see gzip magic `1f 8b` and fail to decode. Evidence: `curl -H "Accept-Encoding: identity" -D-`
  still returns gzip; `mapbox_vector_tile.decode` raises `DecodeError` on the raw bytes,
  succeeds after `gzip.decompress`.
- **No auth on data endpoints.** Every `api2.suhail.ai` data GET returned `200` with no
  `Authorization` header. `settings/app` advertises `AnonUserRestrictionsEnabled: true`,
  `AnonUserParcelClicks: 15`, `AnonUserSessionTimeSec: 900` — these are **UI-side** limits,
  not server-enforced on the REST endpoints we probed.
- **Tile server = Tegola** (`Tegola-Cache: HIT`), `maxzoom: 15`, CORS `Vary: Origin`.

---

## 2. Live source capability inventory

### 2.1 Hosts

| Host | Role |
|------|------|
| `www.suhail.ai` | React/Vite SPA. Routes: `/:Region/metrics`, `/:Region/parcel/:parcelObjectId`, `/parcel/:id`, `/map`, `/mobile-metrics`, `/offer/:offerCode` |
| `api2.suhail.ai` | Primary JSON API (axios base `https://api2.suhail.ai/`) |
| `tiles.suhail.ai` | MVT vector tiles, `gl-styles/ksa.json`, `modes/`, raster overlays |
| `reports.suhail.ai` | PDF reports: `/api/report/Parcel`, `/api/report/Order` |
| `beacon.suhail.ai` | Strapi CMS (news feed, mega-project content, GPTV form) |

### 2.2 REST API surface (from JS bundle + live probes)

Method is GET unless noted. Status column = observed against live probe.

| Endpoint (relative to `api2.suhail.ai/`) | Params | Purpose | Status | Captured by repo? |
|---|---|---|---|---|
| `regions` | – | 13 regions, nested provinces, centroids, bbox, `mapStyleUrl`, `mapKey`, `metricsUrl` | 200 | Partial — `scripts/util/sync_provinces.py` reads a subset |
| `settings/app` | – | anon limits, transaction filter types, map bounds, unit-status colours, report URLs, `realEstateTaxPercentage`, Nafath flag | 200 | **No** |
| `parcel/{parcelObjectId}` | path | **Consolidated** parcel detail incl. geometry + centroid + dimensionsCount | 200 | **No** (new) |
| `transactions?parcelObjectId=` | parcel | Per-parcel transaction records (39 fields) | 200 | Yes (5 fields + raw) |
| `consolidatedTransactions` | `parcelObjectId, regionId, LookbackValue, LookbackType, fromPrice, toPrice, type` | Filtered per-parcel transactions | 200 | **No** (new) |
| `transactionsAsMapboxGeojson` | `RegionId, LookbackValue, LookbackType, NewDaysThreshold, fromPrice, toPrice, type` | Region-wide transaction points as GeoJSON (2728 features for Riyadh/1mo) | 200 | **No** (new) |
| `transactions/neighbourhood?neighborhoodId=` | nbhd | Paginated neighbourhood transactions | 200 | **No** (new) |
| `parcel/buildingRules?parcelObjectId=` | parcel | Zoning/building rules (16 fields incl. setbacks) | 200 | Yes (fully) |
| `api/parcel/metrics/priceOfMeter?parcelObjsIds=&groupingType=Monthly` | parcels | Per-parcel monthly price metrics (neighbourhood-derived) | 200 | Yes (partial — drops `neighborhoodId`) |
| `api/mapMetrics/landMetrics?neighborhoodId=&growthRateType=` | nbhd | Neighbourhood market metrics + growth indicators, per land-use group | 200 | **No** (util-only, not persisted) |
| `api/mapMetrics/landMetrics/list?regionId=&offset=&limit=` | region, page | **Province-wide** paginated neighbourhood metrics (totals, medians, growth, last-execution price per land-use group) | 200 | **No** (new) |
| `api/parcel/landZoningGroups` | – | Zoning-group lookup with national usage counts | 200 | **No** (new) |
| `api/parcel/search` | query | Parcel search | 400 w/o valid query | **No** (new) |
| `api/parcel/shareLink?parcelObjectId=` | parcel | Share link | – | **No** |
| `api/bookmark`, `Bookmark`, `Badges/*`, `oauth/*`, `accounts/*`, `complaints`, `events/log`, `api/attachments`, `api/StrapiContent/*`, `api/MegaProjects/project/content` | – | User/account/CMS features | – | N/A (out of scope for ingestion) |

### 2.3 Tile map style (`gl-styles/ksa.json`)

- 13 per-region vector tile sources: `tiles.suhail.ai/maps/{riyadh,madinah,qassim,asir,eastern,makkah,bahah,hail,jawf,jazan,najran,northern_borders,tabuk}/{z}/{x}/{y}.vector.pbf` plus an all-KSA `maps/ksa/...` source, each `maxzoom: 15` with a `bounds` array.
- Suhail-specific **source-layers** referenced by the style (excludes Mapbox base layers):
  `parcels`, `parcels-centroids`, `neighborhoods`, `neighborhoods-centroids`, `subdivisions`,
  `provinces`, `provinces-centroids`, `dimensions`, `streets`, `building_detection`,
  `non_saudi_ownership_zones`, `mega_projects`, `sb_shape`, `sb_area`, `qi_population_metrics`,
  `metro_lines`, `bus_lines`, `metro_stations`, `riyadh_bus_stations`, `regions`.
- New raster overlays: per-region base rasters on Huawei OBS (`qeye-tiles-prod.obs.me-east-1.myhuaweicloud.com`)
  and named development-project rasters (`tiles.suhail.ai/tiles/{watheer,rakiz,osus,...}`).
- Map coloring modes (`tiles/modes/`): `zoning_color` (by `zoning_id`), `shape_area`,
  `price_of_meter`, `transaction_price`, `plain` — confirms these are the live-styled parcel fields.

### 2.4 Live MVT tile — decoded layers & fields (ground truth)

Decoded from `riyadh/15/20636/14069` (downtown) and `.../20640/14060` (residential). 17 layers present:

**`parcels`** (3083 feats, Polygon) — the headline change. Fields:
`parcel_id, parcel_objectid, neighborhaname, neighborhood_id, province_id, municipality_aname,
block_no, subdivision_id, subdivision_no, shape_area, zoning_id, zoning_color, ruleid,
zoning_group, transaction_price, price_of_meter,
transaction_price_1w/1m/6m/12m, price_of_meter_1w/1m/6m/12m,
transactions_count_1w/1m/6m/12m, transaction_date_1w/1m/6m/12m,
landuseadetailed, landuseagroup, parcel_no`.

**`parcels-base`** (3083, Polygon) — identical field set to `parcels` (base/unstyled copy).

**`parcels-centroids`** (3081, Point) — now carries the same time-series block plus
`transactions_count`, `transaction_date`.

**`neighborhoods`** (Polygon/MultiPolygon) — adds `neighborh_aname, zoning_group` and the
full 1w/1m/6m/12m time-series (`transactions_count_*` are strings here).

**`subdivisions`** — adds `subdivision_name_ar, neighborhood_id, region_id` and time-series.

**`neighborhoods-centroids`** (Point) — now only `neighborh_aname, province_id`.

**`provinces`** (Polygon) — NEW: `province_aname, province_enname, region_id, province_code`.

**`dimensions`** (13773, Point) — NEW: `parcel_objectid, length_m, province_id, azimuth`
(per-edge parcel dimensions / setbacks).

**`streets`** (290, LineString) — NEW: `width, name_ar, name_en`.

**`metro_lines`** (LineString) — `track_name, track_color, track_length`.

**`bus_lines`** (LineString) — `color, type, busroute, origin, originar`.

**`metro_stations`** (Point) — `station_code, station_name, station_long, station_lat`.

**`riyadh_bus_stations`** (Point) — `station_name, station_code, station_long, station_lat`.

**`qi_population_metrics`** (Polygon) — now `grid_id, population_density, rent_apartment,
rent_villa, rent_shop, rent_office, purchasing_power, weighted_median_income_monthly,
poi_count, region_id` — **values are hex colour strings**, not raw numbers.

**`qi_stripes`** (Polygon) — now `strip_id, centroid_longitude, centroid_latitude`.

**`building_detection`** (3082, Polygon) — NEW: `class_pred, prediction_year, region_id`
(AI-detected building footprints).

**`non_saudi_ownership_zones`** (Polygon) — NEW: `id, region_id, province_id, is_show,
name_ar, name_en` (foreign-ownership / special-zone polygons).

### 2.5 Key REST payload shapes (captured)

- **`transactions` record (39 fields)**: `transactionNumber, transactionPrice, priceOfMeter,
  _priceOfMeter, transactionDate, type, propertyType, metricsType, subdivisionNo, subdivisionId,
  neighborhood, neighborhoodId, region, regionId, provinceId, provinceName, parcelId,
  parcelObjectId, parcelNo, blockNo, area, totalArea, noOfProperties, centroidX, centroidY,
  centroid, polygonData (WKT-ish GeoJSON string), geometry, landUsageGroup, landUseGroup,
  landUseaDetailed, sellingType, transactionSource, isLowValueTransaction, orignalTransactionNum,
  propertyNumber, projectName, parcelImageURL, details`. The top-level `data` object also
  carries `lastExecutionDate`, `lastExecutionPrice`.
- **`buildingRules` (16 fields)**: `id, zoningId, zoningColor, zoningGroup, landuse, description,
  name, coloring, coloringDescription, maxBuildingCoefficient, maxBuildingHeight,
  maxParcelCoverage, maxRuleDepth, mainStreetsSetback, secondaryStreetsSetback, sideRearSetback`.
- **`priceOfMeter`**: `data[].{parcelObjId, neighborhoodId, from, to, groupingType,
  neighborhoodMetrics[], parcelMetrics[]}` where each metric = `{neighborhoodId, month, year,
  metricsType, avaragePriceOfMeter}` (API misspells "average").
- **`landMetrics/list`**: `data[].{neighborhoodId, neighborhoodName, provinceId, provinceName,
  totalMetricData{totalCount, totalPrice, median, *GrowthIndicator, *GrowthValue}, landUseGroup[]
  {landUseGroup, totalCount, totalPrice, median, lastExecutionPrice{transactionDate, priceOfMeter}}}`.

---

## 3. Forensic audit of the existing implementation

Pipeline traced end-to-end: discovery (`discovery/tile_discovery.py`, `tile_urls` queue) →
request (`downloader/async_tile_downloader.py`, `run_db_geometric.fetch_many`) → decode
(`decoder/mvt_decoder.py`) → validate/stitch (`geometry/`) → schema-filter
(`SCHEMA_MAP` in `persistence/postgis_persister.py`) → persist (`PostGISPersister`,
`models.py`, Alembic) → enrichment (`enrichment/api_client.py`, `enrichment_persister.py`,
`strategies.py`).

Classification per live capability:

| Capability | Status | Evidence |
|---|---|---|
| Tile discovery / `tile_urls` queue | **Fully captured** — still valid; URL shape `maps/{region}/{z}/{x}/{y}.vector.pbf` unchanged | `gl-styles/ksa.json` sources match `config.tile_base_url`; live tiles 200 |
| Parcels geometry + core attributes | **Fully captured** | 16 core parcel fields in `SCHEMA_MAP['parcels']` match tile |
| Parcels **inline market time-series** (16 fields) + `zoning_group` | **Available from source but not captured** | tile has `transaction_price_1w/1m/6m/12m`, `price_of_meter_*`, `transactions_count_*`, `transaction_date_*`, `zoning_group`; none in `SCHEMA_MAP` → filtered out at `pipeline_orchestrator.py:298` / `run_db_geometric.py:90` |
| Parcels `neighborhood_ar`, `municipality_ar` | **Captured but discarded / mis-mapped** | tile field `neighborhaname`→`neighborhood_ar` exists but `neighborhood_ar` not in `SCHEMA_MAP['parcels']`; `municipality_aname` has no `ARABIC_COLUMN_MAP` entry so `municipality_ar` stays NULL |
| parcels-centroids market data | **Partially captured** | only `transaction_date/price/price_of_meter` kept; time-series + `transactions_count` dropped |
| neighborhoods / subdivisions market data | **Partially captured** | time-series, `zoning_group`, `subdivision_name_ar`, `neighborhood_id`, `region_id` dropped |
| `bus_lines` | **No longer compatible — ZERO fields captured** | tile fields `color,type,busroute,origin,originar`; `SCHEMA_MAP['bus_lines']` expects `route_name,route_color,route_length,route_type,route_id`; `models.BusLines` has yet a third set (`busroute,route_name,route_type`). Nothing matches → only geometry+null id stored |
| `metro_stations` / `riyadh_bus_stations` | **Partially captured / mis-mapped** | tile has `station_long,station_lat`; schema expects `location,line_id/route_id` → those columns NULL |
| `qi_population_metrics` | **Captured but incorrectly interpreted** | schema expects a numeric `population`; tile now emits 9 colour-coded metric fields (`population_density`, `rent_*`, `purchasing_power`, `weighted_median_income_monthly`, `poi_count`). Only `grid_id` survives; `population` always NULL |
| `qi_stripes` | **No longer compatible / likely obsolete** | schema expects `stripe_value,stripe_type`; tile has `centroid_longitude,centroid_latitude`; layer absent from `gl-styles` (not rendered) |
| `dimensions` layer | **Available from source but not captured** | present in `id_column_per_layer` but absent from `layers_to_process`, `table_name_mapping`, `SCHEMA_MAP`, `models` — 13773 features/tile dropped |
| `streets`, `provinces`(tile), `building_detection`, `non_saudi_ownership_zones`, `parcels-base` | **Available from source but not captured** | new tile layers, no schema/model/table |
| Enrichment: transactions | **Partially captured** | only `transaction_id, transaction_price, price_of_meter, transaction_date, area` + `raw_data`; drops `type/propertyType, metricsType, landUseGroup, sellingType, transactionSource, totalArea, subdivisionId, neighborhoodId, polygonData(geometry)` from queryable columns |
| Enrichment: building rules | **Captured but silently reduced** | `enrichment_persister.py:53` dedupes to **one rule per parcel** (`{parcel_objectid: rule}`) despite composite PK `(parcel_objectid, building_rule_id)` — extra rules dropped |
| Enrichment: price metrics `neighborhood_id` | **Captured but discarded** | `api_client.py:244-266` never sets `neighborhood_id` though every metric object contains `neighborhoodId`; column left NULL |
| Enrichment upserts | **Captured but never refreshed** | all conflict handling is `ON CONFLICT DO NOTHING` (`enrichment_persister.py`), so changed transaction/rule/metric values never update on re-run |
| `regions` endpoint richness | **Partially captured** | `sync_provinces.py` reads a subset; `mapKey`, `metricsUrl`, `defaultTransactionsDateRange`, per-region bounds not persisted |
| Provenance (source tile z/x/y, fetch time, per-feature) | **Missing** | no per-row source coordinates or fetch timestamp; `geometry_hash` column defined but never computed in Stage-1 |
| `landMetrics` neighbourhood market intelligence | **Available from source but not captured** | `enhanced_province_discovery.py` fetches `landMetrics` but no persister consumes it |
| Auth / API-key / adaptive rate-limit (docs claim) | **Redundant / aspirational** | `docs/brownfield-architecture.md` claims API-key auth + adaptive rate limiting; code sends no key and has no enrichment rate limiter |

---

## 4. Gap analysis (evidence-indexed)

Precise per-layer field comparison (live tile field, snake_cased + Arabic-mapped, vs
`SCHEMA_MAP`) is reproduced in §2.4. The material gaps, ranked:

1. **Parcels inline market time-series (16 fields) + `zoning_group` are dropped.** This is
   the single biggest miss: the tile now delivers, for free, the same signal the enrichment
   pipeline pays per-parcel API calls to approximate. Evidence: decoded tile vs `SCHEMA_MAP['parcels']`.
2. **`bus_lines` captures zero attributes** — three-way name mismatch (tile vs `SCHEMA_MAP` vs `models`).
3. **`qi_population_metrics` semantics changed** — `population` column stays NULL; 9 new metric fields dropped.
4. **Five new tile layers unmodelled**: `dimensions` (13773/tile), `building_detection` (3082/tile),
   `streets`, `provinces`, `non_saudi_ownership_zones`; plus `parcels-base` duplicate.
5. **Transaction enrichment discards queryable market attributes** (type, land-use, selling
   type, source, areas, subdivision/neighbourhood ids, transaction geometry).
6. **Building-rules dedup bug** collapses multiple rules per parcel to one.
7. **Price-metrics `neighborhood_id` never persisted.**
8. **Mis-mapped Arabic fields** (`municipality_ar`, parcels `neighborhood_ar`).
9. **No per-feature provenance** (source tile, fetch time) and `geometry_hash` never computed.
10. **New high-value endpoints unused**: consolidated `parcel/{id}`, `landMetrics/list`
    (province-wide neighbourhood market data), `landZoningGroups`, `transactionsAsMapboxGeojson`.
11. **`ON CONFLICT DO NOTHING`** everywhere in enrichment → no refresh of changed values.
12. **gzip fragility** in any non-aiohttp read path.

---

## 5. Architectural & platform improvements (recommended)

Prefer general ingestion strengthening over more one-off Suhail hacks:

- **Single source-of-truth layer schema.** `SCHEMA_MAP` (persister), `models.py`,
  `id_column_per_layer`/`aggregation_rules`/`table_name_mapping` (config) and the migrations
  have drifted (e.g. `bus_lines` differs in all three). Collapse to one declarative
  per-layer spec (fields, types, pk, arabic map, geometry type) that generates the schema
  map, the aggregation columns and the DDL, so drift is impossible.
- **Schema-drift detection.** A CI/ops check that decodes a live sample tile and diffs its
  field set against the declared spec; fail/alert on unknown or missing fields. Would have
  caught all of §4 automatically.
- **Raw capture / replay + contract tests.** Persist a small set of real gzipped tiles and
  REST payloads as fixtures (done — `tests/fixtures/suhail_live_2026_07/`) and run the
  decoders/parsers against them in CI. There were previously **no** fixture-replay tests for
  the API client or decoder field mapping.
- **Provenance & lineage.** Add per-feature `source_tile_z/x/y`, `source_region`, `fetched_at`,
  and compute `geometry_hash`, so a row can be traced to the tile and run that produced it and
  change-detection becomes deterministic.
- **Direct structured requests over UI assumptions.** The consolidated `parcel/{id}` and the
  `landMetrics/list` pagination let us pull neighbourhood market intelligence province-wide
  without per-parcel fan-out; prefer these to the sparse per-parcel `transactions`/`buildingRules`.
- **Idempotent upserts.** Replace enrichment `DO NOTHING` with `DO UPDATE` (or a
  content-hash guard) so re-runs refresh changed values; today they cannot.
- **Consistent transport policy.** Unify retry/backoff/timeout across the three enrichment
  fetchers (transactions uses decorator backoff+jitter; rules/metrics use a hand-rolled fixed
  1s loop with no timeout), add explicit 429 handling, and make gzip handling explicit.
- **Dead code / obsolete paths.** `run_db_geometric_fixed.py` duplicates `run_db_geometric.py`;
  `qi_stripes` is no longer in the live style; `parcels-base` is a duplicate of `parcels`.
  Decide keep/drop deliberately.

---

## 6. Implemented in this pass

Scope chosen by **evidence strength × value ÷ risk**. All changes are additive or
correctness fixes; nothing removes existing behaviour.

### Stage 1 (geometric)
- **Parcels inline market time-series captured** — `SCHEMA_MAP['parcels']`, aggregation
  rules, `Parcel` model and migration now include `transaction_price_{1w,1m,6m,12m}`,
  `price_of_meter_{…}`, `transactions_count_{…}`, `transaction_date_{…}`, plus `zoning_group`
  and `neighborhood_ar`. Same time-series added to `parcels-centroids`, `neighborhoods`,
  `subdivisions` (+ `subdivision_name_ar`, `neighborhood_id`, `region_id`).
- **`municipality_ar` mapping fixed** — added `municipality_aname → municipality_ar` to
  `ARABIC_COLUMN_MAP` (was always NULL).
- **Broken layers remapped** — `bus_lines` (native `busroute/color/type/origin/originar`,
  was capturing zero attributes), `metro_stations` / `riyadh_bus_stations`
  (`station_long/station_lat`), `qi_population_metrics` (reshaped colour-coded metric
  fields + `region_id`), `qi_stripes` (`centroid_longitude/latitude`).
- **New layer wired in** — `non_saudi_ownership_zones` (unique `id` PK → clean upsert):
  `layers_to_process`, `table_name_mapping`, `id_column_per_layer`, `SCHEMA_MAP`,
  `NonSaudiOwnershipZones` model, new table in the migration.
- **New keyless layers wired in with two accumulate write modes** (added after the first
  pass — these previously could not be persisted across a multi-tile province run because the
  keyless branch used per-batch `if_exists="replace"`, keeping only the last batch):
  - **`dimensions`** (per-parcel edge measurements: `length_m`, `azimuth`; ~4–6 rows/parcel) →
    **tile-scoped delete+append** (`TILE_SCOPED_LAYERS`, `PostGISPersister.write_tile_scoped`).
    A `source_tile` provenance column records the originating tile; each batch deletes exactly
    its own tiles' rows then appends, so multi-tile runs accumulate and reruns are idempotent.
    Deliberately **not** keyed on `parcel_objectid` (that would collapse every parcel to one edge).
  - **`building_detection`** (AI footprints, year-stamped) → **deterministic synthetic key**
    (`SYNTHETIC_PK_CONFIG`, `compute_synthetic_pk`: SHA1 of `region_id|class_pred|prediction_year`
    + geometry → `bd_id`), reusing the existing upsert path. Idempotent, versions by prediction
    year, and dedupes tile-overlap duplicates for free.
  - Both stamped in the shared `decode_and_validate_tile` choke point, so both persist paths
    inherit them. Migration `d8b1e6f42a90` creates the two tables (indexed on `source_tile`).
- **Still deferred** — `streets` (keyless lines, same pattern available if wanted). Tile
  `provinces` intentionally omitted (collides with the metadata table).

### Stage 2 (enrichment)
- **Transactions enriched** — promoted `type, propertyType, metricsType, landUseGroup,
  landUseaDetailed, sellingType, transactionSource, totalArea, subdivisionId, neighborhoodId,
  isLowValueTransaction` from `raw_data` into queryable columns (model + migration + parser +
  persister).
- **Building-rules dedup bug fixed** — persister now keys on `(parcel_objectid,
  building_rule_id)`, not `parcel_objectid` alone (previously discarded all but one rule).
- **Price-metrics `neighborhood_id` now captured** (was always NULL), with neighborhood
  **stub insertion** added to `fast_store_batch_data` so populating the FK column cannot abort
  a batch when the neighborhood row is absent.
- **Transport/parse separation** — the three parsers are now pure functions
  (`parse_transactions_payload`, `parse_building_rules_payload`, `parse_price_metrics_payload`)
  callable without HTTP, enabling fixture-backed contract tests.

### Tests, fixtures, migration
- Live payloads committed as regression fixtures under
  `tests/fixtures/suhail_live_2026_07/` (tiles + API JSON).
- `tests/unit/test_live_tile_schema.py` (decode real tiles → assert new fields survive the
  schema filter) and `tests/unit/test_enrichment_parsers_contract.py` (parse real API
  payloads → assert promoted fields, multi-rule survival, neighborhood_id). 11 new tests;
  full unit suite 88 passed.
- Alembic migration `c7f4a9d21b60_suhail_2026_source_expansion` (idempotent `ADD COLUMN IF
  NOT EXISTS`, new table, reversible — verified downgrade/upgrade round-trip).

### Deliberately not done (recommended next, with rationale)
- New endpoints as ingest sources (`landMetrics/list` province-wide neighbourhood market
  intelligence; consolidated `parcel/{id}`; `landZoningGroups` lookup) — high value, but new
  persisters/tables beyond this pass's tested scope.
- `streets` — keyless line layer, still deferred (the tile-scoped write mode built for
  `dimensions` applies directly if wanted). `dimensions` and `building_detection` are now done
  (see §6 above).
- Replace enrichment `ON CONFLICT DO NOTHING` with `DO UPDATE` for true refresh-on-rerun.
- Per-feature provenance (`source_tile_z/x/y`, `fetched_at`) and `geometry_hash` computation.
- Collapse the drifting layer-schema definitions (`SCHEMA_MAP` / models / config) into one
  declarative spec + a schema-drift CI check.

## 7. End-to-end validation results (live, 2026-07-15)

Validated against the **live** `tiles.suhail.ai` / `api2.suhail.ai` and the local
`suhail_pipeline` PostgreSQL 18 database, through the real pipeline modules.

**Stage 1** (`fetch_many → decode_and_validate_tile → _apply_arabic_and_columns →
PostGISPersister.write` upsert into schema-identical tables):
- 4/4 live tiles fetched and decoded (7,542 parcels).
- New columns populated: `zoning_group` 7,438; `neighborhood_ar` 7,541; `municipality_ar`
  7,542; `transaction_price_12m` 7,542; `transactions_count_12m>0` 71; `transaction_date_12m` 71.
- **Idempotent**: rerun left row count and values unchanged (7,542 → 7,542).
- **Source-vs-persisted cross-check**: parcel `9941681` persisted
  `price_of_meter=6393.18`, `transaction_date_12m=2026-05-19`, `transactions_count_12m=6`,
  `zoning_group=سكني`, `neighborhood_ar=الروضة` — matches the live `/transactions` API
  (`lastExecutionPrice=6393.0`, 6 transactions).
- Fixed layers captured live: `bus_lines` 24 rows with `busroute` (was zero),
  `metro_stations` 3 with coordinates, `qi_population_metrics` 87 with metric fields,
  `non_saudi_ownership_zones` 1 with `name_en`.

**Stage 2** (live `SuhailAPIClient` → real `fast_store_batch_data`):
- Live fetch for parcel `9941681`: 6 transactions, 1 building rule, 83 metrics.
- Persisted transaction row carried every promoted column
  (`transaction_type=مبنى سكني, metrics_type=فلل, land_use_group=سكني, selling_type=فردي,
  transaction_source=RER, total_area=187.7, subdivision_id=1023186, neighborhood_id=1000417,
  is_low_value_transaction=False`).
- All 80 persisted metrics carried `neighborhood_id` (previously always NULL); neighborhood
  stub insertion prevented an FK-violation batch abort.

**New keyless layers** (live tiles → real persister write modes → dedicated tables):
- `dimensions` (tile-scoped): batch A 18,447 rows → batch B **accumulated** to 30,869
  (= A + B; the old `replace` would have kept only B's 12,422). Reprocessing batch A left the
  count unchanged (idempotent). A parcel retained all 23 of its edges — not collapsed.
- `building_detection` (synthetic key): batch A 4,286 → A∪B 7,541 distinct predictions,
  idempotent on rerun; rows carry `bd_id`, `class_pred`, `prediction_year`, `source_tile`.

All temporary validation tables/rows were cleaned up; the database was left in its prior
state (enrichment tables empty, no seeded rows). Migrations `c7f4a9d21b60` and `d8b1e6f42a90`
both round-trip (downgrade/upgrade verified). Full unit suite: **93 passed**.
