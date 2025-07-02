"""Add foreign key constraints

Revision ID: ddee3a71a1ba
Revises: a96684d26c0a
Create Date: 2025-07-01 05:16:02.184228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'ddee3a71a1ba'
down_revision: Union[str, Sequence[str], None] = 'a96684d26c0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_foreign_key(op.f('fk_building_rules_parcel_objectid_parcels'), 'building_rules', 'parcels', ['parcel_objectid'], ['parcel_objectid'])
    op.create_foreign_key(op.f('fk_neighborhoods_province_id_provinces'), 'neighborhoods', 'provinces', ['province_id'], ['province_id'])
    op.create_foreign_key(op.f('fk_parcel_price_metrics_parcel_objectid_parcels'), 'parcel_price_metrics', 'parcels', ['parcel_objectid'], ['parcel_objectid'])
    op.create_foreign_key(op.f('fk_parcel_price_metrics_neighborhood_id_neighborhoods'), 'parcel_price_metrics', 'neighborhoods', ['neighborhood_id'], ['neighborhood_id'])
    op.create_foreign_key(op.f('fk_parcels_neighborhood_id_neighborhoods'), 'parcels', 'neighborhoods', ['neighborhood_id'], ['neighborhood_id'])
    op.create_foreign_key(op.f('fk_parcels_province_id_provinces'), 'parcels', 'provinces', ['province_id'], ['province_id'])
    op.create_foreign_key(op.f('fk_subdivisions_province_id_provinces'), 'subdivisions', 'provinces', ['province_id'], ['province_id'])
    op.create_foreign_key(op.f('fk_transactions_parcel_objectid_parcels'), 'transactions', 'parcels', ['parcel_objectid'], ['parcel_objectid'])
    op.create_foreign_key(op.f('fk_municipalities_province_id_provinces'), 'municipalities', 'provinces', ['province_id'], ['province_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('fk_municipalities_province_id_provinces'), 'municipalities', type_='foreignkey')
    op.drop_constraint(op.f('fk_transactions_parcel_objectid_parcels'), 'transactions', type_='foreignkey')
    op.drop_constraint(op.f('fk_subdivisions_province_id_provinces'), 'subdivisions', type_='foreignkey')
    op.drop_constraint(op.f('fk_parcels_province_id_provinces'), 'parcels', type_='foreignkey')
    op.drop_constraint(op.f('fk_parcels_neighborhood_id_neighborhoods'), 'parcels', type_='foreignkey')
    op.drop_constraint(op.f('fk_parcel_price_metrics_neighborhood_id_neighborhoods'), 'parcel_price_metrics', type_='foreignkey')
    op.drop_constraint(op.f('fk_parcel_price_metrics_parcel_objectid_parcels'), 'parcel_price_metrics', type_='foreignkey')
    op.drop_constraint(op.f('fk_neighborhoods_province_id_provinces'), 'neighborhoods', type_='foreignkey')
    op.drop_constraint(op.f('fk_building_rules_parcel_objectid_parcels'), 'building_rules', type_='foreignkey')
