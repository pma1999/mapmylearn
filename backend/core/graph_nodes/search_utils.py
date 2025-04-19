"""
Utility functions for search operations with LLM-based retry capabilities.

This module provides a wrapper for search operations that can retry failed searches
by regenerating queries using an LLM when no results are found.
"""

import logging
import re
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
    tavily_key_provider = None,
    search_config: Dict[str, Any] = None,
    regenerate_args: Dict[str, Any] = None,
) -> SearchServiceResult:
    """
    Execute a search with LLM-based query regeneration retry for "no results" errors.
    
    This function attempts a search using the provided initial query (SearchQuery or ResourceQuery).
    If the search returns no results, it will call the provided regenerate_query_func to create 
    a new query and retry the search.
    
    Args:
        state: The current LearningPathState containing context and key providers.
        initial_query: The first SearchQuery or ResourceQuery object to try.
        regenerate_query_func: An async function that takes state and failed_query 
                             (plus any additional args in regenerate_args) and returns a new 
                             SearchQuery or ResourceQuery.
        max_retries: Maximum number of retries to attempt. Default is 1.
        tavily_key_provider: The key provider for Tavily API. If None, will use state["tavily_key_provider"].
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
    
    if tavily_key_provider is None:
        tavily_key_provider = state.get("tavily_key_provider")
        if not tavily_key_provider:
            logger.error("No Tavily key provider found in state or passed as argument")
            # Get query string safely
            query_str = getattr(initial_query, 'keywords', getattr(initial_query, 'query', 'unknown'))
            return SearchServiceResult(
                query=query_str,
                search_provider_error="No Tavily key provider available"
            )
    
    current_query = initial_query
    retries_left = max_retries
    attempts_made = 0
    
    # Pattern to detect "No search results found" in error messages
    no_results_pattern = re.compile(r"no search results found", re.IGNORECASE)
    
    while attempts_made <= max_retries:  # Loop allows original attempt + retry attempts
        attempts_made += 1
        
        # Safely get the query string based on object type
        query_str = ""
        if isinstance(current_query, SearchQuery):
            query_str = current_query.keywords
        elif isinstance(current_query, ResourceQuery):
            query_str = current_query.query
        else:
            logger.error(f"Unsupported query object type: {type(current_query)}")
            # Attempt to get a query string anyway or default
            query_str = getattr(current_query, 'keywords', getattr(current_query, 'query', 'unknown'))
            return SearchServiceResult(query=query_str, search_provider_error="Unsupported query object type")
            
        logger.info(f"Search attempt {attempts_made}/{max_retries+1} with query: '{query_str}'")
        
        # Execute the search with current query string
        result = await perform_search_and_scrape(
            query=query_str,
            tavily_key_provider=tavily_key_provider,
            max_results=search_config.get("max_results", 5),
            scrape_timeout=search_config.get("scrape_timeout", 10)
        )
        
        # Check if search failed with "no results" error
        search_error = result.search_provider_error
        if not search_error or not no_results_pattern.search(search_error):
            # Either no error or error is not "no results" - return as is
            if search_error and not no_results_pattern.search(search_error):
                logger.warning(f"Search failed with error (not 'no results'): {search_error}")
            return result
        
        # We have a "no results" error
        logger.warning(f"Search returned no results for query: '{query_str}'")
        
        # Check if we can retry
        if retries_left <= 0:
            logger.info("No retries left, returning original result with no results")
            return result
        
        # Try to regenerate query
        logger.info(f"Attempting to regenerate query using LLM after no results for: '{query_str}'")
        try:
            # Call the regenerate function with the state, failed query object, and any additional args
            new_query_obj = await regenerate_query_func(state, current_query, **regenerate_args)
            
            if new_query_obj is None:
                logger.error("Query regeneration failed, returned None")
                return result # Return original failure
            
            # Safely get new query string for comparison and logging
            new_query_str = ""
            if isinstance(new_query_obj, SearchQuery):
                new_query_str = new_query_obj.keywords
            elif isinstance(new_query_obj, ResourceQuery):
                new_query_str = new_query_obj.query
            else:
                 logger.error(f"Regeneration returned unsupported query type: {type(new_query_obj)}")
                 return result # Return original failure
                 
            # Don't retry with the exact same query string
            if new_query_str == query_str:
                logger.warning("Regenerated query string is identical to original, won't retry")
                return result # Return original failure
            
            logger.info(f"Successfully regenerated query. Original: '{query_str}', New: '{new_query_str}'")
            current_query = new_query_obj # Use the new query OBJECT for the next loop iteration
            retries_left -= 1
            
        except Exception as e:
            logger.exception(f"Error during query regeneration: {str(e)}")
            # If regeneration fails, return the original error result
            return result
    
    # Should only reach here if max_retries is 0 and the first attempt failed with no results
    return result 