"""baseline after cleanup (full schema)

Revision ID: e1e813183ae0
Revises: bb30239de345
Create Date: 2025-07-06 14:01:26.461652

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'e1e813183ae0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bus_lines',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='MULTILINESTRING', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('busroute', sa.String(), nullable=True),
    sa.Column('route_name', sa.String(), nullable=True),
    sa.Column('route_type', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('land_use_groups',
    sa.Column('landuse_group', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('landuse_group')
    )
    op.create_table('metro_lines',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='MULTILINESTRING', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('track_color', sa.String(), nullable=True),
    sa.Column('track_length', sa.Float(), nullable=True),
    sa.Column('track_name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('metro_stations',
    sa.Column('station_code', sa.String(), nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('station_name', sa.String(), nullable=True),
    sa.Column('line', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('station_code')
    )
    op.create_table('neighborhoods_centroids',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('neighborh_aname', sa.String(), nullable=True),
    sa.Column('province_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('parcels_base',
    sa.Column('parcel_id', sa.String(), nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.PrimaryKeyConstraint('parcel_id')
    )
    op.create_table('parcels_centroids',
    sa.Column('parcel_no', sa.String(), nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('transaction_date', sa.DateTime(), nullable=True),
    sa.Column('transaction_price', sa.Float(), nullable=True),
    sa.Column('price_of_meter', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('parcel_no')
    )
    op.create_table('provinces',
    sa.Column('province_id', sa.BigInteger(), nullable=False),
    sa.Column('province_name', sa.String(), nullable=True),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.PrimaryKeyConstraint('province_id')
    )
    op.create_table('qi_population_metrics',
    sa.Column('grid_id', sa.String(), nullable=False),
    sa.Column('population', sa.Integer(), nullable=True),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.PrimaryKeyConstraint('grid_id')
    )
    op.create_table('qi_stripes',
    sa.Column('strip_id', sa.String(), nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('value', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('strip_id')
    )
    op.create_table('riyadh_bus_stations',
    sa.Column('station_code', sa.String(), nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('station_name', sa.String(), nullable=True),
    sa.Column('route', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('station_code')
    )
    op.create_table('zoning_rules',
    sa.Column('ruleid', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('ruleid')
    )
    op.create_table('neighborhoods',
    sa.Column('neighborhood_id', sa.BigInteger(), nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('neighborhood_name', sa.String(), nullable=True),
    sa.Column('neighborhood_ar', sa.String(), nullable=True),
    sa.Column('region_id', sa.BigInteger(), nullable=True),
    sa.Column('province_id', sa.BigInteger(), nullable=True),
    sa.Column('price_of_meter', sa.Float(), nullable=True),
    sa.Column('shape_area', sa.Float(), nullable=True),
    sa.Column('transaction_price', sa.Float(), nullable=True),
    sa.Column('zoning_id', sa.BigInteger(), nullable=True),
    sa.Column('zoning_color', sa.String(), nullable=True),
    sa.Column('geometry_hash', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['province_id'], ['provinces.province_id'], ),
    sa.PrimaryKeyConstraint('neighborhood_id')
    )
    op.create_table('subdivisions',
    sa.Column('subdivision_id', sa.BigInteger(), nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('subdivision_no', sa.String(), nullable=True),
    sa.Column('shape_area', sa.Float(), nullable=True),
    sa.Column('transaction_price', sa.Float(), nullable=True),
    sa.Column('price_of_meter', sa.Float(), nullable=True),
    sa.Column('zoning_id', sa.BigInteger(), nullable=True),
    sa.Column('zoning_color', sa.String(), nullable=True),
    sa.Column('province_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['province_id'], ['provinces.province_id'], ),
    sa.PrimaryKeyConstraint('subdivision_id')
    )
    op.create_table('parcels',
    sa.Column('parcel_objectid', sa.BigInteger(), nullable=False),
    sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4326, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
    sa.Column('landuseagroup', sa.String(), nullable=True),
    sa.Column('landuseadetailed', sa.String(), nullable=True),
    sa.Column('subdivision_no', sa.String(), nullable=True),
    sa.Column('transaction_price', sa.Float(), nullable=True),
    sa.Column('zoning_id', sa.BigInteger(), nullable=True),
    sa.Column('neighborhood_id', sa.BigInteger(), nullable=True),
    sa.Column('block_no', sa.String(), nullable=True),
    sa.Column('neighborhood_ar', sa.String(), nullable=True),
    sa.Column('subdivision_id', sa.BigInteger(), nullable=True),
    sa.Column('price_of_meter', sa.Float(), nullable=True),
    sa.Column('shape_area', sa.Float(), nullable=True),
    sa.Column('zoning_color', sa.String(), nullable=True),
    sa.Column('ruleid', sa.String(), nullable=True),
    sa.Column('province_id', sa.BigInteger(), nullable=True),
    sa.Column('municipality_ar', sa.String(), nullable=True),
    sa.Column('parcel_id', sa.BigInteger(), nullable=True),
    sa.Column('parcel_no', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('geometry_hash', sa.String(), nullable=True),
    sa.Column('enriched_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('region_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['neighborhood_id'], ['neighborhoods.neighborhood_id'], ),
    sa.ForeignKeyConstraint(['province_id'], ['provinces.province_id'], ),
    sa.ForeignKeyConstraint(['ruleid'], ['zoning_rules.ruleid'], ),
    sa.PrimaryKeyConstraint('parcel_objectid')
    )
    op.create_table('building_rules',
    sa.Column('parcel_objectid', sa.BigInteger(), nullable=False),
    sa.Column('building_rule_id', sa.String(), nullable=False),
    sa.Column('zoning_id', sa.Integer(), nullable=True),
    sa.Column('zoning_color', sa.String(), nullable=True),
    sa.Column('zoning_group', sa.String(), nullable=True),
    sa.Column('landuse', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('coloring', sa.String(), nullable=True),
    sa.Column('coloring_description', sa.String(), nullable=True),
    sa.Column('max_building_coefficient', sa.String(), nullable=True),
    sa.Column('max_building_height', sa.String(), nullable=True),
    sa.Column('max_parcel_coverage', sa.String(), nullable=True),
    sa.Column('max_rule_depth', sa.String(), nullable=True),
    sa.Column('main_streets_setback', sa.String(), nullable=True),
    sa.Column('secondary_streets_setback', sa.String(), nullable=True),
    sa.Column('side_rear_setback', sa.String(), nullable=True),
    sa.Column('raw_data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['parcel_objectid'], ['parcels.parcel_objectid'], ),
    sa.PrimaryKeyConstraint('parcel_objectid', 'building_rule_id'),
    sa.UniqueConstraint('parcel_objectid', 'building_rule_id', name='_parcel_rule_uc')
    )
    op.create_table('parcel_price_metrics',
    sa.Column('metric_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('parcel_objectid', sa.BigInteger(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('metrics_type', sa.String(), nullable=False),
    sa.Column('average_price_of_meter', sa.Float(), nullable=True),
    sa.Column('neighborhood_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['neighborhood_id'], ['neighborhoods.neighborhood_id'], ),
    sa.ForeignKeyConstraint(['parcel_objectid'], ['parcels.parcel_objectid'], ),
    sa.PrimaryKeyConstraint('metric_id'),
    sa.UniqueConstraint('parcel_objectid', 'month', 'year', 'metrics_type', name='_parcel_metric_uc')
    )
    op.create_table('transactions',
    sa.Column('transaction_id', sa.BigInteger(), nullable=False),
    sa.Column('parcel_objectid', sa.BigInteger(), nullable=True),
    sa.Column('transaction_price', sa.Float(), nullable=True),
    sa.Column('price_of_meter', sa.Float(), nullable=True),
    sa.Column('transaction_date', sa.DateTime(), nullable=True),
    sa.Column('area', sa.Float(), nullable=True),
    sa.Column('raw_data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['parcel_objectid'], ['parcels.parcel_objectid'], ),
    sa.PrimaryKeyConstraint('transaction_id'),
    sa.UniqueConstraint('transaction_id', 'parcel_objectid', name='_transaction_parcel_uc')
    )
    # Now create all indexes after all tables using raw SQL for PostGIS compatibility
    op.execute('CREATE INDEX IF NOT EXISTS idx_bus_lines_geometry ON bus_lines USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_metro_lines_geometry ON metro_lines USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_metro_stations_geometry ON metro_stations USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_neighborhoods_centroids_geometry ON neighborhoods_centroids USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_parcels_base_geometry ON parcels_base USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_parcels_centroids_geometry ON parcels_centroids USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_provinces_geometry ON provinces USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_qi_population_metrics_geometry ON qi_population_metrics USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_qi_stripes_geometry ON qi_stripes USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_riyadh_bus_stations_geometry ON riyadh_bus_stations USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_neighborhoods_geometry ON neighborhoods USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_subdivisions_geometry ON subdivisions USING gist (geometry);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_parcels_geometry ON parcels USING gist (geometry);')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transactions')
    op.drop_table('parcel_price_metrics')
    op.drop_table('building_rules')
    op.drop_index('idx_parcels_geometry', table_name='parcels', postgresql_using='gist')
    op.drop_table('parcels')
    op.drop_index('idx_subdivisions_geometry', table_name='subdivisions', postgresql_using='gist')
    op.drop_table('subdivisions')
    op.drop_index('idx_neighborhoods_geometry', table_name='neighborhoods', postgresql_using='gist')
    op.drop_table('neighborhoods')
    op.drop_table('zoning_rules')
    op.drop_index('idx_riyadh_bus_stations_geometry', table_name='riyadh_bus_stations', postgresql_using='gist')
    op.drop_table('riyadh_bus_stations')
    op.drop_index('idx_qi_stripes_geometry', table_name='qi_stripes', postgresql_using='gist')
    op.drop_table('qi_stripes')
    op.drop_index('idx_qi_population_metrics_geometry', table_name='qi_population_metrics', postgresql_using='gist')
    op.drop_table('qi_population_metrics')
    op.drop_index('idx_provinces_geometry', table_name='provinces', postgresql_using='gist')
    op.drop_table('provinces')
    op.drop_index('idx_parcels_centroids_geometry', table_name='parcels_centroids', postgresql_using='gist')
    op.drop_table('parcels_centroids')
    op.drop_index('idx_parcels_base_geometry', table_name='parcels_base', postgresql_using='gist')
    op.drop_table('parcels_base')
    op.drop_index('idx_neighborhoods_centroids_geometry', table_name='neighborhoods_centroids', postgresql_using='gist')
    op.drop_table('neighborhoods_centroids')
    op.drop_index('idx_metro_stations_geometry', table_name='metro_stations', postgresql_using='gist')
    op.drop_table('metro_stations')
    op.drop_index('idx_metro_lines_geometry', table_name='metro_lines', postgresql_using='gist')
    op.drop_table('metro_lines')
    op.drop_table('land_use_groups')
    op.drop_index('idx_bus_lines_geometry', table_name='bus_lines', postgresql_using='gist')
    op.drop_table('bus_lines')
    # ### end Alembic commands ###
