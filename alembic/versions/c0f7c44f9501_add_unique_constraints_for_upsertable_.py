"""
Add unique constraints to upsertable tables for robust pipeline upsert/replace logic

Revision ID: c0f7c44f9501
Revises: 4916f60e3080
Create Date: 2025-07-04 23:32:43.407597

See WHAT_TO_DO_NEXT_PIPELINE_TABLES.md for rationale and table list.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0f7c44f9501'
down_revision: Union[str, Sequence[str], None] = '4916f60e3080'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add unique indexes for upsertable tables (see WHAT_TO_DO_NEXT_PIPELINE_TABLES.md)
    op.create_index('uq_parcels_centroids_parcel_no', 'parcels_centroids', ['parcel_no'], unique=True, postgresql_where=sa.text('"parcel_no" IS NOT NULL'))
    # Skipping neighborhoods_centroids.neighborhood_id: column does not exist
    op.create_index('uq_metro_stations_station_code', 'metro_stations', ['station_code'], unique=True, postgresql_where=sa.text('"station_code" IS NOT NULL'))
    op.create_index('uq_riyadh_bus_stations_station_code', 'riyadh_bus_stations', ['station_code'], unique=True, postgresql_where=sa.text('"station_code" IS NOT NULL'))
    op.create_index('uq_qi_population_metrics_grid_id', 'qi_population_metrics', ['grid_id'], unique=True, postgresql_where=sa.text('"grid_id" IS NOT NULL'))
    op.create_index('uq_qi_stripes_strip_id', 'qi_stripes', ['strip_id'], unique=True, postgresql_where=sa.text('"strip_id" IS NOT NULL'))
    # ...add for any other upsertable tables as needed...


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_parcels_centroids_parcel_no', table_name='parcels_centroids')
    # Skipped neighborhoods_centroids.neighborhood_id: column does not exist
    op.drop_index('uq_metro_stations_station_code', table_name='metro_stations')
    op.drop_index('uq_riyadh_bus_stations_station_code', table_name='riyadh_bus_stations')
    op.drop_index('uq_qi_population_metrics_grid_id', table_name='qi_population_metrics')
    op.drop_index('uq_qi_stripes_strip_id', table_name='qi_stripes')
    # ...
