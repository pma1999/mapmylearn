import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath("."))

if __name__ == "__main__":
    import uvicorn
    
    # Print debugging information
    port_env = os.environ.get("PORT", "8000")
    print(f"PORT environment variable: {port_env}")
    
    try:
        port = int(port_env)
        print(f"Converted PORT to integer: {port}")
        # Run the app with the correct module path
        uvicorn.run("backend.api:app", host="0.0.0.0", port=port)
    except ValueError as e:
        print(f"Error converting PORT to integer: {e}")
        # Fallback to default port
        print("Using default port 8000")
        uvicorn.run("backend.api:app", host="0.0.0.0", port=8000) 