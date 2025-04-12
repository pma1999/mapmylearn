import os
import sys
import logging
from alembic.config import Config
from alembic import command # Ensure this is imported
from sqlalchemy.exc import SQLAlchemyError # Ensure this is imported

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
ALEMBIC_INI_PATH = os.path.join(BACKEND_DIR, "alembic.ini")
SCRIPT_LOCATION = os.path.join(BACKEND_DIR, "migrations")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- Add backend to sys.path ---
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
    logging.info(f"Added {BACKEND_DIR} to sys.path")

# --- Alembic Setup ---
logging.info(f"Using Alembic config: {ALEMBIC_INI_PATH}")
logging.info(f"Using migration script location: {SCRIPT_LOCATION}")

if not os.path.exists(ALEMBIC_INI_PATH):
    logging.error(f"Alembic config file not found at: {ALEMBIC_INI_PATH}")
    sys.exit(1)
if not os.path.exists(SCRIPT_LOCATION):
    logging.error(f"Alembic script location not found at: {SCRIPT_LOCATION}")
    sys.exit(1)

alembic_cfg = Config(ALEMBIC_INI_PATH)
alembic_cfg.set_main_option("script_location", SCRIPT_LOCATION)
alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

# --- Run Upgrade ---
logging.info(f"Attempting to upgrade database to revision 'manual_make_id_identity'...")

os.environ['RUNNING_VIA_SCRIPT'] = 'true'

try:
    # Run Alembic upgrade command programmatically to the specific revision
    command.upgrade(alembic_cfg, "manual_make_id_identity")
    logging.info("Database upgrade completed successfully.")
except SQLAlchemyError as e:
    logging.error(f"Database connection error during migration: {e}")
    sys.exit(1)
except Exception as e:
    logging.error(f"An error occurred during migration: {e}")
    sys.exit(1)
finally:
    os.environ.pop('RUNNING_VIA_SCRIPT', None)
    logging.info("Migration script finished.") 