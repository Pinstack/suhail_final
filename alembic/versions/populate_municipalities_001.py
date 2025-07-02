"""Populate municipalities table from parcels data"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'populate_municipalities_001'
down_revision = 'b932e61b9c19'  # Previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Populate municipalities table from parcels data
    op.execute("""
        INSERT INTO municipalities (municipality_name) 
        SELECT DISTINCT municipality_aname 
        FROM parcels 
        WHERE municipality_aname IS NOT NULL
        AND municipality_aname NOT IN (
            SELECT municipality_name FROM municipalities 
            WHERE municipality_name IS NOT NULL
        )
    """)

def downgrade():
    # Clear municipalities table
    op.execute("""
        DELETE FROM municipalities 
        WHERE municipality_name IN (
            SELECT DISTINCT municipality_aname 
            FROM parcels 
            WHERE municipality_aname IS NOT NULL
        )
    """)
