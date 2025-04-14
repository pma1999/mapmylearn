import os
import secrets # Added for secure random tokens
import hashlib # Added for hashing tokens
from typing import Optional, Tuple # Adjusted imports
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get settings from environment variables
# Use a dedicated secret for email verification, fallback to JWT secret if not set
EMAIL_VERIFICATION_SECRET_KEY = os.getenv("EMAIL_VERIFICATION_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "DEFAULT_FALLBACK_SECRET_KEY_CHANGE_ME"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000") # Default for local dev

# Initialize serializer
serializer = URLSafeTimedSerializer(EMAIL_VERIFICATION_SECRET_KEY)

# Define salt for email verification context
EMAIL_VERIFICATION_SALT = 'email-verification'

def generate_verification_token(user_id: int) -> str:
    """Generates a signed, timed token containing the user ID for email verification."""
    return serializer.dumps(user_id, salt=EMAIL_VERIFICATION_SALT)

def verify_verification_token(token: str, max_age_seconds: int = 3600) -> Optional[int]:
    """
    Verifies the signature and expiry of an email verification token.
    Returns the user ID if valid and not expired, otherwise None.
    Default max_age is 1 hour (3600 seconds).
    """
    try:
        user_id = serializer.loads(
            token,
            salt=EMAIL_VERIFICATION_SALT,
            max_age=max_age_seconds 
        )
        return int(user_id) # Ensure it's an integer
    except SignatureExpired:
        print("Verification token expired")
        return None
    except BadSignature:
        print("Invalid verification token signature")
        return None
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None

def get_verification_link(token: str) -> str:
    """Constructs the full verification link for the frontend."""
    # Ensure frontend URL doesn't have a trailing slash
    base_url = FRONTEND_URL.rstrip('/')
    return f"{base_url}/verify-email?token={token}"

# --- Password Reset Token Functions ---

PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 30

def generate_password_reset_token() -> Tuple[str, str]:
    """Generates a secure random token and its SHA-256 hash.

    Returns:
        Tuple[str, str]: (raw_token, hashed_token_hex)
    """
    raw_token = secrets.token_urlsafe(32) # Generate a 32-byte (256-bit) URL-safe token
    hashed_token = hashlib.sha256(raw_token.encode('utf-8')).digest() # Hash the token
    hashed_token_hex = hashed_token.hex() # Get hex representation for storage
    return raw_token, hashed_token_hex

def hash_token(token: str) -> str:
    """Hashes a given token using SHA-256.

    Args:
        token (str): The raw token to hash.

    Returns:
        str: The hex representation of the hashed token.
    """
    hashed_token = hashlib.sha256(token.encode('utf-8')).digest()
    return hashed_token.hex()

def get_password_reset_link(token: str) -> str:
    """Constructs the full password reset link for the frontend."""
    base_url = FRONTEND_URL.rstrip('/')
    return f"{base_url}/reset-password/{token}" # Changed path and token placement 