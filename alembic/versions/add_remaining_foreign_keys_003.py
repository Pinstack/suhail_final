"""Add foreign key constraint for land_use_groups"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_remaining_foreign_keys_003'
down_revision = 'populate_land_use_groups_002'
branch_labels = None
depends_on = None

def upgrade():
    # Add foreign key for land_use_groups (parcels.landuseagroup -> land_use_groups.landuse_group)
    # Note: landuse_group is the primary key in land_use_groups table, so this should work
    op.create_foreign_key(
        'fk_parcels_landuseagroup',
        'parcels', 'land_use_groups',
        ['landuseagroup'], ['landuse_group']
    )
    
    # Skip municipalities foreign key for now since municipality_name is not unique
    # Would need to add unique constraint first or restructure the relationship

def downgrade():
    # Drop foreign key
    op.drop_constraint('fk_parcels_landuseagroup', 'parcels', type_='foreignkey')
