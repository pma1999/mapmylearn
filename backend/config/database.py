from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# Get database connection details from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is not set, create a default SQLite database for development
if not DATABASE_URL:
    # Default to SQLite for easier development
    sqlite_db_path = os.path.join(os.getcwd(), "learny.db")
    DATABASE_URL = f"sqlite:///{sqlite_db_path}"
    print(f"Using SQLite database at: {sqlite_db_path}")
elif DATABASE_URL.startswith("postgres"):
    # Handle PostgreSQL URLs with potential password encoding issues
    try:
        # If there are special characters in the password, they need to be encoded
        if "@" in DATABASE_URL:
            prefix, rest = DATABASE_URL.split("://")
            auth, server = rest.split("@")
            if ":" in auth:
                user, password = auth.split(":")
                # URL encode the password to handle special characters
                password = quote_plus(password)
                DATABASE_URL = f"{prefix}://{user}:{password}@{server}"
    except Exception as e:
        print(f"Warning: Error processing DATABASE_URL: {e}")
        # Fall back to SQLite if there's an issue
        sqlite_db_path = os.path.join(os.getcwd(), "learny.db")
        DATABASE_URL = f"sqlite:///{sqlite_db_path}"
        print(f"Falling back to SQLite database at: {sqlite_db_path}")

# Create SQLAlchemy engine with appropriate settings
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific settings: enable foreign key constraints
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
else:
    # PostgreSQL or other database engines
    engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10, echo=False)

print(f"Using database: {DATABASE_URL}")

# Create SessionLocal class for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = declarative_base()

# Dependency to get the database session
def get_db():
    """
    Dependency function to get a database session.
    Used in FastAPI route dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 