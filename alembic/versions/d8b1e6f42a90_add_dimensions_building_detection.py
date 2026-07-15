"""Add dimensions and building_detection tile layers

- `dimensions`: per-parcel edge measurements (length_m, azimuth). Many rows per
  parcel, no natural key -> surrogate row_id + `source_tile` for the tile-scoped
  delete+append write. Indexed on source_tile so per-tile deletes stay cheap.
- `building_detection`: AI-detected building footprints/classification, year-stamped.
  Keyless in the source -> deterministic synthetic bd_id primary key for upsert.

Both are additive (new tables). See docs/SUHAIL_SOURCE_AUDIT_2026-07.md §5/§6.

Revision ID: d8b1e6f42a90
Revises: c7f4a9d21b60
Create Date: 2026-07-15
"""
from alembic import op

revision = "d8b1e6f42a90"
down_revision = "c7f4a9d21b60"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.dimensions (
            row_id BIGSERIAL PRIMARY KEY,
            parcel_objectid BIGINT,
            geometry geometry(POINT, 4326),
            length_m DOUBLE PRECISION,
            azimuth DOUBLE PRECISION,
            province_id BIGINT,
            source_tile TEXT
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_dimensions_source_tile "
        "ON public.dimensions (source_tile)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_dimensions_parcel "
        "ON public.dimensions (parcel_objectid)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_dimensions_geom "
        "ON public.dimensions USING GIST (geometry)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.building_detection (
            bd_id BIGINT PRIMARY KEY,
            geometry geometry(GEOMETRY, 4326),
            class_pred TEXT,
            prediction_year BIGINT,
            region_id BIGINT,
            source_tile TEXT
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_building_detection_geom "
        "ON public.building_detection USING GIST (geometry)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.building_detection CASCADE")
    op.execute("DROP TABLE IF EXISTS public.dimensions CASCADE")
