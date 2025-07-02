"""add_valid_foreign_keys

Revision ID: 645f4d2cad7f
Revises: 411b7d986fe1
Create Date: 2025-07-02 14:48:43.401265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '645f4d2cad7f'
down_revision: Union[str, Sequence[str], None] = '411b7d986fe1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the valid foreign key constraint that was missing."""
    # Add foreign key constraint for parcels.neighborhood_id -> neighborhoods.neighborhood_id
    # This is valid because forensic analysis showed no orphaned references
    op.create_foreign_key(
        'parcels_neighborhood_id_fkey',
        'parcels', 'neighborhoods',
        ['neighborhood_id'], ['neighborhood_id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Remove the foreign key constraint."""
    op.drop_constraint('parcels_neighborhood_id_fkey', 'parcels', type_='foreignkey')
