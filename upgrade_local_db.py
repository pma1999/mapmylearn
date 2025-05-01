import os
import sys
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv

# Load .env to potentially get default URL if needed for config
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

ALEMBIC_INI_PATH = 'backend/alembic.ini' 
SCRIPT_LOCATION = os.path.join(os.path.dirname(ALEMBIC_INI_PATH), 'migrations') 
LOCAL_DB_URL = 'sqlite:///./learni.db'   # Relative to project root

DOWN_REVISION_TARGET = 'e1062a0d7bfa' # Revision before the one adding API key columns
UP_REVISION_TARGET = 'head'

def run_local_migration(revision: str):
    """Runs Alembic migration (upgrade or downgrade) targeting the local database."""
    print(f"--- Running Alembic migration to '{revision}' for LOCAL database: {LOCAL_DB_URL} ---")
    original_db_url_env = os.environ.get('DATABASE_URL') 
    
    try:
        alembic_cfg = Config(ALEMBIC_INI_PATH)
        alembic_cfg.set_main_option('sqlalchemy.url', LOCAL_DB_URL)
        alembic_cfg.set_main_option('script_location', SCRIPT_LOCATION)
        
        print(f"Temporarily setting DATABASE_URL environment variable...")
        os.environ['DATABASE_URL'] = LOCAL_DB_URL
            
        print(f"Using script location: {SCRIPT_LOCATION}")
        # Use command.upgrade or command.downgrade based on target
        if revision == "head" or ';' not in revision: # Simple upgrade or specific revision
            command.upgrade(alembic_cfg, revision)
            print(f"--- Successfully upgraded local database to {revision} ---")
        else: # Assuming downgrade if not head/specific rev
            command.downgrade(alembic_cfg, revision)
            print(f"--- Successfully downgraded local database to {revision} ---")
        
    except Exception as e:
        print(f"--- Error migrating local database: {e} ---")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original DATABASE_URL env var
        if original_db_url_env is None:
            if 'DATABASE_URL' in os.environ: del os.environ['DATABASE_URL']
        else:
            os.environ['DATABASE_URL'] = original_db_url_env
        print(f"Restored DATABASE_URL environment variable.")

if __name__ == "__main__":
    print(f"Step 1: Downgrading local DB to {DOWN_REVISION_TARGET}...")
    run_local_migration(DOWN_REVISION_TARGET)
    
    print(f"\nStep 2: Upgrading local DB back to {UP_REVISION_TARGET}...")
    run_local_migration(UP_REVISION_TARGET)
    
    print("\nLocal database migration process finished.") 