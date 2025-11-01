"""add_market_photo_and_moderation

Revision ID: 79fa342a014c
Revises: faa5267d165a
Create Date: 2025-11-01 10:19:13.201113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79fa342a014c'
down_revision: Union[str, None] = 'faa5267d165a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add photo_url column
    op.add_column('markets', sa.Column('photo_url', sa.String(length=500), nullable=True))

    # Create moderation_status enum type
    moderation_status_enum = sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='moderationstatus')
    moderation_status_enum.create(op.get_bind(), checkfirst=True)

    # Add moderation_status column with default 'APPROVED'
    op.add_column('markets', sa.Column('moderation_status', moderation_status_enum, nullable=False, server_default='APPROVED'))


def downgrade() -> None:
    # Drop moderation_status column
    op.drop_column('markets', 'moderation_status')

    # Drop moderation_status enum type
    sa.Enum(name='moderationstatus').drop(op.get_bind(), checkfirst=True)

    # Drop photo_url column
    op.drop_column('markets', 'photo_url')
