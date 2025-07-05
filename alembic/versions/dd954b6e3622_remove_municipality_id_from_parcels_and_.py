"""
remove municipality_id from parcels and drop municipalities table

Revision ID: dd954b6e3622
Revises: a1b2c3d4e5f6
Create Date: 2025-07-05 13:53:49.738047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'dd954b6e3622'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op: municipality_id and municipalities table do not exist in this schema
    pass


def downgrade() -> None:
    # No-op: nothing to revert
    pass
