import os
import logging
import re
import asyncio
import aiohttp
import io # Added for BytesIO
import fitz # Added for PyMuPDF
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

# Maximum characters to extract from scraped content (HTML or PDF)
MAX_SCRAPE_LENGTH = 100000 

# --- Start of Added PDF Helper Function ---
def _extract_pdf_text_sync(pdf_bytes: bytes, source_url: str) -> str:
    """Synchronous helper to extract text from PDF bytes using PyMuPDF.
    
    Designed to be run in a thread executor.

    Args:
        pdf_bytes: The byte content of the PDF file.
        source_url: The original URL for logging context.

    Returns:
        The extracted text content.

    Raises:
        ValueError: If the PDF is encrypted.
        fitz.fitz.FileDataError: If the PDF data is corrupted or invalid.
        RuntimeError: For other PyMuPDF or general exceptions during processing.
    """
    logger.debug(f"Starting PDF text extraction for {source_url}")
    all_text = []
    try:
        with fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf") as doc:
            if doc.is_encrypted:
                logger.warning(f"Skipping encrypted PDF: {source_url}")
                # Raise specific error to be caught in the async function
                raise ValueError("PDF is encrypted") 

            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    page_text = page.get_text("text", sort=True).strip()
                    if page_text:
                        all_text.append(page_text)
                except Exception as page_err:
                    # Log error for specific page but continue if possible
                    logger.error(f"Error extracting text from page {page_num+1} of PDF {source_url}: {page_err}", exc_info=False)

            # Use corrected string literal for joining pages
            clean_text = "\n\n".join(all_text) # Separate pages by double newline
            # Optional: Further cleaning (e.g., excessive whitespace within pages)
            clean_text = re.sub(r'[ 	]*\n[ 	]*', '\n', clean_text) # Normalize line breaks
            clean_text = re.sub(r'\n{3,}', '\n\n', clean_text) # Consolidate multiple newlines

            logger.debug(f"Successfully extracted text from PDF: {source_url}")
            return clean_text

    except (fitz.fitz.FileDataError, ValueError) as e: # Catch known issues
        logger.error(f"Failed to process PDF {source_url}: {e}")
        raise # Re-raise specific errors to be handled distinctly if needed

    except Exception as e:
        # Catch-all for other unexpected errors during fitz processing
        logger.error(f"Unexpected error during PDF processing for {source_url}: {type(e).__name__} - {e}", exc_info=True)
        raise RuntimeError(f"Unexpected error during PDF processing: {type(e).__name__}") from e

# --- End of Added PDF Helper Function ---


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

