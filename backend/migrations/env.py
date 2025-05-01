import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv
import sys # Import sys

# Adjust prepend_sys_path based on CWD
# If running from root ('Learni'), path is 'backend'. If from 'backend', path is '.'
if os.path.basename(os.getcwd()) == 'Learni':
    sys.path.insert(0, 'backend')
else:
    # Assuming execution from 'backend' directory or similar
    sys.path.insert(0, '.')


# Load .env file relative to the project root if possible
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env') # Go up from migrations/ to backend/ to root/
if not os.path.exists(dotenv_path):
    # Try loading .env from the current working directory as a fallback
    dotenv_path = os.path.join(os.getcwd(), '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Loaded .env file from: {dotenv_path}")
else:
    print("Warning: .env file not found.")


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Centralized Database URL Configuration
sqlalchemy_url = None
if os.getenv('RUNNING_VIA_SCRIPT') == 'true':
    sqlalchemy_url = config.get_main_option("sqlalchemy.url")
    if sqlalchemy_url: print(f"Detected RUNNING_VIA_SCRIPT flag. Using URL from config: {sqlalchemy_url}")
else:
    sqlalchemy_url = os.getenv("DATABASE_URL")
    if sqlalchemy_url:
        print(f"Using DATABASE_URL from environment: {sqlalchemy_url}")
    else:
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        db_path = os.path.join(project_root, 'learni.db')
        sqlalchemy_url = f"sqlite:///{db_path}"
        print(f"DATABASE_URL not set. Falling back to local SQLite: {sqlalchemy_url}")

if sqlalchemy_url:
    config.set_main_option("sqlalchemy.url", sqlalchemy_url)
else:
    raise ValueError("Could not determine database URL for Alembic.")


# Interpret the config file for Python logging.
# Suppress logging setup if running via script, assuming script handles it
if config.config_file_name is not None and not os.getenv('RUNNING_VIA_SCRIPT') == 'true':
    try:
        fileConfig(config.config_file_name)
    except Exception as e:
        print(f"Warning: Could not configure logging from alembic.ini: {e}")


# Add model MetaData objects here for autogenerate support
# Import Base from the correct location
try:
    # Assumes models are accessible via the adjusted sys.path
    from models.auth_models import Base
    # Add other Base imports if necessary, e.g., from models.models if it had SQLAlchemy models
    # from models.models import Base as PydanticBase # Example if needed, adjust name
    print("Successfully imported Base from models.auth_models")
except ImportError as e:
    print(f"Error importing Base from models.auth_models: {e}")
    print("Please ensure Alembic is run from the 'backend' directory or the project root directory ('Learni').")
    # Make target_metadata None or raise an error if Base cannot be imported
    # This prevents autogenerate from running with incorrect metadata
    target_metadata = None
    # Optionally raise the error to stop execution:
    # raise ImportError("Failed to import SQLAlchemy Base. Check execution directory and sys.path.") from e
else:
    # target_metadata should reference the SQLAlchemy Base's metadata
    target_metadata = Base.metadata
    # If you had multiple Bases (e.g., Base1, Base2), you would list them:
    # target_metadata = [Base1.metadata, Base2.metadata]

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Use the centrally configured URL
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise ValueError("Database URL not configured for offline mode.")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Include compare_type=True for SQLite type comparison during autogenerate
        compare_type=True if url.startswith('sqlite') else False,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Use the centrally configured URL
    effective_url = config.get_main_option("sqlalchemy.url")
    if not effective_url:
        raise ValueError("Database URL not configured for online mode.")

    # Create engine configuration using the effective URL
    engine_config = config.get_section(config.config_ini_section, {})
    engine_config['sqlalchemy.url'] = effective_url # Ensure the engine uses the correct URL

    connectable = engine_from_config(
        engine_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Include compare_type=True for SQLite type comparison during autogenerate
            compare_type=True if effective_url.startswith('sqlite') else False,
            render_as_batch=effective_url.startswith('sqlite') # Enable batch mode for SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


# Check if target_metadata was successfully loaded before proceeding
if target_metadata is None:
    print("Error: target_metadata not set due to import failure. Cannot run migrations.")
    # Optionally exit or raise an error more formally
    # sys.exit(1)
else:
    if context.is_offline_mode():
        print("Running migrations in offline mode...")
        run_migrations_offline()
    else:
        print("Running migrations in online mode...")
        run_migrations_online() 