"""add currency to rewards

Revision ID: 5edcf469af4a
Revises: c8d9e5f6g7h8
Create Date: 2025-11-06 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5edcf469af4a'
down_revision = 'c8d9e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade():
    # Add currency column with default PRED
    op.add_column('leaderboard_rewards', sa.Column('currency', sa.String(10), nullable=False, server_default='PRED'))


def downgrade():
    # Remove currency column
    op.drop_column('leaderboard_rewards', 'currency')
