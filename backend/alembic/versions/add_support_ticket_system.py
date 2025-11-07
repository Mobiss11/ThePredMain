"""Add support ticket system

Revision ID: support_tickets_001
Revises:
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'support_tickets_001'
down_revision = '4abc70c234d7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create support_tickets table
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='ticketpriority'), nullable=True),
        sa.Column('status', sa.Enum('OPEN', 'IN_PROGRESS', 'WAITING_USER', 'CLOSED', name='ticketstatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('admin_replied', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_support_tickets_id'), 'support_tickets', ['id'], unique=False)

    # Create support_messages table
    op.create_table(
        'support_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('attachment_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_support_messages_id'), 'support_messages', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_support_messages_id'), table_name='support_messages')
    op.drop_table('support_messages')
    op.drop_index(op.f('ix_support_tickets_id'), table_name='support_tickets')
    op.drop_table('support_tickets')
    op.execute('DROP TYPE ticketstatus')
    op.execute('DROP TYPE ticketpriority')
