"""
Resource generation functionality for learning paths.

This module contains all the functions for generating additional resources
at various levels (topic, module, submodule) of the learning path.
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional

from backend.models.models import (
    SearchQuery, 
    ResourceQuery, 
    Resource, 
    ResourceList, 
    LearningPathState, 
    EnhancedModule, 
    Submodule
)
from backend.parsers.parsers import resource_list_parser, resource_query_parser
from backend.services.services import get_llm, get_search_tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.prompts.learning_path_prompts import (
    TOPIC_RESOURCE_QUERY_GENERATION_PROMPT,
    MODULE_RESOURCE_QUERY_GENERATION_PROMPT,
    SUBMODULE_RESOURCE_QUERY_GENERATION_PROMPT,
    RESOURCE_EXTRACTION_PROMPT
)

from backend.core.graph_nodes.helpers import run_chain, escape_curly_braces

# Configure logger
logger = logging.getLogger("learning_path.resources")

def extract_citations_from_content(content: str) -> List[str]:
    """
    Extract citation links from Perplexity response content.
    
    This function uses multiple strategies to find all citation URLs in the content:
    1. Look for a References/Sources section at the end
    2. Find citation brackets with URLs 
    3. Extract direct URLs as a fallback
    
    Args:
        content: The text content from the Perplexity response
        
    Returns:
        List of URLs extracted from the content
    """
    urls = []
    
    # Strategy 1: Look for a References or Sources section with URLs
    references_section = re.search(r'(?:References|Sources)(?::|)\s*((?:.|\n)+)$', content)
    if references_section:
        section_text = references_section.group(1)
        reference_urls = re.findall(r'https?://[^\s\]]+', section_text)
        urls.extend(reference_urls)
    
    # Strategy 2: Look for citation brackets with URLs
    citation_links = re.findall(r'\[(\d+)\]\s*\(?([^)]*https?://[^)\s]+)[^)]*\)?', content)
    for num, url in citation_links:
        url_clean = re.search(r'(https?://[^\s\]]+)', url)
        if url_clean:
            urls.append(url_clean.group(1))
    
    # Strategy 3: Direct URLs as backup
    direct_urls = re.findall(r'https?://\S+', content)
    urls.extend(direct_urls)
    
    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls

async def generate_topic_resources(state: LearningPathState) -> Dict[str, Any]:
    """
    Generates high-quality resources for the entire learning path topic.
    
    Args:
        state: The current LearningPathState with user_topic and learning_path info.
        
    Returns:
        A dictionary containing the generated resources and related data.
    """
    logger.info(f"Generating topic-level resources for: {state['user_topic']}")
    
    # Check if resource generation is enabled
    if state.get("resource_generation_enabled") is False:
        logger.info("Resource generation is disabled, skipping topic resources")
        return {"topic_resources": [], "steps": ["Resource generation is disabled"]}
    
    # Get progress callback
    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Generating resources for topic: {state['user_topic']}",
            phase="topic_resources",
            phase_progress=0.0,
            overall_progress=0.45,
            action="started"
        )
    
    try:
        # Get language information
        output_language = state.get('language', 'en')
        search_language = state.get('search_language', 'en')
        
        # Build learning path context
        learning_path_context = ""
        if state.get("final_learning_path") and "modules" in state["final_learning_path"]:
            modules = state["final_learning_path"]["modules"]
            for i, module in enumerate(modules):
                # Handle both dictionary and object module types
                if hasattr(module, 'title') and isinstance(module.title, str):
                    # It's an object with attributes
                    module_title = escape_curly_braces(module.title)
                    module_desc = escape_curly_braces(module.description)
                elif isinstance(module, dict) and "title" in module:
                    # It's a dictionary
                    module_title = escape_curly_braces(module["title"])
                    module_desc = escape_curly_braces(module.get("description", "No description"))
                else:
                    # Fallback for any other case
                    module_title = escape_curly_braces(f"Module {i+1}")
                    module_desc = escape_curly_braces("No description available")
                
                learning_path_context += f"Module {i+1}: {module_title}\n{module_desc}\n\n"
        
        # If we also have enhanced_modules in the state, use those as well to build context
        elif state.get("enhanced_modules"):
            modules = state["enhanced_modules"]
            for i, module in enumerate(modules):
                module_title = escape_curly_braces(module.title)
                module_desc = escape_curly_braces(module.description)
                learning_path_context += f"Module {i+1}: {module_title}\n{module_desc}\n\n"
        
        # 1. Generate search query for topic resources
        prompt = ChatPromptTemplate.from_template(TOPIC_RESOURCE_QUERY_GENERATION_PROMPT)
        
        logger.info(f"Generating resource search query for topic: {state['user_topic']}")
        if progress_callback:
            await progress_callback(
                f"Analyzing topic to find optimal resource search query...",
                phase="topic_resources",
                phase_progress=0.2,
                overall_progress=0.46,
                action="processing"
            )
        
        escaped_topic = escape_curly_braces(state["user_topic"])
        
        query_result = await run_chain(prompt, lambda: get_llm(key_provider=state.get("google_key_provider")), resource_query_parser, {
            "user_topic": escaped_topic,
            "learning_path_context": learning_path_context,
            "language": output_language,
            "search_language": search_language,
            "format_instructions": resource_query_parser.get_format_instructions()
        })
        
        resource_query = query_result
        
        # Update progress
        if progress_callback:
            await progress_callback(
                f"Searching for high-quality resources on {state['user_topic']}...",
                phase="topic_resources",
                phase_progress=0.4,
                overall_progress=0.47,
                action="processing"
            )
        
        # 2. Execute search for topic resources
        try:
            # Get the Perplexity key provider from state
            pplx_key_provider = state.get("pplx_key_provider")
            search_model = await get_search_tool(key_provider=pplx_key_provider)
            
            logger.info(f"Executing search for topic resources with query: {resource_query.query}")
            
            # Add a system message to request citation links
            system_message = """
            Additional Rules:
            - Always print the full URL instead of just the Citation Number
            - Include a List of References with the full URL in your answer
            - Always cite the sources of your web search
            """
            
            # Execute search with system message
            try:
                search_results = await search_model.ainvoke([
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": resource_query.query}
                ])
            except Exception as e:
                logger.warning(f"Error using system message approach: {str(e)}. Falling back to standard query.")
                search_results = await search_model.ainvoke(resource_query.query)
            
            # Extract citation links using three approaches in order of preference:
            
            # 1. Try to get citations from additional_kwargs if present
            citation_links = []
            if hasattr(search_results, 'additional_kwargs'):
                citations = search_results.additional_kwargs.get('citations', [])
                if citations:
                    logger.info(f"Found {len(citations)} citations in additional_kwargs")
                    citation_links.extend(citations)
            
            # 2. If no citations found in additional_kwargs, extract from content
            if not citation_links:
                content_citations = extract_citations_from_content(search_results.content)
                logger.info(f"Extracted {len(content_citations)} citation links from content")
                citation_links.extend(content_citations)
            
            # Format the search results for processing
            formatted_results = [
                {
                    "source": f"Perplexity Search Result for '{resource_query.query}'",
                    "content": search_results.content,
                    "citations": citation_links
                }
            ]
            
            # Update progress
            if progress_callback:
                await progress_callback(
                    f"Processing search results into curated resources...",
                    phase="topic_resources",
                    phase_progress=0.6,
                    overall_progress=0.48,
                    action="processing"
                )
            
            # 3. Extract and format resources from search results
            resource_extractor_prompt = ChatPromptTemplate.from_template(RESOURCE_EXTRACTION_PROMPT)
            
            additional_context = f"This is the top-level topic of the learning path. Resources should provide comprehensive coverage of {state['user_topic']}."
            
            extraction_result = await run_chain(
                resource_extractor_prompt, 
                lambda: get_llm(key_provider=state.get("google_key_provider")), 
                resource_list_parser, 
                {
                    "search_query": resource_query.query,
                    "target_level": "topic",
                    "user_topic": escaped_topic,
                    "additional_context": additional_context,
                    "search_results": search_results.content,
                    "search_citations": citation_links,  # Add extracted citations
                    "resource_count": 6,  # We want 6 resources for the topic level
                    "format_instructions": resource_list_parser.get_format_instructions()
                }
            )
            
            topic_resources = extraction_result.resources
            
            # Log the results
            logger.info(f"Generated {len(topic_resources)} topic-level resources")
            
            # Update progress with completion message
            if progress_callback:
                # Create preview data for the frontend
                preview_data = {
                    "resource_count": len(topic_resources),
                    "resource_types": [resource.type for resource in topic_resources]
                }
                
                await progress_callback(
                    f"Generated {len(topic_resources)} high-quality resources for {state['user_topic']}",
                    phase="topic_resources",
                    phase_progress=1.0,
                    overall_progress=0.49,
                    preview_data=preview_data,
                    action="completed"
                )
            
            return {
                "topic_resources": topic_resources,
                "topic_resource_query": resource_query,
                "topic_resource_search_results": formatted_results,
                "steps": [f"Generated {len(topic_resources)} resources for topic: {state['user_topic']}"]
            }
            
        except Exception as search_error:
            logger.error(f"Error executing search for topic resources: {str(search_error)}")
            if progress_callback:
                await progress_callback(
                    f"Error searching for topic resources: {str(search_error)}",
                    phase="topic_resources",
                    phase_progress=0.5,
                    overall_progress=0.47,
                    action="error"
                )
            
            return {
                "topic_resources": [],
                "topic_resource_query": resource_query,
                "topic_resource_search_results": [],
                "steps": [f"Error searching for topic resources: {str(search_error)}"]
            }
            
    except Exception as e:
        logger.exception(f"Error generating topic resources: {str(e)}")
        if progress_callback:
            await progress_callback(
                f"Error generating topic resources: {str(e)}",
                phase="topic_resources",
                phase_progress=0.5,
                overall_progress=0.47,
                action="error"
            )
        
        return {
            "topic_resources": [],
            "steps": [f"Error generating topic resources: {str(e)}"]
        }

async def generate_module_resources(state: LearningPathState, module_id: int, module: EnhancedModule) -> Dict[str, Any]:
    """
    Generates resources for a specific module.
    
    Args:
        state: The current LearningPathState.
        module_id: Index of the module.
        module: The EnhancedModule to generate resources for.
        
    Returns:
        A dictionary with generated resources and related data.
    """
    logger.info(f"Generating resources for module {module_id+1}: {module.title}")
    
    # Check if resource generation is enabled
    if state.get("resource_generation_enabled") is False:
        logger.info("Resource generation is disabled, skipping module resources")
        return {"resources": [], "status": "skipped"}
    
    # Get progress callback
    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Generating resources for module: {module.title}",
            phase="module_resources",
            phase_progress=(module_id + 0.5) / max(1, len(state.get("enhanced_modules", []))),
            overall_progress=0.65,
            action="processing"
        )
    
    try:
        # Get language information
        output_language = state.get('language', 'en')
        search_language = state.get('search_language', 'en')
        
        # Build learning path context
        learning_path_context = ""
        modules = state.get("enhanced_modules", [])
        for i, mod in enumerate(modules):
            # Ensure we handle different module types
            if hasattr(mod, 'title') and isinstance(mod.title, str):
                # It's an object with attributes
                indicator = " (CURRENT)" if i == module_id else ""
                mod_title = escape_curly_braces(mod.title)
                mod_desc = escape_curly_braces(mod.description)
                learning_path_context += f"Module {i+1}: {mod_title}{indicator}\n{mod_desc}\n\n"
            elif isinstance(mod, dict) and "title" in mod:
                # It's a dictionary
                indicator = " (CURRENT)" if i == module_id else ""
                mod_title = escape_curly_braces(mod["title"])
                mod_desc = escape_curly_braces(mod.get("description", "No description"))
                learning_path_context += f"Module {i+1}: {mod_title}{indicator}\n{mod_desc}\n\n"
            else:
                # Fallback for any other case
                indicator = " (CURRENT)" if i == module_id else ""
                mod_title = escape_curly_braces(f"Module {i+1}")
                mod_desc = escape_curly_braces("No description available")
                learning_path_context += f"Module {i+1}: {mod_title}{indicator}\n{mod_desc}\n\n"
        
        # 1. Generate search query for module resources
        prompt = ChatPromptTemplate.from_template(MODULE_RESOURCE_QUERY_GENERATION_PROMPT)
        
        logger.info(f"Generating resource search query for module: {module.title}")
        
        # Ensure we're using the correct attribute access for the module
        escaped_topic = escape_curly_braces(state["user_topic"])
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
        
        # 2. Execute search for module resources
        try:
            # Get the Perplexity key provider from state
            pplx_key_provider = state.get("pplx_key_provider")
            search_model = await get_search_tool(key_provider=pplx_key_provider)
            
            logger.info(f"Executing search for module resources with query: {resource_query.query}")
            
            # Add a system message to request citation links
            system_message = """
            Additional Rules:
            - Always print the full URL instead of just the Citation Number
            - Include a List of References with the full URL in your answer
            - Always cite the sources of your web search
            """
            
            # Execute search with system message
            try:
                search_results = await search_model.ainvoke([
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": resource_query.query}
                ])
            except Exception as e:
                logger.warning(f"Error using system message approach: {str(e)}. Falling back to standard query.")
                search_results = await search_model.ainvoke(resource_query.query)
            
            # Extract citation links using three approaches in order of preference:
            
            # 1. Try to get citations from additional_kwargs if present
            citation_links = []
            if hasattr(search_results, 'additional_kwargs'):
                citations = search_results.additional_kwargs.get('citations', [])
                if citations:
                    logger.info(f"Found {len(citations)} citations in additional_kwargs")
                    citation_links.extend(citations)
            
            # 2. If no citations found in additional_kwargs, extract from content
            if not citation_links:
                content_citations = extract_citations_from_content(search_results.content)
                logger.info(f"Extracted {len(content_citations)} citation links from content")
                citation_links.extend(content_citations)
            
            # Format the search results for processing
            formatted_results = [
                {
                    "source": f"Perplexity Search Result for '{resource_query.query}'",
                    "content": search_results.content,
                    "citations": citation_links
                }
            ]
            
            # 3. Extract and format resources from search results
            resource_extractor_prompt = ChatPromptTemplate.from_template(RESOURCE_EXTRACTION_PROMPT)
            
            additional_context = f"This is module {module_id+1} of the learning path focused on {module_title}. Resources should be specific to this module's content."
            
            extraction_result = await run_chain(
                resource_extractor_prompt, 
                lambda: get_llm(key_provider=state.get("google_key_provider")), 
                resource_list_parser, 
                {
                    "search_query": resource_query.query,
                    "target_level": "module",
                    "user_topic": escaped_topic,
                    "additional_context": additional_context,
                    "search_results": search_results.content,
                    "search_citations": citation_links,  # Add extracted citations
                    "resource_count": 4,  # We want 4 resources for module level
                    "format_instructions": resource_list_parser.get_format_instructions()
                }
            )
            
            module_resources = extraction_result.resources
            
            # Log the results
            logger.info(f"Generated {len(module_resources)} resources for module: {module_title}")
            
            # Update the module's resources if it's an object
            if hasattr(module, 'resources') and isinstance(module.resources, list):
                module.resources = module_resources
            
            # Update progress with completion message
            if progress_callback:
                # Create preview data for the frontend
                preview_data = {
                    "module": {
                        "id": module_id,
                        "title": module_title
                    },
                    "resource_count": len(module_resources),
                    "resource_types": [resource.type for resource in module_resources]
                }
                
                await progress_callback(
                    f"Generated {len(module_resources)} resources for module: {module_title}",
                    phase="module_resources",
                    phase_progress=(module_id + 1) / max(1, len(state.get("enhanced_modules", []))),
                    overall_progress=0.66,
                    preview_data=preview_data,
                    action="processing"
                )
            
            return {
                "module_id": module_id,
                "resources": module_resources,
                "resource_query": resource_query,
                "search_results": formatted_results,
                "status": "completed"
            }
            
        except Exception as search_error:
            logger.error(f"Error executing search for module resources: {str(search_error)}")
            if progress_callback:
                await progress_callback(
                    f"Error searching for module resources: {str(search_error)}",
                    phase="module_resources",
                    phase_progress=(module_id + 0.5) / max(1, len(state.get("enhanced_modules", []))),
                    overall_progress=0.65,
                    action="error"
                )
            
            return {
                "module_id": module_id,
                "resources": [],
                "resource_query": resource_query,
                "search_results": [],
                "status": "error",
                "error": str(search_error)
            }
            
    except Exception as e:
        logger.exception(f"Error generating module resources: {str(e)}")
        if progress_callback:
            await progress_callback(
                f"Error generating module resources: {str(e)}",
                phase="module_resources",
                phase_progress=(module_id + 0.5) / max(1, len(state.get("enhanced_modules", []))),
                overall_progress=0.65,
                action="error"
            )
        
        return {
            "module_id": module_id,
            "resources": [],
            "status": "error",
            "error": str(e)
        }

async def generate_submodule_resources(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    submodule_content: str
) -> Dict[str, Any]:
    """
    Generates resources for a specific submodule.
    
    Args:
        state: The current LearningPathState.
        module_id: Index of the parent module.
        sub_id: Index of the submodule.
        module: The EnhancedModule instance.
        submodule: The Submodule instance.
        submodule_content: The content of the submodule.
        
    Returns:
        A dictionary with generated resources and related data.
    """
    logger.info(f"Generating resources for submodule {sub_id+1} in module {module_id+1}: {submodule.title}")
    
    # Check if resource generation is enabled
    if state.get("resource_generation_enabled") is False:
        logger.info("Resource generation is disabled, skipping submodule resources")
        return {"resources": [], "status": "skipped"}
    
    # Get progress callback
    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Generating resources for {module.title} > {submodule.title}",
            phase="submodule_resources",
            phase_progress=0.0,
            overall_progress=0.75,
            action="started"
        )
    
    try:
        # Get language information
        output_language = state.get('language', 'en')
        search_language = state.get('search_language', 'en')
        
        # Build learning path context
        learning_path_context = ""
        for i, mod in enumerate(state.get("enhanced_modules") or []):
            indicator = " (CURRENT)" if i == module_id else ""
            mod_title = escape_curly_braces(mod.title)
            mod_desc = escape_curly_braces(mod.description)
            learning_path_context += f"Module {i+1}: {mod_title}{indicator}\n{mod_desc}\n\n"
        
        # Build module context
        module_title = escape_curly_braces(module.title)
        module_desc = escape_curly_braces(module.description)
        module_context = f"Current Module: {module_title}\nDescription: {module_desc}\nAll Submodules:\n"
        
        for i, s in enumerate(module.submodules):
            indicator = " (CURRENT)" if i == sub_id else ""
            sub_title = escape_curly_braces(s.title)
            sub_desc = escape_curly_braces(s.description)
            module_context += f"  {i+1}. {sub_title}{indicator}\n  {sub_desc}\n"
        
        # Build adjacent submodules context
        adjacent_context = "Adjacent Submodules:\n"
        if sub_id > 0:
            prev = module.submodules[sub_id-1]
            prev_title = escape_curly_braces(prev.title)
            prev_desc = escape_curly_braces(prev.description)
            adjacent_context += f"Previous: {prev_title}\n{prev_desc}\n"
        else:
            adjacent_context += "No previous submodule.\n"
        
        if sub_id < len(module.submodules) - 1:
            nxt = module.submodules[sub_id+1]
            nxt_title = escape_curly_braces(nxt.title)
            nxt_desc = escape_curly_braces(nxt.description)
            adjacent_context += f"Next: {nxt_title}\n{nxt_desc}\n"
        else:
            adjacent_context += "No next submodule.\n"
        
        # 1. Generate search query for submodule resources
        prompt = ChatPromptTemplate.from_template(SUBMODULE_RESOURCE_QUERY_GENERATION_PROMPT)
        
        logger.info(f"Generating resource search query for submodule: {submodule.title}")
        if progress_callback:
            await progress_callback(
                f"Analyzing content to find optimal resources for {submodule.title}...",
                phase="submodule_resources",
                phase_progress=0.2,
                overall_progress=0.76,
                action="processing"
            )
        
        escaped_topic = escape_curly_braces(state["user_topic"])
        submodule_title = escape_curly_braces(submodule.title)
        submodule_description = escape_curly_braces(submodule.description)
        
        query_result = await run_chain(prompt, lambda: get_llm(key_provider=state.get("google_key_provider")), resource_query_parser, {
            "user_topic": escaped_topic,
            "module_title": module_title,
            "submodule_title": submodule_title,
            "submodule_description": submodule_description,
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
            await progress_callback(
                f"Searching for high-quality resources for {submodule.title}...",
                phase="submodule_resources",
                phase_progress=0.4,
                overall_progress=0.78,
                action="processing"
            )
        
        # 2. Execute search for submodule resources
        try:
            # Get the Perplexity key provider from state
            pplx_key_provider = state.get("pplx_key_provider")
            search_model = await get_search_tool(key_provider=pplx_key_provider)
            
            logger.info(f"Executing search for submodule resources with query: {resource_query.query}")
            
            # Add a system message to request citation links
            system_message = """
            Additional Rules:
            - Always print the full URL instead of just the Citation Number
            - Include a List of References with the full URL in your answer
            - Always cite the sources of your web search
            """
            
            # Execute search with system message
            try:
                search_results = await search_model.ainvoke([
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": resource_query.query}
                ])
            except Exception as e:
                logger.warning(f"Error using system message approach: {str(e)}. Falling back to standard query.")
                search_results = await search_model.ainvoke(resource_query.query)
            
            # Extract citation links using three approaches in order of preference:
            
            # 1. Try to get citations from additional_kwargs if present
            citation_links = []
            if hasattr(search_results, 'additional_kwargs'):
                citations = search_results.additional_kwargs.get('citations', [])
                if citations:
                    logger.info(f"Found {len(citations)} citations in additional_kwargs")
                    citation_links.extend(citations)
            
            # 2. If no citations found in additional_kwargs, extract from content
            if not citation_links:
                content_citations = extract_citations_from_content(search_results.content)
                logger.info(f"Extracted {len(content_citations)} citation links from content")
                citation_links.extend(content_citations)
            
            # Format the search results for processing
            formatted_results = [
                {
                    "source": f"Perplexity Search Result for '{resource_query.query}'",
                    "content": search_results.content,
                    "citations": citation_links
                }
            ]
            
            # Update progress
            if progress_callback:
                await progress_callback(
                    f"Processing search results into curated resources...",
                    phase="submodule_resources",
                    phase_progress=0.6,
                    overall_progress=0.8,
                    action="processing"
                )
            
            # 3. Extract and format resources from search results
            resource_extractor_prompt = ChatPromptTemplate.from_template(RESOURCE_EXTRACTION_PROMPT)
            
            additional_context = (
                f"This is submodule {sub_id+1} of module {module_id+1} focused specifically on {submodule.title}. "
                f"Resources should be highly targeted to this specific submodule's content and learning objectives."
            )
            
            # Use a condensed version of the submodule content as additional context
            content_excerpt = submodule_content[:2000] + "..." if len(submodule_content) > 2000 else submodule_content
            additional_context += f"\n\nSubmodule Content Excerpt:\n{escape_curly_braces(content_excerpt)}"
            
            extraction_result = await run_chain(
                resource_extractor_prompt, 
                lambda: get_llm(key_provider=state.get("google_key_provider")), 
                resource_list_parser, 
                {
                    "search_query": resource_query.query,
                    "target_level": "submodule",
                    "user_topic": escaped_topic,
                    "additional_context": additional_context,
                    "search_results": search_results.content,
                    "search_citations": citation_links,  # Add extracted citations
                    "resource_count": 3,  # We want 3 resources for the submodule level
                    "format_instructions": resource_list_parser.get_format_instructions()
                }
            )
            
            submodule_resources = extraction_result.resources
            
            # Log the results
            logger.info(f"Generated {len(submodule_resources)} resources for submodule: {submodule.title}")
            
            # Update progress with completion message
            if progress_callback:
                # Create preview data for the frontend
                preview_data = {
                    "module": {
                        "id": module_id,
                        "title": module.title
                    },
                    "submodule": {
                        "id": sub_id,
                        "title": submodule.title
                    },
                    "resource_count": len(submodule_resources),
                    "resource_types": [resource.type for resource in submodule_resources]
                }
                
                await progress_callback(
                    f"Generated {len(submodule_resources)} resources for {submodule.title}",
                    phase="submodule_resources",
                    phase_progress=1.0,
                    overall_progress=0.82,
                    preview_data=preview_data,
                    action="completed"
                )
            
            return {
                "module_id": module_id,
                "sub_id": sub_id,
                "resources": submodule_resources,
                "resource_query": resource_query,
                "search_results": formatted_results,
                "status": "completed"
            }
            
        except Exception as search_error:
            logger.error(f"Error executing search for submodule resources: {str(search_error)}")
            if progress_callback:
                await progress_callback(
                    f"Error searching for submodule resources: {str(search_error)}",
                    phase="submodule_resources",
                    phase_progress=0.5,
                    overall_progress=0.79,
                    action="error"
                )
            
            return {
                "module_id": module_id,
                "sub_id": sub_id,
                "resources": [],
                "resource_query": resource_query,
                "search_results": [],
                "status": "error",
                "error": str(search_error)
            }
            
    except Exception as e:
        logger.exception(f"Error generating submodule resources: {str(e)}")
        if progress_callback:
            await progress_callback(
                f"Error generating submodule resources: {str(e)}",
                phase="submodule_resources",
                phase_progress=0.5,
                overall_progress=0.78,
                action="error"
            )
        
        return {
            "module_id": module_id,
            "sub_id": sub_id,
            "resources": [],
            "status": "error",
            "error": str(e)
        }

async def initialize_resource_generation(state: LearningPathState) -> Dict[str, Any]:
    """
    Initializes resource generation by setting up tracking variables and defaults.
    
    Args:
        state: The current LearningPathState.
        
    Returns:
        Updated state with resource generation tracking variables.
    """
    logger.info("Initializing resource generation")
    
    # Default to enabling resource generation unless explicitly disabled
    resource_generation_enabled = state.get("resource_generation_enabled", True)
    
    # Get progress callback
    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            "Preparing to generate additional learning resources...",
            phase="resources_init",
            phase_progress=0.0,
            overall_progress=0.4,
            action="started"
        )
    
    if not resource_generation_enabled:
        logger.info("Resource generation is disabled by user configuration")
        if progress_callback:
            await progress_callback(
                "Resource generation has been disabled in the settings",
                phase="resources_init",
                phase_progress=1.0,
                overall_progress=0.4,
                action="skipped"
            )
        
        return {
            "resource_generation_enabled": False,
            "topic_resources": [],
            "module_resources_in_process": {},
            "submodule_resources_in_process": {},
            "steps": ["Resource generation is disabled"]
        }
    
    # Initialize tracking dictionaries
    module_resources_in_process = {}
    submodule_resources_in_process = {}
    
    if progress_callback:
        await progress_callback(
            "Resource generation initialized and ready to begin",
            phase="resources_init",
            phase_progress=1.0,
            overall_progress=0.4,
            action="completed"
        )
    
    return {
        "resource_generation_enabled": True,
        "topic_resources": [],
        "module_resources_in_process": module_resources_in_process,
        "submodule_resources_in_process": submodule_resources_in_process,
        "steps": ["Initialized resource generation"]
    }

async def process_module_resources(state: LearningPathState) -> Dict[str, Any]:
    """
    Processes resource generation for all modules in parallel.
    
    Args:
        state: The current LearningPathState with enhanced_modules.
        
    Returns:
        Updated state with module resources.
    """
    logger.info("Processing resources for all modules")
    
    # Check if resource generation is enabled
    if state.get("resource_generation_enabled") is False:
        logger.info("Resource generation is disabled, skipping module resources")
        return {"steps": ["Resource generation is disabled"]}
    
    # Get enhanced modules
    enhanced_modules = state.get("enhanced_modules")
    if not enhanced_modules:
        logger.warning("No enhanced modules available for resource generation")
        return {"steps": ["No modules available for resource generation"]}
    
    # Get parallelism configuration
    parallel_count = state.get("parallel_count", 2)
    
    # Get progress callback
    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Generating resources for {len(enhanced_modules)} modules with parallelism of {parallel_count}",
            phase="module_resources",
            phase_progress=0.0,
            overall_progress=0.6,
            action="started"
        )
    
    # Create semaphore to control concurrency
    sem = asyncio.Semaphore(parallel_count)
    
    # Helper function to process module resources with semaphore
    async def process_module_resources_bounded(module_id, module):
        async with sem:  # Limits concurrency
            return await generate_module_resources(state, module_id, module)
    
    # Create tasks for all modules
    tasks = [process_module_resources_bounded(idx, module) 
             for idx, module in enumerate(enhanced_modules)]
    
    # Execute tasks in parallel and collect results
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results and update modules with resources
    module_resources_in_process = state.get("module_resources_in_process", {})
    
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Error processing module resources: {str(result)}")
            continue
        
        if isinstance(result, dict) and "module_id" in result and "status" in result:
            module_id = result["module_id"]
            status = result["status"]
            
            # Store the result in the tracking dictionary
            module_resources_in_process[module_id] = result
            
            # If successful, update the module with resources
            if status == "completed" and "resources" in result:
                resources = result["resources"]
                module = enhanced_modules[module_id]
                module.resources = resources
                
                logger.info(f"Added {len(resources)} resources to module {module_id+1}: {module.title}")
    
    # Log completion
    logger.info(f"Completed resource generation for {len(enhanced_modules)} modules")
    
    # Send completion update
    if progress_callback:
        # Count successful modules
        completed_count = sum(1 for result in results 
                              if isinstance(result, dict) and result.get("status") == "completed")
        
        await progress_callback(
            f"Generated resources for {completed_count} out of {len(enhanced_modules)} modules",
            phase="module_resources",
            phase_progress=1.0,
            overall_progress=0.7,
            action="completed"
        )
    
    return {
        "module_resources_in_process": module_resources_in_process,
        "steps": [f"Generated resources for {len(enhanced_modules)} modules"]
    }

async def integrate_resources_with_submodule_processing(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    submodule_content: str,
    original_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Integrates resource generation with submodule content processing.
    This function is meant to be called during submodule content development.
    
    Args:
        state: The current LearningPathState.
        module_id: Index of the parent module.
        sub_id: Index of the submodule.
        module: The EnhancedModule instance.
        submodule: The Submodule instance.
        submodule_content: The content of the submodule.
        original_result: The original result from submodule content processing.
        
    Returns:
        Updated result dictionary with resources added.
    """
    # Check if resource generation is enabled
    if state.get("resource_generation_enabled") is False:
        logger.info(f"Resource generation is disabled, skipping for submodule {module_id}.{sub_id}")
        return original_result  # Return the original result unchanged
    
    logger.info(f"Integrating resources for submodule {sub_id+1} in module {module_id+1}: {submodule.title}")
    
    try:
        # Generate resources for this submodule
        resource_result = await generate_submodule_resources(
            state, 
            module_id, 
            sub_id, 
            module, 
            submodule, 
            submodule_content
        )
        
        # Update the tracking dictionary in the state
        submodule_resources_in_process = state.get("submodule_resources_in_process", {})
        key = f"{module_id}:{sub_id}"
        submodule_resources_in_process[key] = resource_result
        state["submodule_resources_in_process"] = submodule_resources_in_process
        
        # Add resources to the original result
        if resource_result.get("status") == "completed" and "resources" in resource_result:
            original_result["resources"] = resource_result["resources"]
            
            # Also update the submodule itself to ensure resources are reflected in the final output
            submodule.resources = resource_result["resources"]
            
            logger.info(f"Added {len(resource_result['resources'])} resources to submodule {sub_id+1}")
        else:
            # If resource generation failed, still return the original result
            logger.warning(f"Resource generation for submodule {module_id}.{sub_id} did not complete successfully")
        
        return original_result
    
    except Exception as e:
        logger.exception(f"Error integrating resources for submodule {module_id}.{sub_id}: {str(e)}")
        # Still return the original result to ensure content is preserved even if resource generation fails
        return original_result

