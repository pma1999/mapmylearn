from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr

# Load environment variables
load_dotenv()

# Get JWT settings from environment variables or use defaults
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "REPLACE_WITH_SECURE_SECRET_KEY_IN_PRODUCTION")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Model for token data extracted from JWT."""
    user_id: int
    email: EmailStr
    exp: Optional[datetime] = None


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT access token.
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Create JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode a JWT access token and return the token data if valid.
    Returns None if token is invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        exp = payload.get("exp")
        
        if user_id is None or email is None:
            return None
        
        # Convert user_id to int and exp to datetime, handling potential errors
        try:
            return TokenData(user_id=int(user_id), email=email, exp=datetime.fromtimestamp(exp))
        except ValueError:
             # Handle cases where user_id is not a valid int or exp is not a valid timestamp
             return None
    except JWTError:
        return None 