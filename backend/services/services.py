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
import trafilatura # Added for HTML extraction

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

# Configuration
# TODO: Consider moving constants to a config file/object
SEARCH_SERVICE = "tavily"
# Maximum characters to extract from scraped content (HTML or PDF)
MAX_SCRAPE_LENGTH = 100000
# Minimum content length threshold for Trafilatura fallback
TRAFILATURA_MIN_LENGTH_FALLBACK = 100
# Percentage of page height to consider as header/footer margin in PDF
PDF_HEADER_MARGIN_PERCENT = 0.10 # 10%
PDF_FOOTER_MARGIN_PERCENT = 0.10 # 10%

# --- Start of Modified PDF Helper Function ---
def _extract_pdf_text_sync(pdf_bytes: bytes, source_url: str) -> str:
    """Synchronous helper to extract text from PDF bytes using PyMuPDF block analysis.

    Attempts to extract text by analyzing blocks, filtering headers/footers,
    and sorting blocks by reading order. Falls back to simple page text extraction if
    block analysis fails or yields no content.

    Designed to be run in a thread executor.

    Args:
        pdf_bytes: The byte content of the PDF file.
        source_url: The original URL for logging context.

    Returns:
        The extracted and cleaned text content.

    Raises:
        ValueError: If the PDF is encrypted.
        fitz.fitz.FileDataError: If the PDF data is corrupted or invalid.
        RuntimeError: For other PyMuPDF or general exceptions during processing.
    """
    logger.debug(f"Starting PDF block analysis text extraction for {source_url}")
    all_text_content = ""
    extraction_method_used = "block_analysis" # Track method

    try:
        with fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf") as doc:
            if doc.is_encrypted:
                logger.warning(f"Skipping encrypted PDF: {source_url}")
                raise ValueError("PDF is encrypted")

            page_texts = []
            for page_num in range(len(doc)):
                page_text_blocks = []
                try:
                    page = doc.load_page(page_num)
                    page_rect = page.rect
                    page_height = page_rect.height
                    header_limit = page_rect.y0 + page_height * PDF_HEADER_MARGIN_PERCENT
                    footer_limit = page_rect.y1 - page_height * PDF_FOOTER_MARGIN_PERCENT

                    blocks = page.get_text("blocks", sort=False) # Get blocks with coordinates, no initial sort

                    # Filter headers/footers and empty blocks
                    filtered_blocks = [
                        b for b in blocks
                        if b[1] >= header_limit and b[3] <= footer_limit and b[4].strip() # y0>=header, y1<=footer, text exists
                    ]

                    # Sort by reading order (top-to-bottom, left-to-right)
                    filtered_blocks.sort(key=lambda b: (b[1], b[0])) # Sort by y0, then x0

                    page_text_blocks = [b[4].strip() for b in filtered_blocks] # Extract text

                    if page_text_blocks:
                        page_texts.append("\n".join(page_text_blocks)) # Join blocks with single newline

                except Exception as page_err:
                    logger.error(f"Error processing blocks on page {page_num+1} of PDF {source_url}: {page_err}", exc_info=False)
                    # For now, continue processing other pages.

            if page_texts:
                 all_text_content = "\n\n".join(page_texts) # Join pages with double newline

            # --- Fallback to simple page text extraction if block analysis yielded nothing ---
            if not all_text_content.strip():
                logger.warning(f"PDF block analysis yielded no text for {source_url}. Falling back to simple page extraction.")
                extraction_method_used = "page_text_fallback"
                all_text_fallback = []
                for page_num in range(len(doc)):
                     try:
                         page = doc.load_page(page_num)
                         page_text = page.get_text("text", sort=True).strip() # Simple text extraction
                         if page_text:
                             all_text_fallback.append(page_text)
                     except Exception as page_err:
                         logger.error(f"Error during fallback text extraction on page {page_num+1} of PDF {source_url}: {page_err}", exc_info=False)
                all_text_content = "\n\n".join(all_text_fallback)

            # --- Final Cleaning (Applied regardless of method) ---
            if all_text_content:
                # Corrected regex substitutions
                clean_text = re.sub(r'[ \t]*\n[ \t]*', '\n', all_text_content)
                clean_text = re.sub(r'\n{3,}', '\n\n', clean_text).strip()
                logger.debug(f"Successfully extracted text from PDF ({extraction_method_used}): {source_url}")
                return clean_text
            else:
                 logger.warning(f"No text could be extracted from PDF {source_url} using any method.")
                 return "" # Return empty string if no content found

    except (fitz.fitz.FileDataError, ValueError) as e:
        logger.error(f"Failed to process PDF {source_url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during PDF processing for {source_url}: {type(e).__name__} - {e}", exc_info=True)
        raise RuntimeError(f"Unexpected error during PDF processing: {type(e).__name__}") from e

