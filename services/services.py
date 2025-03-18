import os
import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatPerplexity

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_llm(api_key=None):
    """
    Initialize the Google Gemini LLM with provided API key or from environment variables.
    
    Args:
        api_key: Optional explicit Google API key
        
    Returns:
        Initialized ChatGoogleGenerativeAI instance
    """
    google_api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not google_api_key:
        logger.warning("GOOGLE_API_KEY not set")
        logger.debug("No Google API key provided in state or environment variables")
    else:
        logger.debug(f"Using {'provided' if api_key else 'environment'} Google API key")
    
    try:
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-pro-exp-02-05",
            temperature=0.2,
            google_api_key=google_api_key,
        )
    except Exception as e:
        logger.error(f"Error initializing ChatGoogleGenerativeAI: {str(e)}")
        if not google_api_key:
            logger.error("Google API key is required. Make sure to provide a valid API key.")
        raise

def get_search_tool(api_key=None):
    """
    Initialize the Perplexity LLM search tool with either provided API key or from environment variables.
    
    Args:
        api_key: Optional explicit Perplexity API key
        
    Returns:
        Initialized ChatPerplexity instance
    """
    perplexity_api_key = api_key or os.environ.get("PPLX_API_KEY")
    if not perplexity_api_key:
        logger.warning("PPLX_API_KEY not set")
        logger.debug("No Perplexity API key provided in state or environment variables")
    else:
        logger.debug(f"Using {'provided' if api_key else 'environment'} Perplexity API key")
    
    try:
        # Using the sonar model which has search capabilities
        return ChatPerplexity(
            temperature=0.2,
            model="sonar",
            pplx_api_key=perplexity_api_key
        )
    except Exception as e:
        logger.error(f"Error initializing ChatPerplexity: {str(e)}")
        if not perplexity_api_key:
            logger.error("Perplexity API key is required. Make sure to provide a valid API key.")
        raise

def validate_google_key(api_key):
    """
    Validate if the Google API key is functional.
    
    Args:
        api_key: Google API key to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    if not api_key or not isinstance(api_key, str):
        return False, "API key must be a non-empty string"
    
    try:
        # Minimal test to validate key functionality
        llm = ChatGoogleGenerativeAI(
            temperature=0,
            model="gemini-2.0-pro-exp-02-05",
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
    if not api_key or not isinstance(api_key, str):
        return False, "API key must be a non-empty string"
        
    if len(api_key) < 20:
        return False, "Invalid Perplexity API key format"
        
    try:
        # Minimal test to validate key functionality
        model = ChatPerplexity(temperature=0, model="sonar", pplx_api_key=api_key)
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
