#!/usr/bin/env python3
"""
Learning Path Generator v2.3 - FastAPI Launcher Script

This script verifies dependencies, checks API keys, and launches the FastAPI backend.
The backend (located in frontend/api/app.py) exposes all learning path generation
functionality via REST and WebSocket endpoints for consumption by the React frontend.
"""

import os
import sys
import subprocess
import argparse
import webbrowser
from time import sleep
from dotenv import load_dotenv

def check_dependencies():
    try:
        import fastapi
        import uvicorn
        import langchain
        import langgraph
        import pydantic
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False

def install_dependencies():
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Dependencies installed successfully.")

def check_api_keys():
    load_dotenv()
    missing_keys = []
    if not os.environ.get("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    if not os.environ.get("TAVILY_API_KEY"):
        missing_keys.append("TAVILY_API_KEY")
    return missing_keys

def launch_app():
    print("Starting Learning Path Generator FastAPI backend...")
    print("API available at http://localhost:8000")
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "frontend/api/app:app",
        "--reload", "--host", "0.0.0.0", "--port", "8000"
    ])
    sleep(2)
    return process

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Learning Path Generator FastAPI Launcher")
    args = parser.parse_args()

    print("=== Learning Path Generator v2.3 (FastAPI) ===")
    if not check_dependencies():
        print("Some dependencies are missing.")
        if input("Install now? (y/n): ").lower() == 'y':
            install_dependencies()
        else:
            sys.exit(1)
    
    missing_keys = check_api_keys()
    if missing_keys:
        print(f"Warning: Missing API keys: {', '.join(missing_keys)}")
        print("You can still run the backend and enter keys via the React app's settings.")
    
    app_process = launch_app()
    try:
        print("Press Ctrl+C to stop the backend...")
        app_process.wait()
    except KeyboardInterrupt:
        print("Stopping the backend...")
        app_process.terminate()
        print("Backend stopped.")
