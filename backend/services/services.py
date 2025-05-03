import os
import logging
import re
import asyncio
import aiohttp
import io # Added for BytesIO
import fitz # Added for PyMuPDF
import json # Added for parsing Brave response
import threading # Added for thread-safe rate limiting
import time # Added for thread-safe rate limiting
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import BraveSearch # Replaced TavilySearch
from typing import Optional, Union, Tuple, Any
from bs4 import BeautifulSoup
import trafilatura # Added for HTML extraction

# Import models directly for runtime use
from backend.models.models import SearchServiceResult, ScrapedResult

# Import key provider for type hints but with proper import protection
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.services.key_provider import KeyProvider, GoogleKeyProvider, BraveKeyProvider # Renamed TavilyKeyProvider
    # Keep models here for type checking if needed, but they are already imported above
    # from backend.models.models import SearchServiceResult, ScrapedResult 

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
# TODO: Consider moving constants to a config file/object
SEARCH_SERVICE = "brave" # Updated from "tavily"
# Maximum characters to extract from scraped content (HTML or PDF)
MAX_SCRAPE_LENGTH = 100000
# Minimum content length threshold for Trafilatura fallback
TRAFILATURA_MIN_LENGTH_FALLBACK = 100
# Percentage of page height to consider as header/footer margin in PDF
PDF_HEADER_MARGIN_PERCENT = 0.10 # 10%
PDF_FOOTER_MARGIN_PERCENT = 0.10 # 10%

# --- New Constants for Scraping Enhancement ---
TARGET_SUCCESSFUL_SCRAPES = 3 # Desired minimum number of successful scrapes
FETCH_BUFFER = 3 # How many extra results to fetch beyond max_results
# --- End New Constants ---

# Shared rate limiter for Brave Search API (1 call per second)
# brave_search_rate_limiter = aiolimiter.AsyncLimiter(1, 1) # Removed

