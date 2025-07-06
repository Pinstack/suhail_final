"""seed provinces table with authoritative province data

Revision ID: 4916f60e3080
Revises: 9e5cad7a9d98
Create Date: 2025-07-04 23:00:24.750975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '4916f60e3080'
down_revision: Union[str, Sequence[str], None] = '9e5cad7a9d98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add province_name_ar column if it does not exist
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='provinces' AND column_name='province_name_ar'
        ) THEN
            ALTER TABLE provinces ADD COLUMN province_name_ar VARCHAR;
        END IF;
    END$$;
    """)
    # Insert authoritative province data (id and name only)
    op.execute("""
    INSERT INTO provinces (province_id, province_name, province_name_ar)
    VALUES
        (101000, 'Riyadh', 'الرياض'),
        (101001, 'Riyadh City', 'مدينة الرياض'),
        (131000, 'Eastern Province', 'المنطقة الشرقية'),
        (51000, 'Makkah', 'مكة المكرمة'),
        (51003, 'Jeddah', 'جدة'),
        (51004, 'Taif', 'الطائف'),
        (51005, 'Mecca', 'مكة'),
        (51001, 'Rabigh', 'رابغ'),
        (21000, 'Al Madinah', 'المدينة المنورة'),
        (21001, 'Yanbu', 'ينبع'),
        (41000, 'Al Qassim', 'القصيم'),
        (61001, 'Tabuk', 'تبوك')
    ON CONFLICT (province_id) DO NOTHING;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove only the inserted province records
    op.execute("""
    DELETE FROM provinces WHERE province_id IN (
        101000, 101001, 131000, 51000, 51003, 51004, 51005, 51001, 21000, 21001, 41000, 61001
    );
    """)
