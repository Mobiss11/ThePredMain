"""add_user_ban_system

Revision ID: abe3e759bbc6
Revises: 5db54f4ebd6e
Create Date: 2025-11-07 21:02:57.218751

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abe3e759bbc6'
down_revision: Union[str, None] = '5db54f4ebd6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ban system fields to users table
    op.add_column('users', sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('ban_reason', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('banned_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove ban system fields
    op.drop_column('users', 'banned_at')
    op.drop_column('users', 'ban_reason')
    op.drop_column('users', 'is_banned')
