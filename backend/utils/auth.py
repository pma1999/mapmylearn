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

# Startup-time check to ensure bcrypt backend is usable.
# If the bcrypt C-extension or compatible wheel is missing, this will raise an informative error
# explaining how to remediate (pin bcrypt, install wheel, or skip check in CI).
if os.getenv("SKIP_BCRYPT_CHECK", "false").lower() not in ("1", "true", "yes", "y"):
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    try:
        # Perform a quick hash/verify to detect backend availability.
        # Use a non-sensitive constant so logs don't accidentally contain real secrets.
        _healthcheck_secret = "passlib_bcrypt_healthcheck_please_replace"
        _sample_hash = pwd_context.hash(_healthcheck_secret)
        if not pwd_context.verify(_healthcheck_secret, _sample_hash):
            raise RuntimeError("passlib bcrypt verify failed during startup self-check")
    except Exception as _exc:
        # Try to report bcrypt package version if available
        try:
            import bcrypt as _bcrypt_pkg
            _bcrypt_ver = getattr(_bcrypt_pkg, "__version__", "unknown")
        except Exception:
            _bcrypt_ver = None
        _msg = (
            "Critical: passlib/bcrypt runtime check failed.\n\n"
            "This usually means the 'bcrypt' dependency or its compiled wheel is missing or incompatible with "
            "your Python runtime. Recommended remediation steps:\n\n"
            " 1) Ensure 'bcrypt' is installed and matches your Python version: "
            "pip install 'bcrypt==3.2.0'\n"
            " 2) Pin 'passlib[bcrypt]' and 'bcrypt==3.2.0' in your requirements.txt and rebuild your environment.\n"
            " 3) On Windows, prefer installing a prebuilt wheel or use WSL where wheels are available.\n"
            " 4) If running in CI where installing compiled packages is difficult, set SKIP_BCRYPT_CHECK=true to bypass "
            "this check (NOT recommended for production).\n\n"
            f"Detected bcrypt package version: {_bcrypt_ver!r}. Original error: {_exc!r}"
        )
        _logger.critical(_msg)
        # Fail fast so maintainers see and correct environment issues early.
        raise RuntimeError(_msg) from _exc


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
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return None

        exp_dt: Optional[datetime] = None
        if exp is not None:
            try:
                exp_dt = datetime.fromtimestamp(float(exp))
            except (TypeError, ValueError, OverflowError):
                # Invalid exp value
                return None

        return TokenData(user_id=user_id_int, email=email, exp=exp_dt)
    except JWTError:
        return None