# --- Modified _scrape_single_url ---
async def _scrape_single_url(session: aiohttp.ClientSession, url: str, timeout: int) -> Tuple[Optional[str], Optional[str]]:
    """Scrapes cleaned textual content from a single URL (HTML or PDF).

    Args:
        session: The aiohttp client session.
        url: The URL to scrape.
        timeout: Request timeout in seconds.

    Returns:
        A tuple containing (scraped_content, error_message).
        scraped_content is None if an error occurred.
        error_message is None if scraping was successful.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; LearniBot/1.0; +https://github.com/your-repo)'}
    clean_text: Optional[str] = None
    error_message: Optional[str] = None

    try:
        logger.debug(f"Attempting to scrape URL: {url}")
        async with session.get(url, timeout=timeout, headers=headers, ssl=False) as response:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            
            # --- PDF Handling ---
            if "application/pdf" in content_type:
                logger.info(f"Detected PDF content type for: {url}")
                try:
                    pdf_bytes = await response.read()
                    if not pdf_bytes:
                         logger.warning(f"Received empty response body for PDF: {url}")
                         # Use return instead of assignment for immediate exit
                         return None, "Received empty PDF content"
                    
                    loop = asyncio.get_running_loop()
                    # Run synchronous PDF extraction in a thread executor
                    clean_text = await loop.run_in_executor(
                        None, _extract_pdf_text_sync, pdf_bytes, url
                    )
                    logger.info(f"Successfully extracted text from PDF: {url}")
                    # Reset error message on success
                    error_message = None 
                    
                except ValueError as ve: # Catch specific encryption error
                    logger.warning(f"Skipping encrypted PDF {url}: {ve}")
                    clean_text = None # Ensure clean_text is None on error
                    error_message = "Skipped: PDF is encrypted"
                except (fitz.fitz.FileDataError, RuntimeError) as pdf_err: # Catch errors raised by helper
                    logger.error(f"PDF processing failed for {url}: {pdf_err}")
                    clean_text = None # Ensure clean_text is None on error
                    error_message = f"PDF processing error: {type(pdf_err).__name__}"
                except asyncio.CancelledError:
                    logger.warning(f"PDF processing cancelled for {url}")
                    raise # Propagate cancellation
                except Exception as e: # Catch errors during response.read() or executor itself
                    logger.error(f"Error handling PDF content for {url}: {type(e).__name__} - {e}", exc_info=True)
                    clean_text = None # Ensure clean_text is None on error
                    error_message = f"Error reading/processing PDF: {type(e).__name__}"

            # --- HTML Handling ---
            elif "text/html" in content_type:
                logger.debug(f"Detected HTML content type for: {url}")
                try:
                    html_content = await response.text()
                    
                    # Basic cleaning with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'form', 'button', 'input', 'textarea']):
                        tag.decompose()
                    
                    main_content = soup.find('main') or soup.find('article') or soup.find('div', role='main') or soup.find('div', id='content') or soup.find('div', class_='content')
                    target_element = main_content if main_content else soup.find('body')

                    if target_element:
                        clean_text = target_element.get_text(separator='\n', strip=True)
                    else:
                        clean_text = "Could not extract body or main content" # Should be unlikely
                        logger.warning(f"Could not find body or main content for HTML: {url}")

                    # Further cleaning
                    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
                    logger.info(f"Successfully extracted text from HTML: {url}")
                    # Reset error message on success
                    error_message = None 
                except Exception as html_err: # Catch potential errors in HTML processing
                    logger.error(f"Error processing HTML content for {url}: {type(html_err).__name__} - {html_err}", exc_info=True)
                    clean_text = None
                    error_message = f"Error processing HTML: {type(html_err).__name__}"

            # --- Other Content Types ---
            else:
                logger.warning(f"Skipping unsupported content type '{content_type}' for URL: {url}")
                clean_text = None
                error_message = f"Skipped: Unsupported content type ({content_type})"

            # --- Truncation (Applied to both HTML and PDF if text exists) ---
            if clean_text is not None and len(clean_text) > MAX_SCRAPE_LENGTH:
               logger.debug(f"Truncating content for {url} from {len(clean_text)} chars")
               clean_text = clean_text[:MAX_SCRAPE_LENGTH] + "... (truncated)"

            # Final return based on processing outcome
            return clean_text, error_message 

    except asyncio.TimeoutError:
        logger.warning(f"Scrape timed out for {url} after {timeout}s")
        return None, f"Scrape timed out after {timeout}s"
    except aiohttp.ClientResponseError as e:
        logger.warning(f"HTTP error scraping {url}: {e.status} {e.message}")
        # Provide specific HTTP status in error message
        return None, f"HTTP error: {e.status} ({e.message})"
    except aiohttp.ClientError as e:
        logger.warning(f"Client error scraping {url}: {type(e).__name__}")
        return None, f"Scraping error: {type(e).__name__}"
    except Exception as e:
        # Catch unexpected errors during request/initial handling
        logger.error(f"Unexpected error scraping {url}: {type(e).__name__} - {str(e)}", exc_info=True)
        return None, f"Unexpected scraping error: {type(e).__name__}"
# --- End of Modified _scrape_single_url ---


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

        if not isinstance(tavily_response, dict):
            error_msg = f"Tavily search returned non-dict response: {tavily_response}"
            logger.error(error_msg)
            service_result.search_provider_error = error_msg
            return service_result

        scrape_tasks = []
        tavily_results = tavily_response.get("results", [])

        if not isinstance(tavily_results, list):
            # More robust error logging
            error_msg = f"Unexpected Tavily response format: 'results' is not a list. Response: {tavily_response}"
            logger.error(error_msg)
            service_result.search_provider_error = error_msg # Record error in result
            # Potentially raise or return depending on desired strictness
            # For now, return the result object with the error
            return service_result 

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
            # Use return_exceptions=True to handle individual task failures
            scrape_results_tuples = await asyncio.gather(*(task for _, task in scrape_tasks), return_exceptions=True)
            logger.debug(f"Completed gathering scrape results.")

            for i, (url, _) in enumerate(scrape_tasks):
                scrape_outcome = scrape_results_tuples[i]
                if isinstance(scrape_outcome, Exception):
                    if isinstance(scrape_outcome, asyncio.CancelledError):
                        logger.warning(f"Scraping task for {url} was cancelled.")
                        scraped_data_map[url] = (None, "Scraping task cancelled")
                    else:
                        # Log the actual exception from the task
                        logger.error(f"Gather caught exception for scrape task {url}: {scrape_outcome}", exc_info=isinstance(scrape_outcome, Exception))
                        scraped_data_map[url] = (None, f"Gather error: {type(scrape_outcome).__name__}")
                elif isinstance(scrape_outcome, tuple) and len(scrape_outcome) == 2:
                    scraped_data_map[url] = scrape_outcome
                else:
                    logger.error(f"Unexpected scrape outcome type for {url}: {type(scrape_outcome)} - {scrape_outcome}")
                    scraped_data_map[url] = (None, f"Unexpected scrape result type: {type(scrape_outcome).__name__}")

        # Populate the final result object
        for url in urls_to_scrape:
            tavily_info = tavily_result_map.get(url) # Get corresponding Tavily info
            if tavily_info:
                content, error = scraped_data_map.get(url, (None, "Scraping task result missing"))
                service_result.results.append(
                    ScrapedResult(
                        title=tavily_info.get("title"),
                        url=url,
                        tavily_snippet=tavily_info.get("content"), # Use 'content' field from Tavily
                        scraped_content=content,
                        scrape_error=error
                    )
                )
            else:
                 # This shouldn't happen if logic is correct, but log defensively
                 logger.error(f"Could not find original Tavily result info for scraped URL: {url}")

        logger.info(f"Successfully processed search and scrape for query: '{query}', found {len(service_result.results)} results.")

    # Catch potential errors retrieving Tavily key or during Tavily API call
    except aiohttp.ClientError as http_err:
        logger.exception(f"Network error during Tavily search/scrape for query '{query}': {http_err}")
        service_result.search_provider_error = f"Network Error: {type(http_err).__name__}"
    except Exception as e:
        logger.exception(f"General error during search/scrape for query '{query}': {e}")
        # Distinguish API key retrieval error from other errors
        if api_key is None and isinstance(e, (ValueError, AttributeError)): # Check if key provider failed
             service_result.search_provider_error = f"Key Provider Error: {type(e).__name__}: {str(e)}"
             logger.error(f"Failed to retrieve Tavily API key: {e}")
        elif api_key and "401" in str(e): # Check for common auth failure after getting key
             service_result.search_provider_error = "Tavily API key seems invalid (401 Unauthorized)"
             logger.error(service_result.search_provider_error)
        else: # General error during search or processing
             service_result.search_provider_error = f"{type(e).__name__}: {str(e)}"

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
        logger.warning(f"Google API key validation failed: {error_str}") # Log warning
        
        # Check for specific error cases
        if "invalid api key" in error_str.lower():
            return False, "Invalid Google API key format or key not activated"
        
        if "permission" in error_str.lower() or "access" in error_str.lower():
            return False, "API key error: Insufficient permissions or access denied"
        
        if "quota" in error_str.lower() or "limit" in error_str.lower():
            return False, "API key error: Quota exceeded or rate limits reached"
        
        # Default error message
        return False, f"API key validation failed: Check key and permissions."

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
        # Use a simple, common query that is likely to succeed if the key is valid
        await search.ainvoke({"query": "weather today"}) 
        return True, None
    except Exception as e:
        error_str = str(e)
        logger.warning(f"Tavily API key validation failed: {error_str}")

        # Provide clearer error messages based on common issues
        if "401" in error_str and "Unauthorized" in error_str:
            return False, "API key error: Unauthorized. The API key is likely invalid or revoked."
        if "400" in error_str and "query is required" in error_str.lower():
             # This might indicate an API change or unexpected issue, but less likely a key problem
             return False, "API key validation returned Bad Request (400). Check Tavily API status or query format."
        if "rate limit" in error_str.lower():
            return False, "API key error: Rate limit exceeded."
        if "connection error" in error_str.lower() or "cannot connect" in error_str.lower():
            return False, "Network error during API key validation. Check connectivity."

        # Default error message for other exceptions
        return False, f"API key validation failed: {type(e).__name__}. Check key and Tavily service status."
