import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath("."))

try:
    from backend import api
    print("Successfully imported backend.api module!")
    
    from backend.models.models import LearningPathState
    print("Successfully imported models module!")
    
    from backend.services.services import get_llm
    print("Successfully imported services module!")
    
    print("All imports successful!")
except Exception as e:
    print(f"Import error: {str(e)}") 