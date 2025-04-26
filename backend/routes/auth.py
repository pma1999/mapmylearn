from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import os
from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr, Field
import logging

from backend.config.database import get_db
from backend.models.auth_models import User, Session as UserSession
from backend.schemas.auth_schemas import UserCreate, UserLogin, UserResponse, Token, MessageResponse, ForgotPasswordRequest, ResetPasswordRequest
from backend.utils.auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.utils.auth_middleware import get_current_user
from backend.utils.token_manager import (
    generate_verification_token, get_verification_link, verify_verification_token,
    generate_password_reset_token, hash_token, get_password_reset_link, PASSWORD_RESET_TOKEN_EXPIRY_MINUTES
)
from backend.services.email_service import send_verification_email, send_password_reset_email, send_password_reset_confirmation_email
from backend.utils.custom_rate_limiter import rate_limit

# Initialize logger for this file
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Rate limit: 5 requests per 15 minutes per IP
FORGOT_PASSWORD_LIMIT = rate_limit(times=5, minutes=15)
# Rate limit: 10 requests per hour per IP (slightly more lenient for actual resets)
RESET_PASSWORD_LIMIT = rate_limit(times=10, minutes=60)


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user and send verification email.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user (is_email_verified defaults to False in model)
    hashed_password = get_password_hash(user.password)
    # TODO: Read INITIAL_USER_CREDITS from config/settings if implemented
    initial_credits = 3
    current_time_utc = datetime.utcnow() # Get current time
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        credits=initial_credits, # Assign initial credits
        created_at=current_time_utc, # Explicitly set created_at
        # is_email_verified defaults to False (via server_default)
        # last_login is nullable
        # last_monthly_credit_granted_at is nullable
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError as e:
        db.rollback()
        # Log the detailed IntegrityError
        logging.error(f"IntegrityError during user registration: {e}", exc_info=True) # Add exc_info for traceback
        # Also log the original exception if available
        if hasattr(e, 'orig') and e.orig:
             logging.error(f"Original DBAPIError: {e.orig}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not register user", # Keep generic message for frontend
        )
    
    # Send verification email instead of creating token
    try:
        token = generate_verification_token(db_user.id)
        verification_link = get_verification_link(token)
        email_sent = send_verification_email(db_user.email, verification_link)
        if not email_sent:
            # Log the error, but don't fail the registration
            # User can use the resend endpoint later
            print(f"WARNING: Failed to send verification email to {db_user.email} during registration.")
    except Exception as e:
        # Catch potential errors during token generation or email sending
        print(f"ERROR: Could not send verification email during registration for {db_user.email}: {e}")
        # Again, don't fail registration, allow resend

    # Return success message - NO TOKEN
    return MessageResponse(message="Registration successful. Please check your email to verify your account.")


