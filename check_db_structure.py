import sqlalchemy
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import NoSuchTableError, OperationalError
import os
import sys

# Target the local DB file
DB_PATH = 'learni.db'
DB_URL = f'sqlite:///{DB_PATH}' 
DB_NAME_FOR_PRINTING = f"Local SQLite DB ({DB_PATH})"

def check_table_structure(table_name: str):
    print(f"--- Checking structure of table '{table_name}' in {DB_NAME_FOR_PRINTING} ---")

    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return
        
    try:
        engine = create_engine(DB_URL)
        inspector = inspect(engine)
        
        print(f"Attempting to connect to: {DB_URL}")
        
        with engine.connect() as connection:
            print("Connection successful.")
            
            # Check if the table exists
            if not inspector.has_table(table_name):
                print(f"Error: Table '{table_name}' does not exist in the database.")
                print("\nTables found in the database:")
                try:
                    tables = inspector.get_table_names()
                    if tables:
                        for t in tables:
                            print(f"- {t}")
                    else:
                        print("(No tables found)")
                except Exception as list_e:
                    print(f"(Could not list tables: {list_e})")
                return

            print(f"\nColumns found in table '{table_name}':")
            columns = inspector.get_columns(table_name)
            if columns:
                for column in columns:
                    print(f"- Name: {column['name']}, Type: {column['type']}, Nullable: {column['nullable']}")
            else:
                print("(No columns found - this shouldn't happen if table exists)")

    except OperationalError as e:
        print(f"\nError connecting to or querying the database: {e}")
        print("Check connection string, network access, and database status.")
    # Remove DBAPIError handling specific to PostgreSQL
    # except DBAPIError as e:
    #     if "authentication failed" in str(e).lower():
    #          print(f"\nAuthentication failed. Please check the database credentials.")
    #     else:
    #         print(f"\nDatabase API Error: {e}")
    except NoSuchTableError:
        print(f"Error: Table '{table_name}' does not exist (NoSuchTableError).")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_table_structure('users')
    print("\n--- Check complete ---") 