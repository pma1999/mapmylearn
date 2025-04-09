from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from backend.config.database import get_db
from backend.utils.auth import decode_access_token, TokenData
from backend.models.auth_models import User

# Security scheme for JWT Bearer authentication
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that returns the current authenticated user.
    Raises an HTTPException if authentication fails.
    """
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user exists in database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that returns the current authenticated user only if they have admin privileges.
    Raises an HTTPException if the user is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to access this resource",
        )
    
    return current_user


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency that returns the current user if authenticated, or None if not.
    Does not raise an exception if authentication fails.
    """
    authorization = request.headers.get("Authorization")
    
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    token_data = decode_access_token(token)
    
    if token_data is None:
        return None
    
    # Verify user exists in database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None or not user.is_active:
        return None
    
    return user 