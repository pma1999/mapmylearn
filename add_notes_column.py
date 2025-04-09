import os
import sqlite3

def add_notes_column():
    # Get the current working directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Define the path to the SQLite database
    # Adjust this path based on your actual database location
    db_path = os.path.join(current_dir, "learni.db")
    print(f"Looking for database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        # Try to find it
        for root, dirs, files in os.walk(current_dir):
            for file in files:
                if file.endswith(".db"):
                    print(f"Found database: {os.path.join(root, file)}")
        return
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table info to check if column exists
        cursor.execute("PRAGMA table_info(credit_transactions)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Existing columns: {columns}")
        
        if "notes" not in columns:
            print("Adding 'notes' column to credit_transactions table...")
            cursor.execute("ALTER TABLE credit_transactions ADD COLUMN notes VARCHAR")
            conn.commit()
            print("Column added successfully!")
        else:
            print("Column 'notes' already exists.")
        
        conn.close()
        print("Done!")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    add_notes_column() 