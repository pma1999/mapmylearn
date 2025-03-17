import os
import json
from pathlib import Path

# Define history file paths
DEFAULT_HISTORY_FILE = "learning_path_history.json"

def get_history_file_path():
    """
    Get the history file path based on the environment
    
    In production (Railway), we'll use the /data directory 
    which is a persistent volume
    """
    # Check if we're in a Railway environment
    if os.getenv("RAILWAY_STATIC_URL"):
        # Create data directory if it doesn't exist
        data_dir = Path("/data")
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / DEFAULT_HISTORY_FILE
    
    # Default to local file in development
    return DEFAULT_HISTORY_FILE 