"""make_created_by_nullable

Revision ID: 5db54f4ebd6e
Revises: support_tickets_001
Create Date: 2025-11-07 20:45:05.673754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5db54f4ebd6e'
down_revision: Union[str, None] = 'support_tickets_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make created_by nullable to allow admin events
    op.alter_column('markets', 'created_by',
                    existing_type=sa.BigInteger(),
                    nullable=True)


def downgrade() -> None:
    # Make created_by not nullable again
    op.alter_column('markets', 'created_by',
                    existing_type=sa.BigInteger(),
                    nullable=False)
