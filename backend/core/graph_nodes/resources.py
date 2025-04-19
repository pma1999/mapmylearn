"""
Resource generation functionality for learning paths.

This module contains all the functions for generating additional resources
at various levels (topic, module, submodule) of the learning path.
"""

import asyncio
import logging
import re
import os
from typing import Dict, Any, List, Optional

from backend.models.models import (
    SearchQuery,
    ResourceQuery,
    Resource,
    ResourceList,
    LearningPathState,
    EnhancedModule,
    Submodule,
    SearchServiceResult,
    ScrapedResult
)
from backend.parsers.parsers import resource_list_parser, resource_query_parser
from backend.services.services import get_llm, perform_search_and_scrape
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.prompts.learning_path_prompts import (
    TOPIC_RESOURCE_QUERY_GENERATION_PROMPT,
    MODULE_RESOURCE_QUERY_GENERATION_PROMPT,
    SUBMODULE_RESOURCE_QUERY_GENERATION_PROMPT,
    RESOURCE_EXTRACTION_PROMPT
)

from backend.core.graph_nodes.helpers import run_chain, escape_curly_braces
from backend.core.graph_nodes.search_utils import execute_search_with_llm_retry

# Configure logger
logger = logging.getLogger("learning_path.resources")

async def generate_topic_resources(state: LearningPathState) -> Dict[str, Any]:
    """
    Generates high-quality resources for the entire learning path topic using Tavily+Scraper.
    """
    logger.info(f"Generating topic-level resources for: {state['user_topic']}")

    # Check if resource generation is enabled
    if state.get("resource_generation_enabled") is False:
        logger.info("Resource generation is disabled, skipping topic resources")
        return {"topic_resources": [], "topic_resource_query": None, "topic_resource_search_results": [], "steps": ["Resource generation is disabled"]}

    # Get progress callback
    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Generating resources for topic: {state['user_topic']}",
            phase="topic_resources",
            phase_progress=0.0,
            overall_progress=0.45, # Keep overall progress estimate
            action="started"
        )

    resource_query: Optional[ResourceQuery] = None
    search_service_result: Optional[SearchServiceResult] = None

    try:
        # Get language information
        output_language = state.get('language', 'en')
        search_language = state.get('search_language', 'en')
        escaped_topic = escape_curly_braces(state["user_topic"])

        # Build learning path context (same logic as before)
        learning_path_context = ""
        if state.get("final_learning_path") and "modules" in state["final_learning_path"]:
            modules = state["final_learning_path"]["modules"]
            for i, module in enumerate(modules):
                if hasattr(module, 'title') and isinstance(module.title, str):
                    module_title = escape_curly_braces(module.title)
                    module_desc = escape_curly_braces(module.description)
                elif isinstance(module, dict) and "title" in module:
                    module_title = escape_curly_braces(module["title"])
                    module_desc = escape_curly_braces(module.get("description", "No description"))
                else:
                    module_title = escape_curly_braces(f"Module {i+1}")
                    module_desc = escape_curly_braces("No description available")
                learning_path_context += f"Module {i+1}: {module_title}\n{module_desc}\n\n"
        elif state.get("enhanced_modules"):
             modules = state["enhanced_modules"]
             for i, module in enumerate(modules):
                 module_title = escape_curly_braces(module.title)
                 module_desc = escape_curly_braces(module.description)
                 learning_path_context += f"Module {i+1}: {module_title}\n{module_desc}\n\n"

        # 1. Generate search query for topic resources (using Google LLM)
        prompt = ChatPromptTemplate.from_template(TOPIC_RESOURCE_QUERY_GENERATION_PROMPT)
        logger.info(f"Generating resource search query for topic: {escaped_topic}")
        if progress_callback:
            await progress_callback("Analyzing topic to find optimal resource search query...", phase="topic_resources", phase_progress=0.2, overall_progress=0.46, action="processing")

        query_result = await run_chain(prompt, lambda: get_llm(key_provider=state.get("google_key_provider")), resource_query_parser, {
            "user_topic": escaped_topic,
            "learning_path_context": learning_path_context,
            "language": output_language,
            "search_language": search_language,
            "format_instructions": resource_query_parser.get_format_instructions()
        })
        resource_query = query_result # ResourceQuery object

        # Update progress
        if progress_callback:
            await progress_callback(f"Searching & scraping for high-quality resources on {escaped_topic}...", phase="topic_resources", phase_progress=0.4, overall_progress=0.47, action="processing")

        # 2. Execute search and scrape with retry capability
        tavily_key_provider = state.get("tavily_key_provider")
        if not tavily_key_provider:
             raise ValueError("Tavily key provider not found in state for topic resource search.")

        scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))
        max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS", 5))

        # Set operation name for tracking
        provider = tavily_key_provider.set_operation("topic_resource_search")
        
        # Use the new execute_search_with_llm_retry function
        search_service_result = await execute_search_with_llm_retry(
            state=state,
            initial_query=resource_query, # Note: This is a ResourceQuery not SearchQuery
            regenerate_query_func=regenerate_resource_query,
            max_retries=1,
            tavily_key_provider=provider,
            search_config={
                "max_results": max_results_per_query,
                "scrape_timeout": scrape_timeout
            },
            regenerate_args={
                "target_level": "topic"
            }
        )

        # Check for search provider errors
        if search_service_result.search_provider_error:
            logger.warning(f"Search provider error after retry attempts: {search_service_result.search_provider_error}")
            # Continue with whatever results we have, which might be none

        # Log scraping success/failure summary
        scrape_errors = [r.scrape_error for r in search_service_result.results if r.scrape_error]
        successful_scrapes = len(search_service_result.results) - len(scrape_errors)
        logger.info(f"Scraping completed for topic resources query '{resource_query.query}'. Successful: {successful_scrapes}/{len(search_service_result.results)}.")
        if scrape_errors:
            logger.warning(f"Scraping errors encountered: {scrape_errors[:3]}...") # Log first few errors

        # Update progress
        if progress_callback:
            await progress_callback("Processing search results into curated resources...", phase="topic_resources", phase_progress=0.6, overall_progress=0.48, action="processing")

        # 3. Extract and format resources from scraped content (using Google LLM)
        resource_extractor_prompt = ChatPromptTemplate.from_template(RESOURCE_EXTRACTION_PROMPT)
        additional_context = f"This is the top-level topic of the learning path. Resources should provide comprehensive coverage of {escaped_topic}."

        # Prepare context from scraped results
        scraped_context_parts = []
        max_context_per_query_llm = 5 # Limit results used for LLM context
        max_chars_per_result_llm = 100000 # Limit chars per result for LLM context
        results_included_llm = 0
        for res in search_service_result.results:
             if results_included_llm >= max_context_per_query_llm:
                 break
             title = escape_curly_braces(res.title or 'N/A')
             url = res.url
             scraped_context_parts.append(f"### Source: {url} (Title: {title})")
             if res.scraped_content:
                 content = escape_curly_braces(res.scraped_content)
                 truncated_content = content[:max_chars_per_result_llm]
                 if len(content) > max_chars_per_result_llm:
                      truncated_content += "... (truncated)"
                 scraped_context_parts.append(f"Content Snippet:\n{truncated_content}")
                 results_included_llm += 1
             elif res.tavily_snippet: # Fallback to snippet
                 snippet = escape_curly_braces(res.tavily_snippet)
                 error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                 scraped_context_parts.append(f"Tavily Snippet:{error_info}\n{snippet}")
                 results_included_llm += 1
             else:
                 error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                 scraped_context_parts.append(f"Content: Not available.{error_info}")
                 # Don't increment results_included_llm if no content/snippet
             scraped_context_parts.append("---")
        search_results_context_for_llm = "\n".join(scraped_context_parts)
        # Provide URLs as separate context in case LLM needs them
        source_urls_for_llm = [res.url for res in search_service_result.results[:max_context_per_query_llm]]


        extraction_result = await run_chain(
            resource_extractor_prompt,
            lambda: get_llm(key_provider=state.get("google_key_provider")),
            resource_list_parser,
            {
                "search_query": resource_query.query,
                "target_level": "topic",
                "user_topic": escaped_topic,
                "additional_context": additional_context,
                # Use the processed scraped content/snippets as primary context
                "search_results": search_results_context_for_llm,
                # Provide URLs separately for potential reference by the LLM
                "search_citations": source_urls_for_llm,
                "resource_count": 6,  # Number of desired resources
                "format_instructions": resource_list_parser.get_format_instructions()
            }
        )

        topic_resources = extraction_result.resources
        logger.info(f"Generated {len(topic_resources)} topic-level resources")

        # Update progress with completion message
        if progress_callback:
            preview_data = {
                "resource_count": len(topic_resources),
                "resource_types": [resource.type for resource in topic_resources]
            }
            await progress_callback(
                f"Generated {len(topic_resources)} high-quality resources for {escaped_topic}",
                phase="topic_resources",
                phase_progress=1.0,
                overall_progress=0.49, # Keep overall progress estimate
                preview_data=preview_data,
                action="completed"
            )

        return {
            "topic_resources": topic_resources,
            "topic_resource_query": resource_query,
            # Store the detailed search/scrape result object instead of the old formatted string
            "topic_resource_search_results": search_service_result.model_dump() if search_service_result else None,
            "steps": state.get("steps", []) + [f"Generated {len(topic_resources)} resources for topic: {escaped_topic}"]
        }

    except Exception as e:
        logger.exception(f"Error generating topic resources: {str(e)}")
        if progress_callback:
            await progress_callback(f"Error generating topic resources: {str(e)}", phase="topic_resources", phase_progress=0.5, overall_progress=0.47, action="error")

        # Return partial results if available
        return {
            "topic_resources": [],
            "topic_resource_query": resource_query, # Return query if generated
            "topic_resource_search_results": search_service_result.model_dump() if search_service_result else None, # Return search results if obtained
            "steps": state.get("steps", []) + [f"Error generating topic resources: {str(e)}"]
        }


