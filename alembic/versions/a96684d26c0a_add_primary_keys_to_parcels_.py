"""Add primary keys to parcels, neighborhoods, and subdivisions

Revision ID: a96684d26c0a
Revises: be3ab240b473
Create Date: 2025-07-01 05:11:44.359311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'a96684d26c0a'
down_revision: Union[str, Sequence[str], None] = 'be3ab240b473'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- Alter Foreign Key Columns to BIGINT ---
    op.alter_column('building_rules', 'parcel_objectid', existing_type=sa.VARCHAR(), type_=sa.BigInteger, postgresql_using='parcel_objectid::bigint')
    op.alter_column('transactions', 'parcel_objectid', existing_type=sa.VARCHAR(), type_=sa.BigInteger, postgresql_using='parcel_objectid::bigint')
    op.alter_column('parcel_price_metrics', 'parcel_objectid', existing_type=sa.VARCHAR(), type_=sa.BigInteger, postgresql_using='parcel_objectid::bigint')
    op.alter_column('parcel_price_metrics', 'neighborhood_id', existing_type=sa.BIGINT(), type_=sa.BigInteger, postgresql_using='neighborhood_id::bigint')
    op.alter_column('parcels', 'neighborhood_id', existing_type=sa.FLOAT(), type_=sa.BigInteger, postgresql_using='neighborhood_id::bigint')
    
    # --- Add primary keys ---
    op.alter_column('parcels', 'parcel_objectid', existing_type=sa.TEXT(), type_=sa.BigInteger(), nullable=False, postgresql_using='parcel_objectid::bigint')
    op.create_primary_key(op.f('parcels_pkey'), 'parcels', ['parcel_objectid'])

    op.alter_column('neighborhoods', 'neighborhood_id', existing_type=sa.DOUBLE_PRECISION(), type_=sa.BigInteger(), nullable=False, postgresql_using='neighborhood_id::bigint')
    op.create_primary_key(op.f('neighborhoods_pkey'), 'neighborhoods', ['neighborhood_id'])

    op.alter_column('subdivisions', 'subdivision_id', existing_type=sa.BIGINT(), type_=sa.BigInteger(), nullable=False)
    op.create_primary_key(op.f('subdivisions_pkey'), 'subdivisions', ['subdivision_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # --- Revert FK Column Type Changes ---
    op.alter_column('parcels', 'neighborhood_id', existing_type=sa.BigInteger, type_=sa.FLOAT())
    op.alter_column('parcel_price_metrics', 'neighborhood_id', existing_type=sa.BigInteger, type_=sa.BIGINT())
    op.alter_column('parcel_price_metrics', 'parcel_objectid', existing_type=sa.BigInteger, type_=sa.VARCHAR())
    op.alter_column('transactions', 'parcel_objectid', existing_type=sa.BigInteger, type_=sa.VARCHAR())
    op.alter_column('building_rules', 'parcel_objectid', existing_type=sa.BigInteger, type_=sa.VARCHAR())

    # --- Downgrade primary keys ---
    op.drop_constraint(op.f('subdivisions_pkey'), 'subdivisions', type_='primary')
    op.alter_column('subdivisions', 'subdivision_id', existing_type=sa.BigInteger(), type_=sa.BIGINT(), nullable=True)

    op.drop_constraint(op.f('neighborhoods_pkey'), 'neighborhoods', type_='primary')
    op.alter_column('neighborhoods', 'neighborhood_id', existing_type=sa.BigInteger(), type_=sa.DOUBLE_PRECISION(), nullable=True)

    op.drop_constraint(op.f('parcels_pkey'), 'parcels', type_='primary')
    op.alter_column('parcels', 'parcel_objectid', existing_type=sa.BigInteger(), type_=sa.TEXT(), nullable=True)
