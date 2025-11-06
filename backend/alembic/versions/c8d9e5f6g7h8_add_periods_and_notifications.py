"""add periods and notifications

Revision ID: c8d9e5f6g7h8
Revises: b8c9d4e5f6a7
Create Date: 2025-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c8d9e5f6g7h8'
down_revision = 'b8c9d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types with IF NOT EXISTS check
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'periodtype') THEN
                CREATE TYPE periodtype AS ENUM ('week', 'month');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'periodstatus') THEN
                CREATE TYPE periodstatus AS ENUM ('active', 'closed', 'scheduled');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationstatus') THEN
                CREATE TYPE notificationstatus AS ENUM ('pending', 'processing', 'sent', 'failed', 'permanent_failure');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationtype') THEN
                CREATE TYPE notificationtype AS ENUM ('leaderboard_reward', 'market_resolved', 'bet_won', 'bet_lost', 'mission_completed', 'system');
            END IF;
        END $$;
    """)

    # Create leaderboard_periods table if not exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if 'leaderboard_periods' not in inspector.get_table_names():
        op.create_table(
            'leaderboard_periods',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('period_type', postgresql.ENUM('week', 'month', name='periodtype', create_type=False), nullable=False),
            sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('status', postgresql.ENUM('active', 'closed', 'scheduled', name='periodstatus', create_type=False), nullable=False),
            sa.Column('total_rewards_distributed', sa.Integer(), server_default='0', nullable=True),
            sa.Column('participants_count', sa.Integer(), server_default='0', nullable=True),
            sa.Column('winners_count', sa.Integer(), server_default='0', nullable=True),
            sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('closed_by_admin_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_leaderboard_periods_id'), 'leaderboard_periods', ['id'], unique=False)
        op.create_index('ix_leaderboard_periods_status', 'leaderboard_periods', ['status'], unique=False)
        op.create_index('ix_leaderboard_periods_period_type', 'leaderboard_periods', ['period_type'], unique=False)

    # Create telegram_notifications_queue table if not exists
    if 'telegram_notifications_queue' not in inspector.get_table_names():
        op.create_table(
            'telegram_notifications_queue',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('telegram_id', sa.BigInteger(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('message_text', sa.Text(), nullable=False),
            sa.Column('parse_mode', sa.String(length=10), server_default='HTML', nullable=True),
            sa.Column('notification_type', postgresql.ENUM('leaderboard_reward', 'market_resolved', 'bet_won', 'bet_lost', 'mission_completed', 'system', name='notificationtype', create_type=False), nullable=False),
            sa.Column('status', postgresql.ENUM('pending', 'processing', 'sent', 'failed', 'permanent_failure', name='notificationstatus', create_type=False), nullable=False),
            sa.Column('attempts', sa.Integer(), server_default='0', nullable=True),
            sa.Column('max_attempts', sa.Integer(), server_default='5', nullable=True),
            sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('processing_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('metadata', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_telegram_notifications_queue_id'), 'telegram_notifications_queue', ['id'], unique=False)
        op.create_index('ix_telegram_notifications_queue_telegram_id', 'telegram_notifications_queue', ['telegram_id'], unique=False)
        op.create_index('ix_telegram_notifications_queue_user_id', 'telegram_notifications_queue', ['user_id'], unique=False)
        op.create_index('ix_telegram_notifications_queue_status', 'telegram_notifications_queue', ['status'], unique=False)
        op.create_index('ix_telegram_notifications_queue_created_at', 'telegram_notifications_queue', ['created_at'], unique=False)


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Drop telegram_notifications_queue table if exists
    if 'telegram_notifications_queue' in inspector.get_table_names():
        op.drop_index('ix_telegram_notifications_queue_created_at', table_name='telegram_notifications_queue')
        op.drop_index('ix_telegram_notifications_queue_status', table_name='telegram_notifications_queue')
        op.drop_index('ix_telegram_notifications_queue_user_id', table_name='telegram_notifications_queue')
        op.drop_index('ix_telegram_notifications_queue_telegram_id', table_name='telegram_notifications_queue')
        op.drop_index(op.f('ix_telegram_notifications_queue_id'), table_name='telegram_notifications_queue')
        op.drop_table('telegram_notifications_queue')

    # Drop leaderboard_periods table if exists
    if 'leaderboard_periods' in inspector.get_table_names():
        op.drop_index('ix_leaderboard_periods_period_type', table_name='leaderboard_periods')
        op.drop_index('ix_leaderboard_periods_status', table_name='leaderboard_periods')
        op.drop_index(op.f('ix_leaderboard_periods_id'), table_name='leaderboard_periods')
        op.drop_table('leaderboard_periods')

    # Drop types if exist
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationtype') THEN
                DROP TYPE notificationtype;
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationstatus') THEN
                DROP TYPE notificationstatus;
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'periodstatus') THEN
                DROP TYPE periodstatus;
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'periodtype') THEN
                DROP TYPE periodtype;
            END IF;
        END $$;
    """)
