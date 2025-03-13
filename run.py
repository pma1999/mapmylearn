#!/usr/bin/env python3
"""
Learning Path Generator v2.2 - Launcher Script
This script provides a simple way to start the Learning Path Generator application.

The Learning Path Generator now includes advanced parallel processing capabilities to 
fully develop multiple modules simultaneously and execute multiple search queries
in parallel, significantly reducing overall generation time.
"""

import os
import sys
import subprocess
import webbrowser
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
    
    # Start the Streamlit app
    process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py"])
    
    # Wait a moment for Streamlit to start
    sleep(2)
    
    # Open the browser (Streamlit also does this, but just in case)
    webbrowser.open("http://localhost:8501")
    
    return process

if __name__ == "__main__":
    print("=== Learning Path Generator v2.2 ===")
    print("Enhanced with dual-layer parallel processing")
    
    # Check dependencies
    if not check_dependencies():
        print("Some dependencies are missing.")
        install = input("Do you want to install them now? (y/n): ").lower()
        if install == 'y':
            install_dependencies()
        else:
            print("Cannot proceed without required dependencies.")
            sys.exit(1)
    
    # Check API keys
    missing_keys = check_api_keys()
    if missing_keys:
        print(f"Warning: The following API keys are not set: {', '.join(missing_keys)}")
        print("You can still run the app and enter the keys in the web interface.")
    
    # Display information about the enhanced functionality
    print("\nNew Features in v2.2:")
    print("- Dual-layer parallel processing:")
    print("  1. Parallel search execution (multiple searches at once)")
    print("  2. Parallel module processing (multiple modules at once)")
    print("- User-configurable parallelism for both search and module processing")
    print("- Up to 75% faster generation with optimal settings")
    print("- Enhanced real-time progress tracking for all parallel operations")
    print("- Optimized resource usage and API call management")
    
    # Launch the app
    app_process = launch_app()
    
    try:
        # Keep the script running until the user presses Ctrl+C
        print("\nPress Ctrl+C to stop the application...\n")
        app_process.wait()
    except KeyboardInterrupt:
        print("\nStopping the application...")
        app_process.terminate()
        print("Application stopped.") 