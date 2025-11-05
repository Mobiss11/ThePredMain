"""add mission icon

Revision ID: add_mission_icon
Revises:
Create Date: 2025-11-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_mission_icon'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add icon column to missions table
    op.add_column('missions', sa.Column('icon', sa.String(length=10), nullable=True, server_default='🎯'))


def downgrade():
    op.drop_column('missions', 'icon')
