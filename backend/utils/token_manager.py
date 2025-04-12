import os
from typing import Optional
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