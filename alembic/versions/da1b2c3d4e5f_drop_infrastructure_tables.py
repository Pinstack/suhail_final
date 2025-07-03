"""drop_infrastructure_tables

Revision ID: da1b2c3d4e5f
Revises: 5053caba378a
Create Date: 2025-07-10 00:00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'da1b2c3d4e5f'
down_revision = '5053caba378a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # drop unneeded infrastructure/reference layers
    op.drop_table('bus_lines')
    op.drop_table('dimensions')
    op.drop_table('metro_stations')


def downgrade() -> None:
    # these tables are dropped permanently: no downgrade
    pass