async def generate_module_resources(state: LearningPathState, module_id: int, module: EnhancedModule) -> Dict[str, Any]:
    """
    Generates resources for a specific module using Tavily+Scraper.
    """
    logger.info(f"Generating resources for module {module_id+1}: {module.title}")

    # Check if resource generation is enabled
    if state.get("resource_generation_enabled") is False:
        logger.info("Resource generation is disabled, skipping module resources")
        return {"resources": [], "status": "skipped"}

    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Generating resources for module: {module.title}",
            phase="module_resources",
            phase_progress=(module_id + 0.1) / max(1, len(state.get("enhanced_modules", []))), # Adjusted progress slightly
            overall_progress=0.65, # Keep estimate
            action="processing"
        )

    resource_query: Optional[ResourceQuery] = None
    search_service_result: Optional[SearchServiceResult] = None

    try:
        # Get language information
        output_language = state.get('language', 'en')
        search_language = state.get('search_language', 'en')
        escaped_topic = escape_curly_braces(state["user_topic"])

        # Build learning path context (same as before)
        learning_path_context = ""
        modules = state.get("enhanced_modules", [])
        for i, mod in enumerate(modules):
             indicator = " (CURRENT)" if i == module_id else ""
             if hasattr(mod, 'title') and isinstance(mod.title, str):
                 mod_title = escape_curly_braces(mod.title)
                 mod_desc = escape_curly_braces(mod.description)
             elif isinstance(mod, dict) and "title" in mod:
                 mod_title = escape_curly_braces(mod["title"])
                 mod_desc = escape_curly_braces(mod.get("description", "No description"))
             else:
                 mod_title = escape_curly_braces(f"Module {i+1}")
                 mod_desc = escape_curly_braces("No description available")
             learning_path_context += f"Module {i+1}: {mod_title}{indicator}\n{mod_desc}\n\n"

        # 1. Generate search query for module resources
        prompt = ChatPromptTemplate.from_template(MODULE_RESOURCE_QUERY_GENERATION_PROMPT)
        logger.info(f"Generating resource search query for module: {module.title}")
        if progress_callback:
             await progress_callback(f"Analyzing module '{module.title}' to find resource query...", phase="module_resources", phase_progress=(module_id + 0.2) / max(1, len(modules)), overall_progress=0.65, action="processing")

        module_title = escape_curly_braces(module.title if hasattr(module, 'title') else module.get("title", f"Module {module_id+1}"))
        module_description = escape_curly_braces(module.description if hasattr(module, 'description') else module.get("description", "No description"))

        query_result = await run_chain(prompt, lambda: get_llm(key_provider=state.get("google_key_provider")), resource_query_parser, {
            "user_topic": escaped_topic,
            "module_title": module_title,
            "module_description": module_description,
            "learning_path_context": learning_path_context,
            "language": output_language,
            "search_language": search_language,
            "format_instructions": resource_query_parser.get_format_instructions()
        })
        resource_query = query_result

        # Update progress
        if progress_callback:
             await progress_callback(f"Searching & scraping resources for module '{module.title}'...", phase="module_resources", phase_progress=(module_id + 0.4) / max(1, len(modules)), overall_progress=0.65, action="processing")

        # 2. Execute search and scrape with retry capability
        tavily_key_provider = state.get("tavily_key_provider")
        if not tavily_key_provider:
             raise ValueError("Tavily key provider not found in state for module resource search.")

        scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))
        max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS", 5))

        # Set operation name for tracking
        provider = tavily_key_provider.set_operation("module_resource_search")
        
        # Use the new execute_search_with_llm_retry function
        search_service_result = await execute_search_with_llm_retry(
            state=state,
            initial_query=resource_query, # Note: This is a ResourceQuery not SearchQuery
            regenerate_query_func=regenerate_resource_query,
            max_retries=1,
            tavily_key_provider=provider,
            search_config={
                "max_results": max_results_per_query,
                "scrape_timeout": scrape_timeout
            },
            regenerate_args={
                "target_level": "module",
                "context": {
                    "module_title": module_title,
                    "module_description": module_description
                }
            }
        )

        # Check for search provider errors
        if search_service_result.search_provider_error:
            logger.warning(f"Search provider error after retry attempts: {search_service_result.search_provider_error}")
            # Continue with whatever results we have, which might be none

        # Log scraping success/failure summary
        scrape_errors = [r.scrape_error for r in search_service_result.results if r.scrape_error]
        successful_scrapes = len(search_service_result.results) - len(scrape_errors)
        logger.info(f"Scraping completed for module '{module.title}' query '{resource_query.query}'. Successful: {successful_scrapes}/{len(search_service_result.results)}.")
        if scrape_errors:
            logger.warning(f"Scraping errors encountered: {scrape_errors[:3]}...")

        # Update progress
        if progress_callback:
            await progress_callback(f"Processing results for module '{module.title}'...", phase="module_resources", phase_progress=(module_id + 0.6) / max(1, len(modules)), overall_progress=0.66, action="processing")


        # 3. Extract and format resources from scraped content
        resource_extractor_prompt = ChatPromptTemplate.from_template(RESOURCE_EXTRACTION_PROMPT)
        additional_context = f"This is module {module_id+1} of the learning path focused on {module_title}. Resources should be specific to this module's content."

        # Prepare context from scraped results
        scraped_context_parts = []
        max_context_per_query_llm = 5 # Limit results used for LLM context
        max_chars_per_result_llm = 100000 # Limit chars per result for LLM context
        results_included_llm = 0
        for res in search_service_result.results:
             if results_included_llm >= max_context_per_query_llm:
                 break
             title = escape_curly_braces(res.title or 'N/A')
             url = res.url
             scraped_context_parts.append(f"### Source: {url} (Title: {title})")
             if res.scraped_content:
                 content = escape_curly_braces(res.scraped_content)
                 truncated_content = content[:max_chars_per_result_llm]
                 if len(content) > max_chars_per_result_llm:
                      truncated_content += "... (truncated)"
                 scraped_context_parts.append(f"Content Snippet:\n{truncated_content}")
                 results_included_llm += 1
             elif res.tavily_snippet: # Fallback to snippet
                 snippet = escape_curly_braces(res.tavily_snippet)
                 error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                 scraped_context_parts.append(f"Tavily Snippet:{error_info}\n{snippet}")
                 results_included_llm += 1
             else:
                 error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                 scraped_context_parts.append(f"Content: Not available.{error_info}")
             scraped_context_parts.append("---")
        search_results_context_for_llm = "\n".join(scraped_context_parts)
        source_urls_for_llm = [res.url for res in search_service_result.results[:max_context_per_query_llm]]

        extraction_result = await run_chain(
            resource_extractor_prompt,
            lambda: get_llm(key_provider=state.get("google_key_provider")),
            resource_list_parser,
            {
                "search_query": resource_query.query,
                "target_level": "module",
                "user_topic": escaped_topic,
                "additional_context": additional_context,
                "search_results": search_results_context_for_llm,
                "search_citations": source_urls_for_llm,
                "resource_count": 4,  # Desired resource count for modules
                "format_instructions": resource_list_parser.get_format_instructions()
            }
        )

        module_resources = extraction_result.resources
        logger.info(f"Generated {len(module_resources)} resources for module: {module_title}")

        # Update the module's resources if it's an object
        if hasattr(module, 'resources') and isinstance(module.resources, list):
            module.resources = module_resources

        if progress_callback:
            preview_data = {
                "module": {"id": module_id, "title": module_title},
                "resource_count": len(module_resources),
                "resource_types": [resource.type for resource in module_resources]
            }
            await progress_callback(
                f"Generated {len(module_resources)} resources for module: {module_title}",
                phase="module_resources",
                phase_progress=(module_id + 1) / max(1, len(modules)), # Mark as complete for this module
                overall_progress=0.66, # Keep estimate
                preview_data=preview_data,
                action="completed" # Changed from processing
            )

        return {
            "module_id": module_id,
            "resources": module_resources,
            "resource_query": resource_query,
            "search_results": search_service_result.model_dump() if search_service_result else None,
            "status": "completed"
        }

    except Exception as e:
        logger.exception(f"Error generating module resources for '{module.title}': {str(e)}")
        if progress_callback:
            await progress_callback(
                f"Error generating resources for module {module.title}: {str(e)}",
                phase="module_resources",
                phase_progress=(module_id + 0.5) / max(1, len(state.get("enhanced_modules", []))),
                overall_progress=0.65,
                action="error"
            )

        return {
            "module_id": module_id,
            "resources": [],
            "resource_query": resource_query,
            "search_results": search_service_result.model_dump() if search_service_result else None,
            "status": "error",
            "error": str(e)
        }


