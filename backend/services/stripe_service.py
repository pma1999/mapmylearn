import os
import stripe
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
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
                            'name': 'Learning Path Credits',
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
        Returns True if the event was handled successfully.
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )

            # Handle the event
            if event['type'] == 'checkout.session.completed':
                return await self._handle_successful_payment(event['data']['object'], db)

            return True  # Successfully processed (or ignored) the event

        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            raise

    async def _handle_successful_payment(self, session: Dict[str, Any], db: Session) -> bool:
        """
        Handle a successful payment by updating user credits and creating a transaction record.
        """
        # Check if payment was successful
        if session['payment_status'] != 'paid':
            logger.warning(f"Session {session['id']} not paid")
            return False

        # Extract metadata
        user_id = int(session['metadata']['user_id'])
        quantity = int(session['metadata']['credit_quantity'])

        # Check for existing transaction
        existing_transaction = db.query(CreditTransaction).filter_by(
            stripe_checkout_session_id=session['id']
        ).first()

        if existing_transaction:
            logger.info(f"Session {session['id']} already processed")
            return True

        try:
            # Get user
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            # Update user credits
            user.credits += quantity

            # Create transaction record
            transaction = CreditTransaction(
                user_id=user_id,
                amount=quantity,
                transaction_type='purchase',
                stripe_checkout_session_id=session['id'],
                stripe_payment_intent_id=session.get('payment_intent'),
                purchase_metadata={
                    'amount_total': session['amount_total'],
                    'currency': session['currency'],
                    'payment_status': session['payment_status'],
                    'customer_email': session['customer_email']
                },
                balance_after=user.credits,
                notes=f"Purchased {quantity} credits via Stripe"
            )

            db.add(transaction)
            db.commit()

            logger.info(f"Successfully processed payment for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            db.rollback()
            raise

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