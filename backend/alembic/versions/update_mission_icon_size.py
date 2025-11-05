"""update mission icon size

Revision ID: update_mission_icon_size
Revises: add_mission_icon
Create Date: 2025-11-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_mission_icon_size'
down_revision = 'add_mission_icon'
branch_labels = None
depends_on = None


def upgrade():
    # Increase icon field size from 10 to 255 characters
    op.alter_column('missions', 'icon',
               existing_type=sa.String(length=10),
               type_=sa.String(length=255),
               existing_nullable=True,
               existing_server_default='🎯')


def downgrade():
    # Revert to 10 characters
    op.alter_column('missions', 'icon',
               existing_type=sa.String(length=255),
               type_=sa.String(length=10),
               existing_nullable=True,
               existing_server_default='🎯')
