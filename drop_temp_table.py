import sqlite3
import os

LOCAL_DB_PATH = 'learni.db'
TEMP_TABLE_NAME = '_alembic_tmp_credit_transactions'

def drop_temp_table():
    print(f"--- Attempting to drop temporary table {TEMP_TABLE_NAME} from {LOCAL_DB_PATH} ---")
    
    if not os.path.exists(LOCAL_DB_PATH):
        print(f"Error: Database file not found at {LOCAL_DB_PATH}")
        return

    conn = None
    try:
        conn = sqlite3.connect(LOCAL_DB_PATH)
        cursor = conn.cursor()
        
        print(f"Executing: DROP TABLE IF EXISTS {TEMP_TABLE_NAME};")
        cursor.execute(f"DROP TABLE IF EXISTS {TEMP_TABLE_NAME};")
        conn.commit()
        print(f"Successfully dropped table {TEMP_TABLE_NAME} (if it existed).")
        
    except sqlite3.Error as e:
        print(f"\nError interacting with the database: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    drop_temp_table()
    print("\n--- Drop temporary table script finished ---") 