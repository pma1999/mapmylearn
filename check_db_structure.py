import sqlite3
import os

def check_sqlite_db_structure():
    db_path = "learni.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List all tables
    print("Tables in the database:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check credit_transactions table structure
    print("\nStructure of credit_transactions table:")
    cursor.execute("PRAGMA table_info(credit_transactions);")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]}), {'NOT NULL' if col[3] else 'NULL'}")
    
    # Check for indexes
    print("\nIndexes on credit_transactions:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='credit_transactions';")
    indexes = cursor.fetchall()
    for idx in indexes:
        print(f"  - {idx[0]}")
    
    # Sample data from credit_transactions
    print("\nSample data from credit_transactions:")
    try:
        cursor.execute("SELECT * FROM credit_transactions LIMIT 3;")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"  - {row}")
        else:
            print("  (No data)")
    except sqlite3.Error as e:
        print(f"  Error fetching data: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_sqlite_db_structure() 