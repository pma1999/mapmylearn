"""add_public_sharing_to_learning_paths

Revision ID: b8d832d608d3
Revises: e1062a0d7bfa
Create Date: 2025-04-30 21:27:37.385897

"""
from alembic import op
import sqlalchemy as sa
# Remove unused import
# from sqlalchemy.dialects import postgresql 

# revision identifiers, used by Alembic.
revision = 'b8d832d608d3'
down_revision = 'e1062a0d7bfa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Commands adjusted manually ###
    print("Applying migration b8d832d608d3: Adding is_public and share_id to learning_paths")
    
    # Add columns to learning_paths table
    op.add_column('learning_paths', sa.Column('is_public', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('learning_paths', sa.Column('share_id', sa.String(), nullable=True))
    
    # Add required indexes for new columns
    # Use op.f() for potentially dynamically generated index names if preferred, 
    # but explicit names are fine too.
    op.create_index(op.f('ix_learning_paths_is_public'), 'learning_paths', ['is_public'], unique=False)
    op.create_index(op.f('ix_learning_paths_share_id'), 'learning_paths', ['share_id'], unique=True)

    # Optional: Add the specific partial index for PostgreSQL for optimized public lookups
    # This requires detecting the dialect, typical in env.py but can be done here conditionally
    # For simplicity, we'll add it directly here. If running on non-PostgreSQL, 
    # this might need adjustment or conditional logic.
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.create_index(
            'idx_learning_path_public_share_id', 
            'learning_paths', 
            ['share_id', 'is_public'], 
            unique=True, 
            postgresql_where=sa.text('is_public = true') # Use sa.text for where clause
        )
        print("Created PostgreSQL specific partial index for public paths.")
    else:
        # Create a regular index if not PostgreSQL (or handle other dialects)
        # Note: A combined index on (share_id, is_public) might still be useful
        op.create_index('idx_learning_path_public_share_id_fallback', 'learning_paths', ['share_id', 'is_public'], unique=False)
        print("Created fallback index for public paths (non-PostgreSQL).")

    print("Finished applying migration b8d832d608d3")
    # ### end adjusted commands ###


def downgrade() -> None:
    # ### Commands adjusted manually ###
    print("Reverting migration b8d832d608d3: Removing is_public and share_id from learning_paths")
    
    # Remove indexes first
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.drop_index('idx_learning_path_public_share_id', table_name='learning_paths', postgresql_where=sa.text('is_public = true'))
    else:
        op.drop_index('idx_learning_path_public_share_id_fallback', table_name='learning_paths')
        
    op.drop_index(op.f('ix_learning_paths_share_id'), table_name='learning_paths')
    op.drop_index(op.f('ix_learning_paths_is_public'), table_name='learning_paths')
    
    # Remove columns
    op.drop_column('learning_paths', 'share_id')
    op.drop_column('learning_paths', 'is_public')
    
    print("Finished reverting migration b8d832d608d3")
    # ### end adjusted commands ### 