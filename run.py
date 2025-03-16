#!/usr/bin/env python3
"""
Learning Path Generator v2.3 - Launcher Script

This script verifies dependencies, checks API keys, and launches the Streamlit app.
"""

import os
import sys
import subprocess
import webbrowser
import argparse
from time import sleep
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
    print("Starting Learning Path Generator...")
    print("The application will open in your web browser.")
    process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "ui/app.py"])
    sleep(2)
    webbrowser.open("http://localhost:8501")
    return process

def launch_debug_mode(topic=None):
    print("Starting Learning Path Generator in DEBUG mode...")
    debug_args = ["python", "debug_learning_path.py"]
    debug_args.append(topic if topic else "Python programming for beginners")
    debug_args.extend(["--log-level", "DEBUG", "--analyze-logs", "--save-result"])
    print(f"Executing: {' '.join(debug_args)}")
    subprocess.call(debug_args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Learning Path Generator Launcher")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--topic", help="Specify a topic when running in debug mode")
    args = parser.parse_args()

    print("=== Learning Path Generator v2.3 ===")
    if not check_dependencies():
        print("Some dependencies are missing.")
        if input("Install now? (y/n): ").lower() == 'y':
            install_dependencies()
        else:
            sys.exit(1)
    
    missing_keys = check_api_keys()
    if missing_keys:
        print(f"Warning: Missing API keys: {', '.join(missing_keys)}")
        print("You can still run the app and enter keys in the web interface.")
    
    if args.debug:
        launch_debug_mode(args.topic)
    else:
        app_process = launch_app()
        try:
            print("Press Ctrl+C to stop the application...")
            app_process.wait()
        except KeyboardInterrupt:
            print("Stopping the application...")
            app_process.terminate()
            print("Application stopped.")