# Thread-safe rate limiter components for Brave Search
_brave_search_lock = threading.Lock()
_last_brave_call_time = 0.0

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
    brave_key_provider: 'BraveKeyProvider', # Renamed provider
    max_results: int = 5,
    scrape_timeout: int = 10
) -> 'SearchServiceResult':
    """Performs Brave search and scrapes results concurrently. # Updated docstring

    Args:
        query: The search query.
        brave_key_provider: The key provider instance for Brave Search. # Updated docstring
        max_results: Maximum number of search results to retrieve from Brave. # Updated docstring
        scrape_timeout: Timeout in seconds for each scrape request.

    Returns:
        A SearchServiceResult object containing the query, scraped results,
        and any potential errors.
    """
    logger.info(f"Performing search and scrape for query: '{query}' using Brave Search")
    service_result = SearchServiceResult(query=query)
    api_key = None

    try:
        api_key = await brave_key_provider.get_key()
        # Calculate the number of results to fetch including the buffer
        fetch_count = max_results + FETCH_BUFFER
        logger.debug(f"Requesting {fetch_count} search results (max_results={max_results}, buffer={FETCH_BUFFER}) for query: '{query}'")

        # Use BraveSearch.from_api_key and pass fetch_count via search_kwargs
        brave_search = BraveSearch.from_api_key(
            api_key=api_key,
            search_kwargs={"count": fetch_count} # Use fetch_count here
        )

        # --- Thread-safe Rate Limiting --- 
        global _last_brave_call_time # Needed to modify the global variable
        required_delay = 0.0 # Initialize delay
        wait_until_time = 0.0 # Initialize scheduled start time

        logger.debug(f"Acquiring thread lock for Brave search rate limit check: '{query}'")
        with _brave_search_lock: # Acquire thread-safe lock only for time check/update
            current_time = time.monotonic()
            # Calculate the earliest time this call can start (1.05s after the last scheduled start)
            wait_until_time = max(current_time, _last_brave_call_time + 1.05) # Added 50ms buffer
            # Calculate the delay needed from the current time
            required_delay = wait_until_time - current_time
            # Update the global last call time to reserve the slot for *this* call
            _last_brave_call_time = wait_until_time
            logger.debug(f"Rate limit: Current time: {current_time:.2f}, Last scheduled: {_last_brave_call_time:.2f}, Wait until: {wait_until_time:.2f}, Delay: {required_delay:.2f}s. Lock released.")
        # --- Lock is released --- 

        # Perform wait *outside* the lock using asyncio.sleep
        if required_delay > 0:
            logger.info(f"Rate limiting Brave search. Waiting {required_delay:.2f} seconds...")
            await asyncio.sleep(required_delay) # Use asyncio.sleep for cooperative multitasking

        # --- Make the actual call (no lock held here) ---
        logger.debug(f"Rate limit wait complete. Invoking Brave search: '{query}'")
        try:
            brave_response_str = await brave_search.ainvoke({"query": query})
        except Exception as invoke_err:
             logger.error(f"Error during brave_search.ainvoke for '{query}': {invoke_err}", exc_info=True)
             # Add error to result and return, or raise depending on desired behavior
             service_result.search_provider_error = f"Invoke Error: {type(invoke_err).__name__}"
             return service_result # Example: return error result
             # raise # Alternatively, re-raise the exception
        # --- End Rate Limiting Logic & Call ---

        logger.debug(f"Received Brave response for: '{query}'")

        # Parse the JSON string response from Brave
        try:
            brave_results_list = json.loads(brave_response_str)
            if not isinstance(brave_results_list, list):
                 raise ValueError("Brave search response is not a list")
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            error_msg = f"Brave search returned invalid JSON or unexpected format: {e}. Response: {brave_response_str[:500]}..."
            logger.error(error_msg)
            service_result.search_provider_error = error_msg
            return service_result

        scrape_tasks = []
        # Process the parsed list from Brave
        # Rename tavily_result_map -> search_result_map
        search_result_map = {} 
        urls_to_scrape = []

        for result in brave_results_list:
            # Brave uses 'link' for URL and 'snippet' for content snippet
            if isinstance(result, dict) and "link" in result and result["link"] and "title" in result and "snippet" in result:
                url = result["link"]
                if url not in urls_to_scrape:
                    urls_to_scrape.append(url)
                    # Store the necessary mapped info
                    search_result_map[url] = {
                        "url": url, 
                        "title": result.get("title"), 
                        "search_snippet": result.get("snippet") # Map brave 'snippet' to internal 'search_snippet'
                    }
            else:
                logger.warning(f"Skipping invalid or incomplete Brave Search result item: {result}")

        if not urls_to_scrape:
            logger.warning(f"No valid URLs found in Brave Search results for query '{query}'")
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
                    if isinstance(scrape_outcome, asyncio.CancelledError):
                        logger.warning(f"Scraping task for {url} was cancelled.")
                        scraped_data_map[url] = (None, "Scraping task cancelled")
                    else:
                        logger.error(f"Gather caught exception for scrape task {url}: {scrape_outcome}", exc_info=isinstance(scrape_outcome, Exception))
                        scraped_data_map[url] = (None, f"Gather error: {type(scrape_outcome).__name__}")
                elif isinstance(scrape_outcome, tuple) and len(scrape_outcome) == 2:
                    scraped_data_map[url] = scrape_outcome
                else:
                    logger.error(f"Unexpected scrape outcome type for {url}: {type(scrape_outcome)} - {scrape_outcome}")
                    scraped_data_map[url] = (None, f"Unexpected scrape result type: {type(scrape_outcome).__name__}")

        # --- Start Prioritization Logic ---
        successful_scrapes = []
        failed_scrapes = []

        # Populate successful_scrapes and failed_scrapes lists
        for url in urls_to_scrape: # Iterate through all fetched URLs
            search_info = search_result_map.get(url)
            if search_info:
                content, error = scraped_data_map.get(url, (None, "Scraping task result missing"))
                # Treat empty string "" as failure too
                if content: # Check if content is not None and not empty string
                    successful_scrapes.append((url, search_info, content))
                else:
                    # Ensure error string is present, provide default if None
                    error_msg = error if error is not None else "No content found or scrape failed"
                    failed_scrapes.append((url, search_info, error_msg))

        logger.debug(f"Scraping yielded {len(successful_scrapes)} successful scrapes and {len(failed_scrapes)} failed scrapes out of {len(urls_to_scrape)} attempted.")

        final_scraped_results_data = []

        # 1. Add successful scrapes up to TARGET_SUCCESSFUL_SCRAPES, capped by max_results
        num_successful_added = 0
        for url, search_info, content in successful_scrapes:
            # Check if we've reached the overall max_results limit for the final list
            if len(final_scraped_results_data) < max_results:
                # Prioritize adding successful scrapes until the target is met OR max_results is hit
                if num_successful_added < TARGET_SUCCESSFUL_SCRAPES:
                    final_scraped_results_data.append(
                        ScrapedResult(
                            title=search_info.get("title"),
                            url=url,
                            search_snippet=search_info.get("search_snippet"),
                            scraped_content=content,
                            scrape_error=None
                        )
                    )
                    num_successful_added += 1
                else:
                    # If target met, only add more successful ones if space allows
                    # (This case might be less common if max_results is close to target)
                    pass # Optionally add more successful ones here if needed up to max_results
            else:
                break # Stop if we hit max_results cap

        # If target was not met, add remaining successful scrapes up to max_results
        successful_added_beyond_target = 0
        if num_successful_added < TARGET_SUCCESSFUL_SCRAPES:
            for url, search_info, content in successful_scrapes[num_successful_added:]: # Start from where we left off
                if len(final_scraped_results_data) < max_results:
                    final_scraped_results_data.append(
                        ScrapedResult(
                            title=search_info.get("title"),
                            url=url,
                            search_snippet=search_info.get("search_snippet"),
                            scraped_content=content,
                            scrape_error=None
                        )
                    )
                    successful_added_beyond_target += 1
                else:
                    break # Stop if max_results is reached

        total_successful_added = num_successful_added + successful_added_beyond_target
        logger.debug(f"Added {total_successful_added} successful scrapes to the final list (Target: {TARGET_SUCCESSFUL_SCRAPES}).")


        # 2. Fill remaining slots up to max_results with failed scrapes (for snippets/errors)
        remaining_slots = max_results - len(final_scraped_results_data)
        num_failed_added = 0
        if remaining_slots > 0:
            for url, search_info, error in failed_scrapes:
                 if num_failed_added < remaining_slots:
                     final_scraped_results_data.append(
                         ScrapedResult(
                             title=search_info.get("title"),
                             url=url,
                             search_snippet=search_info.get("search_snippet"),
                             scraped_content=None,
                             scrape_error=error
                         )
                     )
                     num_failed_added += 1
                 else:
                     break # Stop if we fill the remaining slots

        logger.debug(f"Added {num_failed_added} failed scrapes to fill remaining {remaining_slots} slots (cap: {max_results}).")

        # Assign the prioritized list to the service result
        service_result.results = final_scraped_results_data
        # --- End Prioritization Logic ---

        logger.info(f"Successfully processed search and scrape for query: '{query}', returning {len(service_result.results)} prioritized results.")

    except aiohttp.ClientError as http_err:
        logger.exception(f"Network error during Brave Search/scrape for query '{query}': {http_err}")
        service_result.search_provider_error = f"Network Error: {type(http_err).__name__}"
    except Exception as e:
        logger.exception(f"General error during search/scrape for query '{query}': {e}")
        if api_key is None and isinstance(e, (ValueError, AttributeError)): 
             service_result.search_provider_error = f"Key Provider Error: {type(e).__name__}: {str(e)}"
             logger.error(f"Failed to retrieve Brave Search API key: {e}") # Updated message
        elif api_key and ("401" in str(e) or "Unauthorized" in str(e)): # Check for common auth failure
             service_result.search_provider_error = "Brave Search API key seems invalid (401 Unauthorized)" # Updated message
             logger.error(service_result.search_provider_error)
        else: 
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

