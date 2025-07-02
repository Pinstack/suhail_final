"""Populate land_use_groups table from parcels data"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'populate_land_use_groups_002'
down_revision = 'populate_municipalities_001'
branch_labels = None
depends_on = None

def upgrade():
    # Populate land_use_groups table from parcels data
    op.execute("""
        INSERT INTO land_use_groups (landuse_group) 
        SELECT DISTINCT landuseagroup 
        FROM parcels 
        WHERE landuseagroup IS NOT NULL
        AND landuseagroup NOT IN (
            SELECT landuse_group FROM land_use_groups 
            WHERE landuse_group IS NOT NULL
        )
    """)

def downgrade():
    # Clear land_use_groups table
    op.execute("""
        DELETE FROM land_use_groups 
        WHERE landuse_group IN (
            SELECT DISTINCT landuseagroup 
            FROM parcels 
            WHERE landuseagroup IS NOT NULL
        )
    """) 