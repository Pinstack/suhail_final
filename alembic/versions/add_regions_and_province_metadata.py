"""
Add regions table and province metadata for Suhail API alignment
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'e1e813183ae0'
branch_labels = None
depends_on = None

def upgrade():
    # Create regions table
    op.create_table(
        'regions',
        sa.Column('region_id', sa.BigInteger, primary_key=True),
        sa.Column('region_key', sa.String(64)),
        sa.Column('region_name', sa.String(128)),
        sa.Column('map_style_url', sa.String(256)),
        sa.Column('map_zoom_level', sa.Float),
        sa.Column('metrics_url', sa.String(256)),
        sa.Column('default_transactions_date_range', sa.String(32)),
        sa.Column('centroid_x', sa.Float),
        sa.Column('centroid_y', sa.Float),
        sa.Column('bbox_sw_x', sa.Float),
        sa.Column('bbox_sw_y', sa.Float),
        sa.Column('bbox_ne_x', sa.Float),
        sa.Column('bbox_ne_y', sa.Float),
        sa.Column('image_url', sa.String(256)),
    )
    # Add columns to provinces
    op.add_column('provinces', sa.Column('region_id', sa.BigInteger, sa.ForeignKey('regions.region_id')))
    op.add_column('provinces', sa.Column('centroid_x', sa.Float))
    op.add_column('provinces', sa.Column('centroid_y', sa.Float))

def downgrade():
    op.drop_column('provinces', 'centroid_x')
    op.drop_column('provinces', 'centroid_y')
    op.drop_column('provinces', 'region_id')
    op.drop_table('regions') 