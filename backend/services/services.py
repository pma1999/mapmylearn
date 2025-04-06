import os
import logging
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatPerplexity
from typing import Optional, Union, Tuple, Any

# Import key provider for type hints but with proper import protection
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.services.key_provider import KeyProvider, GoogleKeyProvider, PerplexityKeyProvider

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_llm(key_provider=None):
    """
    Initialize the Google Gemini LLM with a key from the provider or directly.
    
    Args:
        key_provider: KeyProvider object for Google API key (or direct API key as string)
        
    Returns:
        Initialized ChatGoogleGenerativeAI instance
    """
    google_api_key = None
    
    # Handle different input types
    if hasattr(key_provider, 'get_key') and callable(key_provider.get_key):
        # It's a KeyProvider
        try:
            google_api_key = await key_provider.get_key()
            logger.debug("Retrieved Google API key from provider")
        except Exception as e:
            logger.error(f"Error retrieving Google API key from provider: {str(e)}")
            raise
    elif isinstance(key_provider, str):
        # Direct API key
        google_api_key = key_provider
        logger.debug("Using provided Google API key directly")
    else:
        # Fallback to environment
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        if not google_api_key:
            logger.warning("GOOGLE_API_KEY not set in environment")
        else:
            logger.debug("Using Google API key from environment")
    
    if not google_api_key:
        raise ValueError("No Google API key available from any source")
    
    try:
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.2,
            google_api_key=google_api_key,
            max_output_tokens=8192,
        )
    except Exception as e:
        logger.error(f"Error initializing ChatGoogleGenerativeAI: {str(e)}")
        raise

async def get_search_tool(key_provider=None):
    """
    Initialize the Perplexity LLM search tool with a key from the provider or directly.
    
    Args:
        key_provider: KeyProvider object for Perplexity API key (or direct API key as string)
        
    Returns:
        Initialized ChatPerplexity instance
    """
    perplexity_api_key = None
    
    # Handle different input types
    if hasattr(key_provider, 'get_key') and callable(key_provider.get_key):
        # It's a KeyProvider
        try:
            perplexity_api_key = await key_provider.get_key()
            logger.debug("Retrieved Perplexity API key from provider")
        except Exception as e:
            logger.error(f"Error retrieving Perplexity API key from provider: {str(e)}")
            raise
    elif isinstance(key_provider, str):
        # Direct API key
        perplexity_api_key = key_provider
        logger.debug("Using provided Perplexity API key directly")
    else:
        # Fallback to environment
        perplexity_api_key = os.environ.get("PPLX_API_KEY")
        if not perplexity_api_key:
            logger.warning("PPLX_API_KEY not set in environment")
        else:
            logger.debug("Using Perplexity API key from environment")
    
    if not perplexity_api_key:
        raise ValueError("No Perplexity API key available from any source")
    
    try:
        # Add Referer header to help return citations
        # The Perplexity API may use this to include citation links
        headers = {"Referer": "https://www.perplexity.ai/"}
        
        # Using the sonar model which has search capabilities
        return ChatPerplexity(
            temperature=0.2,
            model="sonar",
            max_tokens=8000,  # Set to 8000 for normal operation
            pplx_api_key=perplexity_api_key,
            extra_headers=headers
        )
    except Exception as e:
        if "extra_headers" in str(e):
            # Fallback if extra_headers param is not supported in this version
            logger.warning("extra_headers not supported, falling back to standard initialization")
            return ChatPerplexity(
                temperature=0.2,
                model="sonar",
                max_tokens=8000,
                pplx_api_key=perplexity_api_key
            )
        logger.error(f"Error initializing ChatPerplexity: {str(e)}")
        raise

def validate_google_key(api_key):
    """
    Validate if the Google API key is functional.
    
    Args:
        api_key: Google API key to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    # Initial format validation
    if not api_key or not isinstance(api_key, str):
        return False, "API key must be a non-empty string"
    
    # Google API key format validation
    pattern = r'^AIza[0-9A-Za-z_-]{35}$'
    if not re.match(pattern, api_key):
        return False, "Invalid Google API key format - must start with 'AIza' followed by 35 characters"
    
    try:
        # Minimal test to validate key functionality
        llm = ChatGoogleGenerativeAI(
            temperature=0,
            model="gemini-2.0-flash",
            google_api_key=api_key,
            max_output_tokens=5
        )
        llm.invoke("test")
        return True, None
    except Exception as e:
        error_str = str(e)
        
        # Check for specific error cases
        if "invalid api key" in error_str.lower():
            return False, "Invalid Google API key format or key not activated"
        
        if "permission" in error_str.lower() or "access" in error_str.lower():
            return False, "API key error: Insufficient permissions or access denied"
        
        if "quota" in error_str.lower() or "limit" in error_str.lower():
            return False, "API key error: Quota exceeded or rate limits reached"
        
        # Default error message
        return False, f"API key validation failed: {error_str}"
        
def validate_perplexity_key(api_key):
    """
    Validate if the Perplexity API key is correctly formatted and functional.
    
    Args:
        api_key: Perplexity API key to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    # Initial format validation
    if not api_key or not isinstance(api_key, str):
        return False, "API key must be a non-empty string"
    
    # Perplexity API key format validation
    pattern = r'^pplx-[0-9A-Za-z]{32,}$'
    if not re.match(pattern, api_key):
        return False, "Invalid Perplexity API key format - must start with 'pplx-' followed by at least 32 characters"
    
    try:
        # Minimal test to validate key functionality
        model = ChatPerplexity(temperature=0, model="sonar", max_tokens=1, pplx_api_key=api_key)  # Minimum tokens for validation
        model.invoke("test")
        return True, None
    except Exception as e:
        error_str = str(e)
        
        # Check for specific error cases and provide more helpful messages
        if "403" in error_str and "Forbidden" in error_str:
            return False, "API key error: Access forbidden. This may be due to an invalid API key or your account has run out of available credits."
        
        if "401" in error_str and "Unauthorized" in error_str:
            return False, "API key error: Unauthorized access. The API key appears to be invalid or has been revoked."
        
        if "429" in error_str and "Too Many Requests" in error_str:
            return False, "API key error: Rate limit exceeded. Your account has made too many requests. Please try again later."
        
        # Default error message if none of the specific cases match
        return False, f"API key validation failed: {error_str}"
