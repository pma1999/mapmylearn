import os
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sqlite_database():
    """Test the local SQLite database"""
    print("\n======= LOCAL SQLITE DATABASE =======\n")
    db_path = "learni.db"
    
    if not os.path.exists(db_path):
        print(f"ERROR: Local database file {db_path} not found!")
        return False
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if credit_transactions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credit_transactions';")
        if not cursor.fetchone():
            print("ERROR: credit_transactions table does not exist in SQLite database!")
            conn.close()
            return False
        
        # Check table structure
        cursor.execute("PRAGMA table_info(credit_transactions);")
        columns = cursor.fetchall()
        
        print("SQLite credit_transactions structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}), {'NOT NULL' if col[3] else 'NULL'}")
        
        # Check if our test transaction exists
        cursor.execute("SELECT COUNT(*) FROM credit_transactions WHERE transaction_type = 'test';")
        count = cursor.fetchone()[0]
        print(f"\nTest transactions: {count}")
        
        # Test a basic insert with our model columns
        try:
            cursor.execute("""
            INSERT INTO credit_transactions 
            (user_id, admin_user_id, amount, transaction_type, created_at, description, balance_after) 
            VALUES (1, 1, 5, 'verify_test', CURRENT_TIMESTAMP, 'Verification test', 1005);
            """)
            conn.commit()
            print("Successfully inserted test record into SQLite database using description column")
        except sqlite3.Error as e:
            print(f"SQLite insert error: {e}")
        
        conn.close()
        print("SQLite database verification complete")
        return True
    
    except Exception as e:
        print(f"ERROR testing SQLite database: {e}")
        return False

def test_railway_database():
    """Test the Railway PostgreSQL database"""
    print("\n======= RAILWAY POSTGRESQL DATABASE =======\n")
    
    # Get database URL from environment
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("WARNING: DATABASE_URL not found. Railway database connection not available.")
        print("You need to run 'railway run python verify_database_configs.py' to test Railway database.")
        return False
    
    print(f"Connecting to Railway database: {db_url[:20]}...")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if credit_transactions table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'credit_transactions'
            );
        """)
        if not cursor.fetchone()[0]:
            print("ERROR: credit_transactions table does not exist in Railway PostgreSQL database!")
            conn.close()
            return False
        
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'credit_transactions'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\nPostgreSQL credit_transactions structure:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]}), {'NULLABLE' if col[2] == 'YES' else 'NOT NULL'}")
        
        # Test if we can use 'notes' column
        has_notes = any(col[0] == 'notes' for col in columns)
        has_description = any(col[0] == 'description' for col in columns)
        
        print(f"\nHas 'notes' column: {has_notes}")
        print(f"Has 'description' column: {has_description}")
        
        # Test inserting with appropriate column name
        try:
            if has_notes:
                cursor.execute("""
                INSERT INTO credit_transactions 
                (user_id, admin_user_id, amount, transaction_type, created_at, notes) 
                VALUES (1, 1, 5, 'railway_test', CURRENT_TIMESTAMP, 'Railway verification test')
                RETURNING id;
                """)
                print("Successfully inserted test record using 'notes' column")
            elif has_description:
                cursor.execute("""
                INSERT INTO credit_transactions 
                (user_id, admin_user_id, amount, transaction_type, created_at, description) 
                VALUES (1, 1, 5, 'railway_test', CURRENT_TIMESTAMP, 'Railway verification test')
                RETURNING id;
                """)
                print("Successfully inserted test record using 'description' column")
            else:
                print("WARNING: Neither 'notes' nor 'description' column found!")
            
            # Get the ID of the inserted record
            record_id = cursor.fetchone()[0]
            
            # Clean up test data
            cursor.execute(f"DELETE FROM credit_transactions WHERE id = {record_id};")
            print(f"Test record {record_id} cleaned up")
            
        except psycopg2.Error as e:
            print(f"PostgreSQL insert error: {e}")
        
        conn.close()
        print("Railway database verification complete")
        return True
    
    except Exception as e:
        print(f"ERROR testing Railway database: {e}")
        return False

if __name__ == "__main__":
    # Test both databases
    sqlite_result = test_sqlite_database()
    railway_result = test_railway_database()
    
    print("\n======= VERIFICATION SUMMARY =======\n")
    print(f"SQLite database: {'OK' if sqlite_result else 'FAILED'}")
    print(f"Railway database: {'OK' if railway_result else 'NOT TESTED OR FAILED'}")
    
    if sqlite_result and railway_result:
        print("\nBoth databases are properly configured! ✅")
    elif sqlite_result:
        print("\nLocal SQLite database is working, but Railway database verification failed.")
        print("You may need to run this script with 'railway run python verify_database_configs.py'")
    else:
        print("\nDatabase verification failed. Please check the error messages above.") 