#!/usr/bin/env python3
"""
Learning Path Generator v2.3 - Launcher Script

This script provides a simple way to start the Learning Path Generator application.
It verifies dependencies, checks API keys, and launches the Streamlit app.
"""

import os
import sys
import subprocess
import webbrowser
import argparse
from time import sleep
from dotenv import load_dotenv

def check_dependencies():
    """Check if all required packages are installed."""
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
    """Install required packages."""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Dependencies installed successfully.")

def check_api_keys():
    """Check if API keys are set."""
    load_dotenv()
    missing_keys = []
    if not os.environ.get("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    if not os.environ.get("TAVILY_API_KEY"):
        missing_keys.append("TAVILY_API_KEY")
    return missing_keys

def launch_app():
    """Launch the Streamlit app."""
    print("Starting Learning Path Generator...")
    print("The application will open in your web browser.")
    process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py"])
    sleep(2)
    webbrowser.open("http://localhost:8501")
    return process

def launch_debug_mode(topic=None):
    """Launch the application in debug mode."""
    print("Starting Learning Path Generator in DEBUG mode...")
    debug_args = ["python", "debug_learning_path.py"]
    
    if topic:
        debug_args.append(topic)
    else:
        debug_args.append("Python programming for beginners")  # Default topic for debugging
    
    debug_args.extend(["--log-level", "DEBUG", "--analyze-logs", "--save-result"])
    
    # Run the debug process in the foreground
    print(f"Executing: {' '.join(debug_args)}")
    subprocess.call(debug_args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Learning Path Generator Launcher")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--topic", help="Specify a topic when running in debug mode")
    args = parser.parse_args()

    print("=== Learning Path Generator v2.3 ===")
    print("Enhanced with dual-layer parallel processing & diagnostics")
    
    if not check_dependencies():
        print("Some dependencies are missing.")
        install = input("Do you want to install them now? (y/n): ").lower()
        if install == 'y':
            install_dependencies()
        else:
            print("Cannot proceed without required dependencies.")
            sys.exit(1)
    
    missing_keys = check_api_keys()
    if missing_keys:
        print(f"Warning: The following API keys are not set: {', '.join(missing_keys)}")
        print("You can still run the app and enter the keys in the web interface.")
    
    if args.debug:
        print("\nRunning in DEBUG MODE")
        print("This mode enables detailed logging and diagnostics")
        launch_debug_mode(args.topic)
    else:
        print("\nFeatures in v2.3:")
        print("- Dual-layer parallel processing:")
        print("  1. Parallel search execution (multiple searches at once)")
        print("  2. Parallel module processing (multiple modules at once)")
        print("- Enhanced diagnostic tools (run with --debug to access)")
        print("- Up to 75% faster generation with optimal settings")
        print("- Enhanced real-time progress tracking for all parallel operations")
        print("- Optimized resource usage and API call management")
        
        app_process = launch_app()
        
        try:
            print("\nPress Ctrl+C to stop the application...\n")
            app_process.wait()
        except KeyboardInterrupt:
            print("\nStopping the application...")
            app_process.terminate()
            print("Application stopped.")
