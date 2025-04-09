import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def test_railway_connection():
    """Test connection to Railway PostgreSQL database"""
    # Railway sets DATABASE_URL automatically in the environment
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: No DATABASE_URL environment variable found.")
        print("Please ensure you're running this script in the Railway environment or have the DATABASE_URL set.")
        return False
    
    if not db_url.startswith("postgres"):
        print(f"WARNING: Non-PostgreSQL connection string detected: {db_url[:10]}...")
        print("This script is intended for testing Railway PostgreSQL connections.")
    
    print(f"Connecting to database: {db_url[:20]}...")
    
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL version: {version[0]}")
        
        # Check if credit_transactions table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'credit_transactions'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("credit_transactions table exists.")
            
            # Check table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'credit_transactions'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print("\nTable structure:")
            for col in columns:
                print(f"  - {col[0]} ({col[1]}), {'NULLABLE' if col[2] == 'YES' else 'NOT NULL'}")
            
            # Check sample data (limited to avoid large results)
            cursor.execute("SELECT COUNT(*) FROM credit_transactions;")
            count = cursor.fetchone()[0]
            print(f"\nTotal records: {count}")
            
            if count > 0:
                cursor.execute("""
                    SELECT id, user_id, admin_user_id, amount, transaction_type, created_at 
                    FROM credit_transactions LIMIT 3;
                """)
                rows = cursor.fetchall()
                print("\nSample data:")
                for row in rows:
                    print(f"  - ID: {row[0]}, User: {row[1]}, Amount: {row[3]}, Type: {row[4]}")
        else:
            print("WARNING: credit_transactions table does not exist in the Railway database.")
        
        conn.close()
        print("Database connection closed successfully.")
        return True
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_railway_connection() 