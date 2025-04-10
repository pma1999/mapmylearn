import psycopg2
import os

# Get DATABASE_URL from environment variable
db_url = 'postgresql://postgres:TyZfITXwCzSldTsWAbWQAgFGpIwfeyDe@interchange.proxy.rlwy.net:22907/railway'

try:
    # Connect to the database
    conn = psycopg2.connect(db_url)
    
    # Create a cursor
    cur = conn.cursor()
    
    # Query the columns of credit_transactions table
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'credit_transactions' 
        ORDER BY ordinal_position;
    """)
    
    # Print the column names
    print("Columns in credit_transactions table:")
    columns = [row[0] for row in cur.fetchall()]
    for col in columns:
        print(f"- {col}")
    
    # Check if balance_after column exists
    if 'balance_after' not in columns:
        print("\nMISSING COLUMN: 'balance_after' does not exist in the credit_transactions table!")
        
    # Close the cursor and connection
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}") 