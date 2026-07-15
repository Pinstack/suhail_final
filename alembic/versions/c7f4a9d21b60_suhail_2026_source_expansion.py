"""Suhail 2026 source expansion: inline market time-series, reshaped layers, new tables

Adds the data the redesigned Suhail tiles / API now expose (see
docs/SUHAIL_SOURCE_AUDIT_2026-07.md):

* parcels / parcels_centroids / neighborhoods / subdivisions: inline market
  time-series (1w/1m/6m/12m transaction price, price-of-meter, transaction count
  and date) plus zoning_group and a few identifiers.
* metro_stations / riyadh_bus_stations: station_long / station_lat.
* qi_population_metrics: reshaped metric fields (colour-coded) + region_id.
* qi_stripes: centroid_longitude / centroid_latitude.
* bus_lines: native tile fields (busroute/color/type/origin/originar).
* non_saudi_ownership_zones: new table (unique id PK).
* transactions: richer queryable columns (type, property/land-use, selling type,
  source, areas, subdivision/neighborhood ids).

All column adds are IF NOT EXISTS and additive; downgrade drops the added columns
and the new table. Existing data is preserved.

Revision ID: c7f4a9d21b60
Revises: b3e8a1c0d4f2
Create Date: 2026-07-15
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7f4a9d21b60"
down_revision = "b3e8a1c0d4f2"
branch_labels = None
depends_on = None


# (window suffix) time-series columns shared by parcels/neighborhoods/subdivisions/centroids
_TS = []
for _w in ("1w", "1m", "6m", "12m"):
    _TS.append((f"transaction_price_{_w}", "DOUBLE PRECISION"))
    _TS.append((f"price_of_meter_{_w}", "DOUBLE PRECISION"))
    _TS.append((f"transactions_count_{_w}", "BIGINT"))
    _TS.append((f"transaction_date_{_w}", "TIMESTAMP"))


def _add(table: str, columns):
    for name, ddl_type in columns:
        op.execute(
            f'ALTER TABLE public."{table}" ADD COLUMN IF NOT EXISTS "{name}" {ddl_type}'
        )


def _drop(table: str, columns):
    for name, _ in columns:
        op.execute(
            f'ALTER TABLE public."{table}" DROP COLUMN IF EXISTS "{name}"'
        )


_PARCELS_COLS = [("zoning_group", "TEXT")] + _TS
_CENTROIDS_COLS = [("transactions_count", "BIGINT")] + _TS
_NEIGHBORHOODS_COLS = [
    ("zoning_group", "TEXT"),
    ("neighborhood_name", "TEXT"),
] + _TS
_SUBDIVISIONS_COLS = [
    ("subdivision_name_ar", "TEXT"),
    ("neighborhood_id", "BIGINT"),
    ("region_id", "BIGINT"),
] + _TS
_METRO_STATION_COLS = [("station_long", "DOUBLE PRECISION"), ("station_lat", "DOUBLE PRECISION")]
_BUS_STATION_COLS = [("station_long", "DOUBLE PRECISION"), ("station_lat", "DOUBLE PRECISION")]
_QI_POP_COLS = [
    ("region_id", "BIGINT"),
    ("population_density", "TEXT"),
    ("rent_apartment", "TEXT"),
    ("rent_villa", "TEXT"),
    ("rent_shop", "TEXT"),
    ("rent_office", "TEXT"),
    ("purchasing_power", "TEXT"),
    ("weighted_median_income_monthly", "TEXT"),
    ("poi_count", "TEXT"),
]
_QI_STRIPE_COLS = [("centroid_longitude", "DOUBLE PRECISION"), ("centroid_latitude", "DOUBLE PRECISION")]
_BUS_LINE_COLS = [
    ("busroute", "TEXT"),
    ("color", "TEXT"),
    ("type", "TEXT"),
    ("origin", "TEXT"),
    ("originar", "TEXT"),
]
_TRANSACTION_COLS = [
    ("transaction_type", "TEXT"),
    ("property_type", "TEXT"),
    ("metrics_type", "TEXT"),
    ("land_use_group", "TEXT"),
    ("land_use_detailed", "TEXT"),
    ("selling_type", "TEXT"),
    ("transaction_source", "TEXT"),
    ("total_area", "DOUBLE PRECISION"),
    ("subdivision_id", "BIGINT"),
    ("neighborhood_id", "BIGINT"),
    ("is_low_value_transaction", "BOOLEAN"),
]


def upgrade() -> None:
    _add("parcels", _PARCELS_COLS)
    _add("parcels_centroids", _CENTROIDS_COLS)
    _add("neighborhoods", _NEIGHBORHOODS_COLS)
    _add("subdivisions", _SUBDIVISIONS_COLS)
    _add("metro_stations", _METRO_STATION_COLS)
    _add("riyadh_bus_stations", _BUS_STATION_COLS)
    _add("qi_population_metrics", _QI_POP_COLS)
    _add("qi_stripes", _QI_STRIPE_COLS)
    _add("bus_lines", _BUS_LINE_COLS)
    _add("transactions", _TRANSACTION_COLS)

    # New layer: non_saudi_ownership_zones (unique id PK, clean upsert).
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.non_saudi_ownership_zones (
            id BIGINT PRIMARY KEY,
            geometry geometry(GEOMETRY, 4326),
            name_ar TEXT,
            name_en TEXT,
            is_show BOOLEAN,
            region_id BIGINT,
            province_id BIGINT
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_non_saudi_ownership_zones_geom "
        "ON public.non_saudi_ownership_zones USING GIST (geometry)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.non_saudi_ownership_zones CASCADE")
    _drop("transactions", _TRANSACTION_COLS)
    _drop("bus_lines", _BUS_LINE_COLS)
    _drop("qi_stripes", _QI_STRIPE_COLS)
    _drop("qi_population_metrics", _QI_POP_COLS)
    _drop("riyadh_bus_stations", _BUS_STATION_COLS)
    _drop("metro_stations", _METRO_STATION_COLS)
    _drop("subdivisions", _SUBDIVISIONS_COLS)
    _drop("neighborhoods", _NEIGHBORHOODS_COLS)
    _drop("parcels_centroids", _CENTROIDS_COLS)
    _drop("parcels", _PARCELS_COLS)
