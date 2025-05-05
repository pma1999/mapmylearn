import asyncio
import contextlib
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession # Assuming async session if using async context manager
from sqlalchemy.orm import Session # Use standard Session if not async
from sqlalchemy.exc import SQLAlchemyError, NoResultFound # Import NoResultFound

from backend.config.database import get_db
from backend.models.auth_models import User, CreditTransaction, TransactionType

logger = logging.getLogger(__name__)


# Define custom exception for insufficient credits
class InsufficientCreditsError(HTTPException):
    def __init__(self, detail: str = "Insufficient credits for the operation."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class CreditService:
    """Service class for managing user credits."""

    def __init__(self, db: Optional[Session] = Depends(get_db)):
        # Allow db to be None initially, but raise error if methods are called without it
        # This supports scenarios where the service might be instantiated without immediate DB access
        self._db = db

    @property
    def db(self) -> Session:
        """Ensures the database session is available when needed."""
        if self._db is None:
            # This condition might occur if the service is instantiated outside a request context
            # where Depends(get_db) doesn't work as expected, or if get_db returns None.
            logger.error("CreditService accessed without a valid database session.")
            raise ValueError("Database session is required for CreditService operations but was not provided or is None.")
        return self._db

    async def charge_credits(self, user_id: int, amount: int, transaction_type: str, notes: Optional[str] = None) -> int:
        """
        Atomically deducts credits from a user within an existing transaction.

        This method assumes it is called within an active SQLAlchemy transaction block
        (e.g., inside `with db.begin():` or after `db.begin()`).
        It uses SELECT FOR UPDATE to lock the user row.

        Args:
            user_id: The ID of the user to charge.
            amount: The positive integer amount of credits to deduct.
            transaction_type: The type of transaction.
            notes: Optional description of the transaction.

        Returns:
            The user's new credit balance after deduction.

        Raises:
            InsufficientCreditsError: If the user does not have enough credits.
            SQLAlchemyError: If a database error occurs.
            NoResultFound: If the user_id does not exist.
            ValueError: If amount is not positive.
        """
        if amount <= 0:
            raise ValueError("Charge amount must be positive")
        if not self._db:
             raise ValueError("Database session is required for charge_credits")

        logger.debug(f"Attempting to charge {amount} credits from user {user_id} (type: {transaction_type}) within transaction.")
        try:
            # Lock the user row for the duration of the transaction block and get current state
            # Use .one() to ensure the user exists, raises NoResultFound otherwise
            user = self.db.query(User).filter(User.id == user_id).with_for_update().one()

            # Check balance
            if user.credits < amount:
                logger.warning(f"Insufficient credits for user {user_id}. Required: {amount}, Available: {user.credits}")
                raise InsufficientCreditsError(
                    f"Insufficient credits. You need {amount} credit(s) for this operation, but have {user.credits}."
                )

            # Deduct credits
            user.credits -= amount
            balance_after_deduction = user.credits
            logger.info(f"Charged {amount} credits from user {user_id}. New balance: {balance_after_deduction}")

            # Log transaction
            deduction_transaction = CreditTransaction(
                user_id=user.id,
                amount=-amount, # Store deducted amount as negative
                transaction_type=transaction_type,
                notes=notes,
                balance_after=balance_after_deduction
            )
            self.db.add(deduction_transaction)
            
            # Flush to ensure transaction is in buffer, but DO NOT COMMIT here.
            # The caller is responsible for committing the transaction.
            # await asyncio.to_thread(self.db.flush) # Not strictly needed unless accessing transaction ID

            return balance_after_deduction

        except NoResultFound:
            logger.error(f"User with ID {user_id} not found during credit charge.")
            raise # Re-raise NoResultFound
        except InsufficientCreditsError:
            raise # Re-raise specific credit error
        except SQLAlchemyError as e:
            logger.exception(f"Database error during credit charge for user {user_id}: {e}")
            # Do not rollback here; the caller's transaction manager handles it.
            raise # Re-raise database error
        except Exception as e:
            logger.exception(f"Unexpected error during credit charge for user {user_id}: {e}")
            # Do not rollback here.
            raise # Re-raise unexpected error

    async def grant_credits(
        self,
        user_id: int,
        amount: int,
        transaction_type: str,
        notes: Optional[str] = None,
        related_transaction_id: Optional[int] = None, # For linking refunds etc.
        stripe_checkout_session_id: Optional[str] = None, # For purchase linking
        stripe_payment_intent_id: Optional[str] = None, # For purchase linking
        purchase_metadata: Optional[dict] = None, # For purchase linking
        admin_user_id: Optional[int] = None # For admin grants
    ) -> int:
        """
        Atomically grants credits to a user within an existing transaction.

        This method assumes it is called within an active SQLAlchemy transaction block.
        It uses SELECT FOR UPDATE to lock the user row.

        Args:
            user_id: The ID of the user to grant credits to.
            amount: The positive integer amount of credits to grant.
            transaction_type: The type of transaction (e.g., purchase, refund, admin_add).
            notes: Optional description of the transaction.
            related_transaction_id: Optional ID of a related transaction (e.g., the charge being refunded).
            stripe_checkout_session_id: Optional Stripe session ID for purchases.
            stripe_payment_intent_id: Optional Stripe payment intent ID for purchases.
            purchase_metadata: Optional dictionary of metadata for purchases.
            admin_user_id: Optional ID of the admin performing the grant.

        Returns:
            The user's new credit balance after the grant.

        Raises:
            SQLAlchemyError: If a database error occurs.
            NoResultFound: If the user_id does not exist.
            ValueError: If amount is not positive.
        """
        if amount <= 0:
            raise ValueError("Grant amount must be positive")
        if not self._db:
             raise ValueError("Database session is required for grant_credits")

        logger.debug(f"Attempting to grant {amount} credits to user {user_id} (type: {transaction_type}) within transaction.")
        try:
            # Lock the user row
            user = self.db.query(User).filter(User.id == user_id).with_for_update().one()

            # Grant credits
            user.credits += amount
            balance_after_grant = user.credits
            logger.info(f"Granted {amount} credits to user {user_id}. New balance: {balance_after_grant}")

            # Log transaction
            grant_transaction = CreditTransaction(
                user_id=user.id,
                amount=amount, # Store granted amount as positive
                transaction_type=transaction_type,
                notes=notes,
                balance_after=balance_after_grant,
                admin_user_id=admin_user_id,
                # learning_path_id=related_transaction_id, # TODO: Clarify if learning_path_id should be used for related TXN
                stripe_checkout_session_id=stripe_checkout_session_id,
                stripe_payment_intent_id=stripe_payment_intent_id,
                purchase_metadata=purchase_metadata
            )
            self.db.add(grant_transaction)

            # Flush optional, DO NOT COMMIT here.

            return balance_after_grant

        except NoResultFound:
            logger.error(f"User with ID {user_id} not found during credit grant.")
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Database error during credit grant for user {user_id}: {e}")
            # Do not rollback here.
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during credit grant for user {user_id}: {e}")
            # Do not rollback here.
            raise

    # Potential future methods: check_balance, etc. 