# --- End of Modified PDF Helper Function ---


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

# --- Start of Modified _scrape_single_url ---
async def _scrape_single_url(session: aiohttp.ClientSession, url: str, timeout: int) -> Tuple[Optional[str], Optional[str]]:
    """Scrapes cleaned textual content from a single URL (HTML or PDF).

    Prioritizes using Trafilatura for HTML and block analysis for PDF, with fallbacks.
    Cleans the content THEN truncates to MAX_SCRAPE_LENGTH.

    Args:
        session: The aiohttp client session.
        url: The URL to scrape.
        timeout: Request timeout in seconds.

    Returns:
        A tuple containing (cleaned_scraped_content, error_message).
        cleaned_scraped_content is None if an error occurred or no content found after cleaning.
        error_message contains details if scraping or processing failed.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; LearniBot/1.0; +https://learni.com/bot)'} # Example Bot UA
    clean_text: Optional[str] = None
    error_message: Optional[str] = None

    try:
        logger.debug(f"Attempting to scrape URL: {url}")
        async with session.get(url, timeout=timeout, headers=headers, ssl=False) as response:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            
            # --- PDF Handling ---
            if "application/pdf" in content_type:
                logger.debug(f"Detected PDF content type for: {url}")
                extraction_method_used = "pdf_block_analysis" # Default assumption
                try:
                    pdf_bytes = await response.read()
                    if not pdf_bytes:
                        logger.warning(f"Received empty response body for PDF: {url}")
                        return None, "Received empty PDF content"

                    loop = asyncio.get_running_loop()
                    clean_text = await loop.run_in_executor(
                        None, _extract_pdf_text_sync, pdf_bytes, url
                    )
                    # _extract_pdf_text_sync now returns empty string if no content, not None
                    if not clean_text:
                         logger.warning(f"PDF extraction yielded no content for {url}")
                         error_message = "No text content extracted from PDF"
                         # clean_text remains "" (empty string) which evaluates as False later
                    else:
                         error_message = None # Success

                except ValueError as ve: # Specific encryption error
                    logger.warning(f"Skipping encrypted PDF {url}: {ve}")
                    clean_text = None
                    error_message = "Skipped: PDF is encrypted"
                    extraction_method_used = "pdf_error_encrypted"
                except (fitz.fitz.FileDataError, RuntimeError) as pdf_err: # Specific processing errors
                    logger.error(f"PDF processing failed for {url}: {pdf_err}")
                    clean_text = None
                    error_message = f"PDF processing error: {type(pdf_err).__name__}"
                    extraction_method_used = "pdf_error_processing"
                except asyncio.CancelledError:
                    logger.warning(f"PDF processing cancelled for {url}")
                    raise
                except Exception as e: # Catch-all for read/executor errors
                    logger.error(f"Error handling PDF content for {url}: {type(e).__name__} - {e}", exc_info=True)
                    clean_text = None
                    error_message = f"Error reading/processing PDF: {type(e).__name__}"
                    extraction_method_used = "pdf_error_unknown"

            # --- HTML Handling ---
            elif "text/html" in content_type:
                logger.debug(f"Detected HTML content type for: {url}")
                extraction_method_used = "trafilatura" # Default assumption
                try:
                    html_content = await response.text()

                    # Attempt extraction with Trafilatura first
                    extracted_text = trafilatura.extract(
                        html_content,
                        include_comments=False, # Don't include comments
                        include_tables=True,    # Include table content if relevant
                        # favor_recall=True,    # Consider if more content is desired at risk of noise
                    )

                    # Check if Trafilatura result is usable
                    if extracted_text and len(extracted_text) >= TRAFILATURA_MIN_LENGTH_FALLBACK:
                        clean_text = extracted_text
                        logger.debug(f"Using Trafilatura extracted content for {url}")
                    else:
                        # Fallback to BeautifulSoup method if Trafilatura failed or got too little
                        extraction_method_used = "beautifulsoup_fallback"
                        logger.warning(f"Trafilatura yielded insufficient content (<{TRAFILATURA_MIN_LENGTH_FALLBACK} chars) for {url}. Falling back to BeautifulSoup.")
                        soup = BeautifulSoup(html_content, 'lxml') # Use lxml parser
                        # Remove common noise tags more aggressively
                        for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'form', 'button', 'input', 'textarea', 'select', 'option', 'label', 'iframe', 'noscript', 'figure', 'figcaption']):
                            tag.decompose()

                        # Find main content areas (add more selectors if needed)
                        main_content = soup.find('main') or \
                                       soup.find('article') or \
                                       soup.find('div', role='main') or \
                                       soup.find('div', id='content') or \
                                       soup.find('div', class_=re.compile(r'\b(content|main|body|article)\b', re.I)) # More flexible class search

                        target_element = main_content if main_content else soup.find('body')

                        if target_element:
                            clean_text = target_element.get_text(separator='\n', strip=True)
                        else:
                            # Extremely unlikely fallback
                            logger.error(f"Could not find body or main content element for HTML fallback: {url}")
                            clean_text = None # Mark as failure
                            error_message = "HTML parsing failed: No body/main element found"

                    # Apply final cleaning steps to text from either method
                    if clean_text:
                        # Corrected regex substitutions
                        clean_text = re.sub(r'[ \t]*\n[ \t]*', '\n', clean_text)
                        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text).strip()
                        logger.info(f"Successfully extracted text from HTML ({extraction_method_used}): {url}")
                        error_message = None # Reset error on success
                    elif not error_message: # If clean_text became None/empty without an explicit error set
                         logger.warning(f"HTML processing ({extraction_method_used}) resulted in empty content for {url}")
                         error_message = "No text content extracted from HTML"

                except Exception as html_err:
                    logger.error(f"Error processing HTML content ({extraction_method_used}) for {url}: {type(html_err).__name__} - {html_err}", exc_info=True)
                    clean_text = None
                    error_message = f"Error processing HTML: {type(html_err).__name__}"
                    extraction_method_used = "html_error_unknown"

            # --- Other Content Types ---
            else:
                logger.warning(f"Skipping unsupported content type '{content_type}' for URL: {url}")
                clean_text = None
                error_message = f"Skipped: Unsupported content type ({content_type})"
                extraction_method_used = "skipped_content_type"

            # --- Truncation (Applied AFTER cleaning if text exists) ---
            if clean_text is not None and len(clean_text) > MAX_SCRAPE_LENGTH:
                logger.debug(f"Truncating content ({extraction_method_used}) for {url} from {len(clean_text)} chars to {MAX_SCRAPE_LENGTH}")
                clean_text = clean_text[:MAX_SCRAPE_LENGTH] + "... (truncated)"
            elif clean_text == "": # Handle case where cleaning resulted in empty string but no error
                clean_text = None # Treat as no content found
                if not error_message: # Avoid overwriting specific errors
                     error_message = "No text content found after cleaning"

            # Return the cleaned (and possibly truncated) text
            return clean_text, error_message

    except asyncio.TimeoutError:
        logger.warning(f"Scrape timed out for {url} after {timeout}s")
        return None, f"Scrape timed out after {timeout}s"
    except aiohttp.ClientResponseError as e:
        logger.warning(f"HTTP error scraping {url}: {e.status} {e.message}")
        return None, f"HTTP error: {e.status} ({e.message})"
    except aiohttp.ClientError as e: # Includes connection errors etc.
        logger.warning(f"Client error scraping {url}: {type(e).__name__}")
        return None, f"Scraping client error: {type(e).__name__}"
    except Exception as e:
        logger.error(f"Unexpected error during initial scrape request for {url}: {type(e).__name__} - {str(e)}", exc_info=True)
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
