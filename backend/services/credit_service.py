import asyncio
import contextlib
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession # Assuming async session if using async context manager
from sqlalchemy.orm import Session # Use standard Session if not async
from sqlalchemy.exc import SQLAlchemyError

from backend.config.database import get_db
from backend.models.auth_models import User, CreditTransaction, TransactionType

logger = logging.getLogger(__name__)


class _CreditOperationContextManager:
    """Async context manager to handle credit deduction and refunds."""

    def __init__(self, db: Session, user: User, amount: int, transaction_type: str, notes: str):
        self.db = db
        self.user = user
        self.amount = amount
        self.transaction_type = transaction_type
        self.notes = notes
        self.deducted = False

    async def __aenter__(self):
        logger.debug(f"Entering credit charge context for user {self.user.id}, type: {self.transaction_type}, amount: {self.amount}")
        try:
            # Ensure user object is up-to-date within the session
            # self.db.refresh(self.user) # Use refresh if user object might be stale

            # 1. Check Credits
            if self.user.credits < self.amount:
                logger.warning(f"Insufficient credits for user {self.user.id}. Required: {self.amount}, Available: {self.user.credits}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient credits. You need {self.amount} credit(s) for this operation, but have {self.user.credits}."
                )

            # 2. Deduct Credit
            self.user.credits -= self.amount
            balance_after_deduction = self.user.credits
            logger.info(f"Deducting {self.amount} credits from user {self.user.id}. New balance: {balance_after_deduction}")

            # 3. Log Deduction Transaction
            deduction_transaction = CreditTransaction(
                user_id=self.user.id,
                amount=-self.amount,
                transaction_type=self.transaction_type,
                notes=self.notes,
                balance_after=balance_after_deduction
            )
            self.db.add(deduction_transaction)

            # 4. Commit Deduction
            await asyncio.to_thread(self.db.commit) # Use asyncio.to_thread for sync commit in async context
            self.deducted = True
            logger.info(f"Committed credit deduction transaction for user {self.user.id}, type: {self.transaction_type}")

            # Optional: Refresh user state after commit
            # await asyncio.to_thread(self.db.refresh, self.user)

        except SQLAlchemyError as e:
            logger.exception(f"Database error during credit deduction for user {self.user.id}: {e}")
            await asyncio.to_thread(self.db.rollback)
            self.deducted = False # Ensure refund logic doesn't run if deduction failed
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during credit check or deduction."
            )
        except HTTPException: # Re-raise HTTP exceptions (like 403)
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during credit deduction for user {self.user.id}: {e}")
            await asyncio.to_thread(self.db.rollback)
            self.deducted = False
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while processing credits."
            )
        return self # Return self or None

    async def __aexit__(self, exc_type, exc_value, traceback):
        logger.debug(f"Exiting credit charge context for user {self.user.id}, type: {self.transaction_type}. Exception Type: {exc_type}")
        if exc_type is not None and self.deducted:
            logger.warning(
                f"Operation failed for user {self.user.id} (Type: {self.transaction_type}). Attempting refund of {self.amount} credits. Error: {exc_value}"
            )
            try:
                # Ensure user object is fresh before refund
                await asyncio.to_thread(self.db.refresh, self.user)

                # 1. Refund Credit
                self.user.credits += self.amount
                balance_after_refund = self.user.credits
                logger.info(f"Refunding {self.amount} credits to user {self.user.id}. New balance: {balance_after_refund}")

                # 2. Log Refund Transaction
                refund_notes = f"Refund for failed {self.transaction_type}: {str(exc_value)[:150]}"
                refund_transaction = CreditTransaction(
                    user_id=self.user.id,
                    amount=self.amount,
                    transaction_type=TransactionType.REFUND,
                    notes=refund_notes,
                    balance_after=balance_after_refund
                )
                self.db.add(refund_transaction)

                # 3. Commit Refund
                await asyncio.to_thread(self.db.commit)
                logger.info(f"Successfully refunded {self.amount} credits to user {self.user.id} due to operation failure.")

            except SQLAlchemyError as refund_err:
                logger.error(f"CRITICAL: Database error during credit refund for user {self.user.id}! Error: {refund_err}")
                await asyncio.to_thread(self.db.rollback)
                # Do not suppress the original exception!
            except Exception as refund_err:
                 logger.error(f"CRITICAL: Unexpected error during credit refund for user {self.user.id}! Error: {refund_err}")
                 await asyncio.to_thread(self.db.rollback)
                 # Do not suppress the original exception!

        # Return False/None to propagate the original exception if one occurred
        return False


class CreditService:
    """Service class for managing user credits."""

    def __init__(self, db: Session = Depends(get_db)):
        if db is None:
             raise ValueError("Database session is required for CreditService")
        self.db = db

    @contextlib.asynccontextmanager
    async def charge(self, user: User, amount: int, transaction_type: str, notes: str):
        """
        Context manager to charge credits for an operation.

        Handles checking balance, deducting credits, logging the transaction,
        and automatically refunding if an exception occurs within the context.

        Args:
            user: The User object performing the action.
            amount: The number of credits to deduct (positive integer).
            transaction_type: The type of transaction (e.g., TransactionType.AUDIO_GENERATION_USE).
            notes: A description of the transaction.

        Raises:
            HTTPException(403): If the user has insufficient credits.
            HTTPException(500): On database errors or unexpected issues.
        """
        if amount <= 0:
            raise ValueError("Charge amount must be positive")

        # We pass the same db session used by the service to the context manager
        context_manager = _CreditOperationContextManager(
            db=self.db,
            user=user,
            amount=amount,
            transaction_type=transaction_type,
            notes=notes
        )
        async with context_manager as cm:
             yield cm # Yield control to the `async with` block

    # Potential future methods: grant_credits, check_balance, etc. 