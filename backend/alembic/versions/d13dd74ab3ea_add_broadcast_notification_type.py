"""Add BROADCAST notification type

Revision ID: d13dd74ab3ea
Revises: abe3e759bbc6
Create Date: 2025-11-08 11:59:09.667325

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd13dd74ab3ea'
down_revision: Union[str, None] = 'abe3e759bbc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add BROADCAST to NotificationType enum
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'BROADCAST'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values, so we can't downgrade
    # The value will remain but won't be used
    pass
