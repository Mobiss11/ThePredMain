"""update_betposition_enum_to_uppercase

Revision ID: 2d6e048c9c08
Revises: update_mission_icon_size
Create Date: 2025-11-05 11:00:59.058488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d6e048c9c08'
down_revision: Union[str, None] = 'update_mission_icon_size'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop and recreate the betposition enum with uppercase values
    op.execute("DROP TYPE IF EXISTS betposition CASCADE")
    op.execute("CREATE TYPE betposition AS ENUM ('YES', 'NO')")

    # Recreate the bets table position column (should be empty anyway)
    # The CASCADE will handle the column, but we need to recreate it
    op.execute("""
        ALTER TABLE bets
        ALTER COLUMN position TYPE betposition
        USING position::text::betposition
    """)


def downgrade() -> None:
    # Revert to lowercase enum
    op.execute("DROP TYPE IF EXISTS betposition CASCADE")
    op.execute("CREATE TYPE betposition AS ENUM ('yes', 'no')")

    op.execute("""
        ALTER TABLE bets
        ALTER COLUMN position TYPE betposition
        USING position::text::betposition
    """)
