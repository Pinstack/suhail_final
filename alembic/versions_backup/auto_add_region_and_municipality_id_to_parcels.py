"""
Add region_id and municipality_id columns to parcels table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c0f7c44f9501'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('parcels', sa.Column('region_id', sa.BigInteger(), nullable=True))

def downgrade():
    op.drop_column('parcels', 'region_id') 