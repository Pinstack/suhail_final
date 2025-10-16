"""fix_arabic_columns_and_tile_urls

Revision ID: 1ac2e2b2c8d2
Revises: 19c587b33197
Create Date: 2025-08-10 22:23:43.650868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ac2e2b2c8d2'
down_revision: Union[str, Sequence[str], None] = '19c587b33197'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix Arabic column configuration and tile server URLs."""
    print("🔧 FIXING ARABIC COLUMNS AND TILE SERVER URLS")
    print("=" * 60)
    
    # PHASE 1: FIX ARABIC COLUMN CONFIGURATION
    print("📝 Phase 1: Fixing Arabic column configuration in provinces...")
    
    # Store current Arabic names and set proper English/Arabic split
    province_fixes = [
        (101000, 'Riyadh', 'الرياض', 'https://tiles.suhail.ai/maps/riyadh/'),
        (101001, 'Al-Diriyah', 'الدرعية', 'https://tiles.suhail.ai/maps/riyadh/'),
        (21000, 'Makkah', 'مكة المكرمة', 'https://tiles.suhail.ai/maps/makkah_region/'),
        (21001, 'Jeddah', 'جدة', 'https://tiles.suhail.ai/maps/makkah_region/'),
        (51000, 'Dammam', 'الدمام', 'https://tiles.suhail.ai/maps/eastern_region/'),
        (51001, 'Al-Ahsa', 'الاحساء', 'https://tiles.suhail.ai/maps/eastern_region/'),
        (51003, 'Jubail', 'الجبيل', 'https://tiles.suhail.ai/maps/eastern_region/'),
        (51004, 'Qatif', 'القطيف', 'https://tiles.suhail.ai/maps/eastern_region/'),
        (51005, 'Khobar', 'الخبر', 'https://tiles.suhail.ai/maps/eastern_region/'),
        (41000, 'Buraydah', 'بريدة', 'https://tiles.suhail.ai/maps/al_qassim/'),
        (61001, 'Khamis Mushait', 'خميس مشيط', 'https://tiles.suhail.ai/maps/asir_region/'),
        (131000, 'Medina', 'المدينة المنورة', 'https://tiles.suhail.ai/maps/al_madenieh/'),
    ]
    
    for province_id, english_name, arabic_name, tile_url in province_fixes:
        op.execute(f"""
            UPDATE provinces SET 
                province_name = '{english_name}',
                province_name_ar = '{arabic_name}',
                tile_server_url = '{tile_url}'
            WHERE province_id = {province_id};
        """)
        print(f"✅ Fixed province {province_id}: {english_name} | {arabic_name}")
    
    print("✅ Phase 1 completed: Arabic columns and tile URLs fixed")
    
    # PHASE 2: VALIDATE FIXES
    print("\n🔍 Phase 2: Validating fixes...")
    
    # This will be checked in the test script
    print("✅ Phase 2 completed: Ready for validation")
    
    print("\n🎯 MIGRATION COMPLETED SUCCESSFULLY!")
    print("Next steps:")
    print("1. Test province configuration loading")
    print("2. Test tile URL generation") 
    print("3. Run province scraping test")


def downgrade() -> None:
    """Revert Arabic column and tile URL fixes."""
    print("⚠️  REVERTING ARABIC AND URL FIXES")
    
    # Revert to original state (Arabic in main column, broken URLs)
    reverts = [
        (101000, 'الرياض', 'الرياض', 'https://tiles.suhail.ai/riyadh/'),
        (101001, 'الدرعية', 'الدرعية', 'https://tiles.suhail.ai/riyadh/'),
        (21000, 'مكة المكرمة', 'مكة المكرمة', 'https://tiles.suhail.ai/makkah_region/'),
        (21001, 'جدة', 'جدة', 'https://tiles.suhail.ai/makkah_region/'),
        (51000, 'الدمام', 'الدمام', 'https://tiles.suhail.ai/eastern_region/'),
        (51001, 'الاحساء', 'الاحساء', 'https://tiles.suhail.ai/eastern_region/'),
        (51003, 'الجبيل', 'الجبيل', 'https://tiles.suhail.ai/eastern_region/'),
        (51004, 'القطيف', 'القطيف', 'https://tiles.suhail.ai/eastern_region/'),
        (51005, 'الخبر', 'الخبر', 'https://tiles.suhail.ai/eastern_region/'),
        (41000, 'بريدة', 'بريدة', 'https://tiles.suhail.ai/al_qassim/'),
        (61001, 'خميس مشيط', 'خميس مشيط', 'https://tiles.suhail.ai/asir_region/'),
        (131000, 'المدينة المنورة', 'المدينة المنورة', 'https://tiles.suhail.ai/al_madenieh/'),
    ]
    
    for province_id, old_name, old_name_ar, old_url in reverts:
        op.execute(f"""
            UPDATE provinces SET 
                province_name = '{old_name}',
                province_name_ar = '{old_name_ar}',
                tile_server_url = '{old_url}'
            WHERE province_id = {province_id};
        """)
    
    print("⚠️  Reverted to original (broken) state")
