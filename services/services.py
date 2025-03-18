import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatPerplexity

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_llm(api_key=None):
    """
    Initialize the LLM with either provided API key or from environment variables.
    
    Args:
        api_key: Optional explicit OpenAI API key
        
    Returns:
        Initialized ChatOpenAI instance
    """
    openai_api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.warning("OPENAI_API_KEY not set")
        logger.debug("No OpenAI API key provided in state or environment variables")
    else:
        logger.debug(f"Using {'provided' if api_key else 'environment'} OpenAI API key")
    
    try:
        return ChatOpenAI(temperature=0.2, model="gpt-4o-mini", api_key=openai_api_key)
    except Exception as e:
        logger.error(f"Error initializing ChatOpenAI: {str(e)}")
        if not openai_api_key:
            logger.error("OpenAI API key is required. Make sure to provide a valid API key.")
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

def validate_openai_key(api_key):
    """
    Validate if the OpenAI API key is correctly formatted and functional.
    
    Args:
        api_key: OpenAI API key to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    if not api_key or not isinstance(api_key, str):
        return False, "API key must be a non-empty string"
        
    if not api_key.startswith("sk-") or len(api_key) < 20:
        return False, "Invalid OpenAI API key format"
        
    try:
        # Minimal test to validate key functionality
        llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", api_key=api_key, max_tokens=5)
        llm.invoke("test")
        return True, None
    except Exception as e:
        return False, f"API key validation failed: {str(e)}"
        
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
