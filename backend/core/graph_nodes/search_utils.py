"""
Utility functions for search operations with LLM-based retry capabilities.

This module provides a wrapper for search operations that can retry failed searches
by regenerating queries using an LLM when no results are found.
"""

import logging
import re
import asyncio # Added for sleep
import random   # Added for jitter
from typing import Callable, Dict, Any, Optional, TypeVar, Awaitable, Union

from backend.models.models import SearchQuery, LearningPathState, SearchServiceResult, ResourceQuery
from backend.services.services import execute_search_with_router

# Configure logger
logger = logging.getLogger("learning_path.search_utils")

# Type for the regenerate query function - Accepts either SearchQuery or ResourceQuery
RegenerateQueryFunc = TypeVar('RegenerateQueryFunc', bound=Callable[..., Awaitable[Optional[Union[SearchQuery, ResourceQuery]]]])
QueryObjectType = Union[SearchQuery, ResourceQuery]

# Define max attempts constant
MAX_SEARCH_ATTEMPTS = 4

async def execute_search_with_llm_retry(
    state: LearningPathState,
    initial_query: QueryObjectType,
    regenerate_query_func: RegenerateQueryFunc,
    search_provider_key_provider = None,  # Deprecated parameter, kept for compatibility
    search_config: Dict[str, Any] = None,
    regenerate_args: Dict[str, Any] = None,
    langsmith_extra: Dict[str, Any] = None,
) -> SearchServiceResult:
    """
    Execute a search with up to 4 total attempts, handling errors and potentially regenerating queries.
    Now uses the SearchServiceRouter to automatically select Google Search native or Brave Search+scraping.

    Retries are performed for:
    1. "No results found" errors (attempts regeneration first, then standard backoff).
    2. Any other search provider errors (e.g., 429, API errors - uses standard backoff).
    
    Args:
        state: The current LearningPathState containing context and user information.
        initial_query: The first SearchQuery or ResourceQuery object to try.
        regenerate_query_func: An async function that takes state and failed_query 
                             (plus any additional args in regenerate_args) and returns a new 
                             SearchQuery or ResourceQuery, or None if regeneration fails.
        search_provider_key_provider: DEPRECATED - key providers are now obtained from state automatically
        search_config: Dictionary with configuration for search execution 
                     (max_results, scrape_timeout). Defaults to {max_results: 5, scrape_timeout: 10}.
        regenerate_args: Additional arguments to pass to regenerate_query_func.
        langsmith_extra: Additional metadata for LangSmith tracing.
    
    Returns:
        A SearchServiceResult object containing the search results or the final error information after all attempts.
    """
    if search_config is None:
        search_config = {"max_results": 5, "scrape_timeout": 10}
    
    if regenerate_args is None:
        regenerate_args = {}
    
    if langsmith_extra is None:
        langsmith_extra = {}
    
    # Log deprecation warning if old parameter is used
    if search_provider_key_provider is not None:
        logger.warning("search_provider_key_provider parameter is deprecated. Key providers are now obtained from state automatically.")
    
    current_query = initial_query
    result: Optional[SearchServiceResult] = None
    
    # Patterns to detect error conditions that should trigger query regeneration
    # Pattern to detect "No search results found" in error messages
    no_results_pattern = re.compile(r"no search results found", re.IGNORECASE)
    # Pattern to detect HTTP 422 errors (unprocessable entity, likely due to overly complex/long query)
    query_unprocessable_pattern = re.compile(r"HTTP error 422", re.IGNORECASE)

    for attempt_number in range(MAX_SEARCH_ATTEMPTS):
        # Safely get the query string based on object type
        query_str = ""
        if isinstance(current_query, SearchQuery):
            query_str = current_query.keywords
        elif isinstance(current_query, ResourceQuery):
            query_str = current_query.query
        else:
            logger.error(f"Unsupported query object type: {type(current_query)}. Aborting search.")
            return SearchServiceResult(query=getattr(current_query, 'keywords', getattr(current_query, 'query', 'unknown')), 
                                       search_provider_error="Unsupported query object type")
            
        logger.info(f"Search attempt {attempt_number + 1}/{MAX_SEARCH_ATTEMPTS} with query: '{query_str}'")
        
        # Enhance LangSmith metadata for this attempt
        attempt_langsmith_extra = langsmith_extra.copy()
        attempt_metadata = attempt_langsmith_extra.get('metadata', {})
        attempt_metadata.update({
            'search_attempt': attempt_number + 1,
            'max_attempts': MAX_SEARCH_ATTEMPTS,
            'query_type': type(current_query).__name__,
            'retry_search': attempt_number > 0
        })
        attempt_langsmith_extra['metadata'] = attempt_metadata
        
        # Update name to include attempt number for clarity
        base_name = attempt_langsmith_extra.get('name', 'SearchWithRetry')
        attempt_langsmith_extra['name'] = f"{base_name}_Attempt_{attempt_number + 1}"
        
        # Use the new SearchServiceRouter instead of direct perform_search_and_scrape call
        try:
            result = await execute_search_with_router(
                state=state,
                query=query_str,
                search_config=search_config,
                langsmith_extra=attempt_langsmith_extra
            )
        except Exception as e:
            # Catch unexpected errors during search execution
            logger.exception(f"Unexpected error during search execution on attempt {attempt_number + 1}/{MAX_SEARCH_ATTEMPTS} for query '{query_str}': {e}")
            result = SearchServiceResult(query=query_str, search_provider_error=f"Internal error during search: {type(e).__name__} - {str(e)}")

        # --- Check result of this attempt --- 
        if result is None:
            # Should theoretically not happen due to try/except, but handle defensively
            logger.error(f"Search result object is unexpectedly None after attempt {attempt_number + 1}/{MAX_SEARCH_ATTEMPTS}.")
            result = SearchServiceResult(query=query_str, search_provider_error="Unknown error during search execution")

        search_error = result.search_provider_error
        
        if not search_error:
            logger.info(f"Search successful on attempt {attempt_number + 1}/{MAX_SEARCH_ATTEMPTS}.")
            return result # Success!

        # --- Handle Failure --- 
        logger.warning(f"Search attempt {attempt_number + 1}/{MAX_SEARCH_ATTEMPTS} failed for query '{query_str}'. Error: {search_error}")
        
        # Check if this was the last attempt
        if attempt_number == MAX_SEARCH_ATTEMPTS - 1:
            logger.error(f"Max search attempts ({MAX_SEARCH_ATTEMPTS}) reached. Returning last error: {search_error}")
            return result # Return the final error result
        
        # --- Decide Action Before Next Attempt --- 
        should_trigger_for_no_results = no_results_pattern.search(search_error)
        should_trigger_for_unprocessable_query = query_unprocessable_pattern.search(search_error)
        
        should_regenerate = should_trigger_for_no_results or should_trigger_for_unprocessable_query
        regenerated = False
        
        if should_regenerate:
            if should_trigger_for_unprocessable_query:
                logger.info(f"Attempting query regeneration after 'HTTP error 422' (query unprocessable) on attempt {attempt_number + 1}.")
            elif should_trigger_for_no_results:
                logger.info(f"Attempting query regeneration after 'no results' on attempt {attempt_number + 1}.")
            try:
                new_query_obj = await regenerate_query_func(state, current_query, **regenerate_args)
                
                if new_query_obj is None:
                    logger.warning("Query regeneration returned None.")
                else:
                    # Safely get new query string
                    new_query_str = getattr(new_query_obj, 'keywords', getattr(new_query_obj, 'query', None))
                    if new_query_str is None:
                         logger.error(f"Regeneration returned unsupported query type: {type(new_query_obj)}.")
                    elif new_query_str == query_str:
                        logger.warning("Regenerated query string is identical to original. Will proceed with backoff.")
                    else:
                        logger.info(f"Successfully regenerated query. New: '{new_query_str}'")
                        current_query = new_query_obj # Use the new query OBJECT for the next iteration
                        regenerated = True
                        # Continue directly to next attempt with new query, skip backoff for regeneration
                        continue 
                        
            except Exception as regen_e:
                logger.exception(f"Error during query regeneration attempt: {str(regen_e)}. Proceeding with backoff.")
            
            # If we reach here after trying regeneration, it means it failed or was skipped.
            logger.warning("Query regeneration failed or was skipped. Proceeding with standard backoff before retry.")
        
        # --- Standard Backoff for next attempt (if not regenerated) ---
        base_delay = 1.0 # Base delay in seconds
        jitter = 0.5 # Max jitter in seconds
        backoff_delay = (base_delay * (2 ** attempt_number)) + random.uniform(0, jitter)
        logger.info(f"Waiting {backoff_delay:.2f} seconds before next search attempt...")
        await asyncio.sleep(backoff_delay)
        # Loop continues to the next attempt_number
            
    # Fallback return (should ideally not be reached if loop logic is correct)
    logger.error(f"Exited search retry loop unexpectedly after {MAX_SEARCH_ATTEMPTS} attempts.")
    return result if result else SearchServiceResult(query=query_str, search_provider_error="Exited retry loop unexpectedly") 