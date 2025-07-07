"""
Add missing columns to quarantined_features for full pipeline compatibility
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a3b4c5d6e7f8'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('quarantined_features') as batch_op:
        batch_op.add_column(sa.Column('region_id', sa.BigInteger, nullable=True))
        batch_op.add_column(sa.Column('geometry', sa.Text, nullable=True))
        batch_op.add_column(sa.Column('properties', sa.Text, nullable=True))
        batch_op.add_column(sa.Column('quarantined_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
        batch_op.alter_column('raw_data', existing_type=sa.Text(), nullable=True)

def downgrade():
    with op.batch_alter_table('quarantined_features') as batch_op:
        batch_op.drop_column('region_id')
        batch_op.drop_column('geometry')
        batch_op.drop_column('properties')
        batch_op.drop_column('quarantined_at')
        batch_op.alter_column('raw_data', existing_type=sa.Text(), nullable=False) 