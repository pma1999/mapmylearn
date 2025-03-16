#!/usr/bin/env python3
"""
Learning Path Generator v2.3 - Streamlit App Launcher

This script provides a simple way to start the Learning Path Generator Streamlit application.
"""

import os
import sys
import subprocess
import webbrowser
import time
import platform
from dotenv import load_dotenv

def check_dependencies():
    try:
        import streamlit
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
    print("\n=== Starting Learning Path Generator ===")
    print("The application will open in your web browser.\n")
    cmd = [sys.executable, "-m", "streamlit", "run", "ui/app.py"]
    process = subprocess.Popen(cmd)
    time.sleep(2)
    webbrowser.open("http://localhost:8501")
    print("\nLearning Path Generator is running!")
    print("Press Ctrl+C to stop the application.")
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nStopping the application...")
        process.terminate()
        print("Application stopped.")

if __name__ == "__main__":
    print("\n=== Learning Path Generator v2.3 ===")
    if not check_dependencies():
        print("\nSome dependencies are missing.")
        if input("Install now? (y/n): ").lower() == 'y':
            install_dependencies()
        else:
            sys.exit(1)
    
    missing_keys = check_api_keys()
    if missing_keys:
        print(f"\nNote: Missing API keys: {', '.join(missing_keys)}")
        print("You can still run the app and enter the keys in the settings page.\n")
    
    print("""
Features in v2.3:
- Dual-layer parallel processing:
  1. Parallel search execution.
  2. Parallel module processing.
- Enhanced UI with module/submodule navigation.
- Real-time progress tracking.
- Download options for JSON and Markdown.
    """)
    
    launch_app()
