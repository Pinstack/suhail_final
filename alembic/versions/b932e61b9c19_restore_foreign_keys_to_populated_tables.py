"""restore_foreign_keys_to_populated_tables

Revision ID: b932e61b9c19
Revises: 645f4d2cad7f
Create Date: 2025-07-02 15:21:49.383642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b932e61b9c19'
down_revision: Union[str, Sequence[str], None] = '645f4d2cad7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Restore the 2 missing foreign keys now that reference tables are populated."""
    
    # Only add the foreign keys that are actually missing
    op.create_foreign_key(
        'parcels_province_id_fkey',
        'parcels', 'provinces',
        ['province_id'], ['province_id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'parcels_ruleid_fkey', 
        'parcels', 'zoning_rules',
        ['ruleid'], ['ruleid'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Remove the foreign key constraints."""
    op.drop_constraint('parcels_province_id_fkey', 'parcels', type_='foreignkey')
    op.drop_constraint('parcels_ruleid_fkey', 'parcels', type_='foreignkey')
