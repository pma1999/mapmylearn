"""add_credits_column_to_users

Revision ID: b10d49747884
Revises: 9b335ab9fb70
Create Date: 2025-04-08 21:37:18.526865

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b10d49747884'
down_revision = '9b335ab9fb70'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add credits column to users table
    op.add_column('users', sa.Column('credits', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    # Remove credits column from users table
    op.drop_column('users', 'credits') 