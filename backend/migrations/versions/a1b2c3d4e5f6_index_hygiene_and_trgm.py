"""index_hygiene_and_trgm

Revision ID: a1b2c3d4e5f6
Revises: 600fc48dcd34
Create Date: 2025-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '600fc48dcd34'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        # Use autocommit for CONCURRENTLY and CREATE EXTENSION
        with op.get_context().autocommit_block():
            # Ensure pg_trgm extension is available
            op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

            # Drop duplicate/legacy indexes if they exist
            op.execute("DROP INDEX IF EXISTS idx_user_email")
            op.execute("DROP INDEX IF EXISTS idx_session_token")
            op.execute("DROP INDEX IF EXISTS idx_learning_path_public_share_id")
            op.execute("DROP INDEX IF EXISTS idx_learning_path_public_share_id_fallback")

            # Create correct partial unique index for public sharing
            op.execute(
                "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_lp_public_share_id_true "
                "ON learning_paths (share_id, is_public) "
                "WHERE is_public = true"
            )

            # Create trigram GIN index for case-insensitive topic search
            op.execute(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learning_paths_topic_trgm "
                "ON learning_paths USING gin (lower(topic) gin_trgm_ops)"
            )
    else:
        # SQLite or other dialects: perform safe drops of duplicate indexes if present
        op.execute("DROP INDEX IF EXISTS idx_user_email")
        op.execute("DROP INDEX IF EXISTS idx_session_token")
        # Skip partial and trigram-specific indexes on non-PostgreSQL


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        with op.get_context().autocommit_block():
            # Drop trigram and corrected partial indexes
            op.execute("DROP INDEX IF EXISTS idx_learning_paths_topic_trgm")
            op.execute("DROP INDEX IF EXISTS idx_lp_public_share_id_true")

            # Recreate legacy indexes to restore previous state
            op.execute("CREATE INDEX IF NOT EXISTS idx_session_token ON sessions (refresh_token)")
            op.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON users (email)")
            op.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_path_public_share_id "
                "ON learning_paths (share_id, is_public) "
                "WHERE is_public = true"
            )
    else:
        # Recreate legacy indexes on non-PostgreSQL
        op.execute("CREATE INDEX IF NOT EXISTS idx_session_token ON sessions (refresh_token)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON users (email)")
