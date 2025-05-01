import os
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv

# Load .env to potentially get default URL, although we override it
# Assume .env is in the parent directory (project root) relative to this script if run from root
# Or in the current dir if run from backend/
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
# Calculate absolute path to script location relative to INI file
# INI is in backend/, migrations is in backend/migrations/
SCRIPT_LOCATION = os.path.join(os.path.dirname(ALEMBIC_INI_PATH), 'migrations') 
LOCAL_DB_URL = 'sqlite:///./learni.db'   # Relative to project root where learni.db is
REVISION_TO_STAMP = 'b8d832d608d3' # The revision ID of the existing script

def stamp_database(connection_string: str, revision: str):
    """Stamps the database to a specific revision using Alembic commands."""
    print(f"Stamping database to revision: {revision} using URL: {connection_string}")
    try:
        alembic_cfg = Config(ALEMBIC_INI_PATH)
        # IMPORTANT: Override settings programmatically
        alembic_cfg.set_main_option('sqlalchemy.url', connection_string)
        # Set script location relative to the INI file's directory
        alembic_cfg.set_main_option('script_location', SCRIPT_LOCATION)
        
        # Indicate script execution to env.py (optional, depends on env.py logic)
        # os.environ['RUNNING_VIA_SCRIPT'] = 'true' 
        
        # Run the stamp command
        print(f"Using script location: {SCRIPT_LOCATION}")
        command.stamp(alembic_cfg, revision)
        
        print(f"Successfully stamped database to revision {revision}")
        
    except Exception as e:
        print(f"Error stamping database: {e}")
        import traceback
        traceback.print_exc()
    # finally:
        # Cleanup environment variable if set
        # if 'RUNNING_VIA_SCRIPT' in os.environ:
        #     del os.environ['RUNNING_VIA_SCRIPT']

if __name__ == "__main__":
    # Check if the target revision script exists before stamping
    migration_script_path = os.path.join(SCRIPT_LOCATION, 'versions', f'{REVISION_TO_STAMP}_add_public_sharing_to_learning_paths.py')
    if not os.path.exists(migration_script_path):
        print(f"Error: Migration script for revision {REVISION_TO_STAMP} not found at {migration_script_path}")
    else:
        print(f"Found migration script: {migration_script_path}")
        stamp_database(LOCAL_DB_URL, REVISION_TO_STAMP) 