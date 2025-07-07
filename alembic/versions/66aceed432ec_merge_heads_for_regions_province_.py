"""Merge heads for regions/province alignment

Revision ID: 66aceed432ec
Revises: e1e813183ae0, a1b2c3d4e5f6
Create Date: 2025-07-07 16:32:10.563372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66aceed432ec'
down_revision: Union[str, Sequence[str], None] = ('e1e813183ae0', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
