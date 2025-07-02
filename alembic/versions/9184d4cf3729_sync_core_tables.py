"""Sync core tables

Revision ID: 9184d4cf3729
Revises: 
Create Date: 2025-07-01 04:51:21.034904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '9184d4cf3729'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### Manually adjusted by developer ###

    # --- Schema changes for 'building_rules' ---
    op.alter_column('building_rules', 'rule_id',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.create_unique_constraint('_parcel_rule_uc', 'building_rules', ['parcel_objectid', 'rule_id'])

    # --- Schema changes for 'neighborhoods' ---
    op.add_column('neighborhoods', sa.Column('geometry_hash', sa.String(), nullable=True))
    op.alter_column('neighborhoods', 'neighborhood_id',
               existing_type=sa.BIGINT(),
               nullable=False,
               autoincrement=True)
    # Fix rename
    op.alter_column('neighborhoods', 'neighborh_aname',
               new_column_name='neighborhood_name',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=True)
    op.alter_column('neighborhoods', 'zoning_id',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.BigInteger(),
               existing_nullable=True)
    op.alter_column('neighborhoods', 'zoning_color',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=True)

    # --- Schema changes for 'parcel_price_metrics' ---
    op.add_column('parcel_price_metrics', sa.Column('neighborhood_id', sa.BigInteger(), nullable=True))
    op.alter_column('parcel_price_metrics', 'parcel_objectid',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('parcel_price_metrics', 'month',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('parcel_price_metrics', 'year',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('parcel_price_metrics', 'metrics_type',
               existing_type=sa.VARCHAR(),
               nullable=False)

    # --- Schema changes for 'parcels' ---
    # Add new audit and feature columns
    op.add_column('parcels', sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('parcels', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('parcels', sa.Column('is_active', sa.Boolean(), server_default='t', nullable=False))
    op.add_column('parcels', sa.Column('geometry_hash', sa.String(), nullable=True))
    op.add_column('parcels', sa.Column('enriched_at', sa.DateTime(timezone=True), nullable=True))

    # Fix renames and type changes
    op.alter_column('parcels', 'landuseagroup', new_column_name='landuse_agroup', existing_type=sa.TEXT(), type_=sa.String())
    op.alter_column('parcels', 'landuseadetailed', new_column_name='landuse_adetailed', existing_type=sa.TEXT(), type_=sa.String())
    op.alter_column('parcels', 'neighborhaname', new_column_name='neighborha_name', existing_type=sa.TEXT(), type_=sa.String())
    op.alter_column('parcels', 'ruleid', new_column_name='rule_id', existing_type=sa.TEXT(), type_=sa.String())

    op.alter_column('parcels', 'parcel_objectid',
               existing_type=sa.TEXT(),
               type_=sa.BigInteger(),
               nullable=False,
               autoincrement=True,
               postgresql_using='parcel_objectid::bigint')

    op.alter_column('parcels', 'geometry',
               existing_type=geoalchemy2.types.Geometry(srid=4326, from_text='ST_GeomFromEWKT', name='geometry'),
               type_=geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4326, from_text='ST_GeomFromEWKT', name='geometry', nullable=False),
               nullable=False)
    op.alter_column('parcels', 'subdivision_no',
               existing_type=sa.TEXT(),
               type_=sa.String())
    op.alter_column('parcels', 'block_no',
               existing_type=sa.TEXT(),
               type_=sa.String())
    op.alter_column('parcels', 'subdivision_id',
               existing_type=sa.TEXT(),
               type_=sa.String())
    op.alter_column('parcels', 'zoning_color',
               existing_type=sa.TEXT(),
               type_=sa.String())
    op.alter_column('parcels', 'municipality_aname',
               existing_type=sa.TEXT(),
               type_=sa.String())
    op.alter_column('parcels', 'parcel_no',
               existing_type=sa.TEXT(),
               type_=sa.String())

    # --- Schema changes for 'transactions' ---
    op.alter_column('transactions', 'parcel_objectid',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.create_unique_constraint('_transaction_parcel_uc', 'transactions', ['transaction_id', 'parcel_objectid'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### Manually adjusted by developer - downgrade may be incomplete ###
    op.drop_constraint('_transaction_parcel_uc', 'transactions', type_='unique')
    op.alter_column('transactions', 'parcel_objectid',
               existing_type=sa.VARCHAR(),
               nullable=True)

    op.alter_column('parcels', 'rule_id', new_column_name='ruleid', type_=sa.TEXT())
    op.alter_column('parcels', 'neighborha_name', new_column_name='neighborhaname', type_=sa.TEXT())
    op.alter_column('parcels', 'landuse_adetailed', new_column_name='landuseadetailed', type_=sa.TEXT())
    op.alter_column('parcels', 'landuse_agroup', new_column_name='landuseagroup', type_=sa.TEXT())

    op.drop_column('parcels', 'enriched_at')
    op.drop_column('parcels', 'geometry_hash')
    op.drop_column('parcels', 'is_active')
    op.drop_column('parcels', 'updated_at')
    op.drop_column('parcels', 'created_at')


    op.drop_column('parcel_price_metrics', 'neighborhood_id')

    op.alter_column('neighborhoods', 'neighborhood_name', new_column_name='neighborh_aname', type_=sa.TEXT())
    op.drop_column('neighborhoods', 'geometry_hash')

    op.drop_constraint('_parcel_rule_uc', 'building_rules', type_='unique')
    # ### end Alembic commands ###
