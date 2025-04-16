import os
import logging
import re
import asyncio
import aiohttp
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from typing import Optional, Union, Tuple, Any
from bs4 import BeautifulSoup

# Import models directly for runtime use
from backend.models.models import SearchServiceResult, ScrapedResult

# Import key provider for type hints but with proper import protection
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.services.key_provider import KeyProvider, GoogleKeyProvider, TavilyKeyProvider
    # Keep models here for type checking if needed, but they are already imported above
    # from backend.models.models import SearchServiceResult, ScrapedResult 

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

async def _scrape_single_url(session: aiohttp.ClientSession, url: str, timeout: int) -> Tuple[Optional[str], Optional[str]]:
    """Scrapes cleaned textual content from a single URL.

    Args:
        session: The aiohttp client session.
        url: The URL to scrape.
        timeout: Request timeout in seconds.

    Returns:
        A tuple containing (scraped_content, error_message).
        scraped_content is None if an error occurred.
        error_message is None if scraping was successful.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; LearniBot/1.0; +https://github.com/your-repo)'} # Be polite and identifiable
    try:
        async with session.get(url, timeout=timeout, headers=headers, ssl=False) as response: # Consider ssl=False implications
            response.raise_for_status() # Raise error for bad responses (4xx or 5xx)
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                return None, f"Skipped: Non-HTML content ({content_type})"

            html_content = await response.text()
            # Basic cleaning with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove common non-content tags
            for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'form', 'button', 'input', 'textarea']):
                tag.decompose()

            # Attempt to find main content areas (common patterns)
            main_content = soup.find('main') or soup.find('article') or soup.find('div', role='main') or soup.find('div', id='content') or soup.find('div', class_='content')

            # Fallback to body if no main content area is found
            target_element = main_content if main_content else soup.find('body')

            if target_element:
                # Extract text, trying to preserve some structure with newlines
                clean_text = target_element.get_text(separator='\n', strip=True)
            else:
                clean_text = "Could not extract body or main content"

            # Optional: Further cleaning (e.g., excessive whitespace)
            clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text) # Consolidate multiple newlines

            # Limit content size if needed
            MAX_SCRAPE_LENGTH = 30000 # Limit to 30k characters
            if len(clean_text) > MAX_SCRAPE_LENGTH:
               clean_text = clean_text[:MAX_SCRAPE_LENGTH] + "... (truncated)"

            return clean_text, None

    except asyncio.TimeoutError:
        logger.warning(f"Scrape timed out for {url} after {timeout}s")
        return None, f"Scrape timed out after {timeout}s"
    except aiohttp.ClientResponseError as e:
        logger.warning(f"HTTP error scraping {url}: {e.status} {e.message}")
        return None, f"HTTP error: {e.status}"
    except aiohttp.ClientError as e:
        # Handles connection errors, etc.
        logger.warning(f"Client error scraping {url}: {type(e).__name__}")
        return None, f"Scraping error: {type(e).__name__}"
    except Exception as e:
        # Catch other potential errors (e.g., BeautifulSoup parsing)
        logger.error(f"Unexpected error scraping {url}: {type(e).__name__} - {str(e)}", exc_info=True)
        return None, f"Unexpected scraping error: {type(e).__name__}"

async def perform_search_and_scrape(
    query: str,
    tavily_key_provider: 'TavilyKeyProvider',
    max_results: int = 5,
    scrape_timeout: int = 10
) -> 'SearchServiceResult':
    """Performs Tavily search and scrapes results concurrently.

    Args:
        query: The search query.
        tavily_key_provider: The key provider instance for Tavily.
        max_results: Maximum number of search results to retrieve from Tavily.
        scrape_timeout: Timeout in seconds for each scrape request.

    Returns:
        A SearchServiceResult object containing the query, scraped results,
        and any potential errors.
    """
    # Removed lazy import as it's now imported at module level
    # from backend.models.models import SearchServiceResult, ScrapedResult 

    logger.info(f"Performing search and scrape for query: '{query}'")
    service_result = SearchServiceResult(query=query)
    api_key = None

    try:
        api_key = await tavily_key_provider.get_key()
        tavily_search = TavilySearch(
            max_results=max_results,
            include_raw_content=False,
            include_answer=False,
            tavily_api_key=api_key
        )

        logger.debug(f"Invoking Tavily search for: '{query}'")
        tavily_response = await tavily_search.ainvoke({"query": query})
        logger.debug(f"Received Tavily response for: '{query}'")

        scrape_tasks = []
        tavily_results = tavily_response.get("results", [])

        if not isinstance(tavily_results, list):
            raise ValueError(f"Unexpected Tavily response format: 'results' is not a list. Response: {tavily_response}")

        urls_to_scrape = []
        tavily_result_map = {}
        for result in tavily_results:
            if isinstance(result, dict) and "url" in result and result["url"]:
                url = result["url"]
                if url not in urls_to_scrape:
                    urls_to_scrape.append(url)
                    tavily_result_map[url] = result
            else:
                logger.warning(f"Skipping invalid or incomplete Tavily result item: {result}")

        if not urls_to_scrape:
            logger.warning(f"No valid URLs found in Tavily results for query '{query}'")
            return service_result

        logger.debug(f"Prepared {len(urls_to_scrape)} unique URLs for scraping.")
        scraped_data_map = {}

        async with aiohttp.ClientSession() as session:
            for url in urls_to_scrape:
                task = asyncio.create_task(
                    _scrape_single_url(session, url, scrape_timeout),
                    name=f"scrape_{url}"
                )
                scrape_tasks.append((url, task))

            logger.debug(f"Gathering results for {len(scrape_tasks)} scraping tasks.")
            scrape_results_tuples = await asyncio.gather(*(task for _, task in scrape_tasks), return_exceptions=True)
            logger.debug(f"Completed gathering scrape results.")

            for i, (url, _) in enumerate(scrape_tasks):
                scrape_outcome = scrape_results_tuples[i]
                if isinstance(scrape_outcome, Exception):
                    logger.error(f"Gather error for scrape task {url}: {scrape_outcome}")
                    scraped_data_map[url] = (None, f"Gather error: {str(scrape_outcome)}")
                else:
                    scraped_data_map[url] = scrape_outcome

        for url in urls_to_scrape:
            tavily_info = tavily_result_map[url]
            content, error = scraped_data_map.get(url, (None, "Scraping task result not found"))
            service_result.results.append(
                ScrapedResult(
                    title=tavily_info.get("title"),
                    url=url,
                    tavily_snippet=tavily_info.get("content"),
                    scraped_content=content,
                    scrape_error=error
                )
            )
        logger.info(f"Successfully processed search and scrape for query: '{query}', found {len(service_result.results)} results.")

    except Exception as e:
        logger.exception(f"Error during search/scrape for query '{query}': {e}")
        service_result.search_provider_error = f"{type(e).__name__}: {str(e)}"
        if api_key is None and isinstance(e, ValueError):
            logger.error("Failed to retrieve Tavily API key.")
        elif api_key and "401" in str(e):
             logger.error("Tavily API key seems invalid (401 Unauthorized). Please check the key.")

    return service_result

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

async def validate_tavily_key(api_key: str) -> Tuple[bool, Optional[str]]:
    """Validate if the Tavily API key is correctly formatted and functional."""
    if not api_key or not isinstance(api_key, str):
        return False, "API key must be a non-empty string"

    # Tavily API key format validation
    pattern = r'^tvly-[0-9A-Za-z-]{10,}$'
    if not re.match(pattern, api_key):
        return False, "Invalid Tavily API key format - must start with 'tvly-'"

    try:
        # Minimal test call to Tavily API
        search = TavilySearch(max_results=1, tavily_api_key=api_key)
        await search.ainvoke({"query": "test"})
        return True, None
    except Exception as e:
        error_str = str(e)
        logger.warning(f"Tavily API key validation failed: {error_str}")

        if "401" in error_str and "Unauthorized" in error_str:
            return False, "API key error: Unauthorized access. The API key appears to be invalid or revoked."
        if "400" in error_str and "query" in error_str:
             return False, "API key validation returned Bad Request (400). Check key or API status."
        if "rate limit" in error_str.lower():
            return False, "API key error: Rate limit exceeded."

        # Default error message
        return False, f"API key validation failed: {error_str}"