async def generate_submodule_resources(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    submodule_content: str # Assuming content generation happens before resource finding
) -> Dict[str, Any]:
    """
    Generates resources for a specific submodule using Tavily+Scraper.
    """
    logger.info(f"Generating resources for submodule {sub_id+1} in module {module_id+1}: {submodule.title}")

    if state.get("resource_generation_enabled") is False:
        logger.info("Resource generation is disabled, skipping submodule resources")
        return {"resources": [], "status": "skipped"}

    progress_callback = state.get('progress_callback')
    # Note: Progress reporting for submodules needs careful calculation based on total submodules
    total_submodules = sum(len(m.submodules) for m in state.get("enhanced_modules", []))
    completed_submodules_before = sum(len(m.submodules) for i, m in enumerate(state.get("enhanced_modules", [])) if i < module_id)
    current_submodule_index = completed_submodules_before + sub_id

    if progress_callback:
        await progress_callback(
            f"Generating resources for {module.title} > {submodule.title}",
            phase="submodule_resources",
            phase_progress=(current_submodule_index + 0.1) / max(1, total_submodules),
            overall_progress=0.75, # Keep estimate
            action="started" # Changed from processing
        )

    resource_query: Optional[ResourceQuery] = None
    search_service_result: Optional[SearchServiceResult] = None

    try:
        # Get language information
        output_language = state.get('language', 'en')
        search_language = state.get('search_language', 'en')
        escaped_topic = escape_curly_braces(state["user_topic"])

        # Build context (similar logic as before)
        learning_path_context = ""
        for i, mod in enumerate(state.get("enhanced_modules") or []):
             indicator = " (CURRENT MODULE)" if i == module_id else ""
             mod_title = escape_curly_braces(mod.title)
             mod_desc = escape_curly_braces(mod.description)
             learning_path_context += f"Module {i+1}: {mod_title}{indicator}\n{mod_desc}\n\n"

        module_title = escape_curly_braces(module.title)
        module_context = f"Current Module: {module_title}\nSubmodules:\n"
        for i, s in enumerate(module.submodules):
            indicator = " (CURRENT SUBMODULE)" if i == sub_id else ""
            sub_title = escape_curly_braces(s.title)
            sub_desc = escape_curly_braces(s.description)
            module_context += f"  {i+1}. {sub_title}{indicator}\n  {sub_desc}\n"

        adjacent_context = "Adjacent Submodules:\n"
        if sub_id > 0:
            prev = module.submodules[sub_id-1]
            prev_title = escape_curly_braces(prev.title); prev_desc = escape_curly_braces(prev.description)
            adjacent_context += f"Previous: {prev_title}\n{prev_desc}\n"
        else: adjacent_context += "No previous submodule.\n"
        if sub_id < len(module.submodules) - 1:
            nxt = module.submodules[sub_id+1]
            nxt_title = escape_curly_braces(nxt.title); nxt_desc = escape_curly_braces(nxt.description)
            adjacent_context += f"Next: {nxt_title}\n{nxt_desc}\n"
        else: adjacent_context += "No next submodule.\n"


        # 1. Generate search query for submodule resources
        prompt = ChatPromptTemplate.from_template(SUBMODULE_RESOURCE_QUERY_GENERATION_PROMPT)
        logger.info(f"Generating resource search query for submodule: {submodule.title}")
        if progress_callback:
             await progress_callback(f"Analyzing content to find optimal resources for {submodule.title}...", phase="submodule_resources", phase_progress=(current_submodule_index + 0.2) / max(1, total_submodules), overall_progress=0.76, action="processing")

        submodule_title = escape_curly_braces(submodule.title)
        submodule_description = escape_curly_braces(submodule.description)

        query_result = await run_chain(prompt, lambda: get_llm(key_provider=state.get("google_key_provider")), resource_query_parser, {
            "user_topic": escaped_topic,
            "module_title": module_title,
            "submodule_title": submodule_title,
            "submodule_description": submodule_description,
            "submodule_content": escape_curly_braces(submodule_content[:2000]), # Use generated content for context, truncated
            "submodule_order": sub_id + 1,
            "submodule_count": len(module.submodules),
            "module_order": module_id + 1,
            "module_count": len(state.get("enhanced_modules") or []),
            "module_context": module_context,
            "adjacent_context": adjacent_context,
            "language": output_language,
            "search_language": search_language,
            "format_instructions": resource_query_parser.get_format_instructions()
        })
        resource_query = query_result

        # Update progress
        if progress_callback:
            await progress_callback(f"Searching & scraping resources for {submodule.title}...", phase="submodule_resources", phase_progress=(current_submodule_index + 0.4) / max(1, total_submodules), overall_progress=0.78, action="processing")


        # 2. Execute search and scrape with retry capability
        tavily_key_provider = state.get("tavily_key_provider")
        if not tavily_key_provider:
             raise ValueError("Tavily key provider not found in state for submodule resource search.")

        scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))
        # Fewer results for submodules usually
        max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS_SUBMODULE", 5))

        # Set operation name for tracking
        provider = tavily_key_provider.set_operation("submodule_resource_search")
        
        # Use the new execute_search_with_llm_retry function
        search_service_result = await execute_search_with_llm_retry(
            state=state,
            initial_query=resource_query, # Note: This is a ResourceQuery not SearchQuery
            regenerate_query_func=regenerate_resource_query,
            max_retries=1,
            tavily_key_provider=provider,
            search_config={
                "max_results": max_results_per_query,
                "scrape_timeout": scrape_timeout
            },
            regenerate_args={
                "target_level": "submodule",
                "context": {
                    "submodule_title": submodule_title,
                    "submodule_description": submodule_description,
                    "module_title": module_title
                }
            }
        )

        # Check for search provider errors
        if search_service_result.search_provider_error:
            logger.warning(f"Search provider error after retry attempts: {search_service_result.search_provider_error}")
            # Continue with whatever results we have, which might be none

        # Log scraping success/failure summary
        scrape_errors = [r.scrape_error for r in search_service_result.results if r.scrape_error]
        successful_scrapes = len(search_service_result.results) - len(scrape_errors)
        logger.info(f"Scraping completed for submodule '{submodule.title}' query '{resource_query.query}'. Successful: {successful_scrapes}/{len(search_service_result.results)}.")
        if scrape_errors:
            logger.warning(f"Scraping errors encountered: {scrape_errors[:3]}...")


        # Update progress
        if progress_callback:
            await progress_callback(f"Processing results for {submodule.title}...", phase="submodule_resources", phase_progress=(current_submodule_index + 0.6) / max(1, total_submodules), overall_progress=0.8, action="processing")


        # 3. Extract and format resources from scraped content
        resource_extractor_prompt = ChatPromptTemplate.from_template(RESOURCE_EXTRACTION_PROMPT)
        additional_context = (
            f"This is submodule {sub_id+1} ('{submodule.title}') of module {module_id+1} ('{module_title}'). "
            f"Resources should be highly targeted to this specific submodule's content and learning objectives. "
            f"Submodule Content Summary:\n{submodule_content[:500]}..." # Include summary of content
        )

        # Prepare context from scraped results
        scraped_context_parts = []
        max_context_per_query_llm = 5 # Limit results used for LLM context
        max_chars_per_result_llm = 100000 # Limit chars per result for LLM context
        results_included_llm = 0
        for res in search_service_result.results:
             if results_included_llm >= max_context_per_query_llm:
                 break
             title = escape_curly_braces(res.title or 'N/A')
             url = res.url
             scraped_context_parts.append(f"### Source: {url} (Title: {title})")
             if res.scraped_content:
                 content = escape_curly_braces(res.scraped_content)
                 truncated_content = content[:max_chars_per_result_llm]
                 if len(content) > max_chars_per_result_llm:
                      truncated_content += "... (truncated)"
                 scraped_context_parts.append(f"Content Snippet:\n{truncated_content}")
                 results_included_llm += 1
             elif res.tavily_snippet: # Fallback to snippet
                 snippet = escape_curly_braces(res.tavily_snippet)
                 error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                 scraped_context_parts.append(f"Tavily Snippet:{error_info}\n{snippet}")
                 results_included_llm += 1
             else:
                 error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                 scraped_context_parts.append(f"Content: Not available.{error_info}")
             scraped_context_parts.append("---")
        search_results_context_for_llm = "\n".join(scraped_context_parts)
        source_urls_for_llm = [res.url for res in search_service_result.results[:max_context_per_query_llm]]


        extraction_result = await run_chain(
            resource_extractor_prompt,
            lambda: get_llm(key_provider=state.get("google_key_provider")),
            resource_list_parser,
            {
                "search_query": resource_query.query,
                "target_level": "submodule",
                "user_topic": escaped_topic,
                "additional_context": additional_context,
                "search_results": search_results_context_for_llm,
                "search_citations": source_urls_for_llm,
                "resource_count": 3,  # Desired resource count for submodules
                "format_instructions": resource_list_parser.get_format_instructions()
            }
        )

        submodule_resources = extraction_result.resources
        logger.info(f"Generated {len(submodule_resources)} resources for submodule: {submodule_title}")

        # Update the submodule's resources
        submodule.resources = submodule_resources

        # Update progress
        if progress_callback:
            preview_data = {
                 "module": {"id": module_id, "title": module_title},
                 "submodule": {"id": sub_id, "title": submodule_title},
                 "resource_count": len(submodule_resources),
                 "resource_types": [resource.type for resource in submodule_resources]
             }
            await progress_callback(
                 f"Generated {len(submodule_resources)} resources for {submodule.title}",
                 phase="submodule_resources",
                 phase_progress=(current_submodule_index + 1) / max(1, total_submodules),
                 overall_progress=0.8, # Keep estimate
                 preview_data=preview_data,
                 action="completed"
             )

        return {
            "module_id": module_id,
            "submodule_id": sub_id,
            "resources": submodule_resources,
            "resource_query": resource_query,
            "search_results": search_service_result.model_dump() if search_service_result else None,
            "status": "completed"
        }

    except Exception as e:
        logger.exception(f"Error generating submodule resources for '{submodule.title}': {str(e)}")
        if progress_callback:
             await progress_callback(
                 f"Error generating resources for {submodule.title}: {str(e)}",
                 phase="submodule_resources",
                 phase_progress=(current_submodule_index + 0.5) / max(1, total_submodules),
                 overall_progress=0.78,
                 action="error"
             )

        return {
            "module_id": module_id,
            "submodule_id": sub_id,
            "resources": [],
            "resource_query": resource_query,
            "search_results": search_service_result.model_dump() if search_service_result else None,
            "status": "error",
            "error": str(e)
        }

