"""add leaderboard rewards

Revision ID: b8c9d4e5f6a7
Revises: update_mission_icon_size
Create Date: 2025-11-06 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8c9d4e5f6a7'
down_revision = 'update_mission_icon_size'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create leaderboard_rewards table
    op.create_table(
        'leaderboard_rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('period', sa.Enum('WEEK', 'MONTH', name='rewardperiod'), nullable=False),
        sa.Column('rank_from', sa.Integer(), nullable=False),
        sa.Column('rank_to', sa.Integer(), nullable=False),
        sa.Column('reward_amount', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leaderboard_rewards_id'), 'leaderboard_rewards', ['id'], unique=False)

    # Insert default weekly rewards
    op.execute("""
        INSERT INTO leaderboard_rewards (period, rank_from, rank_to, reward_amount, is_active) VALUES
        ('WEEK', 1, 1, 50000, true),
        ('WEEK', 2, 2, 30000, true),
        ('WEEK', 3, 3, 20000, true),
        ('WEEK', 4, 10, 10000, true),
        ('WEEK', 11, 50, 5000, true);
    """)

    # Insert default monthly rewards
    op.execute("""
        INSERT INTO leaderboard_rewards (period, rank_from, rank_to, reward_amount, is_active) VALUES
        ('MONTH', 1, 1, 200000, true),
        ('MONTH', 2, 2, 120000, true),
        ('MONTH', 3, 3, 80000, true),
        ('MONTH', 4, 10, 40000, true),
        ('MONTH', 11, 50, 20000, true),
        ('MONTH', 51, 100, 10000, true);
    """)


def downgrade() -> None:
    op.drop_index(op.f('ix_leaderboard_rewards_id'), table_name='leaderboard_rewards')
    op.drop_table('leaderboard_rewards')
    op.execute("DROP TYPE rewardperiod")