async def validate_brave_key(api_key: str) -> Tuple[bool, Optional[str]]: # Renamed function
    """Validate if the Brave Search API key is correctly formatted and functional.""" # Updated docstring
    if not api_key or not isinstance(api_key, str):
        return False, "API key must be a non-empty string"

    # No standard prefix check for Brave keys based on docs

    try:
        # Minimal test call to Brave Search API
        search = BraveSearch.from_api_key(api_key=api_key) # Use BraveSearch
        # Use a simple, common query
        await search.ainvoke({"query": "test"}) 
        return True, None
    except Exception as e:
        error_str = str(e)
        logger.warning(f"Brave Search API key validation failed: {error_str}") # Updated message

        # Provide clearer error messages based on common issues for Brave (adapt as needed)
        # Langchain might wrap HTTP errors, check the error message content
        if "401" in error_str or "Unauthorized" in error_str or "invalid api key" in error_str.lower():
            return False, "API key error: Unauthorized. The Brave Search API key is likely invalid or revoked." # Updated message
        # Add checks for other potential Brave errors if known (e.g., 400, rate limits)
        # if "400" in error_str ... :
        #     return False, "API key validation returned Bad Request (400). Check Brave API status or query format."
        if "rate limit" in error_str.lower():
            return False, "API key error: Rate limit exceeded."
        if "connection error" in error_str.lower() or "cannot connect" in error_str.lower():
            return False, "Network error during API key validation. Check connectivity."

        # Default error message for other exceptions
        return False, f"API key validation failed: {type(e).__name__}. Check key and Brave Search service status." # Updated message
