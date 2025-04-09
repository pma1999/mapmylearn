"""
Key provider service.

This module provides a secure way to retrieve API keys only when needed,
without storing them in permanent state structures.
"""

import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime
from backend.services.key_management import ApiKeyManager
from backend.services.usage_tracker import UsageTracker

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
    - Keys are now primarily provided by the server from environment variables
    - Legacy support for user-provided keys remains but is not the primary path
    - Prepares for usage tracking for future credit system
    - Keys are never stored in the object's state
    - Keys are retrieved only at the moment they are needed
    """
    
    def __init__(self, key_type: str, token_or_key: Optional[str] = None, user_id: Optional[str] = None):
        """
        Initialize a key provider.
        
        Args:
            key_type: Type of key ('google' or 'perplexity')
            token_or_key: Optional token for retrieving the key or direct API key
                         (if None, uses server-provided keys)
            user_id: Optional user identifier for usage tracking
        """
        self.key_type = key_type
        self.token_or_key = token_or_key
        self.user_id = user_id
        self._is_direct_key = token_or_key is not None and (
            (key_type == "google" and token_or_key.startswith("AIza")) or
            (key_type == "perplexity" and token_or_key.startswith("pplx-"))
        )
        self.use_server_keys = True  # New flag to indicate server-provided keys
        self.operation = "api_call"  # Default operation, can be updated
        
    async def get_key(self) -> str:
        """
        Get the actual API key at the point of use.
        
        Returns:
            str: The API key
            
        Raises:
            ValueError: If no valid key can be retrieved
        """
        key_manager = get_key_manager()
        
        # First try to get the key from environment variables (server-provided)
        server_key = key_manager.get_env_key(self.key_type)
        if server_key:
            # Track usage for the future credit system
            await self._track_key_usage(server_key, True)
            logger.info(f"Using server-provided {self.key_type} API key")
            return server_key
        
        # If we were given a direct API key (legacy support), use it as fallback
        if self._is_direct_key:
            await self._track_key_usage(self.token_or_key, False)
            logger.info(f"Using direct {self.key_type} API key (legacy support)")
            return self.token_or_key
            
        # Try to get the key from the token (legacy support)
        if self.token_or_key and not self._is_direct_key:
            try:
                user_key = key_manager.get_key(self.token_or_key, self.key_type)
                await self._track_key_usage(user_key, False)
                logger.info(f"Using token-based {self.key_type} API key (legacy support)")
                return user_key
            except ValueError as e:
                logger.warning(f"Failed to get {self.key_type} key from token: {str(e)}")
                # Continue to try environment variables
        
        # If we reach this point, we couldn't retrieve a valid key
        raise ValueError(f"No valid {self.key_type} API key available. Server configuration issue.")
    
    def set_operation(self, operation: str) -> 'KeyProvider':
        """
        Set the operation being performed with this key.
        
        Args:
            operation: The operation name (e.g., 'generate_learning_path')
            
        Returns:
            Self for method chaining
        """
        self.operation = operation
        return self
    
    async def _track_key_usage(self, key: str, is_server_key: bool) -> None:
        """
        Track API key usage for future credit system.
        
        Args:
            key: The API key being used
            is_server_key: Whether this is a server-provided key
        """
        # Create metadata with masked key for tracking
        masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 10 else "***masked***"
        metadata = {
            "masked_key": masked_key,
            "is_server_key": is_server_key
        }
        
        # Use the usage tracker to record this API call
        await UsageTracker.record_usage(
            user_id=self.user_id,
            key_type=self.key_type,
            is_server_key=is_server_key,
            operation=self.operation,
            metadata=metadata
        )
        
    def __repr__(self) -> str:
        """Safe string representation that doesn't expose the key."""
        if self.use_server_keys:
            return f"{self.__class__.__name__}(key_type={self.key_type}, server_provided=True)"
        if self._is_direct_key:
            return f"{self.__class__.__name__}(key_type={self.key_type}, direct_key=True)"
        if self.token_or_key:
            truncated = self.token_or_key[:7] + "..."
            return f"{self.__class__.__name__}(key_type={self.key_type}, token={truncated})"
        return f"{self.__class__.__name__}(key_type={self.key_type}, using_env=True)"


class GoogleKeyProvider(KeyProvider):
    """Key provider specialized for Google API keys."""
    
    def __init__(self, token_or_key: Optional[str] = None, user_id: Optional[str] = None):
        """Initialize with google key type."""
        super().__init__("google", token_or_key, user_id)


class PerplexityKeyProvider(KeyProvider):
    """Key provider specialized for Perplexity API keys."""
    
    def __init__(self, token_or_key: Optional[str] = None, user_id: Optional[str] = None):
        """Initialize with perplexity key type."""
        super().__init__("perplexity", token_or_key, user_id) 