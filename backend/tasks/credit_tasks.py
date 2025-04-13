import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, select, update
from backend.config.database import SessionLocal # Use the project's way to get DB sessions
from backend.models.auth_models import User, CreditTransaction
# TODO: Import settings if a central config is implemented
# from backend.core.config import settings 

logger = logging.getLogger(__name__)

# TODO: Read MONTHLY_USER_CREDITS from config/settings if implemented
MONTHLY_CREDITS_TO_GRANT = 1

async def grant_monthly_credits():
    """
    Scheduled task to grant monthly credits to users based on their registration day.
    Credits are not cumulative.
    """
    logger.info("Starting monthly credit grant task...")
    db: Session = SessionLocal()
    try:
        today_utc = datetime.utcnow()
        today_date = today_utc.date()
        day_of_month = today_date.day

        logger.debug(f"Running monthly credit check for day {day_of_month} of the month.")

        # Find users whose registration day matches today's day
        # Using func.extract which is generally portable (PostgreSQL, SQLite)
        stmt = select(User).where(
            func.extract('day', User.created_at) == day_of_month,
            User.is_active == True # Optional: Grant only to active users?
        )
        users_to_process = db.scalars(stmt).all()

        granted_count = 0
        users_processed_count = len(users_to_process)
        logger.info(f"Found {users_processed_count} users registered on day {day_of_month}.")

        for user in users_to_process:
            should_grant = False
            last_grant = user.last_monthly_credit_granted_at

            if last_grant is None:
                # Never received monthly credit OR last grant date wasn't recorded (for existing users)
                should_grant = True
                logger.debug(f"User {user.id}: Eligible (no previous grant date).")
            else:
                # Check if ~1 month has passed since the last grant
                # We use >= 28 days as a safe lower bound for a month to handle month length variations
                # We also check if the last grant was actually before the start of *today* UTC
                # to prevent double-granting if the job runs multiple times on the same day.
                days_since_last_grant = (today_utc.date() - last_grant.date()).days
                if days_since_last_grant >= 28:
                    should_grant = True
                    logger.debug(f"User {user.id}: Eligible ({days_since_last_grant} days since last grant on {last_grant.date()}).")
                else:
                     logger.debug(f"User {user.id}: Not eligible ({days_since_last_grant} days since last grant on {last_grant.date()}, needs >= 28).")


            if should_grant:
                # Use a nested try-except block to handle errors for individual users
                try:
                    # Atomically update credits and last grant date using SQLAlchemy's update
                    # This helps prevent race conditions if multiple tasks run
                    update_stmt = (
                        update(User)
                        .where(User.id == user.id)
                        # Ensure we are updating the correct user and avoid lost updates
                        .where(User.last_monthly_credit_granted_at == user.last_monthly_credit_granted_at) 
                        .values(
                            credits=User.credits + MONTHLY_CREDITS_TO_GRANT,
                            last_monthly_credit_granted_at=today_utc
                        )
                        .returning(User.credits) # Get the updated credit balance
                    )
                    
                    # Execute the update statement within the session
                    # result = db.execute(update_stmt) # Older style
                    # updated_balance = result.scalar_one_or_none() # Older style

                    # Simpler approach: update object in session and flush/commit later
                    original_balance = user.credits
                    user.credits += MONTHLY_CREDITS_TO_GRANT
                    user.last_monthly_credit_granted_at = today_utc
                    updated_balance = user.credits # Get the balance after update

                    # Create credit transaction record
                    transaction = CreditTransaction(
                        user_id=user.id,
                        amount=MONTHLY_CREDITS_TO_GRANT,
                        transaction_type="monthly_grant", # Use a specific type
                        notes=f"Monthly credit grant ({MONTHLY_CREDITS_TO_GRANT}) applied on {today_date}",
                        balance_after=updated_balance, # Store the balance AFTER transaction
                        created_at=today_utc # Use consistent timestamp
                    )
                    db.add(transaction)
                    
                    # Flush changes for this user to DB transaction buffer
                    db.flush() 
                    
                    granted_count += 1
                    logger.info(f"Successfully granted {MONTHLY_CREDITS_TO_GRANT} credit(s) to user {user.id} (Email: {user.email}). New balance: {updated_balance}")

                except Exception as e_user:
                    # Log the error for this specific user and rollback this user's changes
                    logger.error(f"Error processing user {user.id} ({user.email}) during monthly credit grant: {e_user}", exc_info=True)
                    # Rolling back the session here might impact previous successful users in the loop if not careful.
                    # For simplicity now, we log and continue. A robust implementation might use savepoints per user.
                    # If flush failed, the session might be compromised, consider full rollback.
                    # Given the simple nature, just continuing is likely okay. We won't commit this user's partial changes.


        # Commit all successful transactions together at the end
        if granted_count > 0:
             try:
                 db.commit()
                 logger.info(f"Committed grants for {granted_count} users.")
             except Exception as e_commit:
                 logger.error(f"Failed to commit monthly credit grants: {e_commit}", exc_info=True)
                 db.rollback() # Rollback everything if final commit fails
        else:
            logger.info("No credits granted in this run.")


    except Exception as e_main:
        logger.error(f"Critical error during the monthly credit grant task: {e_main}", exc_info=True)
        db.rollback() # Rollback any potential changes if a major error occurred
    finally:
        db.close() # Ensure the session is closed
        logger.info("Monthly credit grant task finished.") 