# Functions to manage the resource generation process within the graph

async def initialize_resource_generation(state: LearningPathState) -> Dict[str, Any]:
    """
    Initializes tracking for resource generation across modules and submodules.
    """
    logger.info("Initializing resource generation tracking.")
    if state.get("resource_generation_enabled") is False:
        logger.info("Resource generation is disabled globally.")
        return {
            "module_resources_in_process": {},
            "submodule_resources_in_process": {},
            "topic_resources": [], # Ensure initialized
            "steps": state.get("steps", []) + ["Resource generation disabled"]
        }

    module_count = len(state.get("enhanced_modules", []))
    module_resources_in_process = {mod_id: {"status": "pending"} for mod_id in range(module_count)}

    submodule_resources_in_process = {}
    for mod_id, module in enumerate(state.get("enhanced_modules", [])):
        for sub_id, _ in enumerate(module.submodules):
            submodule_key = f"{mod_id}_{sub_id}"
            submodule_resources_in_process[submodule_key] = {"status": "pending"}

    return {
        "module_resources_in_process": module_resources_in_process,
        "submodule_resources_in_process": submodule_resources_in_process,
        "topic_resources": [], # Ensure initialized
        "steps": state.get("steps", []) + ["Initialized resource generation tracking"]
    }


async def process_module_resources(state: LearningPathState) -> Dict[str, Any]:
    """
    Generates resources for all modules concurrently.
    This node runs AFTER submodules are processed.
    """
    logger.info("Starting concurrent generation of resources for all modules.")
    if state.get("resource_generation_enabled") is False:
        logger.info("Resource generation is disabled, skipping module resource processing.")
        # Update status for all modules
        module_resources_in_process = state.get("module_resources_in_process", {})
        for mod_id in module_resources_in_process:
             module_resources_in_process[mod_id]["status"] = "skipped"
        return {"module_resources_in_process": module_resources_in_process}


    modules: List[EnhancedModule] = state.get("enhanced_modules", [])
    if not modules:
        logger.warning("No enhanced modules found in state to generate resources for.")
        return {}

    tasks = []
    module_resources_in_process = state.get("module_resources_in_process", {})

    # Create tasks only for modules not already processed or skipped
    for module_id, module in enumerate(modules):
        if module_resources_in_process.get(module_id, {}).get("status") == "pending":
             tasks.append(generate_module_resources(state, module_id, module))
        else:
             logger.debug(f"Skipping resource generation for module {module_id+1}, status: {module_resources_in_process.get(module_id, {}).get('status')}")


    if not tasks:
         logger.info("No pending modules found for resource generation.")
         return {"module_resources_in_process": module_resources_in_process} # Return current state


    logger.info(f"Executing resource generation for {len(tasks)} modules concurrently.")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Update module_resources_in_process based on results
    processed_count = 0
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Error during concurrent module resource generation task: {result}")
            # Need to find which module failed - requires more complex tracking or assumptions
            # For now, log the error but don't update state accurately for the failed one
        elif isinstance(result, dict) and "module_id" in result:
            module_id = result["module_id"]
            module_resources_in_process[module_id] = {
                "status": result.get("status", "error"),
                "error": result.get("error"),
                "resource_count": len(result.get("resources", [])),
                "query": result.get("resource_query").query if result.get("resource_query") else None,
                # Avoid storing full search results in state if possible
                # "search_results": result.get("search_results")
            }
            if result.get("status") == "completed":
                processed_count += 1
        else:
             logger.warning(f"Unexpected result type from generate_module_resources: {type(result)}")

    logger.info(f"Completed processing resources for {processed_count}/{len(tasks)} pending modules.")

    # Update overall state (this might be redundant if modules were updated in place)
    # The 'enhanced_modules' list in the state should now have updated resources
    # due to the in-place update within generate_module_resources.

    return {
        "module_resources_in_process": module_resources_in_process,
        "steps": state.get("steps", []) + [f"Processed resources for {processed_count} modules"]
    }



