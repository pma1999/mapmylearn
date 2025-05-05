import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, select, update
from backend.config.database import SessionLocal # Use the project's way to get DB sessions
from backend.models.auth_models import User, CreditTransaction, TransactionType
# TODO: Import settings if a central config is implemented
# from backend.core.config import settings 

logger = logging.getLogger(__name__)

# TODO: Read MONTHLY_USER_CREDITS from config/settings if implemented
MONTHLY_CREDITS_TO_GRANT = 1

async def grant_monthly_credits():
    """
    Scheduled task to grant monthly credits to users based on their registration day.
    Credits are not cumulative.
    Uses SELECT FOR UPDATE to lock user rows during processing.
    """
    logger.info("Starting monthly credit grant task...")
    db: Session = SessionLocal()
    granted_count = 0
    users_processed_count = 0
    try:
        today_utc = datetime.utcnow()
        today_date = today_utc.date()
        day_of_month = today_date.day

        logger.debug(f"Running monthly credit check for day {day_of_month} of the month.")

        # --- Start Transaction --- 
        # Process all users within a single transaction for efficiency,
        # but handle individual user errors gracefully.
        with db.begin(): 
            # Find users whose registration day matches today's day
            # Lock the rows to prevent concurrent modifications during this task run
            # Using func.extract which is generally portable (PostgreSQL, SQLite)
            stmt = select(User).where(
                func.extract('day', User.created_at) == day_of_month,
                User.is_active == True # Optional: Grant only to active users?
            ).with_for_update() # Add lock here
            
            users_to_process = db.scalars(stmt).all()
            users_processed_count = len(users_to_process)
            logger.info(f"Found and locked {users_processed_count} users registered on day {day_of_month}.")

            for user in users_to_process:
                should_grant = False
                last_grant = user.last_monthly_credit_granted_at

                if last_grant is None:
                    # Never received monthly credit OR last grant date wasn't recorded
                    should_grant = True
                    logger.debug(f"User {user.id}: Eligible (no previous grant date).")
                else:
                    # Check if ~1 month has passed since the last grant
                    days_since_last_grant = (today_utc.date() - last_grant.date()).days
                    if days_since_last_grant >= 28:
                        should_grant = True
                        logger.debug(f"User {user.id}: Eligible ({days_since_last_grant} days since last grant on {last_grant.date()}).")
                    else:
                         logger.debug(f"User {user.id}: Not eligible ({days_since_last_grant} days since last grant on {last_grant.date()}, needs >= 28).")

                if should_grant:
                    # Update user object directly in the session (already locked)
                    original_balance = user.credits
                    user.credits += MONTHLY_CREDITS_TO_GRANT
                    user.last_monthly_credit_granted_at = today_utc
                    updated_balance = user.credits

                    # Create credit transaction record
                    transaction = CreditTransaction(
                        user_id=user.id,
                        amount=MONTHLY_CREDITS_TO_GRANT,
                        transaction_type="monthly_grant",
                        notes=f"Monthly credit grant ({MONTHLY_CREDITS_TO_GRANT}) applied on {today_date}",
                        balance_after=updated_balance,
                        created_at=today_utc
                    )
                    db.add(transaction)
                    # No need to flush/commit per user, the outer `with db.begin()` handles it.
                    granted_count += 1
                    logger.info(f"Prepared grant for user {user.id}. New balance: {updated_balance}")

        # If the `with db.begin()` block finishes without error, the transaction is committed.
        if granted_count > 0:
            logger.info(f"Committed grants for {granted_count} users out of {users_processed_count} processed.")
        else:
             logger.info(f"No credits granted in this run ({users_processed_count} users processed). Transaction committed (no changes)." if users_processed_count > 0 else "No eligible users found. Transaction committed (no changes).")

    except Exception as e_main:
        # Rollback is handled automatically by `with db.begin()`
        logger.error(f"Critical error during the monthly credit grant task: {e_main}", exc_info=True)
        # The transaction will be rolled back.
    finally:
        if db:
            db.close() # Ensure the session is closed
        logger.info("Monthly credit grant task finished.") 