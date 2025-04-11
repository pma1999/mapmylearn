"""
Secure API key management service.

This module provides secure storage and retrieval of API keys using a token-based system.
Keys are stored securely with encryption and accessible only with valid tokens.
"""

import os
import time
import uuid
import logging
import secrets
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import re

logger = logging.getLogger(__name__)

# Default token expiration time (24 hours)
DEFAULT_TOKEN_EXPIRY = 60 * 60 * 24  # 24 hours in seconds


class ApiKeyManager:
    """
    Secure API key manager that stores keys with encryption and provides token-based access.
    
    This class provides:
    - Secure storage of API keys with encryption
    - Token generation for referencing keys
    - Time-limited token expiration
    - Validation of key formats
    - Fallback to environment variables
    """
    
    def __init__(self, server_secret: Optional[str] = None, token_expiry: int = DEFAULT_TOKEN_EXPIRY):
        """
        Initialize the API key manager.
        
        Args:
            server_secret: Secret used for encryption (defaults to env var or generates one)
            token_expiry: Time in seconds until tokens expire (default 24 hours)
            
        Raises:
            ValueError: In production environment, if SERVER_SECRET_KEY is not provided
        """
        # Check if running in production environment
        is_production = self._is_production_environment()
        
        # Set up encryption
        self.server_secret = server_secret or os.environ.get("SERVER_SECRET_KEY")
        
        # In production, require SERVER_SECRET_KEY to be set
        if is_production and not self.server_secret:
            error_msg = ("In production, SERVER_SECRET_KEY must be set. "
                         "Aborting startup to prevent insecure operation.")
            logger.critical(error_msg)
            raise ValueError(error_msg)
            
        if not self.server_secret:
            # Generate a secret if none provided (note: will cause tokens to invalidate on restart)
            self.server_secret = secrets.token_hex(32)
            logger.warning("No SERVER_SECRET_KEY provided. Generated temporary secret. "
                           "This will cause tokens to invalidate on server restart.")
        
        # Use the server secret to derive an encryption key
        salt = b'learncompass_api_key_manager'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.server_secret.encode()))
        self.cipher = Fernet(key)
        
        # Token configuration
        self.token_expiry = token_expiry
        
        # In-memory secure storage
        self._key_store: Dict[str, Dict[str, Any]] = {}
        self._token_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Key types
        self.KEY_TYPE_GOOGLE = "google"
        self.KEY_TYPE_PERPLEXITY = "perplexity"
        
        logger.info("API Key Manager initialized")

    def _is_production_environment(self) -> bool:
        """
        Determine if the application is running in a production environment.
        
        Returns:
            bool: True if in production, False otherwise
        """
        # Check for Railway-specific environment variables
        if os.environ.get("RAILWAY_STATIC_URL"):
            return True
            
        # Check for explicit ENVIRONMENT variable
        if os.environ.get("ENVIRONMENT", "").lower() == "production":
            return True
            
        return False

    def _encrypt(self, value: str) -> str:
        """Encrypt a value using the cipher."""
        return self.cipher.encrypt(value.encode()).decode()
    
    def _decrypt(self, encrypted_value: str) -> str:
        """Decrypt a value using the cipher."""
        try:
            return self.cipher.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {str(e)}")
            raise ValueError("Invalid or corrupted encrypted value")
    
    def _generate_token(self) -> str:
        """Generate a unique token for API key reference."""
        return str(uuid.uuid4())
    
    def validate_key_format(self, key_type: str, key_value: str) -> bool:
        """
        Validate the format of an API key using regex patterns.
        
        Args:
            key_type: Type of key ('google' or 'perplexity')
            key_value: The API key to validate
            
        Returns:
            bool: True if the key format is valid
        """
        if not key_value or not isinstance(key_value, str):
            return False
            
        if key_type == self.KEY_TYPE_GOOGLE:
            # Google API keys start with 'AIza' followed by 35 alphanumeric characters
            pattern = r'^AIza[0-9A-Za-z_-]{35}$'
            return bool(re.match(pattern, key_value))
        
        elif key_type == self.KEY_TYPE_PERPLEXITY:
            # Perplexity API keys start with 'pplx-' followed by alphanumeric characters
            pattern = r'^pplx-[0-9A-Za-z]{32,}$'
            return bool(re.match(pattern, key_value))
            
        return False
    
    def store_key(self, key_type: str, key_value: str, ip_address: Optional[str] = None) -> str:
        """
        Securely store an API key and return a token for future access.
        
        Args:
            key_type: Type of key ('google' or 'perplexity')
            key_value: The API key to store
            ip_address: Optional IP address for additional security
            
        Returns:
            str: Token that can be used to retrieve the key
        """
        if not self.validate_key_format(key_type, key_value):
            raise ValueError(f"Invalid {key_type} API key format")
        
        # Generate a unique token
        token = self._generate_token()
        
        # Create expiration timestamp
        expiry_time = datetime.now() + timedelta(seconds=self.token_expiry)
        
        # Encrypt the key
        encrypted_key = self._encrypt(key_value)
        
        # Store the encrypted key
        self._key_store[token] = {
            "key_type": key_type,
            "encrypted_value": encrypted_key,
            "created_at": datetime.now().isoformat(),
        }
        
        # Store token metadata
        self._token_metadata[token] = {
            "key_type": key_type,
            "expires_at": expiry_time.isoformat(),
            "ip_address": ip_address,
            "last_used": datetime.now().isoformat()
        }
        
        logger.info(f"Stored {key_type} API key with token {token[:8]}... (expires {expiry_time.isoformat()})")
        return token
    
    def get_key(self, token: str, key_type: str, ip_address: Optional[str] = None) -> str:
        """
        Retrieve an API key using its token.
        
        Args:
            token: The token referencing the API key
            key_type: Type of key to validate against
            ip_address: Optional IP address for validation
            
        Returns:
            str: The decrypted API key
            
        Raises:
            ValueError: If token is invalid, expired, or key_type doesn't match
        """
        # Check if token exists
        if token not in self._key_store or token not in self._token_metadata:
            logger.warning(f"Invalid token {token[:8] if token else 'None'}...")
            raise ValueError("Invalid token")
        
        # Get metadata
        metadata = self._token_metadata[token]
        
        # Check key type
        if metadata["key_type"] != key_type:
            logger.warning(f"Key type mismatch for token {token[:8]}...")
            raise ValueError(f"Token is for {metadata['key_type']} API key, not {key_type}")
        
        # Check expiration
        expiry_time = datetime.fromisoformat(metadata["expires_at"])
        if datetime.now() > expiry_time:
            logger.warning(f"Expired token {token[:8]}... (expired {expiry_time.isoformat()})")
            # Remove expired entries
            self._key_store.pop(token, None)
            self._token_metadata.pop(token, None)
            raise ValueError("Token has expired")
        
        # Optionally check IP address
        if ip_address and metadata.get("ip_address") and metadata["ip_address"] != ip_address:
            logger.warning(f"IP address mismatch for token {token[:8]}...")
            raise ValueError("Token cannot be used from this IP address")
        
        # Update last used timestamp
        metadata["last_used"] = datetime.now().isoformat()
        
        # Get and decrypt the key
        encrypted_key = self._key_store[token]["encrypted_value"]
        key = self._decrypt(encrypted_key)
        
        logger.debug(f"Retrieved {key_type} API key with token {token[:8]}...")
        return key
    
    def update_token_expiry(self, token: str, new_expiry: Optional[int] = None) -> bool:
        """
        Update the expiration time of a token.
        
        Args:
            token: The token to update
            new_expiry: New expiration time in seconds from now (uses default if None)
            
        Returns:
            bool: True if successful, False if token not found
        """
        if token not in self._token_metadata:
            return False
        
        expiry_seconds = new_expiry if new_expiry is not None else self.token_expiry
        new_expiry_time = datetime.now() + timedelta(seconds=expiry_seconds)
        self._token_metadata[token]["expires_at"] = new_expiry_time.isoformat()
        
        logger.debug(f"Updated expiry for token {token[:8]}... to {new_expiry_time.isoformat()}")
        return True
    
    def delete_token(self, token: str) -> bool:
        """
        Delete a token and its associated API key.
        
        Args:
            token: The token to delete
            
        Returns:
            bool: True if successful, False if token not found
        """
        key_deleted = self._key_store.pop(token, None) is not None
        meta_deleted = self._token_metadata.pop(token, None) is not None
        
        if key_deleted or meta_deleted:
            logger.debug(f"Deleted token {token[:8]}...")
            return True
        return False
    
    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens.
        
        Returns:
            int: Number of tokens deleted
        """
        now = datetime.now()
        tokens_to_delete = []
        
        for token, metadata in self._token_metadata.items():
            expiry_time = datetime.fromisoformat(metadata["expires_at"])
            if now > expiry_time:
                tokens_to_delete.append(token)
        
        count = 0
        for token in tokens_to_delete:
            if self.delete_token(token):
                count += 1
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired tokens")
        return count
        
    def get_env_key(self, key_type: str) -> Optional[str]:
        """
        Get an API key from environment variables.
        
        Args:
            key_type: Type of key ('google' or 'perplexity')
            
        Returns:
            Optional[str]: The API key if found and valid, None otherwise
        """
        if key_type == self.KEY_TYPE_GOOGLE:
            key = os.environ.get("GOOGLE_API_KEY")
        elif key_type == self.KEY_TYPE_PERPLEXITY:
            key = os.environ.get("PPLX_API_KEY")
        else:
            logger.warning(f"Unknown key type: {key_type}")
            return None
        
        if key and self.validate_key_format(key_type, key):
            logger.debug(f"Retrieved {key_type} API key from environment variables")
            return key
        
        if key:
            logger.warning(f"Invalid {key_type} API key format in environment variables")
        else:
            logger.warning(f"No {key_type} API key found in environment variables")
        
        return None 