async def add_resources_to_final_learning_path(state: LearningPathState) -> Dict[str, Any]:
    """
    Adds generated resources to the final learning path structure.
    
    Args:
        state: The current LearningPathState with final_learning_path and resources.
        
    Returns:
        Updated state with resources added to final_learning_path.
    """
    logger.info("Adding resources to final learning path")
    
    # Check if resource generation was enabled
    if state.get("resource_generation_enabled") is False:
        logger.info("Resource generation was disabled, skipping resource integration")
        return {"steps": ["Resource generation was disabled"]}
    
    # Get the final learning path
    final_learning_path = state.get("final_learning_path")
    if not final_learning_path:
        logger.warning("No final learning path available")
        return {"steps": ["No final learning path available"]}
    
    # Get progress callback
    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            "Finalizing resources for learning path...",
            phase="resources_finalize",
            phase_progress=0.0,
            overall_progress=0.95,
            action="started"
        )
    
    try:
        # Get topic resources
        topic_resources = state.get("topic_resources") or []
        
        # Convert topic resources to dictionary format for the final learning path
        topic_resources_dicts = []
        for resource in topic_resources:
            topic_resources_dicts.append({
                "title": resource.title,
                "description": resource.description,
                "url": resource.url,
                "type": resource.type
            })
        
        # Add topic resources to the final learning path
        final_learning_path["topic_resources"] = topic_resources_dicts
        
        # Get module resources from the tracker
        module_resources_in_process = state.get("module_resources_in_process") or {}
        
        # Process each module in the final learning path
        if "modules" in final_learning_path:
            modules_array = final_learning_path["modules"]
            
            # Check if modules_array contains dictionaries or EnhancedModule objects
            for module_idx, module in enumerate(modules_array):
                # Handle different module types
                is_dict_module = isinstance(module, dict)
                
                # Initialize resources array if not present
                if is_dict_module:
                    if "resources" not in module:
                        module["resources"] = []
                else:
                    # For object-style modules, we need to ensure resources is initialized
                    # but this should be handled by the model defaults
                    pass
                
                # Add module resources if available
                if module_idx in module_resources_in_process:
                    result = module_resources_in_process[module_idx]
                    if result.get("status") == "completed" and "resources" in result:
                        module_resources = []
                        for resource in result["resources"]:
                            resource_dict = {
                                "title": resource.title,
                                "description": resource.description,
                                "url": resource.url,
                                "type": resource.type
                            }
                            module_resources.append(resource_dict)
                        
                        # Add resources to module based on its type
                        if is_dict_module:
                            module["resources"] = module_resources
                        else:
                            # For object modules, we'd need to update the object's resources
                            # But in final_learning_path it should be a dictionary
                            logger.warning(f"Module {module_idx} is not a dictionary, may not store resources properly")
                            # Try to convert the module's resources to the expected format
                            module_resources_attr = getattr(module, "resources", [])
                            if module_resources_attr:
                                dict_resources = []
                                for res in module_resources_attr:
                                    dict_resources.append({
                                        "title": res.title,
                                        "description": res.description,
                                        "url": res.url,
                                        "type": res.type
                                    })
                                # Update the object's resources dictionary
                                setattr(module, "resources", dict_resources)
                
                # Process submodules
                submodule_resources_in_process = state.get("submodule_resources_in_process") or {}
                
                # Handle submodules based on module type
                if is_dict_module and "submodules" in module:
                    submodules_array = module["submodules"]
                    for sub_idx, submodule in enumerate(submodules_array):
                        # Initialize resources array if not present
                        if "resources" not in submodule:
                            submodule["resources"] = []
                        
                        # Add submodule resources if available
                        key = f"{module_idx}:{sub_idx}"
                        if key in submodule_resources_in_process:
                            result = submodule_resources_in_process[key]
                            if result.get("status") == "completed" and "resources" in result:
                                sub_resources = []
                                for resource in result["resources"]:
                                    sub_resources.append({
                                        "title": resource.title,
                                        "description": resource.description,
                                        "url": resource.url,
                                        "type": resource.type
                                    })
                                submodule["resources"] = sub_resources
                elif hasattr(module, "submodules") and module.submodules:
                    # For object-style modules with submodules
                    for sub_idx, submodule in enumerate(module.submodules):
                        # Add submodule resources if available
                        key = f"{module_idx}:{sub_idx}"
                        if key in submodule_resources_in_process:
                            result = submodule_resources_in_process[key]
                            if result.get("status") == "completed" and "resources" in result:
                                sub_resources = []
                                for resource in result["resources"]:
                                    sub_resources.append({
                                        "title": resource.title,
                                        "description": resource.description,
                                        "url": resource.url,
                                        "type": resource.type
                                    })
                                # Update object's resources
                                submodule.resources = result["resources"]
                                
                                # Also update dictionary representation if it exists
                                if isinstance(module, dict) and "submodules" in module and isinstance(module["submodules"], list) and sub_idx < len(module["submodules"]):
                                    # Update dictionary representation
                                    module["submodules"][sub_idx]["resources"] = sub_resources
        
        # Update metadata to include resource counts
        if "metadata" not in final_learning_path:
            final_learning_path["metadata"] = {}
        
        # Count the resources
        topic_resource_count = len(topic_resources)
        
        module_resource_count = 0
        for module in final_learning_path.get("modules", []):
            if isinstance(module, dict):
                module_resource_count += len(module.get("resources", []))
            else:
                module_resource_count += len(getattr(module, "resources", []))
        
        submodule_resource_count = 0
        for module in final_learning_path.get("modules", []):
            if isinstance(module, dict) and "submodules" in module:
                for submodule in module.get("submodules", []):
                    submodule_resource_count += len(submodule.get("resources", []))
            elif hasattr(module, "submodules"):
                for submodule in module.submodules:
                    submodule_resource_count += len(getattr(submodule, "resources", []))
        
        total_resource_count = topic_resource_count + module_resource_count + submodule_resource_count
        
        # Add resource counts to metadata
        final_learning_path["metadata"]["topic_resource_count"] = topic_resource_count
        final_learning_path["metadata"]["module_resource_count"] = module_resource_count
        final_learning_path["metadata"]["submodule_resource_count"] = submodule_resource_count
        final_learning_path["metadata"]["total_resource_count"] = total_resource_count
        final_learning_path["metadata"]["has_resources"] = total_resource_count > 0
        
        logger.info(f"Added {total_resource_count} resources to the final learning path")
        
        # Update progress with completion message
        if progress_callback:
            await progress_callback(
                f"Added {total_resource_count} resources to the learning path",
                phase="resources_finalize",
                phase_progress=1.0,
                overall_progress=0.98,
                preview_data={
                    "topic_resources": topic_resource_count,
                    "module_resources": module_resource_count,
                    "submodule_resources": submodule_resource_count,
                    "total_resources": total_resource_count
                },
                action="completed"
            )
        
        return {
            "final_learning_path": final_learning_path,
            "steps": [f"Added {total_resource_count} resources to the final learning path"]
        }
    
    except Exception as e:
        logger.exception(f"Error adding resources to final learning path: {str(e)}")
        
        if progress_callback:
            await progress_callback(
                f"Error finalizing resources: {str(e)}",
                phase="resources_finalize",
                phase_progress=0.5,
                overall_progress=0.96,
                action="error"
            )
        
        return {
            "final_learning_path": final_learning_path,
            "steps": [f"Error adding resources to final learning path: {str(e)}"]
        } 