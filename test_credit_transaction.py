import os
import sys

# Add the backend directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
sys.path.append(backend_dir)

# Import the database and model
from backend.config.database import engine, SessionLocal, get_db
from backend.models.auth_models import User, CreditTransaction
from sqlalchemy.orm import Session
import datetime

def test_add_credit_transaction():
    """
    Test adding a credit transaction with notes
    """
    print("Testing credit transaction creation...")
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Get an admin user
        admin_user = db.query(User).filter(User.is_admin == True).first()
        
        if not admin_user:
            print("No admin user found. Creating one...")
            # Create an admin user if none exists
            admin_user = User(
                email="admin@test.com",
                hashed_password="$2b$12$8VK5NL.wBV.LD9kx9Ulhme/R/M.QyD1m9F/FA8qSh5CH3kB3CzKJi",  # password: admin123
                full_name="Admin User",
                is_active=True,
                is_admin=True,
                credits=1000,
                created_at=datetime.datetime.now()
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"Created admin user: {admin_user.email}")
        
        # Create a test transaction
        transaction = CreditTransaction(
            user_id=admin_user.id,
            admin_user_id=admin_user.id,
            amount=10,
            transaction_type="test",
            notes="Test transaction",  # This should be mapped to the 'description' column in SQLite
            balance_after=admin_user.credits + 10  # Set the balance_after field
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        print(f"Created transaction: ID={transaction.id}, Amount={transaction.amount}, Notes={transaction.notes}")
        print("Test completed successfully!")
        
        return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    test_add_credit_transaction() 