async def integrate_resources_with_submodule_processing(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    submodule_content: str, # Content generated in the previous step
    original_result: Dict[str, Any] # Result from process_single_submodule
) -> Dict[str, Any]:
    """
    Generates resources for a submodule and integrates them into the original result.

    This function acts as a wrapper or subsequent step after submodule content
    is generated, allowing resource generation to happen alongside or after
    content development within the submodule processing loop.
    """
    logger.debug(f"Integrating resources for submodule {module_id+1}.{sub_id+1}: {submodule.title}")

    submodule_key = f"{module_id}_{sub_id}"
    submodule_resources_in_process = state.get("submodule_resources_in_process", {})

    if state.get("resource_generation_enabled") is False:
        logger.debug(f"Resource generation disabled, skipping integration for {submodule_key}")
        submodule_resources_in_process[submodule_key] = {"status": "skipped"}
        original_result["resources"] = [] # Ensure resources list is empty
        original_result["resource_query"] = None
        original_result["resource_search_results"] = None
        return {**original_result, "submodule_resources_in_process": submodule_resources_in_process}


    # Check if already processed
    if submodule_resources_in_process.get(submodule_key, {}).get("status") != "pending":
        logger.debug(f"Resource generation already processed for {submodule_key}, status: {submodule_resources_in_process.get(submodule_key, {}).get('status')}")
        # Ensure the original result reflects the previously generated resources
        # This assumes the 'submodule' object passed in already has the resources if completed previously
        original_result["resources"] = submodule.resources
        # We might not have stored query/results in state, so set to None
        original_result["resource_query"] = None
        original_result["resource_search_results"] = None
        return {**original_result, "submodule_resources_in_process": submodule_resources_in_process}

    # Generate resources for this submodule
    resource_result = await generate_submodule_resources(
        state, module_id, sub_id, module, submodule, submodule_content
    )

    # Update tracking state
    submodule_resources_in_process[submodule_key] = {
        "status": resource_result.get("status", "error"),
        "error": resource_result.get("error"),
        "resource_count": len(resource_result.get("resources", [])),
        "query": resource_result.get("resource_query").query if resource_result.get("resource_query") else None,
    }

    # Integrate results into the original submodule processing result
    # The 'submodule' object was updated in-place by generate_submodule_resources
    original_result["resources"] = resource_result.get("resources", [])
    original_result["resource_query"] = resource_result.get("resource_query")
    original_result["resource_search_results"] = resource_result.get("search_results") # Store the SearchServiceResult dict

    logger.debug(f"Finished integrating resources for submodule {module_id+1}.{sub_id+1}. Status: {resource_result.get('status')}")

    # Return the combined result, including updated tracking state
    return {**original_result, "submodule_resources_in_process": submodule_resources_in_process}



