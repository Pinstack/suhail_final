"""relax qi_stripes and qi_population_metrics geometry to Geometry

MVT data for these layers can be MultiPolygon while the baseline schema used
POLYGON only, causing upsert failures during db-geometric.

Revision ID: b3e8a1c0d4f2
Revises: 1ac2e2b2c8d2
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b3e8a1c0d4f2"
down_revision: Union[str, Sequence[str], None] = "1ac2e2b2c8d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE qi_stripes
        ALTER COLUMN geometry TYPE geometry(Geometry, 4326)
        USING geometry::geometry(Geometry, 4326);
        """
    )
    op.execute(
        """
        ALTER TABLE qi_population_metrics
        ALTER COLUMN geometry TYPE geometry(Geometry, 4326)
        USING geometry::geometry(Geometry, 4326);
        """
    )


def downgrade() -> None:
    # Reverting to strict POLYGON is lossy (MultiPolygon → first polygon only).
    op.execute(
        """
        ALTER TABLE qi_stripes
        ALTER COLUMN geometry TYPE geometry(Polygon, 4326)
        USING (
            CASE
                WHEN GeometryType(geometry) = 'POLYGON' THEN geometry::geometry(Polygon, 4326)
                WHEN GeometryType(geometry) = 'MULTIPOLYGON'
                    THEN ST_GeometryN(geometry, 1)::geometry(Polygon, 4326)
                ELSE ST_Buffer(geometry, 0)::geometry(Polygon, 4326)
            END
        );
        """
    )
    op.execute(
        """
        ALTER TABLE qi_population_metrics
        ALTER COLUMN geometry TYPE geometry(Polygon, 4326)
        USING (
            CASE
                WHEN GeometryType(geometry) = 'POLYGON' THEN geometry::geometry(Polygon, 4326)
                WHEN GeometryType(geometry) = 'MULTIPOLYGON'
                    THEN ST_GeometryN(geometry, 1)::geometry(Polygon, 4326)
                ELSE ST_Buffer(geometry, 0)::geometry(Polygon, 4326)
            END
        );
        """
    )
