import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Database Connection ---
# Use the public proxy URL directly for reliability with `railway run`
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logging.error("Database URL is missing in the script!")
    sys.exit(1)

logging.info("Attempting to connect to the database...")

engine = None
try:
    engine = create_engine(DATABASE_URL)

    # --- Schema Inspection for users.id ---
    with engine.connect() as connection:
        logging.info("Database connection successful.")
        logging.info("Querying information_schema for 'users.id' column details...")

        # Query for id column details, including default and identity info
        query = text("""
            SELECT 
                column_name, 
                column_default, 
                is_nullable, 
                is_identity, 
                identity_generation
            FROM information_schema.columns
            WHERE table_schema = 'public'  -- Assuming default 'public' schema
            AND table_name = 'users'
            AND column_name = 'id';
        """)

        result = connection.execute(query)
        row = result.fetchone() # Expecting only one row for the 'id' column

        if not row:
            logging.warning("Could not find the 'id' column in the 'public.users' table.")
            sys.exit(0)

        print("\n--- Actual Schema for 'users.id' column ---")
        col_data = dict(row._mapping) # Convert RowProxy to dict-like
        print(f"Column:         {col_data.get('column_name')}")
        print(f"Is Nullable:    {col_data.get('is_nullable')}") # Should be 'NO'
        print(f"Column Default: {col_data.get('column_default')}") # EXPECTING something like nextval('users_id_seq'::regclass)
        print(f"Is Identity:    {col_data.get('is_identity')}") # Could be 'YES'
        print(f"Identity Gen:   {col_data.get('identity_generation')}") # e.g., 'BY DEFAULT'
        print("-" * 40)

except SQLAlchemyError as e:
    logging.error(f"Database connection or query failed:")
    logging.error(e)
    sys.exit(1)
except Exception as e:
    logging.error(f"An unexpected error occurred: {e}")
    sys.exit(1)
finally:
    if engine:
        engine.dispose()
        logging.info("Database engine disposed.")

print("\nID column verification script finished.") 