import os
from pathlib import Path
from dotenv import load_dotenv

print("Testing .env file loading...")

# Try to load from relative path
env_path = Path('.') / 'backend' / '.env'
print(f"Looking for .env file at: {env_path.absolute()}")
load_dotenv(dotenv_path=env_path)

# Try to load from current directory
if not os.getenv('LANGSMITH_PROJECT'):
    env_path = Path('.') / '.env'
    print(f"Second attempt: Looking for .env file at: {env_path.absolute()}")
    load_dotenv(dotenv_path=env_path)

# Check if variables loaded
print(f"LANGSMITH_TRACING: {os.getenv('LANGSMITH_TRACING')}")
print(f"LANGSMITH_PROJECT: {os.getenv('LANGSMITH_PROJECT')}")
print(f"LANGSMITH_API_KEY: {os.getenv('LANGSMITH_API_KEY')}")
print(f"LANGSMITH_ENDPOINT: {os.getenv('LANGSMITH_ENDPOINT')}") 