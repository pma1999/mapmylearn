import os
import sys

# Add the backend directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
sys.path.append(backend_dir)

# Import the database and model
from backend.config.database import engine, SessionLocal, get_db
from backend.models.auth_models import User, CreditTransaction
# Import the password hashing function
from backend.utils.auth import get_password_hash
from sqlalchemy.orm import Session
import datetime

def _ensure_test_admin(db: Session) -> User:
    """
    Finds an existing admin user or creates a new one for testing.
    Uses dynamic password hashing.
    """
    admin_user = db.query(User).filter(User.is_admin == True).first()
    
    if not admin_user:
        print("No admin user found. Creating one for testing...")
        # Use a clear test password and hash it dynamically
        test_password = "test_admin_password_123!" 
        hashed_password = get_password_hash(test_password)
        
        admin_user = User(
            email="admin_test@example.com", # Use a distinct email for tests
            hashed_password=hashed_password,
            full_name="Test Admin User",
            is_active=True,
            is_admin=True,
            is_email_verified=True, # Assume verified for tests
            credits=1000,
            created_at=datetime.datetime.now(datetime.timezone.utc) # Use timezone-aware datetime
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Created test admin user: {admin_user.email}")
        
    return admin_user

def test_add_credit_transaction():
    """
    Test adding a credit transaction with notes.
    Uses a helper function to get/create the admin user.
    """
    print("Testing credit transaction creation...")
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Get or create the test admin user using the helper
        admin_user = _ensure_test_admin(db)
        
        # Create a test transaction
        transaction = CreditTransaction(
            user_id=admin_user.id,
            admin_user_id=admin_user.id, # Admin assigns credits to themselves in this test case
            amount=10,
            transaction_type="test_grant", # More specific type
            notes="Test transaction grant", 
            balance_after=admin_user.credits + 10, # Note: This assumes no concurrent changes
            created_at=datetime.datetime.now(datetime.timezone.utc) # Use timezone-aware datetime
        )
        
        # Add transaction and update user credits (in a real scenario, this should be atomic)
        admin_user.credits += transaction.amount # Manually update for balance_after calculation correctness ( ideally handled by a service layer)
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        db.refresh(admin_user) # Refresh admin user to get updated credits if needed elsewhere
        
        print(f"Created transaction: ID={transaction.id}, Amount={transaction.amount}, Notes={transaction.notes}, New Balance: {admin_user.credits}")
        print("Test completed successfully!")
        
        # Optional: Add an assertion
        assert transaction.id is not None
        assert transaction.notes == "Test transaction grant"
        assert admin_user.credits == transaction.balance_after # Verify balance calculation
        
        return True
    
    except Exception as e:
        print(f"Error during test: {str(e)}")
        db.rollback()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    if test_add_credit_transaction():
        print("Test passed.")
    else:
        print("Test failed.")
        sys.exit(1) # Indicate failure 