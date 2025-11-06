"""add_subscription_mission_fields

Revision ID: 4abc70c234d7
Revises: 596679ba5016
Create Date: 2025-11-06 14:39:21.950311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4abc70c234d7'
down_revision: Union[str, None] = '596679ba5016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add fields for subscription missions and custom icons
    op.add_column('missions', sa.Column('channel_id', sa.String(255), nullable=True))
    op.add_column('missions', sa.Column('channel_username', sa.String(255), nullable=True))
    op.add_column('missions', sa.Column('channel_url', sa.String(500), nullable=True))
    op.add_column('missions', sa.Column('custom_icon_url', sa.String(500), nullable=True))


def downgrade() -> None:
    # Remove subscription mission fields
    op.drop_column('missions', 'custom_icon_url')
    op.drop_column('missions', 'channel_url')
    op.drop_column('missions', 'channel_username')
    op.drop_column('missions', 'channel_id')
