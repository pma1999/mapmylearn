import argparse
import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import func
from dotenv import load_dotenv
import logging

# Add the project root to the Python path to allow importing backend modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import backend modules
try:
    from backend.config.database import SessionLocal, engine, Base # Use SessionLocal for script session
    from backend.models.auth_models import User, CreditTransaction
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    print("Ensure the script is run from the project root or the PYTHONPATH is set correctly.")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_initial_admin(email: str):
    """Creates the initial admin user if none exists."""
    db: Session = SessionLocal()
    try:
        # Check if any admin users already exist
        existing_admin = db.query(User).filter(User.is_admin == True).first()
        if existing_admin:
            logger.error(f"An admin user already exists ({existing_admin.email}). Cannot use initial creation tool.")
            return False

        # Find the user by the provided email
        user = db.query(User).filter(func.lower(User.email) == func.lower(email)).first()
        if not user:
            logger.error(f"User with email '{email}' not found. Please ensure the user is registered first.")
            return False

        # Promote the user to admin
        user.is_admin = True
        logger.info(f"Promoting user '{email}' to admin.")

        # Grant initial credits (optional, matching previous behavior)
        initial_credits = 50
        if user.credits is None: # Handle case where credits might be NULL
            user.credits = 0
        new_balance = user.credits + initial_credits
        user.credits = new_balance
        logger.info(f"Granting {initial_credits} initial credits. New balance: {new_balance}")

        # Create a credit transaction record
        transaction = CreditTransaction(
            user_id=user.id,
            amount=initial_credits,
            transaction_type="system_add",
            notes="Initial admin creation via CLI",
            balance_after=new_balance # Use the calculated new balance
        )
        db.add(transaction)

        db.commit()
        logger.info(f"Successfully promoted user '{email}' to admin with initial credits.")
        return True

    except Exception as e:
        db.rollback()
        logger.exception(f"An error occurred during initial admin creation for '{email}': {e}")
        return False
    finally:
        db.close()

def main():
    # Load environment variables from .env file, useful for local execution
    load_dotenv()

    # Ensure database connection URL is set (needed by SessionLocal)
    if not os.environ.get("DATABASE_URL"):
        logger.error("DATABASE_URL environment variable not set.")
        sys.exit(1)
        
    # Create the database tables if they don't exist (optional, but good for standalone scripts)
    # Comment out if migrations handle table creation exclusively
    # Base.metadata.create_all(bind=engine)

    parser = argparse.ArgumentParser(description="Admin management utility for Learnì.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Subparser for creating the initial admin
    parser_create = subparsers.add_parser("create-initial", help="Create the first admin user.")
    parser_create.add_argument("--email", required=True, help="Email address of the user to promote.")

    args = parser.parse_args()

    if args.command == "create-initial":
        logger.info(f"Attempting to create initial admin user: {args.email}")
        if not create_initial_admin(args.email):
            sys.exit(1) # Exit with error code if creation failed
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 