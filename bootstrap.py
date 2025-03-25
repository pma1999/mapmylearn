import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath("."))

if __name__ == "__main__":
    import uvicorn
    # Run the app with the correct module path
    uvicorn.run("backend.api:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000))) 