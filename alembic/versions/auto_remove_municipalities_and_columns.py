"""
Auto-remove municipalities table and municipality_id columns from all tables (safe, idempotent)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'auto_remove_municipalities_and_columns'
down_revision = 'dd954b6e3622'
branch_labels = None
depends_on = None

def upgrade():
    # Drop municipality_id columns from all tables if they exist
    with op.batch_alter_table('parcels', schema=None) as batch_op:
        try:
            batch_op.drop_column('municipality_id')
        except Exception:
            pass
    with op.batch_alter_table('neighborhoods', schema=None) as batch_op:
        try:
            batch_op.drop_column('municipality_id')
        except Exception:
            pass
    with op.batch_alter_table('subdivisions', schema=None) as batch_op:
        try:
            batch_op.drop_column('municipality_id')
        except Exception:
            pass
    # Drop municipalities table if it exists
    try:
        op.drop_table('municipalities')
    except Exception:
        pass

def downgrade():
    # No-op: irreversible cleanup
    pass 