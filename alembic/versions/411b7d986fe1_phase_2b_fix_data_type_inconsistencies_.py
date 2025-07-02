"""Phase 2B: Fix data type inconsistencies for ID fields

Revision ID: 411b7d986fe1
Revises: ddee3a71a1ba
Create Date: 2025-07-01 11:13:59.578871

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '411b7d986fe1'
down_revision: Union[str, Sequence[str], None] = 'ddee3a71a1ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Phase 2B: Fix data type inconsistencies for ID fields.
    
    Convert Float/String ID columns to BigInteger to match MVT source data types:
    - parcels.parcel_id: DOUBLE PRECISION -> BIGINT
    - parcels.zoning_id: DOUBLE PRECISION -> BIGINT  
    - parcels.subdivision_id: CHARACTER VARYING -> BIGINT
    - subdivisions.zoning_id: DOUBLE PRECISION -> BIGINT
    """
    
    # Fix parcels.parcel_id (DOUBLE PRECISION -> BIGINT)
    op.alter_column(
        'parcels', 
        'parcel_id',
        existing_type=sa.Float(),
        type_=sa.BigInteger(),
        existing_nullable=True,
        # Use ROUND() to handle any fractional values, then cast
        postgresql_using='ROUND(parcel_id)::bigint'
    )
    
    # Fix parcels.zoning_id (DOUBLE PRECISION -> BIGINT)
    op.alter_column(
        'parcels',
        'zoning_id', 
        existing_type=sa.Float(),
        type_=sa.BigInteger(),
        existing_nullable=True,
        postgresql_using='ROUND(zoning_id)::bigint'
    )
    
    # Fix parcels.subdivision_id (CHARACTER VARYING -> BIGINT)
    # Handle string to integer conversion with validation and trimming
    op.alter_column(
        'parcels',
        'subdivision_id',
        existing_type=sa.String(),
        type_=sa.BigInteger(),
        existing_nullable=True,
        # Trim whitespace and only convert valid numeric strings
        postgresql_using='''
        CASE
            WHEN TRIM(subdivision_id) ~ '^[0-9]+$' THEN TRIM(subdivision_id)::bigint
            ELSE NULL
        END
        '''
    )
    
    # Fix subdivisions.zoning_id (DOUBLE PRECISION -> BIGINT) 
    op.alter_column(
        'subdivisions',
        'zoning_id',
        existing_type=sa.Float(),
        type_=sa.BigInteger(),
        existing_nullable=True,
        postgresql_using='ROUND(zoning_id)::bigint'
    )


def downgrade() -> None:
    """
    Revert Phase 2B changes back to original types.
    Note: Some precision may be lost in the conversion back to float types.
    """
    
    # Revert subdivisions.zoning_id (BIGINT -> DOUBLE PRECISION)
    op.alter_column(
        'subdivisions',
        'zoning_id',
        existing_type=sa.BigInteger(),
        type_=sa.Float(),
        existing_nullable=True,
        postgresql_using='zoning_id::double precision'
    )
    
    # Revert parcels.subdivision_id (BIGINT -> CHARACTER VARYING)
    op.alter_column(
        'parcels',
        'subdivision_id',
        existing_type=sa.BigInteger(),
        type_=sa.String(),
        existing_nullable=True,
        postgresql_using='subdivision_id::varchar'
    )
    
    # Revert parcels.zoning_id (BIGINT -> DOUBLE PRECISION)
    op.alter_column(
        'parcels',
        'zoning_id',
        existing_type=sa.BigInteger(),
        type_=sa.Float(),
        existing_nullable=True,
        postgresql_using='zoning_id::double precision'
    )
    
    # Revert parcels.parcel_id (BIGINT -> DOUBLE PRECISION)
    op.alter_column(
        'parcels',
        'parcel_id',
        existing_type=sa.BigInteger(),
        type_=sa.Float(),
        existing_nullable=True,
        postgresql_using='parcel_id::double precision'
    )
