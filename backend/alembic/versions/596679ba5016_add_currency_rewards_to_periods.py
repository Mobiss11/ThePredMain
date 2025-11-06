"""add_currency_rewards_to_periods

Revision ID: 596679ba5016
Revises: 5edcf469af4a
Create Date: 2025-11-06 14:09:47.441132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '596679ba5016'
down_revision: Union[str, None] = '5edcf469af4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add separate reward columns for TON and PRED
    op.add_column('leaderboard_periods', sa.Column('total_ton_rewards', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('leaderboard_periods', sa.Column('total_pred_rewards', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove currency reward columns
    op.drop_column('leaderboard_periods', 'total_pred_rewards')
    op.drop_column('leaderboard_periods', 'total_ton_rewards')
