"""add_user_role_and_credit_transactions

Revision ID: 3877029518ce
Revises: b10d49747884
Create Date: 2025-04-08 21:44:05.588592

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3877029518ce'
down_revision = 'b10d49747884'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True, server_default='false'))
    
    # Create credit_transactions table
    op.create_table('credit_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for credit_transactions table
    op.create_index('idx_credit_transaction_user_id', 'credit_transactions', ['user_id'], unique=False)
    op.create_index('idx_credit_transaction_admin_id', 'credit_transactions', ['admin_id'], unique=False)
    op.create_index('idx_credit_transaction_timestamp', 'credit_transactions', [sa.text('timestamp DESC')], unique=False)
    op.create_index('idx_credit_transaction_action_type', 'credit_transactions', ['action_type'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_credit_transaction_action_type', table_name='credit_transactions')
    op.drop_index('idx_credit_transaction_timestamp', table_name='credit_transactions')
    op.drop_index('idx_credit_transaction_admin_id', table_name='credit_transactions')
    op.drop_index('idx_credit_transaction_user_id', table_name='credit_transactions')
    
    # Drop credit_transactions table
    op.drop_table('credit_transactions')
    
    # Drop is_admin column from users table
    op.drop_column('users', 'is_admin') 