@router.post("/login", response_model=Token)
async def login(response: Response, request: Request, user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT token.
    """
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not verified. Please check your email.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
    }
    
    # Calculate expiration time
    token_expires = ACCESS_TOKEN_EXPIRE_MINUTES
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=token_expires),
    )
    
    # Create refresh token if remember_me is True
    if user_credentials.remember_me:
        # Delete existing sessions for the user if any
        db.query(UserSession).filter(
            UserSession.user_id == user.id,
        ).delete()
        
        # Create new session with refresh token
        try:
            refresh_days = 30  # 30 days for remember me
            
            # Get device info and IP address
            device_info = request.headers.get("User-Agent")
            ip_address = request.client.host if hasattr(request, 'client') else None
            
            # Try creating the session with all fields
            try:
                session = UserSession.create_refresh_token(
                    user_id=user.id,
                    expiry_days=refresh_days,
                    device_info=device_info,
                    ip_address=ip_address
                )
            except Exception as e:
                # If that fails, try without last_used_at in case it's the problem
                print(f"Warning: Creating full session failed: {e}")
                # Create without explicit last_used_at field
                session = UserSession(
                    user_id=user.id,
                    refresh_token=str(uuid.uuid4()),
                    expires_at=datetime.utcnow() + timedelta(days=refresh_days),
                    device_info=device_info,
                    ip_address=ip_address
                )
            
            db.add(session)
            db.commit()
            
            # Determine environment to set proper cookie settings
            is_production = os.getenv("ENVIRONMENT", "development") == "production"
            
            # Set refresh token cookie with appropriate security settings
            response.set_cookie(
                key="refresh_token",
                value=session.refresh_token,
                httponly=True,
                secure=is_production,  # Only secure in production
                samesite="strict" if is_production else "lax",  # Strict in production, lax in development
                max_age=refresh_days * 24 * 3600,  # 30 days in seconds
                path="/",
            )
            
            print(f"User {user.email} logged in with remember-me enabled")
        except Exception as e:
            # If session creation fails, log error but continue
            print(f"Warning: Error creating session: {e}")
            # Rollback the session creation, but not the user login update
            db.rollback()
            print(f"User {user.email} logged in without persistent session due to error")
    else:
        print(f"User {user.email} logged in without remember-me")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": token_expires * 60,  # Convert to seconds
        "user": user,
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(response: Response, request: Request, db: Session = Depends(get_db)):
    """
    Refresh an expired access token using a refresh token.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Find session by refresh token
    session = db.query(UserSession).filter(
        UserSession.refresh_token == refresh_token,
        UserSession.expires_at > datetime.utcnow(),
    ).first()
    
    if not session:
        # Clear invalid cookie
        response.delete_cookie(key="refresh_token", path="/")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user or not user.is_active:
        response.delete_cookie(key="refresh_token", path="/")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
    }
    
    access_token = create_access_token(token_data)
    
    # Update last login and session timestamp
    user.last_login = datetime.utcnow()
    
    try:
        # If session is nearing expiration (less than 7 days), extend it
        if session.expires_at < datetime.utcnow() + timedelta(days=7):
            print(f"Extending session for user {user.email}")
            session.expires_at = datetime.utcnow() + timedelta(days=30)
            
        # Try to update additional session metadata
        # Use try/except in case the last_used_at column doesn't exist yet
        try:
            session.last_used_at = datetime.utcnow()
        except Exception as e:
            print(f"Warning: Could not update last_used_at: {e}")
            
        # Update ip_address if possible
        session.ip_address = request.client.host if hasattr(request, 'client') else None
        
        # Save changes
        db.commit()
    except Exception as e:
        print(f"Warning: Error updating session data: {e}")
        # Try to commit just the user update
        try:
            db.commit()
        except:
            db.rollback()
    
    print(f"Token refreshed for user {user.email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "user": user,
    }


@router.post("/logout")
async def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    """
    Log out a user by invalidating their refresh token.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if refresh_token:
        # Delete session from database
        db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token,
        ).delete()
        db.commit()
        
        # Clear refresh token cookie
        response.delete_cookie(key="refresh_token", path="/")
    
    return {"detail": "Successfully logged out"}


@router.get("/status")
async def auth_status(current_user: User = Depends(get_current_user)):
    """
    Check if the user is currently authenticated and return user details.
    Relies on the get_current_user dependency to validate the token.
    """
    logger.info(f"Auth status request processed for user: {current_user.id}") # TEMPORARY LOGGING
    return current_user

@router.get("/credits")
async def get_user_credits(current_user: User = Depends(get_current_user)):
    """
    Get the current user's credit balance.
    """
    return {
        "credits": current_user.credits,
        "user_id": current_user.id,
        "email": current_user.email
    } 

@router.get("/verify-email", response_model=MessageResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user's email address using the provided token."""
    user_id = verify_verification_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification link",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Should not happen if token is valid, but handle defensively
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link",
        )

    if user.is_email_verified:
        return MessageResponse(message="Email is already verified. You can log in.")

    # Mark email as verified
    user.is_email_verified = True
    try:
        db.commit()
        print(f"Email verified successfully for user {user.email}")
        return MessageResponse(message="Email verified successfully. You can now log in.")
    except Exception as e:
        db.rollback()
        print(f"ERROR: Failed to update email verification status for user {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify email. Please try again later.",
        )

class ResendRequest(BaseModel):
    email: EmailStr

