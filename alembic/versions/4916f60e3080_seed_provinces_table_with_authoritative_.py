"""seed provinces table with authoritative province data

Revision ID: 4916f60e3080
Revises: 9e5cad7a9d98
Create Date: 2025-07-04 23:00:24.750975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4916f60e3080'
down_revision: Union[str, Sequence[str], None] = '9e5cad7a9d98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Insert authoritative province data (id and name only)
    op.execute("""
    INSERT INTO provinces (province_id, province_name) VALUES
        (101000, 'الرياض'),
        (101001, 'الدرعية'),
        (131000, 'المدينة المنورة'),
        (51000, 'الدمام'),
        (51003, 'الجبيل'),
        (51004, 'القطيف'),
        (51005, 'الخبر'),
        (51001, 'الاحساء'),
        (21000, 'مكة المكرمة'),
        (21001, 'جدة'),
        (41000, 'بريدة'),
        (61001, 'خميس مشيط')
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
