import os
import sys
import time
import logging
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load .env to potentially get default URL, although we override it
dotenv_path_root = os.path.join(os.path.dirname(__file__), '.env')
dotenv_path_backend = os.path.join(os.path.dirname(__file__), 'backend', '.env')

if os.path.exists(dotenv_path_backend):
    load_dotenv(dotenv_path=dotenv_path_backend)
    print(f"Loaded .env from {dotenv_path_backend}")
elif os.path.exists(dotenv_path_root):
     load_dotenv(dotenv_path=dotenv_path_root)
     print(f"Loaded .env from {dotenv_path_root}")
else:
     print("Warning: .env file not found in standard locations.")


ALEMBIC_INI_PATH = 'backend/alembic.ini' # Relative to project root
SCRIPT_LOCATION = os.path.join(os.path.dirname(ALEMBIC_INI_PATH), 'migrations') 
# Load database URLs from environment variables
LOCAL_DB_URL = os.getenv('DATABASE_URL')
RAILWAY_DB_URL = os.getenv('RAILWAY_DB_URL')

if not LOCAL_DB_URL:
    logging.error("DATABASE_URL environment variable not set.")
    sys.exit(1)

if not RAILWAY_DB_URL:
    logging.error("RAILWAY_DB_URL environment variable not set.")
    sys.exit(1)

def run_upgrade(connection_string: str, revision: str = "head", set_env_var: bool = False):
    """Runs Alembic upgrade, optionally setting DATABASE_URL env var."""
    original_db_url_env = os.environ.get('DATABASE_URL') # Store original env var
    
    print(f"--- Running Alembic upgrade to '{revision}' for URL: {connection_string[:connection_string.find('@')]}@... ---")
    try:
        alembic_cfg = Config(ALEMBIC_INI_PATH)
        # Override settings programmatically
        alembic_cfg.set_main_option('sqlalchemy.url', connection_string)
        alembic_cfg.set_main_option('script_location', SCRIPT_LOCATION)
        
        # Temporarily set DATABASE_URL env var if requested
        if set_env_var:
            print(f"Temporarily setting DATABASE_URL environment variable for this command...")
            os.environ['DATABASE_URL'] = connection_string
            
        print(f"Using script location: {SCRIPT_LOCATION}")
        command.upgrade(alembic_cfg, revision)
        
        print(f"--- Successfully upgraded database to {revision} ---")
        
    except Exception as e:
        print(f"--- Error upgrading database: {e} ---")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original DATABASE_URL env var if it was changed
        if set_env_var:
            if original_db_url_env is None:
                # If it didn't exist before, remove it
                if 'DATABASE_URL' in os.environ:
                    del os.environ['DATABASE_URL']
                    print("Restored DATABASE_URL environment variable (removed).")
            else:
                # If it existed, restore its original value
                os.environ['DATABASE_URL'] = original_db_url_env
                print(f"Restored DATABASE_URL environment variable to original value.")
        # Cleanup script execution flag if set (optional)
        # if 'RUNNING_VIA_SCRIPT' in os.environ:
        #     del os.environ['RUNNING_VIA_SCRIPT']

def wait_for_db(db_url, retries=5, delay=5):
    # Implementation of wait_for_db function
    pass

if __name__ == "__main__":
    print("Applying migrations to LOCAL database ONLY...")
    
    # 1. Upgrade Local Database
    run_upgrade(LOCAL_DB_URL, "head", set_env_var=False)
    
    # 2. Upgrade Railway Database (temporarily set env var to force env.py)
    # print("\\n--- Skipping Railway DB upgrade for this run ---")
    # run_upgrade(RAILWAY_DB_URL, "head", set_env_var=True) 
    
    print("Migration process finished for local database.") 