@router.post("/resend-verification", response_model=MessageResponse, dependencies=[Depends(rate_limit(times=5, minutes=1))])
async def resend_verification_email(request: ResendRequest, db: Session = Depends(get_db)):
    """Resends the verification email to a user if their account is not yet verified."""
    user = db.query(User).filter(User.email == request.email).first()

    if user and not user.is_email_verified:
        try:
            token = generate_verification_token(user.id)
            verification_link = get_verification_link(token)
            email_sent = send_verification_email(user.email, verification_link)
            if not email_sent:
                print(f"WARNING: Failed to resend verification email to {user.email}.")
                # Don't expose detailed error to user
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail="Could not send verification email. Please try again later."
                )
            print(f"Resent verification email to {user.email}")
            # Return generic success message even if email failed, for security
        except HTTPException as http_exc:
             raise http_exc # Re-raise HTTP exceptions from send_email failure
        except Exception as e:
            print(f"ERROR: Failed to resend verification email for {request.email}: {e}")
            # Don't expose detailed error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Could not send verification email. Please try again later."
            )

    # Always return a generic message to prevent email enumeration
    return MessageResponse(message="If an account with that email exists and requires verification, a new email has been sent.") 

@router.post("/forgot-password", response_model=MessageResponse, dependencies=[Depends(FORGOT_PASSWORD_LIMIT)])
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiates the password reset process for a user.
    Generates a reset token, saves its hash, and sends a reset link via email.
    Always returns a generic success message to prevent email enumeration.
    """
    user = db.query(User).filter(User.email == request.email).first()

    # Security: Only proceed if user exists AND email is verified
    if user and user.is_email_verified:
        try:
            raw_token, token_hash = generate_password_reset_token()
            expiry_time = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRY_MINUTES)
            
            user.password_reset_token_hash = token_hash
            user.password_reset_token_expires_at = expiry_time
            db.commit()
            
            reset_link = get_password_reset_link(raw_token)
            email_sent = send_password_reset_email(user.email, reset_link)
            if not email_sent:
                # Log failure but don't expose error to user
                logging.error(f"Failed to send password reset email to {user.email}")
                # Note: DB changes are already committed, user can try again later.

        except Exception as e:
            db.rollback() # Rollback DB changes if anything fails during token/email process
            logging.error(f"Error during forgot password process for {request.email}: {e}", exc_info=True)
            # Fall through to generic response to avoid leaking info

    # Generic success response regardless of user existence or errors
    return MessageResponse(message="If an account with that email exists and is verified, a password reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse, dependencies=[Depends(RESET_PASSWORD_LIMIT)])
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Resets the user's password using a valid reset token.
    Verifies the token, updates the password, invalidates the token, and logs out other sessions.
    """
    if not request.token or not request.new_password:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token and new password are required.",
         )
    
    hashed_token = hash_token(request.token)
    
    # Find user by the hashed token
    user = db.query(User).filter(User.password_reset_token_hash == hashed_token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset link.",
        )

    # Check if the token has expired
    if user.password_reset_token_expires_at is None or user.password_reset_token_expires_at < datetime.utcnow():
        # Optionally clear the expired token fields here
        # user.password_reset_token_hash = None
        # user.password_reset_token_expires_at = None
        # db.commit() # Commit separately or as part of the main transaction later
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset link.",
        )
        
    # --- Token is valid, proceed with password reset --- 
    try:
        new_hashed_password = get_password_hash(request.new_password)
        
        # Start transaction
        user.hashed_password = new_hashed_password
        user.password_reset_token_hash = None # Invalidate the token
        user.password_reset_token_expires_at = None # Invalidate the token expiry
        
        # Invalidate all existing refresh token sessions for this user
        db.query(UserSession).filter(UserSession.user_id == user.id).delete()
        
        db.commit() # Commit all changes
        
        # Send confirmation email
        try:
             send_password_reset_confirmation_email(user.email)
        except Exception as e:
            logging.error(f"Failed to send password reset confirmation email to {user.email}: {e}")
            # Don't fail the request if confirmation email fails
            
        return MessageResponse(message="Password has been reset successfully.")

    except Exception as e:
        db.rollback()
        logging.error(f"Error during password reset for user {user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting the password. Please try again.",
        ) 