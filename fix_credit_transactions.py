import os
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_credit_transactions_table():
    """
    Adds the missing 'notes' column to the credit_transactions table in SQLite database.
    """
    # Get database path from environment or use default
    db_path = os.environ.get("DATABASE_URL", "sqlite:///./app.db")
    
    # If using SQLite URL format, extract the file path
    if db_path.startswith("sqlite:///"):
        db_path = db_path[10:]
    
    logger.info(f"Using database at: {db_path}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the notes column already exists
        cursor.execute("PRAGMA table_info(credit_transactions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "notes" not in columns:
            logger.info("Adding 'notes' column to credit_transactions table...")
            
            # Add the notes column
            cursor.execute("ALTER TABLE credit_transactions ADD COLUMN notes VARCHAR")
            
            # Commit the changes
            conn.commit()
            logger.info("Successfully added 'notes' column!")
        else:
            logger.info("The 'notes' column already exists in credit_transactions table.")
        
        conn.close()
        logger.info("Database connection closed.")
        
        return True
    except Exception as e:
        logger.error(f"Error fixing credit_transactions table: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_credit_transactions_table()
    if success:
        print("Credit transactions table fixed successfully!")
    else:
        print("Failed to fix credit transactions table. Check the logs for details.") 