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
from backend.services.services import perform_search_and_scrape

# Configure logger
logger = logging.getLogger("learning_path.search_utils")

# Type for the regenerate query function - Accepts either SearchQuery or ResourceQuery
RegenerateQueryFunc = TypeVar('RegenerateQueryFunc', bound=Callable[..., Awaitable[Optional[Union[SearchQuery, ResourceQuery]]]])
QueryObjectType = Union[SearchQuery, ResourceQuery]

async def execute_search_with_llm_retry(
    state: LearningPathState,
    initial_query: QueryObjectType,
    regenerate_query_func: RegenerateQueryFunc,
    max_retries: int = 1,
    search_provider_key_provider = None,
    search_config: Dict[str, Any] = None,
    regenerate_args: Dict[str, Any] = None,
) -> SearchServiceResult:
    """
    Execute a search with retry capabilities for specific errors:
    1. LLM-based query regeneration retry for "no results found" errors.
    2. Exponential backoff retry for HTTP 429 (Rate Limit) errors.
    
    Args:
        state: The current LearningPathState containing context and key providers.
        initial_query: The first SearchQuery or ResourceQuery object to try.
        regenerate_query_func: An async function that takes state and failed_query 
                             (plus any additional args in regenerate_args) and returns a new 
                             SearchQuery or ResourceQuery.
        max_retries: Maximum number of *query regeneration* retries to attempt. Default is 1.
        search_provider_key_provider: The key provider for the search service (e.g., Brave).
        search_config: Dictionary with configuration for perform_search_and_scrape 
                     (max_results, scrape_timeout). Defaults to {max_results: 5, scrape_timeout: 10}.
        regenerate_args: Additional arguments to pass to regenerate_query_func.
    
    Returns:
        A SearchServiceResult object containing the search results or error information.
    """
    if search_config is None:
        search_config = {"max_results": 5, "scrape_timeout": 10}
    
    if regenerate_args is None:
        regenerate_args = {}
    
    if search_provider_key_provider is None:
        provider_key_in_state = "brave_key_provider"
        search_provider_key_provider = state.get(provider_key_in_state)
        if not search_provider_key_provider:
            logger.error(f"No search provider key provider found in state ({provider_key_in_state}) or passed as argument")
            query_str = getattr(initial_query, 'keywords', getattr(initial_query, 'query', 'unknown'))
            return SearchServiceResult(
                query=query_str,
                search_provider_error=f"No {provider_key_in_state} available"
            )
    
    current_query = initial_query
    regeneration_retries_left = max_retries # Separate counter for regeneration
    outer_attempts_made = 0
    
    # Pattern to detect "No search results found" in error messages
    no_results_pattern = re.compile(r"no search results found", re.IGNORECASE)
    # Pattern to detect 429 error messages (simple check)
    rate_limit_pattern = re.compile(r"429")
    
    # --- Outer loop for Query Regeneration Retries --- 
    while outer_attempts_made <= max_retries: 
        outer_attempts_made += 1
        
        # Safely get the query string based on object type
        query_str = ""
        if isinstance(current_query, SearchQuery):
            query_str = current_query.keywords
        elif isinstance(current_query, ResourceQuery):
            query_str = current_query.query
        else:
            logger.error(f"Unsupported query object type: {type(current_query)}")
            query_str = getattr(current_query, 'keywords', getattr(current_query, 'query', 'unknown'))
            return SearchServiceResult(query=query_str, search_provider_error="Unsupported query object type")
            
        logger.info(f"Search attempt {outer_attempts_made}/{max_retries+1} with query: '{query_str}'")
        
        # --- Inner loop for 429 Rate Limit Retries --- 
        MAX_429_RETRIES = 3
        retry_429_attempt = 0
        base_delay = 1.1  # Start delay slightly over 1 second
        result = None # Initialize result for this outer attempt
        
        while retry_429_attempt <= MAX_429_RETRIES:
            try:
                # Execute the search with current query string
                result = await perform_search_and_scrape(
                    query=query_str,
                    brave_key_provider=search_provider_key_provider,
                    max_results=search_config.get("max_results", 5),
                    scrape_timeout=search_config.get("scrape_timeout", 10)
                )
        
                search_error = result.search_provider_error
                is_429_error = search_error and rate_limit_pattern.search(search_error)
        
                if not is_429_error:
                    break # Exit 429 loop on success or non-429 error
        
                # Handle 429 Error
                logger.warning(f"Rate limit (429) hit for query '{query_str}'. Attempt {retry_429_attempt + 1}/{MAX_429_RETRIES + 1}.")
        
                if retry_429_attempt >= MAX_429_RETRIES:
                    logger.error(f"Max 429 retries ({MAX_429_RETRIES}) exceeded for query '{query_str}'.")
                    break # Exit loop, returning the 429 error result
        
                retry_429_attempt += 1
                # Exponential backoff with jitter
                delay = (base_delay * (2 ** (retry_429_attempt - 1))) + (random.uniform(0, 0.5))
                logger.info(f"Waiting {delay:.2f} seconds before retrying query '{query_str}' due to rate limit...")
                await asyncio.sleep(delay)
                # Continue the inner loop to retry perform_search_and_scrape
        
            except Exception as e:
                 # Catch unexpected errors during perform_search_and_scrape itself
                 logger.exception(f"Unexpected error during perform_search_and_scrape for query '{query_str}': {e}")
                 result = SearchServiceResult(query=query_str, search_provider_error=f"Internal error during search: {type(e).__name__}")
                 break # Exit 429 loop
        # --- End Inner loop --- 
        
        # Ensure result is not None (should only happen if initial try block had an exception)
        if result is None:
            logger.error("Search result object is unexpectedly None after 429 retry loop.")
            result = SearchServiceResult(query=query_str, search_provider_error="Unknown error during search execution")
            
        # --- Check final result of this outer attempt --- 
        search_error = result.search_provider_error

        # Check for "no results" error specifically for query regeneration
        is_no_results_error = search_error and no_results_pattern.search(search_error)

        if not is_no_results_error:
            # Success, or an error *other* than "no results" (e.g., final 429, or other API error)
            if search_error:
                logger.warning(f"Search failed with error (not 'no results'): {search_error}")
            # Return the result (success or the non-'no results' error)
            return result 
            
        # We have a "no results" error - proceed with regeneration logic if possible
        logger.warning(f"Search returned no results for query: '{query_str}'")
        
        # Check if we can regenerate query (based on outer loop retries)
        if regeneration_retries_left <= 0:
            logger.info("No regeneration retries left, returning original result with no results")
            return result # Return the 'no results' error object
        
        # Try to regenerate query
        logger.info(f"Attempting to regenerate query using LLM (Attempt {max_retries - regeneration_retries_left + 1}/{max_retries}) after no results for: '{query_str}'")
        try:
            # Call the regenerate function with the state, failed query object, and any additional args
            new_query_obj = await regenerate_query_func(state, current_query, **regenerate_args)
            
            if new_query_obj is None:
                logger.error("Query regeneration failed, returned None. Returning original 'no results' error.")
                return result # Return original failure
            
            # Safely get new query string for comparison and logging
            new_query_str = ""
            if isinstance(new_query_obj, SearchQuery):
                new_query_str = new_query_obj.keywords
            elif isinstance(new_query_obj, ResourceQuery):
                new_query_str = new_query_obj.query
            else:
                 logger.error(f"Regeneration returned unsupported query type: {type(new_query_obj)}. Returning original 'no results' error.")
                 return result # Return original failure
                 
            # Don't retry with the exact same query string
            if new_query_str == query_str:
                logger.warning("Regenerated query string is identical to original, won't retry regeneration. Returning original 'no results' error.")
                return result # Return original failure
            
            logger.info(f"Successfully regenerated query. Original: '{query_str}', New: '{new_query_str}'")
            current_query = new_query_obj # Use the new query OBJECT for the next outer loop iteration
            regeneration_retries_left -= 1 # Decrement regeneration counter
            # Continue the outer loop
            
        except Exception as e:
            logger.exception(f"Error during query regeneration: {str(e)}")
            # If regeneration fails, return the original 'no results' error result
            return result
        
    # --- End Outer loop --- 
    
    # If we exit the outer loop (meaning regeneration retries exhausted), return the last result we got (which was a 'no results' error)
    logger.info("Exhausted query regeneration retries.")
    return result 