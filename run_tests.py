import os
import sys
import pytest

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath("."))

if __name__ == "__main__":
    # Run pytest with any command line arguments passed to this script
    sys.exit(pytest.main(sys.argv[1:])) 