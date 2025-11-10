"""add_ton_wallet_integration

Revision ID: 86fc6d99a06c
Revises: 42cdd14f53a4
Create Date: 2025-11-10 18:18:03.302150

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86fc6d99a06c'
down_revision: Union[str, None] = '42cdd14f53a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create wallet_addresses table
    op.create_table(
        'wallet_addresses',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('ton_address', sa.String(length=255), nullable=False),
        sa.Column('raw_address', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('ton_address')
    )

    # Create indexes for wallet_addresses
    op.create_index('ix_wallet_addresses_id', 'wallet_addresses', ['id'], unique=False)
    op.create_index('ix_wallet_addresses_user_id', 'wallet_addresses', ['user_id'], unique=False)
    op.create_index('ix_wallet_addresses_ton_address', 'wallet_addresses', ['ton_address'], unique=False)

    # Add new columns to transactions table
    op.add_column('transactions', sa.Column('deposit_address', sa.String(length=255), nullable=True))
    op.add_column('transactions', sa.Column('confirmations', sa.BigInteger(), nullable=True, server_default='0'))
    op.add_column('transactions', sa.Column('converted_amount', sa.DECIMAL(precision=20, scale=2), nullable=True))
    op.add_column('transactions', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))

    # Add index for tx_hash if not exists
    op.create_index('ix_transactions_tx_hash', 'transactions', ['tx_hash'], unique=False)

    # Add index for status if not exists
    op.create_index('ix_transactions_status', 'transactions', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes from transactions
    op.drop_index('ix_transactions_status', table_name='transactions')
    op.drop_index('ix_transactions_tx_hash', table_name='transactions')

    # Remove columns from transactions
    op.drop_column('transactions', 'expires_at')
    op.drop_column('transactions', 'converted_amount')
    op.drop_column('transactions', 'confirmations')
    op.drop_column('transactions', 'deposit_address')

    # Drop indexes from wallet_addresses
    op.drop_index('ix_wallet_addresses_ton_address', table_name='wallet_addresses')
    op.drop_index('ix_wallet_addresses_user_id', table_name='wallet_addresses')
    op.drop_index('ix_wallet_addresses_id', table_name='wallet_addresses')

    # Drop wallet_addresses table
    op.drop_table('wallet_addresses')
