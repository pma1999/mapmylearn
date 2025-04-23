from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import logging

from backend.config.database import get_db
from backend.models.auth_models import User
from backend.utils.auth_middleware import get_current_user
from backend.services.stripe_service import StripeService

logger = logging.getLogger(__name__)
router = APIRouter()
stripe_service = StripeService()

class CreateCheckoutSessionRequest(BaseModel):
    quantity: int

class CheckoutSessionResponse(BaseModel):
    sessionId: str
    url: str

@router.post("/payments/checkout-sessions", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Checkout session for credit purchase.
    """
    try:
        if request.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be positive"
            )

        session = await stripe_service.create_checkout_session(
            user=current_user,
            quantity=request.quantity
        )

        return CheckoutSessionResponse(
            sessionId=session['sessionId'],
            url=session['url']
        )

    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook events.
    """
    try:
        # Get the raw payload and signature header
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')

        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature header"
            )

        # Process the webhook
        await stripe_service.handle_webhook_event(payload, sig_header, db)

        return Response(status_code=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process webhook"
        )

@router.get("/payments/session/{session_id}")
async def get_checkout_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a Stripe Checkout session.
    """
    try:
        session = await stripe_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Verify the session belongs to the current user
        if str(current_user.id) != session.get('metadata', {}).get('user_id'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this session"
            )

        return {
            'status': session.get('payment_status'),
            'amount_total': session.get('amount_total'),
            'currency': session.get('currency'),
            'customer_email': session.get('customer_email'),
            'metadata': session.get('metadata'),
            'payment_intent_id': session.get('payment_intent')
        }

    except Exception as e:
        logger.error(f"Error retrieving checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve checkout session"
        ) 