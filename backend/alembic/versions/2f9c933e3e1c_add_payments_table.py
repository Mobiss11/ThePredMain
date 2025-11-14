"""add_payments_table

Revision ID: 2f9c933e3e1c
Revises: 86fc6d99a06c
Create Date: 2025-11-14 18:21:19.053540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f9c933e3e1c'
down_revision: Union[str, None] = '86fc6d99a06c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create PaymentMethod enum
    op.execute("CREATE TYPE paymentmethod AS ENUM ('cryptocloud')")

    # Create PaymentStatus enum
    op.execute("CREATE TYPE paymentstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled')")

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('invoice_id', sa.String(length=255), nullable=True),
        sa.Column('payment_url', sa.String(length=1000), nullable=True),
        sa.Column('amount', sa.DECIMAL(precision=20, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('crypto_amount', sa.DECIMAL(precision=20, scale=8), nullable=True),
        sa.Column('crypto_currency', sa.String(length=10), nullable=True),
        sa.Column('pred_amount', sa.DECIMAL(precision=20, scale=2), nullable=True),
        sa.Column('payment_method', sa.Enum('cryptocloud', name='paymentmethod'), nullable=False, server_default='cryptocloud'),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'cancelled', name='paymentstatus'), nullable=False, server_default='pending'),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('payment_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # Create indexes
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)
    op.create_index(op.f('ix_payments_invoice_id'), 'payments', ['invoice_id'], unique=True)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_index(op.f('ix_payments_invoice_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')

    # Drop table
    op.drop_table('payments')

    # Drop enums
    op.execute('DROP TYPE paymentstatus')
    op.execute('DROP TYPE paymentmethod')
