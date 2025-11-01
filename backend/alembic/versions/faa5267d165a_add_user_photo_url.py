"""add_user_photo_url

Revision ID: faa5267d165a
Revises: 001_initial
Create Date: 2025-11-01 09:39:33.778004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'faa5267d165a'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('photo_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'photo_url')
