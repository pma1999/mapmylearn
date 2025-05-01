import sqlite3
import argparse
import os
import sys

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the database file relative to the script directory
db_path = os.path.join(script_dir, 'learni.db')

def execute_query(database_path, query):
    conn = None # Initialize conn to None
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        print(f"Executing query on {database_path}:")
        print(f"> {query}")
        
        cursor.execute(query)
        
        # If it's a SELECT statement, fetch and print results
        # Simple check, might not cover all SELECT variations (e.g., WITH clauses)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            if rows:
                # Print header
                colnames = [description[0] for description in cursor.description]
                print("\nResults:")
                print(" | ".join(colnames))
                print("-" * (sum(len(c) for c in colnames) + 3 * (len(colnames) - 1)))
                # Print rows
                for row in rows:
                    print(" | ".join(map(str, row)))
            else:
                print("\nQuery executed, no results returned.")
        else:
            # For non-SELECT statements (INSERT, UPDATE, DELETE, etc.), commit changes
            conn.commit()
            print(f"\nQuery executed successfully. {cursor.rowcount} rows affected.")
            
    except sqlite3.Error as e:
        print(f"\nAn error occurred: {e}")
    finally:
        # Close the connection
        if conn:
            conn.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    # Check if db exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)
        
    parser = argparse.ArgumentParser(description='Execute an SQL query on the learni.db database.')
    parser.add_argument('-q', '--query', required=True, help='The SQL query to execute.')
    
    args = parser.parse_args()
    
    execute_query(db_path, args.query) 