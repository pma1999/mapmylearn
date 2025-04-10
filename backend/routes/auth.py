from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import os
from typing import Optional

from backend.config.database import get_db
from backend.models.auth_models import User, Session as UserSession
from backend.schemas.auth_schemas import UserCreate, UserLogin, UserResponse, Token
from backend.utils.auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.utils.auth_middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        created_at=datetime.utcnow(),
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not register user",
        )
    
    # Create access token
    token_data = {
        "sub": str(db_user.id),
        "email": db_user.email,
    }
    
    access_token = create_access_token(token_data)
    
    # Return token and user data
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "user": db_user,
    }


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
        refresh_days = 30  # 30 days for remember me
        session = UserSession.create_refresh_token(
            user_id=user.id,
            expiry_days=refresh_days,
            device_info=request.headers.get("User-Agent"),
            ip_address=request.client.host if hasattr(request, 'client') else None
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
    
    # If session is nearing expiration (less than 7 days), extend it
    if session.expires_at < datetime.utcnow() + timedelta(days=7):
        print(f"Extending session for user {user.email}")
        session.expires_at = datetime.utcnow() + timedelta(days=30)
        
    # Update additional session metadata
    session.last_used_at = datetime.utcnow()
    session.ip_address = request.client.host if hasattr(request, 'client') else None
    
    # Save changes
    db.commit()
    
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
    Check if the current user's authentication token is valid.
    Returns the user's information if authenticated.
    """
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