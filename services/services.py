import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

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
    try:
        return ChatOpenAI(temperature=0.2, model="gpt-4o-mini", api_key=openai_api_key)
    except Exception as e:
        logger.error(f"Error initializing ChatOpenAI: {str(e)}")
        raise

def get_search_tool(api_key=None):
    """
    Initialize the search tool with either provided API key or from environment variables.
    
    Args:
        api_key: Optional explicit Tavily API key
        
    Returns:
        Initialized TavilySearchResults instance
    """
    tavily_api_key = api_key or os.environ.get("TAVILY_API_KEY")
    if not tavily_api_key:
        logger.warning("TAVILY_API_KEY not set")
    try:
        return TavilySearchResults(max_results=5, tavily_api_key=tavily_api_key)
    except Exception as e:
        logger.error(f"Error initializing TavilySearchResults: {str(e)}")
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
        
def validate_tavily_key(api_key):
    """
    Validate if the Tavily API key is correctly formatted and functional.
    
    Args:
        api_key: Tavily API key to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    if not api_key or not isinstance(api_key, str):
        return False, "API key must be a non-empty string"
        
    if not api_key.startswith("tvly-") or len(api_key) < 20:
        return False, "Invalid Tavily API key format"
        
    try:
        # Minimal test to validate key functionality
        search_tool = TavilySearchResults(max_results=1, tavily_api_key=api_key)
        search_tool.invoke({"query": "test"})
        return True, None
    except Exception as e:
        return False, f"API key validation failed: {str(e)}"
