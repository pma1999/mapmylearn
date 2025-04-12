import os
import sys
from sqlalchemy import create_engine, text, inspect, Column, Boolean
from sqlalchemy.exc import OperationalError, ProgrammingError
from dotenv import load_dotenv

# Ensure the backend directory is in the Python path
# Assuming the script is run from the workspace root
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Load environment variables from backend/.env relative to workspace root
dotenv_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
if not os.path.exists(dotenv_path):
    print(f"Error: .env file not found at {dotenv_path}")
    # Attempt loading from current dir's .env as a fallback for different execution contexts
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(dotenv_path):
       print(f"Error: .env file also not found at {dotenv_path}")
       sys.exit(1)
    else:
       print(f"Warning: Loading .env from project root instead of backend folder: {dotenv_path}")
load_dotenv(dotenv_path=dotenv_path)


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found in the loaded .env file.")
    sys.exit(1)

# Basic check for common DB types to adjust syntax if needed, can be expanded
is_sqlite = DATABASE_URL.startswith("sqlite")
print(f"Detected Database Type (basic check): {'SQLite' if is_sqlite else 'Other (assuming PostgreSQL/MySQL)'}")


print(f"Connecting to database: {'SQLite file' if is_sqlite else DATABASE_URL.split('@')[-1]}...") # Mask credentials for non-sqlite

try:
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    table_name = "users"
    column_name = "is_email_verified"

    with engine.connect() as connection:
        with connection.begin(): # Start transaction
            print(f"Checking table '{table_name}' for column '{column_name}'...")

            columns = inspector.get_columns(table_name)
            column_exists = any(c['name'] == column_name for c in columns)

            if not column_exists:
                print(f"Column '{column_name}' not found. Adding column...")
                # Add the column. Defaulting works differently across DBs.
                # SQLAlchemy model default/server_default is better for ORM use.
                # For raw SQL, we add NOT NULL and handle default via update/app logic.
                add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} BOOLEAN NOT NULL DEFAULT false"
                if is_sqlite:
                    # SQLite accepts BOOLEAN but stores 0/1. Default value syntax is standard.
                     add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} BOOLEAN NOT NULL DEFAULT 0"

                try:
                    connection.execute(text(add_column_sql))
                    print(f"Column '{column_name}' added.")
                except (OperationalError, ProgrammingError) as e:
                     print(f"Error adding column: {e}")
                     print("Please check the SQL syntax for your specific database.")
                     raise e


                print("Marking all existing users as verified (backfill)...")
                # Update all users that existed before the column was added
                # Use 1 for true in SQLite, true otherwise
                true_val = "1" if is_sqlite else "true"
                update_sql = text(f"UPDATE {table_name} SET {column_name} = {true_val}")
                result = connection.execute(update_sql)
                print(f"{result.rowcount} existing users marked as verified.")
            else:
                print(f"Column '{column_name}' already exists.")
                print("Ensuring any unverified existing users are marked as verified...")
                # Ensure idempotency: update only those that might be false
                # Use 0 for false in SQLite, false otherwise
                false_val = "0" if is_sqlite else "false"
                true_val = "1" if is_sqlite else "true"
                update_sql = text(f"UPDATE {table_name} SET {column_name} = {true_val} WHERE {column_name} = {false_val}")
                result = connection.execute(update_sql)
                if result.rowcount > 0:
                    print(f"{result.rowcount} existing users marked as verified.")
                else:
                    print("No existing users needed updating.")

            print("Database update script completed successfully.")

except OperationalError as e:
    # Provide more specific guidance for common connection errors
    if "authentication failed" in str(e).lower():
         print(f"Database authentication failed: {e}")
         print("Please check your database username and password in the .env file.")
    elif "database" in str(e).lower() and "does not exist" in str(e).lower():
         print(f"Database does not exist: {e}")
         print("Please ensure the database specified in DATABASE_URL has been created.")
    elif "connection refused" in str(e).lower():
         print(f"Database connection refused: {e}")
         print("Please ensure the database server is running and accessible.")
    else:
        print(f"Error connecting to the database or executing SQL: {e}")
        print("Please check your DATABASE_URL in the .env file and ensure the database server is running.")
    sys.exit(1)
except Exception as e:
    import traceback
    print(f"An unexpected error occurred: {e}")
    print(traceback.format_exc()) # Print full traceback for debugging
    sys.exit(1)
