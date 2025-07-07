"""
Add province_id_mapping and quarantined_features tables for robust province ID remapping and quarantine
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a2b3c4d5e6f7'
down_revision = '66aceed432ec'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'province_id_mapping',
        sa.Column('source_province_id', sa.BigInteger, primary_key=True),
        sa.Column('canonical_province_id', sa.BigInteger, nullable=False),
        sa.Column('mapping_reason', sa.String(128)),
        sa.Column('last_seen', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        'quarantined_features',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('feature_type', sa.String(64), nullable=False),
        sa.Column('feature_id', sa.BigInteger),
        sa.Column('province_id', sa.BigInteger),
        sa.Column('region_id', sa.BigInteger),
        sa.Column('geometry', sa.Text),  # Use sa.Text for WKT, or use geoalchemy2 for PostGIS
        sa.Column('properties', sa.Text),
        sa.Column('quarantined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('quarantined_features')
    op.drop_table('province_id_mapping') 