async def add_resources_to_final_learning_path(state: LearningPathState) -> Dict[str, Any]:
    """
    Adds the generated topic resources to the final learning path structure.
    Module/submodule resources should already be attached to their respective objects.
    """
    logger.info("Adding generated topic resources to the final learning path structure.")
    final_path = state.get("final_learning_path")
    topic_resources = state.get("topic_resources", [])

    if not final_path:
        logger.warning("Final learning path not found in state. Cannot add topic resources.")
        return {} # Or raise error?

    if state.get("resource_generation_enabled") is False:
        logger.info("Resource generation was disabled, ensuring no resources are added.")
        final_path["topic_resources"] = []
        # Ensure module/submodule resources are also empty if added previously
        if "modules" in final_path and isinstance(final_path["modules"], list):
             for module_data in final_path["modules"]:
                  if isinstance(module_data, dict):
                       module_data["resources"] = []
                       if "submodules" in module_data and isinstance(module_data["submodules"], list):
                            for sub_data in module_data["submodules"]:
                                 if isinstance(sub_data, dict):
                                      sub_data["resources"] = []
                  elif hasattr(module_data, 'resources'): # Handle object case if needed
                       module_data.resources = []
                       if hasattr(module_data, 'submodules'):
                            for sub_data in module_data.submodules:
                                 if hasattr(sub_data, 'resources'):
                                      sub_data.resources = []

    else:
        # Add topic resources
        final_path["topic_resources"] = topic_resources
        logger.info(f"Added {len(topic_resources)} topic resources to the final learning path.")

        # Add module resources from the processed state
        module_resources_data = state.get("module_resources_in_process", {})
        module_resource_count = 0
        submodule_resource_count = 0 # Initialize here

        if "modules" in final_path and isinstance(final_path["modules"], list):
            for module_index, module_data in enumerate(final_path["modules"]):
                # Find resources for this module index
                processed_module_resources = module_resources_data.get(module_index, {}).get("resources", [])
                if processed_module_resources:
                     if isinstance(module_data, dict):
                          module_data["resources"] = processed_module_resources
                     elif hasattr(module_data, 'resources'):
                          module_data.resources = processed_module_resources
                     module_resource_count += len(processed_module_resources)

                # Count submodule resources (already added in the previous step)
                if isinstance(module_data, dict):
                     if "submodules" in module_data and isinstance(module_data["submodules"], list):
                          for sub_data in module_data["submodules"]:
                               if isinstance(sub_data, dict):
                                    submodule_resource_count += len(sub_data.get("resources", []))
                elif hasattr(module_data, 'submodules'):
                     for sub_data in module_data.submodules:
                          if hasattr(sub_data, 'resources'):
                               submodule_resource_count += len(sub_data.resources)

        logger.info(f"Final path includes {len(topic_resources)} topic resources, {module_resource_count} module resources, and {submodule_resource_count} submodule resources.")


    return {"final_learning_path": final_path}

