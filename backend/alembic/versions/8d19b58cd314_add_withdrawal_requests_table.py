"""add_withdrawal_requests_table

Revision ID: 8d19b58cd314
Revises: 2f9c933e3e1c
Create Date: 2025-11-14 19:08:19.078888

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d19b58cd314'
down_revision: Union[str, None] = '2f9c933e3e1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum using native PostgreSQL syntax with IF NOT EXISTS check
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE withdrawalstatus AS ENUM ('pending', 'processing', 'completed', 'rejected', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create withdrawal_requests table using existing enum type
    # Note: We use create_type=False to prevent SQLAlchemy from creating the enum again
    from sqlalchemy.dialects.postgresql import ENUM

    withdrawal_status_enum = ENUM('pending', 'processing', 'completed', 'rejected', 'cancelled', name='withdrawalstatus', create_type=False)

    op.create_table(
        'withdrawal_requests',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('pred_amount', sa.DECIMAL(precision=20, scale=2), nullable=False),
        sa.Column('ton_amount', sa.DECIMAL(precision=20, scale=8), nullable=True),
        sa.Column('ton_address', sa.String(length=255), nullable=False),
        sa.Column('status', withdrawal_status_enum, nullable=False, server_default='pending'),
        sa.Column('tx_hash', sa.String(length=255), nullable=True),
        sa.Column('admin_note', sa.Text(), nullable=True),
        sa.Column('processed_by', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['processed_by'], ['users.id'], )
    )

    # Create indexes
    op.create_index(op.f('ix_withdrawal_requests_id'), 'withdrawal_requests', ['id'], unique=False)
    op.create_index(op.f('ix_withdrawal_requests_user_id'), 'withdrawal_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_withdrawal_requests_status'), 'withdrawal_requests', ['status'], unique=False)
    op.create_index(op.f('ix_withdrawal_requests_tx_hash'), 'withdrawal_requests', ['tx_hash'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_withdrawal_requests_tx_hash'), table_name='withdrawal_requests')
    op.drop_index(op.f('ix_withdrawal_requests_status'), table_name='withdrawal_requests')
    op.drop_index(op.f('ix_withdrawal_requests_user_id'), table_name='withdrawal_requests')
    op.drop_index(op.f('ix_withdrawal_requests_id'), table_name='withdrawal_requests')

    # Drop table
    op.drop_table('withdrawal_requests')

    # Drop enum
    op.execute('DROP TYPE withdrawalstatus')
