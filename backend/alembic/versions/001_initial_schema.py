"""Initial schema with users, markets, bets, transactions, missions

Revision ID: 001_initial
Revises:
Create Date: 2025-10-30 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('pred_balance', sa.DECIMAL(precision=20, scale=2), nullable=False, server_default='10000.00'),
        sa.Column('ton_balance', sa.DECIMAL(precision=20, scale=2), nullable=False, server_default='0.00'),
        sa.Column('rank', sa.String(length=50), nullable=False, server_default='Bronze'),
        sa.Column('total_bets', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_wins', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_losses', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('win_streak', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('referrer_id', sa.BigInteger(), nullable=True),
        sa.Column('referral_code', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.id'], ),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
    op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True)

    # Create markets table
    op.create_table(
        'markets',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('yes_odds', sa.DECIMAL(precision=5, scale=2), nullable=False, server_default='50.00'),
        sa.Column('no_odds', sa.DECIMAL(precision=5, scale=2), nullable=False, server_default='50.00'),
        sa.Column('total_volume_pred', sa.DECIMAL(precision=20, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_volume_ton', sa.DECIMAL(precision=20, scale=2), nullable=False, server_default='0.00'),
        sa.Column('yes_pool_pred', sa.DECIMAL(precision=20, scale=2), nullable=False, server_default='0.00'),
        sa.Column('no_pool_pred', sa.DECIMAL(precision=20, scale=2), nullable=False, server_default='0.00'),
        sa.Column('yes_pool_ton', sa.DECIMAL(precision=20, scale=2), nullable=False, server_default='0.00'),
        sa.Column('no_pool_ton', sa.DECIMAL(precision=20, scale=2), nullable=False, server_default='0.00'),
        sa.Column('status', sa.Enum('OPEN', 'CLOSED', 'RESOLVED', 'CANCELLED', name='marketstatus'), nullable=False, server_default='OPEN'),
        sa.Column('outcome', sa.Enum('YES', 'NO', 'CANCELLED', name='marketoutcome'), nullable=True),
        sa.Column('resolve_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('views_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('bets_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('is_promoted', sa.String(length=50), nullable=False, server_default='none'),
        sa.Column('promoted_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    )
    op.create_index(op.f('ix_markets_id'), 'markets', ['id'], unique=False)
    op.create_index(op.f('ix_markets_status'), 'markets', ['status'], unique=False)
    op.create_index(op.f('ix_markets_category'), 'markets', ['category'], unique=False)

    # Create bets table
    op.create_table(
        'bets',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('market_id', sa.BigInteger(), nullable=False),
        sa.Column('position', sa.Enum('YES', 'NO', name='betposition'), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=20, scale=2), nullable=False),
        sa.Column('currency', sa.Enum('PRED', 'TON', name='betcurrency'), nullable=False),
        sa.Column('odds', sa.DECIMAL(precision=5, scale=2), nullable=False),
        sa.Column('potential_win', sa.DECIMAL(precision=20, scale=2), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'WON', 'LOST', 'CANCELLED', name='betstatus'), nullable=False, server_default='PENDING'),
        sa.Column('payout', sa.DECIMAL(precision=20, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ),
    )
    op.create_index(op.f('ix_bets_id'), 'bets', ['id'], unique=False)
    op.create_index(op.f('ix_bets_user_id'), 'bets', ['user_id'], unique=False)
    op.create_index(op.f('ix_bets_market_id'), 'bets', ['market_id'], unique=False)

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('type', sa.Enum('DEPOSIT', 'WITHDRAW', 'BET', 'WIN', 'REFERRAL', 'MISSION', 'PROMOTION', name='transactiontype'), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('amount', sa.DECIMAL(precision=20, scale=2), nullable=False),
        sa.Column('tx_hash', sa.String(length=255), nullable=True),
        sa.Column('ton_address', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', name='transactionstatus'), nullable=False, server_default='PENDING'),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_user_id'), 'transactions', ['user_id'], unique=False)

    # Create missions table
    op.create_table(
        'missions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reward_amount', sa.DECIMAL(precision=20, scale=2), nullable=False),
        sa.Column('reward_currency', sa.String(length=10), nullable=False, server_default='PRED'),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('requirements', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_missions_id'), 'missions', ['id'], unique=False)

    # Create user_missions table
    op.create_table(
        'user_missions',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('mission_id', sa.BigInteger(), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('claimed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('user_id', 'mission_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], ),
    )


def downgrade() -> None:
    op.drop_table('user_missions')
    op.drop_table('missions')
    op.drop_table('transactions')
    op.drop_table('bets')
    op.drop_table('markets')
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS marketstatus')
    op.execute('DROP TYPE IF EXISTS marketoutcome')
    op.execute('DROP TYPE IF EXISTS betposition')
    op.execute('DROP TYPE IF EXISTS betcurrency')
    op.execute('DROP TYPE IF EXISTS betstatus')
    op.execute('DROP TYPE IF EXISTS transactiontype')
    op.execute('DROP TYPE IF EXISTS transactionstatus')
