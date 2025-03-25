"""
Key provider service.

This module provides a secure way to retrieve API keys only when needed,
without storing them in permanent state structures.
"""

import logging
from typing import Optional
from backend.services.key_management import ApiKeyManager

logger = logging.getLogger(__name__)

# Singleton instance of ApiKeyManager
_key_manager = None

def get_key_manager() -> ApiKeyManager:
    """Get or create the ApiKeyManager singleton instance."""
    global _key_manager
    if _key_manager is None:
        _key_manager = ApiKeyManager()
    return _key_manager


class KeyProvider:
    """
    Key provider that retrieves actual API keys only when needed.
    
    This class provides a secure way to handle API keys:
    - Keys are never stored in the object's state
    - Keys are retrieved only at the moment they are needed
    - Supports both token-based and environment variable keys
    - Provides safe fallback mechanism
    """
    
    def __init__(self, key_type: str, token_or_key: Optional[str] = None):
        """
        Initialize a key provider.
        
        Args:
            key_type: Type of key ('google' or 'perplexity')
            token_or_key: Optional token for retrieving the key or direct API key
                         (if None, uses env vars)
        """
        self.key_type = key_type
        self.token_or_key = token_or_key
        self._is_direct_key = token_or_key is not None and (
            (key_type == "google" and token_or_key.startswith("AIza")) or
            (key_type == "perplexity" and token_or_key.startswith("pplx-"))
        )
        
    async def get_key(self) -> str:
        """
        Get the actual API key at the point of use.
        
        Returns:
            str: The API key
            
        Raises:
            ValueError: If no valid key can be retrieved
        """
        # If we were given a direct API key, just return it
        if self._is_direct_key:
            return self.token_or_key
            
        key_manager = get_key_manager()
        
        # Try to get the key from the token first
        if self.token_or_key and not self._is_direct_key:
            try:
                return key_manager.get_key(self.token_or_key, self.key_type)
            except ValueError as e:
                logger.warning(f"Failed to get {self.key_type} key from token: {str(e)}")
                # Fall through to environment variables
        
        # Try to get the key from environment variables
        env_key = key_manager.get_env_key(self.key_type)
        if env_key:
            return env_key
        
        # If we get here, we couldn't retrieve a valid key
        raise ValueError(f"No valid {self.key_type} API key available. Please provide a valid API key or set it in environment variables.")
        
    def __repr__(self) -> str:
        """Safe string representation that doesn't expose the key."""
        if self._is_direct_key:
            return f"{self.__class__.__name__}(key_type={self.key_type}, direct_key=True)"
        if self.token_or_key:
            truncated = self.token_or_key[:7] + "..."
            return f"{self.__class__.__name__}(key_type={self.key_type}, token={truncated})"
        return f"{self.__class__.__name__}(key_type={self.key_type}, using_env=True)"


class GoogleKeyProvider(KeyProvider):
    """Key provider specialized for Google API keys."""
    
    def __init__(self, token_or_key: Optional[str] = None):
        """Initialize with google key type."""
        super().__init__("google", token_or_key)


class PerplexityKeyProvider(KeyProvider):
    """Key provider specialized for Perplexity API keys."""
    
    def __init__(self, token_or_key: Optional[str] = None):
        """Initialize with perplexity key type."""
        super().__init__("perplexity", token_or_key) 