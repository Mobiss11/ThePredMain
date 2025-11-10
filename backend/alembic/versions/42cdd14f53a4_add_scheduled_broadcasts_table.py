"""add_scheduled_broadcasts_table

Revision ID: 42cdd14f53a4
Revises: d13dd74ab3ea
Create Date: 2025-11-10 11:21:02.689175

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42cdd14f53a4'
down_revision: Union[str, None] = 'd13dd74ab3ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create BroadcastStatus enum
    op.execute("""
        CREATE TYPE broadcaststatus AS ENUM (
            'PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED'
        )
    """)

    # Create scheduled_broadcasts table
    op.create_table(
        'scheduled_broadcasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('parse_mode', sa.String(length=10), nullable=True),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('target', sa.String(length=20), nullable=True),
        sa.Column('target_telegram_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED', name='broadcaststatus'), nullable=False),
        sa.Column('total_recipients', sa.Integer(), nullable=True),
        sa.Column('sent_count', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_broadcasts_id'), 'scheduled_broadcasts', ['id'], unique=False)
    op.create_index(op.f('ix_scheduled_broadcasts_scheduled_at'), 'scheduled_broadcasts', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_scheduled_broadcasts_status'), 'scheduled_broadcasts', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scheduled_broadcasts_status'), table_name='scheduled_broadcasts')
    op.drop_index(op.f('ix_scheduled_broadcasts_scheduled_at'), table_name='scheduled_broadcasts')
    op.drop_index(op.f('ix_scheduled_broadcasts_id'), table_name='scheduled_broadcasts')
    op.drop_table('scheduled_broadcasts')
    op.execute('DROP TYPE broadcaststatus')