async def regenerate_resource_query(
    state: LearningPathState,
    failed_query: ResourceQuery,
    target_level: str = "topic",
    context: Dict[str, Any] = None
) -> ResourceQuery:
    """
    Regenerates a resource search query after a "no results found" error.
    
    This function uses an LLM to create an alternative resource search query
    when the original query returns no results. It provides the failed query 
    as context and instructs the LLM to broaden or rephrase the search while
    maintaining focus on finding high-quality learning resources.
    
    Args:
        state: The current LearningPathState with user_topic.
        failed_query: The ResourceQuery object that failed to return results.
        target_level: The level for which resources are being searched ('topic', 'module', 'submodule').
        context: Additional context specific to the resource level, such as module or submodule details.
        
    Returns:
        A new ResourceQuery object with an alternative query.
    """
    if context is None:
        context = {}
    
    logger.info(f"Regenerating {target_level} resource query after no results for: {failed_query.query}")
    
    # Get language information from state
    output_language = state.get('language', 'en')
    search_language = state.get('search_language', 'en')
    
    # Get Google key provider from state
    google_key_provider = state.get("google_key_provider")
    if not google_key_provider:
        logger.warning("Google key provider not found in state for resource query regeneration")
    
    # Build context specific details based on target_level
    resource_level_context = ""
    if target_level == "topic":
        resource_level_context = f"This query is for finding high-quality resources for the ENTIRE topic: {state['user_topic']}"
    elif target_level == "module" and 'module_title' in context:
        resource_level_context = f"This query is for finding resources for a SPECIFIC MODULE: {context['module_title']}\nModule Description: {context.get('module_description', 'No description available')}"
    elif target_level == "submodule" and 'submodule_title' in context:
        resource_level_context = f"This query is for finding resources for a SPECIFIC SUBMODULE: {context['submodule_title']}\nSubmodule Description: {context.get('submodule_description', 'No description available')}"
    else:
        resource_level_context = f"This query is for finding learning resources related to: {state['user_topic']}"
    
    prompt_text = """
# RESOURCE SEARCH QUERY RETRY SPECIALIST INSTRUCTIONS

The following search query returned NO RESULTS when searching for learning resources:

FAILED QUERY: {failed_query}

Resource Level Context:
{resource_level_context}

I need you to generate a DIFFERENT search query that is more likely to find results but still focused on retrieving HIGH-QUALITY LEARNING RESOURCES for this specific learning need.

## ANALYSIS OF FAILED QUERY

Analyze why the previous query might have failed:
- Was it too specific with too many quoted terms?
- Did it use uncommon terminology or jargon?
- Was it too long or complex?
- Did it combine too many concepts that rarely appear together?
- Did it focus too narrowly on a specific resource type or format?

## NEW QUERY REQUIREMENTS

Create ONE alternative search query that:
1. Is BROADER or uses more common terminology
2. Maintains focus on finding high-quality learning resources (tutorials, guides, courses, videos, etc.)
3. Uses fewer quoted phrases (one at most)
4. Is more likely to match existing educational content
5. Balances specificity (finding relevant resources) with generality (getting actual results)

## LANGUAGE INSTRUCTIONS
- Generate your analysis and response in {output_language}.
- For the search query, use {search_language} to maximize retrieving high-quality resources.

## QUERY FORMAT RULES
- CRITICAL: Ensure your new query is DIFFERENT from the failed one
- Fewer keywords is better than too many
- QUOTE USAGE RULE: NEVER use more than ONE quoted phrase. Quotes are ONLY for essential multi-word concepts
- Getting some relevant results is BETTER than getting zero results
- Try different resource-related terms (tutorial, course, guide, learn, beginner, introduction, etc.)
- For technical topics, consider including common platforms, websites, or formats where such resources might be found

Your response should include just ONE search query and a brief rationale for why this query might work better.

{format_instructions}
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    try:
        result = await run_chain(prompt, lambda: get_llm(key_provider=google_key_provider), resource_query_parser, {
            "user_topic": state["user_topic"],
            "failed_query": failed_query.query,
            "resource_level_context": resource_level_context,
            "output_language": output_language,
            "search_language": search_language,
            "format_instructions": resource_query_parser.get_format_instructions()
        })
        
        if not result or not hasattr(result, 'query'):
            logger.error("Resource query regeneration returned invalid result")
            return None
            
        logger.info(f"Successfully regenerated resource query: {result.query}")
        return result
    except Exception as e:
        logger.exception(f"Error regenerating resource query: {str(e)}")
        return None 