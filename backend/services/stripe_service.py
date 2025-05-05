import os
import stripe
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound
from backend.models.auth_models import User, CreditTransaction
from backend.config.database import get_db

logger = logging.getLogger(__name__)

# Initialize Stripe with the secret key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
# STRIPE_PRICE_ID is not used for dynamic pricing here, maybe keep for other potential uses or remove if confirmed unused.
# STRIPE_PRICE_ID = os.getenv('STRIPE_PRICE_ID')

# Constants
FIXED_CREDIT_PRICE_CENTS = 100  # €1.00 per credit in cents

class StripeService:
    def __init__(self):
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable is not set")
        if not STRIPE_WEBHOOK_SECRET:
            raise ValueError("STRIPE_WEBHOOK_SECRET environment variable is not set")
        # if not STRIPE_PRICE_ID:
        #     raise ValueError("STRIPE_PRICE_ID environment variable is not set")

    async def create_checkout_session(self, user: User, quantity: int) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for credit purchase with a fixed price.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        try:
            # Use the fixed unit price
            unit_amount = FIXED_CREDIT_PRICE_CENTS

            session = stripe.checkout.Session.create(
                customer_email=user.email,
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'unit_amount': unit_amount, # Fixed price per credit
                        'product_data': {
                            'name': 'Course Credits',
                            'description': f'Purchase {quantity} credits for generating courses'
                        },
                    },
                    'quantity': quantity,
                }],
                mode='payment',
                success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/purchase-result?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/purchase-result?session_id={{CHECKOUT_SESSION_ID}}",
                metadata={
                    'user_id': str(user.id),
                    'credit_quantity': str(quantity),
                    'unit_amount': str(unit_amount) # Store the fixed unit amount used
                }
            )

            return {
                'sessionId': session.id,
                'url': session.url
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {str(e)}")
            raise

    async def handle_webhook_event(self, payload: bytes, sig_header: str, db: Session) -> bool:
        """
        Handle Stripe webhook events, particularly successful payments.
        Returns True if the event was handled successfully (or ignored idempotently).
        """
        event = None # Define event outside try block
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            logger.info(f"Received Stripe event: {event['type']}, ID: {event['id']}")

        except ValueError as e:
            # Invalid payload
            logger.error(f"Invalid Stripe webhook payload: {e}")
            raise # Re-raise as it indicates a problem with the request itself
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid Stripe webhook signature: {e}")
            raise # Re-raise signature error

        # Handle the event
        if event and event['type'] == 'checkout.session.completed':
            # Use a database transaction for handling the payment
            try:
                with db.begin(): # Start transaction
                    payment_handled = await self._handle_successful_payment(
                        event['data']['object'], db
                    )
                # Transaction committed successfully if no exception
                return payment_handled
            except IntegrityError as e:
                 # This specifically catches the unique constraint violation if the
                 # _handle_successful_payment tries to commit a duplicate transaction.
                 # The rollback is handled automatically by `with db.begin()`.
                 logger.warning(f"Webhook IntegrityError for event {event['id']} (likely duplicate): {e}. Handled idempotently.")
                 return True # Treat as success (idempotency handled)
            except Exception as e:
                 # Catch other errors during _handle_successful_payment or commit
                 # Rollback is handled automatically.
                 logger.error(f"Error processing successful checkout event {event['id']}: {str(e)}", exc_info=True)
                 # Decide if we should raise or return False. Returning False might cause Stripe to retry.
                 # Let's return False to indicate processing failure for this attempt.
                 return False
        else:
            logger.info(f"Ignoring Stripe event type: {event['type'] if event else 'N/A'}")
            return True  # Indicate we successfully ignored the event

    async def _handle_successful_payment(self, session_data: Dict[str, Any], db: Session) -> bool:
        """
        Handle a successful payment by updating user credits and creating a transaction record.
        Assumes it's called within an active transaction block.
        Uses SELECT FOR UPDATE on the User row.
        Relies on database unique constraint for idempotency.
        Returns True on success, raises exceptions on failure.
        """
        checkout_session_id = session_data['id']
        payment_status = session_data['payment_status']
        payment_intent_id = session_data.get('payment_intent')

        # Check if payment was successful
        if payment_status != 'paid':
            logger.warning(f"Checkout session {checkout_session_id} status is not 'paid' ({payment_status}). Skipping credit grant.")
            return False # Indicate not processed due to status

        # Extract metadata
        try:
            user_id = int(session_data['metadata']['user_id'])
            quantity = int(session_data['metadata']['credit_quantity'])
        except (KeyError, ValueError) as e:
             logger.error(f"Missing or invalid metadata in checkout session {checkout_session_id}: {e}")
             # Cannot proceed without valid user_id and quantity
             raise ValueError(f"Invalid metadata in session {checkout_session_id}") from e

        # --- Modification Block (within the caller's transaction) ---
        try:
            # Get user with row lock
            user = db.query(User).filter(User.id == user_id).with_for_update().one()

            # Create transaction record BEFORE updating user credits
            # This ensures that if the INSERT fails due to the unique constraint,
            # we don't proceed with the credit update.
            transaction = CreditTransaction(
                user_id=user_id,
                amount=quantity,
                transaction_type='purchase',
                stripe_checkout_session_id=checkout_session_id,
                stripe_payment_intent_id=payment_intent_id,
                purchase_metadata={
                    'amount_total': session_data['amount_total'],
                    'currency': session_data['currency'],
                    'payment_status': payment_status,
                    'customer_email': session_data['customer_email']
                },
                # Calculate balance_after based on current credits + grant amount
                balance_after=user.credits + quantity, 
                notes=f"Purchased {quantity} credits via Stripe (Session: {checkout_session_id})"
            )
            db.add(transaction)
            
            # Flush to check unique constraint before updating credits
            # If this fails with IntegrityError, the outer handler will catch it.
            db.flush() 
            
            # Update user credits only AFTER successful transaction flush
            user.credits += quantity
            logger.info(f"Successfully processed payment for user {user_id} (Session: {checkout_session_id}). New balance: {user.credits}")
            return True

        except NoResultFound:
            logger.error(f"User {user_id} not found for checkout session {checkout_session_id}")
            # Re-raise or handle as appropriate, indicates data inconsistency
            raise ValueError(f"User {user_id} not found processing session {checkout_session_id}")
        except IntegrityError:
             # This is expected if the transaction/session ID already exists.
             # Log and re-raise so the outer handler can catch it and return True (idempotent).
             logger.warning(f"IntegrityError likely due to duplicate webhook for session {checkout_session_id}")
             raise 
        except Exception as e:
             # Catch unexpected errors during DB operations
             logger.exception(f"Error processing payment DB operations for user {user_id} (Session: {checkout_session_id}): {e}")
             raise # Re-raise to be caught by the outer handler and trigger rollback

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a Stripe Checkout session by ID.
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving Stripe session: {str(e)}")
            return None 