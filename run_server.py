import os
import sys
import uvicorn
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath("."))

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Import and run the API server
    from backend.api import app
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=port) 