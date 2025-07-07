import asyncio
import logging
import re
import json
import os
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

import aiohttp
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser

from backend.models.models import (
    SearchQuery, 
    LearningPathState, 
    EnhancedModule, 
    Submodule, 
    SubmoduleContent,
    SearchServiceResult,
    ScrapedResult,
    QuizQuestion,
    QuizQuestionList,
    ResearchEvaluation
)
from backend.parsers.parsers import submodule_parser, module_queries_parser, quiz_questions_parser, search_queries_parser # Added search_queries_parser
from backend.services.services import get_llm, execute_search_with_router, get_llm_with_search, get_llm_for_evaluation
from backend.core.graph_nodes.helpers import run_chain, escape_curly_braces, batch_items, MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT # Import constant
from backend.core.graph_nodes.search_utils import execute_search_with_llm_retry

# Import the extracted prompts
from backend.prompts.learning_path_prompts import (
    SUBMODULE_PLANNING_PROMPT,
    SUBMODULE_QUIZ_GENERATION_PROMPT,
    MODULE_SUBMODULE_PLANNING_QUERY_GENERATION_PROMPT, # Added new prompt import
    ENHANCED_SUBMODULE_CONTENT_DEVELOPMENT_PROMPT # Added enhanced prompt import
    # Removed imports for prompts now defined inline
    # SUBMODULE_QUERY_GENERATION_PROMPT,
    # SUBMODULE_CONTENT_DEVELOPMENT_PROMPT
)

async def regenerate_submodule_content_query(
    state: LearningPathState,
    failed_query: SearchQuery,
    module_id: int = None,
    sub_id: int = None,
    module: EnhancedModule = None,
    submodule: Submodule = None
) -> Optional[SearchQuery]: # Return type changed to Optional[SearchQuery]
    """
    Regenerates a search query for submodule content development after a "no results found" error.
    
    This function uses an LLM to create an alternative search query when the original
    content-focused query returns no results. It provides the failed query as context
    and instructs the LLM to broaden or rephrase the search while maintaining focus on
    finding information relevant to developing the submodule content.
    
    Args:
        state: The current LearningPathState with user_topic.
        failed_query: The SearchQuery object that failed to return results.
        module_id: The index of the current module.
        sub_id: The index of the current submodule.
        module: The EnhancedModule object containing the submodule.
        submodule: The Submodule object for which content is being developed.
        
    Returns:
        A new SearchQuery object with keywords and rationale, or None if regeneration fails.
    """
    logger = logging.getLogger("learning_path.submodule_processor") # Use relevant logger
    logger.info(f"Regenerating submodule content query after no results for: {failed_query.keywords}")
    
    # Get language information from state
    from backend.utils.language_utils import get_full_language_name
    output_language_code = state.get('language', 'en')
    search_language_code = state.get('search_language', 'en')
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)
    
    # Get Google key provider from state
    google_key_provider = state.get("google_key_provider")
    if not google_key_provider:
        logger.warning("Google key provider not found in state for submodule query regeneration")
        return None # Return None if provider is missing
    
    # Build context information
    submodule_context = ""
    if module and submodule:
        escaped_topic = escape_curly_braces(state.get("user_topic", "the user's topic"))
        module_title = escape_curly_braces(module.title)
        submodule_title = escape_curly_braces(submodule.title)
        submodule_description = escape_curly_braces(submodule.description)
        
        submodule_context = f"""
Topic: {escaped_topic}
Module: {module_title}
Submodule: {submodule_title}
Submodule Description: {submodule_description}
Position: Submodule {sub_id + 1} of {len(module.submodules)} in Module {module_id + 1}
        """
    else:
         logger.warning("Module or submodule context missing for query regeneration.")
         # Optionally return None or create minimal context

    prompt_text = """
# SEARCH QUERY RETRY SPECIALIST INSTRUCTIONS

The following search query returned NO RESULTS when searching for information to develop content for a learning submodule:

FAILED QUERY: {failed_query}

## SUBMODULE CONTEXT
{submodule_context}

I need you to generate a DIFFERENT search query that is more likely to find results but still focused on retrieving RELEVANT INFORMATION for developing educational content about this submodule.

## ANALYSIS OF FAILED QUERY

Analyze why the previous query might have failed:
- Was it too specific with too many quoted terms?
- Did it use uncommon terminology or jargon?
- Was it too long or complex?
- Did it combine too many concepts that rarely appear together?
- Did it include too many technical terms or specific frameworks?

## NEW QUERY REQUIREMENTS

Create ONE alternative search query that:
1. Is BROADER or uses more common terminology
2. Maintains focus on the same subject matter as the original query
3. Uses fewer quoted phrases (one at most)
4. Is more likely to match existing educational content
5. Balances specificity (finding relevant content) with generality (getting actual results)

## LANGUAGE INSTRUCTIONS
- Generate your analysis and response in {output_language}.
- For the search query keywords, use {search_language} to maximize retrieving high-quality information.

## QUERY FORMAT RULES
- CRITICAL: Ensure your new query is DIFFERENT from the failed one
- Fewer keywords is better than too many
- QUOTE USAGE RULE: NEVER use more than ONE quoted phrase. Quotes are ONLY for essential multi-word concepts
- Getting some relevant results is BETTER than getting zero results
- Try different terms or synonyms that might be more common in educational content

Your response MUST be a JSON object containing only the 'keywords' (the new search query string) and 'rationale' (your brief analysis and justification for the new query).

{format_instructions}
"""
    try:
        # REMOVED local SingleSearchQueryOutput class definition

        # Use the correct SearchQuery model for the parser
        parser = PydanticOutputParser(pydantic_object=SearchQuery)
        
        prompt = ChatPromptTemplate.from_template(prompt_text)
        
        # Call run_chain with the correct parser and format instructions
        result = await run_chain(prompt, lambda: get_llm(key_provider=google_key_provider, user=state.get('user')), parser, {
            "failed_query": failed_query.keywords,
            "submodule_context": submodule_context,
            "output_language": output_language,
            "search_language": search_language,
            "format_instructions": parser.get_format_instructions() # Use correct parser's instructions
        })
        
        # Check if the result is a valid SearchQuery object
        if result and isinstance(result, SearchQuery):
            logger.info(f"Successfully regenerated submodule content query: Keywords='{result.keywords}', Rationale='{result.rationale}'")
            # Return the valid SearchQuery object directly
            return result
        else:
            logger.error(f"Submodule query regeneration returned empty or invalid result type: {type(result)}")
            return None
    except Exception as e:
        logger.exception(f"Error regenerating submodule content query: {str(e)}")
        return None

# Optional: Import the prompt registry for more advanced prompt management
# from prompts.prompt_registry import registry

# Helper function to extract JSON from potentially markdown-formatted strings
def extract_json_from_markdown(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from text that might be formatted as markdown code blocks.
    
    Args:
        text: The text that may contain markdown-formatted JSON
        
    Returns:
        Parsed JSON object or None if extraction failed
    """
    # First try to parse directly as JSON (in case it's already valid JSON)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(code_block_pattern, text)
    
    # If we found code blocks, try each one
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    # If no code blocks or none contained valid JSON, try a more lenient approach
    # Look for text that appears to be JSON (starting with { and ending with })
    json_object_pattern = r'(\{[\s\S]*\})'
    object_matches = re.findall(json_object_pattern, text)
    
    for match in object_matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    # If we couldn't extract JSON, return None
    return None

async def plan_submodules(state: LearningPathState) -> Dict[str, Any]:
    """
    Breaks down each module into 3-5 detailed submodules using an LLM chain.
    Processes modules in parallel based on the parallel_count configuration.
    
    Args:
        state: The current LearningPathState containing basic modules.
        
    Returns:
        A dictionary with enhanced modules (each including planned submodules) and a list of steps.
    """
    logging.info("Planning submodules for each module in parallel")
    if not state.get("modules"):
        logging.warning("No modules available")
        return {"enhanced_modules": [], "steps": ["No modules available"]}
    
    # Get parallelism configuration - use the parallel_count from the user settings
    parallel_count = state.get("parallel_count", 2)
    logging.info(f"Planning submodules with parallelism of {parallel_count}")
    
    progress_callback = state.get("progress_callback")
    if progress_callback:
        # Enhanced progress update with phase information
        await progress_callback(
            f"Planning submodules for {len(state['modules'])} modules with parallelism of {parallel_count}...",
            phase="submodule_planning",
            phase_progress=0.0,
            overall_progress=0.55,
            action="started"
        )
    
    # Create semaphore to control concurrency based on parallel_count
    sem = asyncio.Semaphore(parallel_count)
    
    # Helper function to plan submodules for a module with semaphore
    async def plan_module_submodules_bounded(idx, module):
        async with sem:  # Limits concurrency based on parallel_count
            return await plan_module_submodules(state, idx, module)
    
    # Create tasks to process each module in parallel
    tasks = [plan_module_submodules_bounded(idx, module) 
             for idx, module in enumerate(state.get("modules", []))]
    
    # Execute tasks in parallel and collect results
    enhanced_modules = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results and handle any exceptions
    processed_modules = []
    for idx, result in enumerate(enhanced_modules):
        if isinstance(result, Exception):
            logging.error(f"Error processing module {idx+1}: {str(result)}")
            # Create a fallback module with no submodules
            from backend.models.models import EnhancedModule
            processed_modules.append(EnhancedModule(
                title=state["modules"][idx].title,
                description=state["modules"][idx].description,
                submodules=[]
            ))
        else:
            processed_modules.append(result)
    
    # Create preview data for frontend display
    preview_modules = []
    total_submodules = 0
    
    for module in processed_modules:
        submodule_previews = []
        for submodule in module.submodules:
            submodule_previews.append({
                "title": submodule.title,
                "description": submodule.description[:100] + "..." if len(submodule.description) > 100 else submodule.description
            })
            total_submodules += 1
            
        preview_modules.append({
            "title": module.title,
            "submodules": submodule_previews
        })
    
    if progress_callback:
        await progress_callback(
            f"Planned {total_submodules} submodules across {len(processed_modules)} modules in parallel",
            phase="submodule_planning",
            phase_progress=1.0,
            overall_progress=0.6,
            preview_data={"type": "all_submodules_planned", "data": {"modules": preview_modules, "total_submodules_planned": total_submodules}}, # Enhanced preview_data
            action="completed"
        )
    
    return {
        "enhanced_modules": processed_modules, 
        "steps": [f"Planned submodules for {len(processed_modules)} modules in parallel using {parallel_count} parallel processes"]
    }

async def plan_module_submodules(state: LearningPathState, idx: int, module) -> Any:
    """
    Plans submodules for a specific module.
    
    Args:
        state: The current state.
        idx: Index of the module.
        module: The module to process.
        
    Returns:
        Enhanced module with planned submodules.
    """
    logging.info(f"Planning submodules for module {idx+1}: {module.title}")
    
    # Get progress callback
    progress_callback = state.get("progress_callback")
    
    # Send module-specific progress update
    if progress_callback:
        # Calculate overall progress based on module index
        total_modules = len(state.get("modules", []))
        module_progress = (idx + 0.2) / max(1, total_modules)  # Add 0.2 to avoid 0 progress
        overall_progress = 0.55 + (module_progress * 0.05)  # submodule planning is 5% of overall
        
        await progress_callback(
            f"Planning submodules for module {idx+1}: {module.title}",
            phase="submodule_planning",
            phase_progress=module_progress,
            overall_progress=overall_progress,
            preview_data={"current_module": {"title": module.title, "index": idx}},
            action="processing"
        )
    
    # Get language from state
    from backend.utils.language_utils import get_full_language_name
    output_language_code = state.get('language', 'en')
    output_language = get_full_language_name(output_language_code)
    
    learning_path_context = "\n".join([f"Module {i+1}: {mod.title}\n{mod.description}" 
                                       for i, mod in enumerate(state["modules"])])
    
    # Check if a specific number of submodules was requested
    submodule_count_instruction = ""
    if state.get("desired_submodule_count"):
        submodule_count_instruction = f"IMPORTANT: Create EXACTLY {state['desired_submodule_count']} submodules for this module. Not more, not less."
    
    # Modify the prompt to include the submodule count instruction if specified
    base_prompt = SUBMODULE_PLANNING_PROMPT
    if submodule_count_instruction:
        # Insert the instruction before the format_instructions placeholder
        base_prompt = base_prompt.replace("{format_instructions}", f"{submodule_count_instruction}\n\n{{format_instructions}}")
    
    # Using the extracted prompt template
    prompt = ChatPromptTemplate.from_template(base_prompt)
    try:
        result = await run_chain(prompt, lambda: get_llm(key_provider=state.get("google_key_provider"), user=state.get('user')), submodule_parser, {
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "module_description": module.description,
            "learning_path_context": learning_path_context,
            "language": output_language,
            "format_instructions": submodule_parser.get_format_instructions()
        })
        submodules = result.submodules
        
        # If a specific number of submodules was requested but not achieved, adjust the list
        if state.get("desired_submodule_count") and len(submodules) != state["desired_submodule_count"]:
            logging.warning(f"Requested {state['desired_submodule_count']} submodules but got {len(submodules)} for module {idx+1}")
            if len(submodules) > state["desired_submodule_count"]:
                # Trim excess submodules if we got too many
                submodules = submodules[:state["desired_submodule_count"]]
                logging.info(f"Trimmed submodules to match requested count of {state['desired_submodule_count']}")
        
        # Set order for each submodule
        for i, sub in enumerate(submodules):
            sub.order = i + 1
            
        # Create the enhanced module
        try:
            enhanced_module = module.model_copy(update={"submodules": submodules})
        except Exception:
            from backend.models.models import EnhancedModule
            enhanced_module = EnhancedModule(
                title=module.title,
                description=module.description,
                submodules=submodules
            )
            
        logging.info(f"Planned {len(submodules)} submodules for module {idx+1}")
        
        # Send progress update for completed module submodule planning
        if progress_callback:
            submodule_previews = []
            for submodule_idx, submodule in enumerate(submodules): # Added submodule_idx
                submodule_previews.append({
                    "id": submodule_idx, # Added id for keying
                    "title": submodule.title,
                    "order": submodule_idx, # Added order
                    "description_preview": submodule.description[:100] + "..." if len(submodule.description) > 100 else submodule.description,
                    "status": "planned" # Initial status
                })
                
            # Calculate slightly more progress
            module_progress = (idx + 1) / max(1, total_modules)
            overall_progress = 0.55 + (module_progress * 0.05)
            
            await progress_callback(
                f"Planned {len(submodules)} submodules for module {idx+1}: {module.title}",
                phase="submodule_planning", 
                phase_progress=module_progress,
                overall_progress=overall_progress,
                preview_data={
                    "type": "module_submodules_planned", # Specific type
                    "data": { # Wrapped in data
                        "module_id": idx, # Identify parent module
                        "module_title": module.title, 
                        "submodules": submodule_previews
                    }
                },
                action="processing" # This is still part of an ongoing process
            )
        
        return enhanced_module
        
    except Exception as e:
        logging.error(f"Error planning submodules for module {idx+1}: {str(e)}")
        
        # Send error progress update
        if progress_callback:
            await progress_callback(
                f"Error planning submodules for module {idx+1}: {str(e)}",
                phase="submodule_planning",
                phase_progress=(idx + 0.5) / max(1, len(state.get("modules", []))),
                overall_progress=0.57,
                action="error"
            )
            
        raise  # Propagate the exception to be handled in the parent function

async def initialize_submodule_processing(state: LearningPathState) -> Dict[str, Any]:
    """
    Initializes the batch processing of submodules by setting up tracking variables.
    Implements LangGraph's map-reduce pattern for optimized parallel processing.
    
    Args:
        state: The current state with enhanced modules.
        
    Returns:
        Updated state with batch processing tracking variables.
    """
    logging.info("Initializing submodule batch processing with LangGraph-optimized distribution")
    
    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback(
            "Preparing to enhance modules with targeted research and content development...",
            phase="submodule_research",
            phase_progress=0.0,
            overall_progress=0.6,
            action="started"
        )
    
    enhanced_modules = state.get("enhanced_modules")
    if not enhanced_modules:
        logging.warning("No enhanced modules available")
        return {
            "submodule_batches": [],
            "current_submodule_batch_index": 0,
            "submodules_in_process": {},
            "developed_submodules": [],
            "quiz_generation_enabled": True,  # Default to enabled
            "quiz_questions_by_submodule": {},
            "quiz_generation_in_progress": {},
            "quiz_generation_errors": {},
            "steps": ["No enhanced modules available"]
        }
    
    # Get the user-configured parallelism setting
    submodule_parallel_count = state.get("submodule_parallel_count", 2)
    
    # Create a flat list of all submodules across all modules
    # This follows LangGraph's pattern of mapping items first
    all_submodules = []
    for module_id, module in enumerate(enhanced_modules):
        if module.submodules:
            for sub_id in range(len(module.submodules)):
                all_submodules.append({
                    "module_id": module_id,
                    "sub_id": sub_id,
                    "module_title": module.title,
                    "submodule_title": module.submodules[sub_id].title,
                    "module_idx": module_id,     # For balanced sorting later
                    "total_submodules": len(module.submodules),  # Needed for balanced batching
                })
    
    if not all_submodules:
        logging.warning("No valid submodules found")
        return {
            "submodule_batches": [],
            "current_submodule_batch_index": 0,
            "submodules_in_process": {},
            "developed_submodules": [],
            "quiz_generation_enabled": True,  # Default to enabled
            "quiz_questions_by_submodule": {},
            "quiz_generation_in_progress": {},
            "quiz_generation_errors": {},
            "steps": ["No valid submodules found"]
        }
    
    # Optimize the distribution to balance work across batches
    # Instead of just alternating modules, we implement a more sophisticated strategy:
    # 1. Modules with more submodules should have their submodules distributed widely
    # 2. We'll sort by a custom key to achieve maximum distribution
    
    # First step: count submodules per module
    module_counts = {}
    for item in all_submodules:
        module_id = item["module_id"]
        module_counts[module_id] = module_counts.get(module_id, 0) + 1
    
    # Second step: create a more sophisticated distribution key
    # This prioritizes spreading out submodules from larger modules first
    def distribution_key(item):
        # Primary sort: submodule index divided by total submodules in module
        # This spreads out submodules from same module evenly
        relative_position = item["sub_id"] / max(1, item["total_submodules"])
        
        # Secondary sort: module ID to ensure consistent ordering
        module_id = item["module_id"]
        
        # The key prioritizes distributing all "first" submodules, then all "second" etc.
        # While keeping different modules together within each group
        return (relative_position, module_id)
    
    # Sort by our balanced distribution key
    all_submodules.sort(key=distribution_key)
    
    # Create the actual pairs for batch processing
    all_pairs = [(item["module_id"], item["sub_id"]) for item in all_submodules]
    
    # Create batches of size submodule_parallel_count
    submodule_batches = batch_items(all_pairs, submodule_parallel_count)
    
    total_submodules = len(all_submodules)
    total_batches = len(submodule_batches)
    
    logging.info(
        f"Using LangGraph map-reduce pattern: Organized {total_submodules} submodules into "
        f"{total_batches} batches with parallelism of {submodule_parallel_count}")
    
    # Create module title to submodule titles mapping for progress display
    module_to_submodules = {}
    for item in all_submodules:
        module_id = item["module_id"]
        if module_id not in module_to_submodules:
            module_to_submodules[module_id] = {
                "title": item["module_title"],
                "submodules": []
            }
        module_to_submodules[module_id]["submodules"].append({
            "title": item["submodule_title"],
            "sub_id": item["sub_id"]
        })
    
    # Create a preview of the batch processing plan
    preview_data = {
        "modules": [
            {
                "title": data["title"],
                "submodule_count": len(data["submodules"])
            } for module_id, data in module_to_submodules.items()
        ],
        "total_submodules": total_submodules,
        "total_batches": total_batches,
        "parallel_processing": submodule_parallel_count
    }
    
    # Initialize quiz generation settings - enable by default
    quiz_generation_enabled = state.get("quiz_generation_enabled", True)
    
    if progress_callback:
        # Add quiz information to progress message
        quiz_info = "with quiz generation enabled" if quiz_generation_enabled else "without quiz generation"
        await progress_callback(
            f"Preparing to process {total_submodules} submodules in {total_batches} batches "
            f"with {submodule_parallel_count} submodules in parallel ({quiz_info})",
            phase="submodule_research",
            phase_progress=0.1,
            overall_progress=0.6,
            preview_data=preview_data,
            action="processing"
        )
    
    return {
        "submodule_batches": submodule_batches,
        "current_submodule_batch_index": 0,
        "submodules_in_process": {},
        "developed_submodules": [],
        "quiz_generation_enabled": quiz_generation_enabled,
        "quiz_questions_by_submodule": {},
        "quiz_generation_in_progress": {},
        "quiz_generation_errors": {},
        "steps": [f"Initialized LangGraph-optimized submodule processing with batch size {submodule_parallel_count} and quiz generation {'enabled' if quiz_generation_enabled else 'disabled'}"]
    }

async def process_submodule_batch(state: LearningPathState) -> Dict[str, Any]:
    """
    Processes a batch of submodules in parallel, following LangGraph's map-reduce pattern.
    
    This function:
    1. Maps a set of submodules to parallel processing tasks
    2. Executes those tasks concurrently up to the user's configured parallelism limit
    3. Reduces the results back into the main state
    
    Args:
        state: The current state with enhanced modules and batch tracking.
        
    Returns:
        Updated state with processed submodules.
    """
    # Get the batch processing configuration
    submodule_parallel_count = state.get("submodule_parallel_count", 2)
    progress_callback = state.get("progress_callback")
    sub_batches = state.get("submodule_batches") or []
    current_index = state.get("current_submodule_batch_index", 0)
    batch_progress = 0
    overall_progress = 0.6
    
    logging.info(f"Processing submodule batch {current_index+1}/{len(sub_batches)} with parallelism of {submodule_parallel_count}")
    
    if progress_callback:
        # Calculate overall progress based on batch index and total batches
        total_batches = len(sub_batches)
        batch_progress = current_index / max(1, total_batches)
        # Research phase is from 60% to 70% of overall progress
        overall_progress = 0.6 + (batch_progress * 0.1)
        
        await progress_callback(
            f"Processing batch {current_index+1} of {len(sub_batches)} with {submodule_parallel_count} parallel tasks...",
            phase="submodule_research",
            phase_progress=batch_progress,
            overall_progress=overall_progress,
            action="processing"
        )
    
    # Check if all batches are already processed
    if current_index >= len(sub_batches):
        logging.info("All submodule batches processed")
        return {"steps": ["All submodule batches processed"]}
    
    # Get the current batch to process
    current_batch = sub_batches[current_index]
    
    # Get the enhanced modules
    enhanced_modules = state.get("enhanced_modules", [])
    if not enhanced_modules:
        logging.error("No enhanced modules found in state")
        return {"steps": ["Error: No enhanced modules found"]}
    
    # Get submodules tracking dictionary
    submodules_in_process = state.get("submodules_in_process", {})
    if submodules_in_process is None:
        submodules_in_process = {}
    
    # Prepare tasks for batch processing if we have items in the current batch
    tasks = []
    success_count = 0
    error_count = 0
    processed_submodules = []
    next_index = current_index + 1
    
    if current_batch:
        # Create tasks for parallel processing
        for module_id, sub_id in current_batch:
            # Validate indices
            if module_id < len(enhanced_modules):
                module = enhanced_modules[module_id]
                if sub_id < len(module.submodules):
                    submodule = module.submodules[sub_id]
                    # Only process if not already processed
                    # Convert tuple key to string
                    key = f"{module_id}:{sub_id}"
                    if key not in submodules_in_process or submodules_in_process[key].get("status") not in ["completed", "processing"]:
                        # Mark as processing
                        submodules_in_process[key] = {"status": "processing"}
                        # Add to tasks
                        tasks.append(process_single_submodule(state, module_id, sub_id, module, submodule))
        
        # If we have tasks, process them with asyncio.gather
        if tasks:
            try:
                # Start time for performance tracking
                import time
                start_time = time.time()
                
                # Process all tasks concurrently with gather
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update the tracking dictionary with results
                for result in results:
                    if isinstance(result, Exception):
                        error_count += 1
                        logging.error(f"Task error: {str(result)}")
                        continue
                    
                    if isinstance(result, dict):
                        module_id = result.get("module_id")
                        sub_id = result.get("sub_id")
                        status = result.get("status")
                        
                        if module_id is not None and sub_id is not None:
                            # Convert tuple key to string
                            key = f"{module_id}:{sub_id}"
                            submodules_in_process[key] = result
                            
                            if status == "completed":
                                success_count += 1
                                # Add to processed preview for frontend
                                if module_id < len(enhanced_modules):
                                    processed_submodules.append({
                                        "module_title": enhanced_modules[module_id].title,
                                        "submodule_title": enhanced_modules[module_id].submodules[sub_id].title,
                                        "status": "completed"
                                    })
                            elif status == "error":
                                error_count += 1
                
                # Calculate elapsed time
                elapsed_time = time.time() - start_time
                
                # Update batch progress for next phase
                batch_progress = (current_index + 1) / max(1, total_batches)
                # Content development is from 70% to 95% of overall progress
                overall_progress = 0.7 + (batch_progress * 0.25)
                
                if progress_callback:
                    # Calculate new overall progress
                    await progress_callback(
                        f"Completed batch {current_index+1}/{len(sub_batches)}: "
                        f"{success_count} successful, {error_count} failed in {elapsed_time:.2f} seconds",
                        phase="content_development",
                        phase_progress=batch_progress,
                        overall_progress=overall_progress,
                        preview_data={"processed_submodules": processed_submodules},
                        action="processing"
                    )
                    
                logging.info(f"Batch {current_index+1} results: {success_count} successful, {error_count} failed")
            except Exception as e:
                logging.error(f"Error in processing submodule batch: {str(e)}")
                if progress_callback:
                    await progress_callback(
                        f"Error processing batch: {str(e)}",
                        phase="content_development",
                        phase_progress=batch_progress,
                        overall_progress=overall_progress,
                        action="error"
                    )
        else:
            logging.info(f"No tasks to process in batch {current_index+1}")
            if progress_callback:
                await progress_callback(
                    f"No tasks to process in batch {current_index+1}",
                    phase="content_development",
                    phase_progress=batch_progress,
                    overall_progress=overall_progress,
                    action="processing"
                )
    
    # Update the list of developed submodules based on completed tasks
    # This is part of the "reduce" phase from the map-reduce pattern
    developed_submodules = state.get("developed_submodules", [])
    
    # Process all submodules from the current batch
    for module_id, sub_id in current_batch:
        # Convert tuple key to string
        key = f"{module_id}:{sub_id}"
        data = submodules_in_process.get(key, {})
        
        if data.get("status") == "completed" and module_id < len(enhanced_modules):
            module = enhanced_modules[module_id]
            if sub_id < len(module.submodules):
                # Convert SearchServiceResult objects to dictionaries
                search_results_raw = data.get("search_results", [])
                search_results_dicts = []
                if isinstance(search_results_raw, list):
                    for res in search_results_raw:
                        if hasattr(res, 'model_dump'): # Check if it's a Pydantic model (v2)
                           search_results_dicts.append(res.model_dump())
                        elif isinstance(res, dict): # Keep dicts as is (fallback)
                            search_results_dicts.append(res)
                        # else: log warning? skip?
                elif search_results_raw: # Handle case where it might be a single object?
                     if hasattr(search_results_raw, 'model_dump'):
                          search_results_dicts.append(search_results_raw.model_dump())
                     elif isinstance(search_results_raw, dict):
                          search_results_dicts.append(search_results_raw)

                # Create a SubmoduleContent object for the completed submodule
                developed_submodules.append(SubmoduleContent(
                    module_id=module_id,
                    submodule_id=sub_id,
                    title=module.submodules[sub_id].title,
                    description=module.submodules[sub_id].description,
                    search_queries=data.get("search_queries", []),
                    search_results=search_results_dicts, # Use the converted list of dicts
                    content=data.get("content", ""),
                    quiz_questions=data.get("quiz_questions", None),
                    resources=data.get("resources", []) # Add the resources here
                ))
    
    # Update progress based on completion percentage
    if progress_callback:
        processed_count = current_index + 1
        total_count = len(sub_batches)
        percentage = min(100, int((processed_count / total_count) * 100))
        
        # If this is the last batch, increase the phase progress to 1.0
        if next_index >= len(sub_batches):
            await progress_callback(
                f"Completed all {total_count} batches of submodule processing ({percentage}% complete)",
                phase="content_development",
                phase_progress=1.0,
                overall_progress=0.95,
                action="completed"
            )
        else:
            await progress_callback(
                f"Completed batch {current_index+1}/{len(sub_batches)} ({percentage}% of submodules processed)",
                phase="content_development",
                phase_progress=batch_progress,
                overall_progress=overall_progress,
                action="processing"
            )
    
    # Return the updated state with next batch index
    return {
        "current_submodule_batch_index": next_index,
        "submodules_in_process": submodules_in_process,
        "developed_submodules": developed_submodules,
        "steps": [f"Processed submodule batch {current_index+1} with {len(tasks)} parallel tasks using LangGraph pattern"]
    }

async def process_single_submodule(
    state: LearningPathState, 
    module_id: int, 
    sub_id: int, 
    module: EnhancedModule, 
    submodule: Submodule
) -> Dict[str, Any]:
    """
    Processes a single submodule in an optimized atomic operation that combines
    query generation, search, and content development.
    
    This function follows LangGraph's map-reduce pattern for parallel processing:
    1. It receives a single submodule state to process
    2. It processes the entire submodule independently
    3. It returns a complete result that can be integrated back into the main state
    
    Args:
        state: The current state.
        module_id: The index of the module.
        sub_id: The index of the submodule.
        module: The module object.
        submodule: The submodule object.
        
    Returns:
        Updated submodule with content.
    """
    logger = logging.getLogger("learning_path.submodule_processor")
    logger.info(f"Processing submodule {sub_id+1} in module {module_id+1}: {submodule.title}")
    
    progress_callback = state.get('progress_callback')
    
    try:
        # Track timing for performance analysis
        import time
        start_time = time.time()
        
        # Update progress if callback is available
        if progress_callback:
            await progress_callback(
                f"Processing: Module {module_id+1} > Submodule {sub_id+1}: {submodule.title}",
                phase="submodule_research",
                phase_progress=0.1, # Example progress
                overall_progress=0.6 + ( (module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10) ), # Approximate overall progress
                preview_data={
                    "type": "submodule_processing_started",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "submodule_title": submodule.title,
                        "status_detail": "research_started"
                    }
                },
                action="processing"
            )
        
        # STEP 1: Generate submodule-specific queries
        step_start = time.time()
        submodule_search_queries = await generate_submodule_specific_queries(
            state, module_id, sub_id, module, submodule
        )
        query_gen_time = time.time() - step_start
        logger.debug(f"Generated {len(submodule_search_queries)} queries for submodule in {query_gen_time:.2f}s")
        
        if progress_callback:
            await progress_callback(
                f"Generated search query for {module.title} > {submodule.title}",
                phase="submodule_research",
                phase_progress=0.3, # Example progress
                overall_progress=0.61 + ( (module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10) ),
                preview_data={
                    "type": "submodule_status_update",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "status_detail": "query_generated",
                        "queries": [q.keywords for q in submodule_search_queries] if submodule_search_queries else []
                    }
                },
                action="processing"
            )
        
        # STEP 2: Execute search for each query in parallel
        step_start = time.time()
        submodule_search_results = await execute_submodule_specific_searches(
            state, module_id, sub_id, module, submodule, submodule_search_queries
        )
        search_time = time.time() - step_start
        logger.debug(f"Completed {len(submodule_search_results)} searches in {search_time:.2f}s")
        
        if progress_callback:
            await progress_callback(
                f"Completed research for {module.title} > {submodule.title}",
                phase="submodule_research",
                phase_progress=0.8, # Example progress
                overall_progress=0.65 + ( (module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10) ),
                preview_data={
                    "type": "submodule_status_update",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "status_detail": "research_completed",
                        "search_result_count": len(submodule_search_results) if submodule_search_results else 0
                    }
                },
                action="completed" # This specific sub-phase is completed
            )
        
        # STEP 3: Develop submodule content based on search results
        step_start = time.time()
        
        # Transition to content development phase
        if progress_callback:
            await progress_callback(
                f"Developing content for {module.title} > {submodule.title}",
                phase="content_development",
                phase_progress=0.2, # Example progress
                overall_progress=0.67 + ( (module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10) ),
                preview_data={
                    "type": "submodule_status_update",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "status_detail": "content_development_started"
                    }
                },
                action="processing"
            )
            
        # STEP 3: Ensure research sufficiency before content development
        submodule_search_queries, submodule_search_results = await gather_research_until_sufficient(
            state,
            module_id,
            sub_id,
            module,
            submodule,
            submodule_search_queries,
            submodule_search_results,
            progress_callback,
        )

        submodule_content = await develop_submodule_specific_content(
            state,
            module_id,
            sub_id,
            module,
            submodule,
            submodule_search_queries,
            submodule_search_results,
        )
        content_time = time.time() - step_start
        
        # STEP 4: Generate quiz questions for the submodule
        step_start = time.time()
        
        # Transition to quiz generation phase
        if progress_callback:
            await progress_callback(
                f"Generating quiz questions for {module.title} > {submodule.title}",
                phase="quiz_generation",
                phase_progress=0.0, # Example progress
                overall_progress=0.75 + ( (module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10) ),
                preview_data={
                    "type": "submodule_status_update",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "status_detail": "quiz_generation_started"
                    }
                },
                action="started"
            )
        
        # Generate quiz questions if content was successfully developed
        quiz_questions = []
        if submodule_content and not submodule_content.startswith("Error:"):
            quiz_questions = await generate_submodule_quiz(
                state, module_id, sub_id, module, submodule, submodule_content
            )
        else:
            logger.warning(f"Skipping quiz generation for submodule {module_id}.{sub_id} due to content generation failure")
            
            # Send progress update for skipped quiz generation
            if progress_callback:
                await progress_callback(
                    f"Skipped quiz generation for {module.title} > {submodule.title} due to content generation failure",
                    phase="quiz_generation",
                    phase_progress=0.0,
                    overall_progress=0.75 + ( (module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10) ),
                    preview_data={
                        "type": "submodule_status_update",
                        "data": {
                            "module_id": module_id,
                            "submodule_id": sub_id,
                            "status_detail": "quiz_generation_skipped"
                        }
                    },
                    action="skipped"
                )
        
        quiz_time = time.time() - step_start
        
        # STEP 5: Generate resources for the submodule (new)
        step_start = time.time()
        
        # Create initial result without resources
        initial_result = {
            "status": "completed", 
            "module_id": module_id,
            "sub_id": sub_id,
            "search_queries": submodule_search_queries, 
            "search_results": submodule_search_results, 
            "content": submodule_content,
            "quiz_questions": quiz_questions,
            "processing_time": {
                "total": 0,  # Will update at the end
                "query_generation": query_gen_time,
                "search": search_time,
                "content_development": content_time,
                "quiz_generation": quiz_time,
                "resource_generation": 0  # Will update at the end
            }
        }
        
        # Skip resource integration if content generation failed
        if submodule_content and not submodule_content.startswith("Error:"):
            # Import the resource integration function
            from backend.core.graph_nodes.resources import integrate_resources_with_submodule_processing
            
            # Generate resources and integrate with the result
            result = await integrate_resources_with_submodule_processing(
                state, module_id, sub_id, module, submodule, submodule_content, initial_result, submodule_search_results
            )
        else:
            logger.warning(f"Skipping resource generation for submodule {module_id}.{sub_id} due to content generation failure")
            result = initial_result
        
        # Calculate resource generation time
        resource_time = time.time() - step_start
        
        # Calculate total processing time
        total_time = time.time() - start_time
        
        # Update the timing information in the result
        result["processing_time"]["resource_generation"] = resource_time
        result["processing_time"]["total"] = total_time
        
        logger.info(
            f"Completed submodule {module_id+1}.{sub_id+1} in {total_time:.2f}s "
            f"(Query: {query_gen_time:.2f}s, Search: {search_time:.2f}s, "
            f"Content: {content_time:.2f}s, Quiz: {quiz_time:.2f}s, Resources: {resource_time:.2f}s)"
        )
        
        if progress_callback:
            await progress_callback(
                f"Completed development for {module.title} > {submodule.title} in {total_time:.2f}s",
                phase="content_development",
                phase_progress=0.5,
                overall_progress=0.7 + ( (module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10) ),
                preview_data={
                    "type": "submodule_completed",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "status_detail": "fully_processed",
                        "quiz_question_count": len(quiz_questions) if quiz_questions else 0,
                        "resource_count": len(result.get("resources", [])) # Assuming result has resources by now
                    }
                },
                action="completed"
            )
        
        # Return the completed submodule data with module/submodule identifiers for proper "reduce" phase
        return result
    except Exception as e:
        logger.exception(f"Error processing submodule {sub_id+1} of module {module_id+1}: {str(e)}")
        if progress_callback:
            await progress_callback(
                f"Error in {module.title} > {submodule.title}: {str(e)}",
                phase="content_development",
                phase_progress=0.3,
                overall_progress=0.65 + ( (module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10) ),
                preview_data={
                    "type": "submodule_error",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "error_message": str(e)
                    }
                },
                action="error"
            )
        
        # Return error status with identifiers to maintain batch processing integrity
        return {
            "status": "error", 
            "module_id": module_id,
            "sub_id": sub_id,
            "error": str(e)
        }

async def generate_submodule_specific_queries(
    state: LearningPathState, 
    module_id: int, 
    sub_id: int, 
    module: EnhancedModule, 
    submodule: Submodule
) -> List[SearchQuery]:
    """
    Generates a single high-quality search query specific to a submodule.
    
    Args:
        state: The current LearningPathState.
        module_id: Index of the parent module.
        sub_id: Index of the submodule.
        module: The EnhancedModule instance.
        submodule: The Submodule instance.
        
    Returns:
        A list containing a single SearchQuery instance.
    """
    logger = logging.getLogger("learning_path.query_generator")
    logger.info(f"Generating search query for submodule {module_id}.{sub_id}: {submodule.title}")
    
    # Get the Google key provider from state
    google_key_provider = state.get("google_key_provider")
    
    # Get progress callback
    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback(
            f"Generating targeted search query for {module.title} > {submodule.title}",
            phase="submodule_research",
            phase_progress=0.2,
            overall_progress=0.61,
            action="processing"
        )
    
    # Get language information from state
    from backend.utils.language_utils import get_full_language_name
    output_language_code = state.get('language', 'en')
    search_language_code = state.get('search_language', 'en')
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)
    
    # Import función para escapar llaves
    from backend.core.graph_nodes.helpers import escape_curly_braces
    
    # Preparar contexto sobre el módulo y el submódulo
    # Escapar las llaves en todos los campos de texto
    user_topic = escape_curly_braces(state["user_topic"])
    module_title = escape_curly_braces(module.title)
    module_description = escape_curly_braces(module.description)
    submodule_title = escape_curly_braces(submodule.title)
    submodule_description = escape_curly_braces(submodule.description)
    submodule_depth = escape_curly_braces(submodule.depth_level)
    
    learning_context = {
        "topic": user_topic,
        "module_title": module_title,
        "module_description": module_description,
        "submodule_title": submodule_title,
        "submodule_description": submodule_description,
        "depth_level": submodule_depth
    }
    
    # Create context about other modules and submodules
    other_modules = []
    for i, m in enumerate(state.get("enhanced_modules", [])):
        other_modules.append({
            "title": escape_curly_braces(m.title),
            "description": escape_curly_braces(m.description[:200] + "..." if len(m.description) > 200 else m.description),
            "is_current": i == module_id
        })
    
    # Compile the context with a description of other modules
    learning_path_context = f"""
Topic: {learning_context['topic']}

Current Module: {learning_context['module_title']} 
Description: {learning_context['module_description']}

Current Submodule: {learning_context['submodule_title']}
Description: {learning_context['submodule_description']}
Depth Level: {learning_context['depth_level']}

Other Modules in Course:
"""
    for m in other_modules:
        learning_path_context += f"- {'[Current] ' if m['is_current'] else ''}{m['title']}: {m['description']}\n"
    
    # Set up module context and counts
    module_context = f"Current Module: {module_title}\nDescription: {module_description}"
    module_count = len(state.get("enhanced_modules", []))
    submodule_count = len(module.submodules)
    
    # Modified prompt template for single optimal query
    single_query_prompt = """
# EXPERT RESEARCHER INSTRUCTIONS

Your task is to create a SINGLE OPTIMAL search query for in-depth research on a specific educational submodule.

## SUBMODULE CONTEXT
- Topic: {user_topic}
- Module: {module_title} (Module {module_order} of {module_count})
- Submodule: {submodule_title} (Submodule {submodule_order} of {submodule_count})
- Description: {submodule_description}

## MODULE CONTEXT
{module_context}

## LEARNING PATH CONTEXT
{learning_path_context}

## LANGUAGE STRATEGY
- Final content will be presented to the user in {output_language}.
- For search queries, use {search_language} to maximize information quality.
- If the topic is highly specialized or regional/cultural, consider whether the search language should be adjusted for optimal results.

## SEARCH QUERY REQUIREMENTS

### 1. Keyword-Focused Format for Information Gathering
Your query MUST be optimized for retrieving detailed information via a search engine API (like Google or Brave Search) to be used for WRITING educational content: # Updated Tavily to Brave Search
- Use the most relevant and specific keywords and technical terms from the submodule title and description.
- Combine core concepts logically (e.g., use quotes for exact technical phrases if needed).
- Focus on terms that will find explanations, examples, processes, methodologies, case studies, or data related to the submodule topic.
- Avoid conversational language, questions, or instructions to the search engine.
- Aim for a concise yet comprehensive set of keywords for effective information retrieval.

### 2. Information Gathering Focus
Your query must target information that will be used to DEVELOP educational content:
- Focus on finding detailed, factual information about the submodule topic
- Seek comprehensive explanations of processes, concepts, and principles
- Look for examples, case studies, and applications that illustrate key points
- Target technical details, methodologies, and current best practices
- Request content that covers both theoretical foundations and practical applications

### 3. Content Development Needs
The query keywords should help find:
- Explanatory content rather than just basic definitions
- In-depth material that explains mechanisms and processes
- Content that addresses common misconceptions or challenges
- Varied perspectives and approaches to the subject matter
- Information helpful for creating comprehensive teaching materials

## YOUR TASK

Create ONE exceptionally well-crafted search engine query (keywords, phrases) that will:
1. Target the most critical information needed for this specific submodule
2. Be comprehensive enough to gather essential educational content
3. Retrieve detailed, accurate, and authoritative information
4. Focus precisely on the unique aspects of this submodule
5. Balance breadth and depth to maximize learning value

Provide:
1. The optimal search engine query string
2. A brief but comprehensive rationale explaining why this is the ideal query for finding information to develop this submodule

{format_instructions}
"""
    
    prompt = ChatPromptTemplate.from_template(single_query_prompt)
    
    from pydantic import BaseModel, Field
    
    class SingleSearchQueryOutput(BaseModel):
        query: str = Field(description="The optimal search query to use")
        rationale: str = Field(description="Explanation of why this query is optimal for this submodule")
    
    from langchain.output_parsers import PydanticOutputParser
    single_query_parser = PydanticOutputParser(pydantic_object=SingleSearchQueryOutput)
    
    try:
        result = await run_chain(prompt, lambda: get_llm(key_provider=google_key_provider, user=state.get('user')), single_query_parser, {
            "user_topic": user_topic,
            "module_title": module_title,
            "module_description": module_description,
            "submodule_title": submodule_title,
            "submodule_description": submodule_description,
            "module_order": module_id + 1,
            "module_count": module_count,
            "submodule_order": sub_id + 1,
            "submodule_count": submodule_count,
            "module_context": module_context,
            "learning_path_context": learning_path_context,
            "output_language": output_language,
            "search_language": search_language,
            "format_instructions": single_query_parser.get_format_instructions()
        })
        
        # Create a single high-quality SearchQuery
        query = SearchQuery(
            keywords=result.query,
            rationale=result.rationale
        )
        
        logging.info(f"Generated optimal search query for submodule {sub_id+1}: {query.keywords}")
        return [query]  # Return as list for compatibility with existing code
    except Exception as e:
        logging.error(f"Error generating submodule search query: {str(e)}")
        # Create a fallback query
        fallback_query = SearchQuery(
            keywords=f"{module_title} {submodule_title} tutorial comprehensive guide",
            rationale="Fallback query due to error in query generation"
        )
        return [fallback_query]

async def execute_submodule_specific_searches(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    sub_queries: List[SearchQuery]
) -> List[SearchServiceResult]:
    """
    Execute web searches specific to a submodule to gather content for development.
    Uses retry with regeneration for queries that return no results.
    """
    logging.info(f"Executing web searches for submodule {module_id+1}.{sub_id+1}: {submodule.title}")
    
    if not sub_queries:
        logging.warning(f"No search queries provided for submodule {module_id+1}.{sub_id+1}")
        return []
    
    # Get key parameters
    brave_key_provider = state.get("brave_key_provider") # Renamed tavily_key_provider
    if not brave_key_provider:
        raise ValueError(f"Brave Search key provider not found in state for submodule {module_id+1}.{sub_id+1}") # Updated message
    
    # Get search configuration
    max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS", 5))
    scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))
    
    results = []
    
    # Create a semaphore to limit concurrency
    sem = asyncio.Semaphore(3)  # Allow up to 3 concurrent searches
    
    async def bounded_search_with_retry(query_obj: SearchQuery):
        async with sem:
            # Set operation name for tracking
            provider = brave_key_provider.set_operation("submodule_content_search") # Renamed tavily_key_provider
            
            # Use the new execute_search_with_llm_retry function
            return await execute_search_with_llm_retry(
                state=state,
                initial_query=query_obj,
                regenerate_query_func=regenerate_submodule_content_query,
                search_provider_key_provider=provider, # Corrected parameter name
                search_config={
                    "max_results": max_results_per_query,
                    "scrape_timeout": scrape_timeout
                },
                regenerate_args={
                    "module_id": module_id,
                    "sub_id": sub_id,
                    "module": module,
                    "submodule": submodule
                }
            )
    
    try:
        tasks = [bounded_search_with_retry(query) for query in sub_queries]
        results_or_excs = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, res_or_exc in enumerate(results_or_excs):
            if isinstance(res_or_exc, Exception):
                logging.error(f"Search error for submodule {module_id+1}.{sub_id+1}: {str(res_or_exc)}")
                # Create an error result
                error_result = SearchServiceResult(
                    query=sub_queries[i].keywords,
                    search_provider_error=f"Search task error: {str(res_or_exc)}"
                )
                results.append(error_result)
            else:
                results.append(res_or_exc)
                # Log any search provider errors
                if res_or_exc.search_provider_error:
                    logging.warning(f"Search provider error for submodule query '{sub_queries[i].keywords}': {res_or_exc.search_provider_error}")
        
        return results
    
    except Exception as e:
        logging.exception(f"Error executing searches for submodule {module_id+1}.{sub_id+1}: {str(e)}")
        return [SearchServiceResult(
            query=f"Error: {str(e)}",
            search_provider_error=f"Failed to execute submodule searches: {str(e)}"
        )]

async def develop_submodule_specific_content(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    sub_queries: List[SearchQuery],
    sub_search_results: List[SearchServiceResult]
) -> str:
    """
    Develops comprehensive, detailed content for a submodule using enhanced prompting.
    """
    logger = logging.getLogger("learning_path.content_developer")
    logger.info(f"Developing enhanced content for submodule: {submodule.title}")

    # Get language and style settings
    from backend.utils.language_utils import get_full_language_name
    output_language_code = state.get('language', 'en')
    output_language = get_full_language_name(output_language_code)
    style = state.get('explanation_style', 'standard')

    # Enhanced style descriptions with length guidance
    style_descriptions = {
        "standard": """
**Style Instructions**: Provide balanced, comprehensive explanations suitable for focused learning. Use clear terminology and provide extensive detail with good depth. Structure content logically with smooth transitions between concepts. Aim for 1800-2200 words of substantial educational content.
""",
        "simple": """
**Style Instructions**: Explain concepts as if teaching someone intelligent but new to the topic. Prioritize absolute clarity and understanding. Use accessible vocabulary while maintaining accuracy. Include plenty of analogies and step-by-step breakdowns. Build concepts very gradually. Aim for 1600-2000 words with extensive explanations and examples.
""",
        "technical": """
**Style Instructions**: Provide precise, detailed technical exposition. Use correct technical terminology and formal language. Include specific mechanisms, implementation details, and underlying principles. Assume solid foundational knowledge but explain advanced concepts thoroughly. Aim for 2000-2500 words with comprehensive technical depth.
""",
        "example": """
**Style Instructions**: Illustrate every key concept with concrete, practical examples. Include relevant code snippets, case studies, or real-world scenarios throughout. Each major point should be demonstrated with at least one detailed example. Focus heavily on application and implementation. Aim for 1800-2300 words with extensive practical examples.
""",
        "conceptual": """
**Style Instructions**: Emphasize core principles, the 'why' behind concepts, and relationships between ideas. Focus on building mental models and deep understanding. Explore implications and connections extensively. Prioritize conceptual frameworks over implementation details. Aim for 1700-2100 words with thorough conceptual exploration.
""",
        "grumpy_genius": """
**Style Instructions**: Adopt the persona of a brilliant expert who finds explaining this topic mildly tedious but does so with comedic reluctance and sharp insights. Use phrases like "Look, this is actually straightforward once you stop overthinking it..." or "*Sigh*... Fine, let me explain why everyone gets this wrong...". Maintain accuracy while adding personality and humor. Aim for 1800-2200 words with engaging, personality-driven explanations.
"""
    }

    style_instructions = style_descriptions.get(style, style_descriptions["standard"])

    # Build comprehensive context sections
    learning_path_context = _build_learning_path_context(state, module_id)
    module_context = _build_module_context(module, sub_id)
    adjacent_context = _build_adjacent_context(module, sub_id)
    
    # Enhanced search results context with better organization
    search_results_context = _build_enhanced_search_context(sub_search_results)

    # Use the new enhanced prompt
    from backend.prompts.learning_path_prompts import ENHANCED_SUBMODULE_CONTENT_DEVELOPMENT_PROMPT
    prompt = ChatPromptTemplate.from_template(ENHANCED_SUBMODULE_CONTENT_DEVELOPMENT_PROMPT)

    # Execute enhanced content generation with retry for 429 errors
    try:
        llm_getter = lambda: get_llm_with_search(
            key_provider=state.get("google_key_provider"),
            user=state.get("user")
        )

        developed_content = await run_chain(
            prompt,
            llm_getter,
            StrOutputParser(),
            {
                "user_topic": escape_curly_braces(state["user_topic"]),
                "module_title": escape_curly_braces(module.title),
                "module_order": module_id + 1,
                "module_count": len(state.get("enhanced_modules", [])),
                "submodule_title": escape_curly_braces(submodule.title),
                "submodule_order": sub_id + 1,
                "submodule_count": len(module.submodules),
                "submodule_description": escape_curly_braces(submodule.description),
                "core_concept": escape_curly_braces(submodule.core_concept),
                "learning_objective": escape_curly_braces(submodule.learning_objective),
                "key_components": escape_curly_braces(', '.join(submodule.key_components)),
                "depth_level": escape_curly_braces(submodule.depth_level),
                "learning_path_context": learning_path_context,
                "module_context": module_context,
                "adjacent_context": adjacent_context,
                "style_instructions": style_instructions,
                "language": output_language,
                "search_results_context": search_results_context
            },
            max_retries=5,
            initial_retry_delay=1.0,
        )

        # Validate content length and quality
        content_length = len(developed_content)
        logger.info(f"Generated enhanced content for {submodule.title}: {content_length} characters")
        
        if content_length < 3000:  # Roughly 1500 words
            logger.warning(f"Generated content may be shorter than expected: {content_length} chars")

        return developed_content

    except Exception as e:
        logger.exception(f"Error in enhanced content development: {str(e)}")
        raise

async def generate_submodule_quiz(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    submodule_content: str
) -> List[QuizQuestion]:
    """
    Generates quiz questions for a submodule based on its content.
    
    Args:
        state: The current LearningPathState.
        module_id: Index of the parent module.
        sub_id: Index of the submodule.
        module: The EnhancedModule instance.
        submodule: The Submodule instance.
        submodule_content: The content of the submodule.
        
    Returns:
        A list of quiz questions for the submodule.
    """
    logger = logging.getLogger("learning_path.quiz_generator")
    logger.info(f"Generating quiz questions for submodule {sub_id+1} of module {module_id+1}: {submodule.title}")
    
    # Get progress callback
    progress_callback = state.get("progress_callback")
    
    # Check if quiz generation is enabled (default to True if not specified)
    if state.get("quiz_generation_enabled") is False:
        logger.info(f"Quiz generation is disabled, skipping for submodule {module_id}.{sub_id}")
        return []
    
    try:
        # Track timing for performance analysis
        import time
        start_time = time.time()
        
        # Send progress update
        if progress_callback:
            await progress_callback(
                f"Generating quiz questions for {module.title} > {submodule.title}",
                phase="quiz_generation",
                phase_progress=0.1,
                overall_progress=0.8,
                action="processing"
            )
        
        # Get output language from state
        from backend.utils.language_utils import get_full_language_name
        output_language_code = state.get('language', 'en')
        output_language = get_full_language_name(output_language_code)
        
        # Import escape function from helpers
        from backend.core.graph_nodes.helpers import escape_curly_braces
        
        # Escape curly braces in content and fields to avoid template parsing issues
        escaped_content = escape_curly_braces(submodule_content)
        user_topic = escape_curly_braces(state["user_topic"])
        module_title = escape_curly_braces(module.title)
        submodule_title = escape_curly_braces(submodule.title)
        submodule_description = escape_curly_braces(submodule.description)
        
        # Modify the original prompt to explicitly ask for raw JSON without markdown formatting
        # Add an explicit instruction not to use markdown formatting
        modified_quiz_prompt = SUBMODULE_QUIZ_GENERATION_PROMPT + """
## IMPORTANT FORMAT INSTRUCTIONS
- Return ONLY the raw JSON output without any markdown formatting
- DO NOT wrap your response in ```json or ``` markdown code blocks
- Provide a clean, valid JSON object that can be directly parsed
"""
        
        # Create prompt using the modified quiz generation prompt template
        prompt = ChatPromptTemplate.from_template(modified_quiz_prompt)
        
        # Get Google LLM for quiz generation
        llm = await get_llm(key_provider=state.get("google_key_provider"), user=state.get('user'))
        
        # Try using the standard parser first, but have fallback mechanisms
        try:
            # Invoke the LLM chain with the quiz generation prompt
            result = await run_chain(prompt, lambda: get_llm(key_provider=state.get("google_key_provider"), user=state.get('user')), quiz_questions_parser, {
                "user_topic": user_topic,
                "module_title": module_title,
                "submodule_title": submodule_title,
                "submodule_description": submodule_description,
                "submodule_content": escaped_content[:MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT],  # Limit content length to avoid token limits
                "language": output_language,
                "format_instructions": quiz_questions_parser.get_format_instructions()
            })
            
            # Extract questions from result if parsing was successful
            quiz_questions = result.questions
            
        except Exception as parsing_error:
            # If standard parsing fails, try our custom JSON extraction approach
            logger.warning(f"Standard parsing failed, attempting to extract JSON from response: {str(parsing_error)}")
            
            # Use run_chain with StrOutputParser instead of direct chain invocation
            raw_response = await run_chain(
                prompt,
                lambda: get_llm(key_provider=state.get("google_key_provider"), user=state.get('user')),
                StrOutputParser(),
                {
                    "user_topic": user_topic,
                    "module_title": module_title,
                    "submodule_title": submodule_title,
                    "submodule_description": submodule_description,
                    "submodule_content": escaped_content[:MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT],
                    "language": output_language,
                    "format_instructions": quiz_questions_parser.get_format_instructions()
                },
                max_retries=3,
                initial_retry_delay=1.0
            )
            
            # Try to extract and parse JSON from the raw response
            json_data = extract_json_from_markdown(raw_response)
            
            if json_data and "questions" in json_data:
                # Create a QuizQuestionList from the extracted JSON
                result = QuizQuestionList(**json_data)
                quiz_questions = result.questions
                logger.info("Successfully extracted quiz questions from markdown-formatted response")
            else:
                # If JSON extraction fails, log the error and return an empty list
                logger.error(f"Failed to extract valid JSON from LLM response: {raw_response[:500]}...")
                if progress_callback:
                    await progress_callback(
                        f"Could not generate quiz questions for {module.title} > {submodule.title} due to formatting issues",
                        phase="quiz_generation",
                        phase_progress=0.5,
                        overall_progress=0.8,
                        action="error"
                    )
                return []
        
        # Validate that we received questions
        if not quiz_questions:
            logger.warning(f"No quiz questions generated for submodule {module_id}.{sub_id}")
            return []
        
        # Ensure we have 10 questions (or trim if more)
        if len(quiz_questions) > 10:
            logger.info(f"Trimming excess quiz questions from {len(quiz_questions)} to 10")
            quiz_questions = quiz_questions[:10]
        
        # Log completion and timing
        generation_time = time.time() - start_time
        logger.info(f"Generated {len(quiz_questions)} quiz questions for submodule {module_id}.{sub_id} in {generation_time:.2f}s")
        
        # Send progress update on completion
        if progress_callback:
            await progress_callback(
                f"Generated {len(quiz_questions)} quiz questions for {module.title} > {submodule.title}",
                phase="quiz_generation",
                phase_progress=1.0,
                overall_progress=0.85,
                preview_data={"quiz_count": len(quiz_questions)},
                action="completed"
            )
        
        return quiz_questions
    
    except Exception as e:
        error_msg = f"Error generating quiz questions for submodule {module_id}.{sub_id}: {str(e)}"
        logger.exception(error_msg)
        
        # Update quiz generation errors tracking
        if state.get("quiz_generation_errors") is None:
            state["quiz_generation_errors"] = {}
        
        # Use string key for dictionary
        error_key = f"{module_id}:{sub_id}"
        state["quiz_generation_errors"][error_key] = str(e)
        
        # Send error progress update
        if progress_callback:
            await progress_callback(
                f"Error generating quiz questions: {str(e)}",
                phase="quiz_generation",
                phase_progress=0.5,
                overall_progress=0.8,
                action="error"
            )
        
        return []

async def finalize_enhanced_learning_path(state: LearningPathState) -> Dict[str, Any]:
    """
    Finalizes the enhanced course with all processed submodules.
    
    Args:
        state: The current state with all processed submodules.
        
    Returns:
        Final state with the complete enhanced course.
    """
    logging.info("Finalizing enhanced course")
    
    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback(
            "Finalizing your course with all enhanced content...",
            phase="final_assembly",
            phase_progress=0.0,
            overall_progress=0.95,
            action="started"
        )
    
    logger = logging.getLogger("learning_path.finalizer")
    logger.info("Finalizing enhanced course with submodules")
    try:
        if not state.get("developed_submodules"):
            logger.warning("No developed submodules available")
            return {"final_learning_path": {"topic": state["user_topic"], "modules": []}, "steps": ["No submodules developed"]}
            
        # Group submodules by module
        module_to_subs = {}
        for sub in state["developed_submodules"]:
            module_to_subs.setdefault(sub.module_id, []).append(sub)
            
        # Sort submodules within each module
        for module_id in module_to_subs:
            module_to_subs[module_id].sort(key=lambda s: s.submodule_id)
            
        # Send progress update
        if progress_callback:
            await progress_callback(
                "Organizing all developed content into final structure...",
                phase="final_assembly",
                phase_progress=0.5,
                overall_progress=0.97,
                action="processing"
            )
        
        final_modules = []
        total_quiz_questions = 0
        
        for module_id, module in enumerate(state.get("enhanced_modules") or []):
            subs = module_to_subs.get(module_id, [])
            submodule_data = []
            
            for sub in subs:
                summary = sub.summary if hasattr(sub, 'summary') else (sub.content[:200].strip() + "..." if sub.content else "")
                
                # Include quiz questions if available
                quiz_data = None
                if hasattr(sub, 'quiz_questions') and sub.quiz_questions:
                    quiz_data = []
                    for quiz in sub.quiz_questions:
                        quiz_data.append({
                            "question": quiz.question,
                            "options": [{"text": opt.text, "is_correct": opt.is_correct} for opt in quiz.options],
                            "explanation": quiz.explanation
                        })
                    total_quiz_questions += len(quiz_data)
                
                # Build research_context from raw scraped results
                research_parts = []
                for res in getattr(sub, "search_results", []):
                    # Ensure res is a dict before accessing keys
                    if isinstance(res, dict):
                        text = res.get("scraped_content") or res.get("search_snippet") or "" # Renamed tavily_snippet
                        if text:
                            snippet = text[:3000]
                            research_parts.append(f"Source: {res.get('url')}\n{snippet}")
                    else:
                        # Log if res is not a dict (unexpected)
                        logging.warning(f"Unexpected type for search result item in finalization: {type(res)}")
                research_context = "\n\n".join(research_parts)[:10000]

                # Add submodule data with quiz info and research context
                submodule_data.append({
                    "id": sub.submodule_id,
                    "title": sub.title,
                    "description": sub.description,
                    "content": sub.content,
                    "order": sub.submodule_id + 1,
                    "summary": summary,
                    "connections": getattr(sub, 'connections', {}),
                    "quiz_questions": quiz_data,
                    "resources": getattr(sub, 'resources', []),
                    "research_context": research_context
                })
            
            # Build module data
            module_data = {
                "id": module_id,
                "title": module.title,
                "description": module.description,
                "core_concept": getattr(module, 'core_concept', ""),
                "learning_objective": getattr(module, 'learning_objective', ""),
                "prerequisites": getattr(module, 'prerequisites', []),
                "key_components": getattr(module, 'key_components', []),
                "expected_outcomes": getattr(module, 'expected_outcomes', []),
                "submodules": submodule_data,
                "resources": []
            }
            
            final_modules.append(module_data)
            
        # Create the final course structure with quiz questions
        final_learning_path = {
            "topic": state["user_topic"], 
            "modules": final_modules, 
            "execution_steps": state["steps"],
            "metadata": {
                "total_modules": len(final_modules),
                "total_submodules": sum(len(module["submodules"]) for module in final_modules),
                "total_quiz_questions": total_quiz_questions,
                "has_quizzes": total_quiz_questions > 0
            }
        }
        
        logger.info(f"Finalized course with {len(final_modules)} modules and {total_quiz_questions} quiz questions")
        
        # Build preview data for frontend
        preview_modules = []
        total_submodules = 0
        
        for module in final_modules:
            module_preview = {
                "title": module["title"],
                "submodule_count": len(module["submodules"]),
                "description": module["description"][:150] + "..." if len(module["description"]) > 150 else module["description"],
                "quiz_count": sum(1 for sub in module["submodules"] if sub.get("quiz_questions"))
            }
            preview_modules.append(module_preview)
            total_submodules += len(module["submodules"])
        
        preview_data = {
            "modules": preview_modules,
            "total_modules": len(final_modules),
            "total_submodules": total_submodules,
            "total_quiz_questions": total_quiz_questions
        }
        
        if progress_callback:
            await progress_callback(
                f"Learning path complete with {len(final_modules)} modules, {total_submodules} detailed submodules, and {total_quiz_questions} quiz questions",
                phase="final_assembly",
                phase_progress=1.0,
                overall_progress=1.0,
                preview_data=preview_data,
                action="completed"
            )
            
        return {"final_learning_path": final_learning_path, "steps": ["Finalized enhanced course"]}
    except Exception as e:
        logger.exception(f"Error finalizing course: {str(e)}")
        
        # Send error progress update
        if progress_callback:
            await progress_callback(
                f"Error finalizing course: {str(e)}",
                phase="final_assembly",
                phase_progress=0.5,
                overall_progress=0.97,
                action="error"
            )
            
        return {"final_learning_path": {"topic": state["user_topic"], "modules": [], "error": str(e)}, "steps": [f"Error: {str(e)}"]}

def check_submodule_batch_processing(state: LearningPathState) -> str:
    """
    Checks if all submodule batches have been processed and provides detailed progress.
    
    Args:
        state: The current LearningPathState.
        
    Returns:
        "all_batches_processed" if all batches are done, otherwise "continue_processing".
    """
    current_index = state.get("current_submodule_batch_index")
    batches = state.get("submodule_batches")
    
    if current_index is None or batches is None:
        logging.warning("Submodule batch processing state is not properly initialized")
        return "all_batches_processed"
    
    if current_index >= len(batches):
        # All batches processed, provide summary statistics
        total_processed = len(state.get("developed_submodules", []))
        total_batches = len(batches)
        
        # Get completed submodules with timing information
        submodules_in_process = state.get("submodules_in_process", {})
        successful_submodules = [v for k, v in submodules_in_process.items() 
                                if v.get("status") == "completed"]
        error_submodules = [v for k, v in submodules_in_process.items() 
                           if v.get("status") == "error"]
        
        # Calculate timing statistics if available
        timing_stats = "No timing data available"
        if successful_submodules and "processing_time" in successful_submodules[0]:
            total_times = [s["processing_time"]["total"] for s in successful_submodules 
                          if "processing_time" in s]
            if total_times:
                avg_time = sum(total_times) / len(total_times)
                min_time = min(total_times)
                max_time = max(total_times)
                timing_stats = f"Average: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s"
        
        # Log detailed completion information
        logger = logging.getLogger("learning_path.batch_processor")
        logger.info(f"All {total_batches} submodule batches processed successfully")
        logger.info(f"Completed {total_processed} submodules with {len(error_submodules)} errors")
        logger.info(f"Processing time statistics: {timing_stats}")
        
        # DO NOT create an asyncio task directly, as this might be called in a sync context
        # Just log the completion message
        logger.info(f"All {total_processed} submodules across {total_batches} batches completed")
        
        return "all_batches_processed"
    else:
        # Calculate progress percentage
        progress_pct = int((current_index / len(batches)) * 100)
        
        # Calculate submodules processed so far
        processed_count = 0
        total_count = 0
        submodules_in_process = state.get("submodules_in_process", {})
        for batch in batches[:current_index]:
            for module_id, sub_id in batch:
                total_count += 1
                key = f"{module_id}:{sub_id}"
                if key in submodules_in_process:
                    if submodules_in_process[key].get("status") in ["completed", "error"]:
                        processed_count += 1
        
        # Log progress information
        remaining = len(batches) - current_index
        logger = logging.getLogger("learning_path.batch_processor")
        logger.info(f"Continue processing: batch {current_index+1} of {len(batches)} ({progress_pct}% complete)")
        logger.info(f"Processed {processed_count}/{total_count} submodules so far, {remaining} batches remaining")
        
        # DO NOT create an asyncio task directly
        # Just log the progress without using a callback
        logger.info(f"Progress: {progress_pct}% - Processing batch {current_index+1} of {len(batches)}")
        
        return "continue_processing"

# --- New Functions for Module Planning Research ---

async def generate_module_specific_planning_queries(state: LearningPathState, module_id: int, module: EnhancedModule) -> List[SearchQuery]:
    """
    Generates search queries specifically for planning the structure of a given module.
    """
    logger = logging.getLogger("learning_path.submodule_planner")
    logger.info(f"Generating structural planning queries for module {module_id+1}: {module.title}")

    # Get providers and language settings
    from backend.utils.language_utils import get_full_language_name
    google_key_provider = state.get("google_key_provider")
    output_language_code = state.get('language', 'en')
    search_language_code = state.get('search_language', 'en')
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)

    # Prepare context
    user_topic = escape_curly_braces(state["user_topic"])
    # Extract module title/desc safely, using .get() if it might be a dict from basic modules
    module_title = escape_curly_braces(module.title if hasattr(module, 'title') else module.get('title', f'Module {module_id+1}'))
    module_description = escape_curly_braces(module.description if hasattr(module, 'description') else module.get('description', 'No description'))
    module_count = len(state.get("modules", [])) # Use initial basic modules for count

    learning_path_context = "\n".join([
        f"Module {i+1}: {escape_curly_braces(mod.title if hasattr(mod, 'title') else mod.get('title', f'Module {i+1}'))}\n{escape_curly_braces(mod.description if hasattr(mod, 'description') else mod.get('description', 'No description'))}"
        for i, mod in enumerate(state.get("modules", [])) # Use initial basic modules for context
    ])

    prompt = ChatPromptTemplate.from_template(MODULE_SUBMODULE_PLANNING_QUERY_GENERATION_PROMPT)

    try:
        result = await run_chain(prompt, lambda: get_llm(key_provider=google_key_provider, user=state.get('user')), search_queries_parser, {
            "module_title": module_title,
            "module_description": module_description,
            "module_order": module_id + 1,
            "module_count": module_count,
            "user_topic": user_topic,
            "learning_path_context": learning_path_context,
            "language": output_language,
            "search_language": search_language,
            "format_instructions": search_queries_parser.get_format_instructions()
        })
        search_queries = result.queries
        logger.info(f"Generated {len(search_queries)} planning queries for module {module_id+1}")
        return search_queries
    except Exception as e:
        logger.error(f"Error generating module planning queries for module {module_id+1}: {str(e)}")
        return [] # Return empty list on failure

async def regenerate_module_planning_query(
    state: LearningPathState,
    failed_query: SearchQuery, # Assuming regenerate_query_func in search_utils passes SearchQuery
    module_id: int,
    module: EnhancedModule
) -> Optional[SearchQuery]: # Return SearchQuery or None
    """
    Regenerates a search query for module structural planning after a "no results found" error.

    Uses an LLM to create an alternative search query when the original planning query fails.
    Provides context about the failed query and the module structure.

    Args:
        state: The current LearningPathState.
        failed_query: The SearchQuery object that failed.
        module_id: The index of the current module.
        module: The EnhancedModule object for context.

    Returns:
        A new SearchQuery object with keywords and rationale, or None if regeneration fails.
    """
    logger = logging.getLogger("learning_path.submodule_planner") # Use correct logger
    logger.info(f"Regenerating module planning query for module {module_id+1} after no results for: {failed_query.keywords}")

    # Get language information from state
    from backend.utils.language_utils import get_full_language_name
    output_language_code = state.get('language', 'en')
    search_language_code = state.get('search_language', 'en')
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)

    # Get Google key provider from state
    google_key_provider = state.get("google_key_provider")
    if not google_key_provider:
        logger.warning("Google key provider not found in state for module planning query regeneration")
        # Decide if we should return None or raise an error, returning None for now
        return None

    # Build context information
    module_title = escape_curly_braces(module.title)
    module_description = escape_curly_braces(module.description)
    user_topic = escape_curly_braces(state.get("user_topic", "the user's topic"))

    # Construct a basic module context string
    module_context = f"""
Topic: {user_topic}
Module {module_id + 1}: {module_title}
Module Description: {module_description}
Objective: Regenerate a search query suitable for finding curriculum examples or structural guides for this specific module.
    """

    # Define the prompt text inline, asking for JSON output with keywords and rationale
    prompt_text = """
# MODULE PLANNING SEARCH QUERY RETRY SPECIALIST

The following search query returned NO RESULTS when searching for curriculum structures or syllabus examples for a course module:

FAILED QUERY: {failed_query}

## MODULE CONTEXT
{module_context}

I need you to generate a DIFFERENT search query that is more likely to find relevant structural information (like syllabus examples, curriculum outlines, typical topic progressions) for this specific module.

## ANALYSIS OF FAILED QUERY
Briefly analyze why the previous query might have failed (e.g., too specific, too niche, awkward phrasing for educational content search).

## NEW QUERY REQUIREMENTS
Create ONE alternative search query that:
1. Is broad enough to find syllabus/curriculum examples but specific enough to the module topic.
2. Uses terminology common in educational or curriculum planning contexts.
3. Avoids excessive quotes or overly complex structure.
4. Focuses on finding *structural* information, not just general topic info.

## LANGUAGE INSTRUCTIONS
- Generate your analysis and response in {output_language}.
- For the search query keywords, use {search_language} to maximize finding high-quality information.

Your response MUST be a JSON object containing only the 'keywords' (the new search query string) and 'rationale' (your brief analysis and justification for the new query).

{format_instructions}
"""

    # Set up the Pydantic parser for the SearchQuery model
    parser = PydanticOutputParser(pydantic_object=SearchQuery)

    prompt = ChatPromptTemplate.from_template(prompt_text)
    # Get the LLM instance via the provider
    llm = await get_llm(key_provider=google_key_provider, user=state.get('user')) # Assuming get_llm returns a compatible LLM instance

    # Construct the chain
    chain = prompt | llm | parser

    try:
        # Invoke the chain - run_chain might not be needed if using LCEL directly
        regenerated_query_object = await chain.ainvoke({ # Use ainovke for async
            "failed_query": failed_query.keywords,
            "module_context": module_context,
            "output_language": output_language,
            "search_language": search_language,
            "format_instructions": parser.get_format_instructions(),
        })

        if regenerated_query_object and isinstance(regenerated_query_object, SearchQuery):
            logger.info(f"Successfully regenerated module planning query: Keywords='{regenerated_query_object.keywords}', Rationale='{regenerated_query_object.rationale}'")
            # Return the validated SearchQuery object directly
            return regenerated_query_object
        else:
            logger.warning("Query regeneration did not return a valid SearchQuery object.")
            return None # Return None if parsing failed or object is not as expected
    except Exception as e:
        # Catch potential exceptions during LLM call or parsing
        logger.exception(f"Error regenerating module planning query: {str(e)}")
        return None

async def execute_module_specific_planning_searches(
    state: LearningPathState,
    module_id: int,
    module: EnhancedModule,
    planning_queries: List[SearchQuery]
) -> List[SearchServiceResult]:
    """Executes web searches for module structural planning queries using Brave+Scrape.""" # Updated docstring
    logger = logging.getLogger("learning_path.submodule_planner") # Define logger
    logger.info(f"Executing web searches for module planning: {module.title}") # Use logger
    
    if not planning_queries:
        logger.warning(f"No planning queries provided for module {module.title}") # Use logger
        return []
    
    brave_key_provider = state.get("brave_key_provider") # Renamed tavily_key_provider
    if not brave_key_provider:
        module_title_safe = escape_curly_braces(module.title)
        logger.error(f"Brave Search key provider not found for module {module_id+1} ({module_title_safe}) planning search.") # Use logger, updated message
        # Create error results for each query
        return [SearchServiceResult(query=q.keywords, search_provider_error="Missing Brave Key Provider") for q in planning_queries]
    
    max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS", 5))
    scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))
    
    results = []
    sem = asyncio.Semaphore(3) # Limit concurrent searches
    
    async def bounded_search_with_planning_retry(query_obj: SearchQuery):
        async with sem:
            provider = brave_key_provider.set_operation("module_planning_search") # Renamed tavily_key_provider
            # Use retry function, passing the correct key provider
            return await execute_search_with_llm_retry(
                state=state,
                initial_query=query_obj,
                regenerate_query_func=regenerate_module_planning_query, 
                search_provider_key_provider=provider, # Corrected parameter name
                search_config={
                    "max_results": max_results_per_query,
                    "scrape_timeout": scrape_timeout
                },
                regenerate_args={
                    "module_id": module_id,
                    "module": module
                }
            )
            
    try:
        tasks = [bounded_search_with_planning_retry(q) for q in planning_queries]
        results_or_excs = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, res_or_exc in enumerate(results_or_excs):
            if isinstance(res_or_exc, Exception):
                query_keywords = planning_queries[i].keywords
                logger.error(f"Planning search failed for query '{query_keywords}': {str(res_or_exc)}") # Use logger
                processed_results.append(SearchServiceResult(
                    query=query_keywords,
                    search_provider_error=f"Search task error: {str(res_or_exc)}"
                ))
            elif isinstance(res_or_exc, SearchServiceResult):
                 processed_results.append(res_or_exc)
                 if res_or_exc.search_provider_error:
                     logger.warning(f"Search provider error for planning query '{res_or_exc.query}': {res_or_exc.search_provider_error}") # Use logger
            else:
                 # Handle unexpected return type
                 query_keywords = planning_queries[i].keywords
                 logger.error(f"Unexpected result type for planning query '{query_keywords}': {type(res_or_exc)}") # Use logger
                 processed_results.append(SearchServiceResult(
                     query=query_keywords,
                     search_provider_error=f"Unexpected result type: {type(res_or_exc).__name__}"
                 ))
                 
        return processed_results
        
    except Exception as e:
        logger.exception(f"Error executing planning searches for module {module.title}: {str(e)}") # Use logger
        return [SearchServiceResult(
            query=f"Error: {str(e)}",
            search_provider_error=f"Failed to execute planning searches: {str(e)}"
        )]

# --- End New Functions ---


async def plan_submodules(state: LearningPathState) -> Dict[str, Any]:
    """
    Breaks down each module into 3-5 detailed submodules using an LLM chain.
    Performs structural research for each module before planning.
    Processes modules in parallel based on the parallel_count configuration.

    Args:
        state: The current LearningPathState containing basic modules.

    Returns:
        A dictionary with enhanced modules (each including planned submodules) and a list of steps.
    """
    logging.info("Planning submodules for each module in parallel with structural research") # Updated log message
    # Get basic modules list from the state (generated by create_learning_path)
    basic_modules = state.get("modules")
    if not basic_modules:
        logging.warning("No basic modules available from create_learning_path")
        return {"enhanced_modules": [], "steps": ["No basic modules available"]}

    # Get parallelism configuration - use the parallel_count from the user settings
    parallel_count = state.get("parallel_count", 2)
    logging.info(f"Planning submodules with parallelism of {parallel_count}")

    progress_callback = state.get("progress_callback")
    if progress_callback:
        # Enhanced progress update with phase information
        await progress_callback(
            f"Planning submodules for {len(basic_modules)} modules (with research) using parallelism={parallel_count}...", # Updated message
            phase="submodule_planning",
            phase_progress=0.0,
            overall_progress=0.55, # Keep estimate
            action="started"
        )

    # Create semaphore to control concurrency based on parallel_count
    sem = asyncio.Semaphore(parallel_count)

    # NEW HELPER: Calls the wrapper function that includes research
    async def plan_and_research_module_submodules_bounded(idx, module):
        async with sem: # Limits concurrency based on parallel_count
             return await plan_and_research_module_submodules(state, idx, module)

    tasks = [plan_and_research_module_submodules_bounded(idx, module) # NEW TASK LIST
             for idx, module in enumerate(basic_modules)] # Iterate over basic_modules

    enhanced_modules_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results and handle any exceptions
    processed_modules = []
    # IMPORTANT: Ensure EnhancedModule is available from top-level import
    # No need for local imports here anymore.
    for idx, result in enumerate(enhanced_modules_results):
        if isinstance(result, Exception):
            module_title = basic_modules[idx].title if hasattr(basic_modules[idx], 'title') else basic_modules[idx].get('title', f'Module {idx+1}')
            module_desc = basic_modules[idx].description if hasattr(basic_modules[idx], 'description') else basic_modules[idx].get('description', 'No description')
            logging.error(f"Error processing module {idx+1} ('{module_title}'): {str(result)}")
            # Create a fallback module with no submodules using the top-level imported EnhancedModule
            # from backend.models.models import EnhancedModule # REMOVED
            processed_modules.append(EnhancedModule(
                title=module_title,
                description=module_desc,
                submodules=[]
            ))
        elif isinstance(result, EnhancedModule): # Check if the result is the expected type
            processed_modules.append(result)
        else:
            # Handle unexpected result type
            module_title = basic_modules[idx].title if hasattr(basic_modules[idx], 'title') else basic_modules[idx].get('title', f'Module {idx+1}')
            module_desc = basic_modules[idx].description if hasattr(basic_modules[idx], 'description') else basic_modules[idx].get('description', 'No description')
            logging.error(f"Unexpected result type for module {idx+1} ('{module_title}'): {type(result)}")
            # Create fallback using top-level imported EnhancedModule
            # from backend.models.models import EnhancedModule # REMOVED
            processed_modules.append(EnhancedModule(
                title=module_title,
                description=module_desc,
                submodules=[]
            ))

    # Create preview data for frontend display
    preview_modules = []
    total_submodules = 0

    for module in processed_modules:
        # Ensure module is EnhancedModule before accessing attributes
        if isinstance(module, EnhancedModule):
            submodule_previews = []
            # Check if submodules exist and is iterable
            if hasattr(module, 'submodules') and module.submodules:
                for submodule in module.submodules:
                     # Ensure submodule has title and description
                     sub_title = getattr(submodule, 'title', 'Untitled Submodule')
                     sub_desc = getattr(submodule, 'description', '')
                     submodule_previews.append({
                         "title": sub_title,
                         "description": sub_desc[:100] + "..." if len(sub_desc) > 100 else sub_desc
                     })
                     total_submodules += 1

            preview_modules.append({
                "title": getattr(module, 'title', 'Untitled Module'),
                "submodules": submodule_previews
            })
        else:
             # Handle case where module is not EnhancedModule (e.g., error fallback)
             preview_modules.append({
                  "title": getattr(module, 'title', 'Error Processing Module'),
                  "submodules": []
             })

    if progress_callback:
        await progress_callback(
            f"Planned {total_submodules} submodules across {len(processed_modules)} modules (with research)", # Updated message
            phase="submodule_planning",
            phase_progress=1.0,
            overall_progress=0.6, # Keep estimate
            preview_data={"type": "all_submodules_planned", "data": {"modules": preview_modules, "total_submodules_planned": total_submodules}}, # Enhanced preview_data
            action="completed"
        )

    return {
        "enhanced_modules": processed_modules,
        "steps": state.get("steps", []) + [f"Planned submodules for {len(processed_modules)} modules with structural research using {parallel_count} parallel processes"] # Updated step description
    }

async def plan_module_submodules(
    state: LearningPathState,
    idx: int,
    module, # Keep type Any for now, as it comes from basic modules list initially
    planning_search_context: Optional[str] = None # Add new optional argument
) -> EnhancedModule: # Return type should be EnhancedModule
    """
    Plans submodules for a specific module, potentially using planning search results.
    
    Args:
        state: The current state.
        idx: Index of the module.
        module: The module to process.
        planning_search_context: Optional string containing context from planning searches.
        
    Returns:
        Enhanced module with planned submodules.
    """
    logging.info(f"Planning submodules for module {idx+1}: {module.title}")
    
    # Get progress callback
    progress_callback = state.get("progress_callback")
    
    # Send module-specific progress update
    if progress_callback:
        # Calculate overall progress based on module index
        total_modules = len(state.get("modules", []))
        module_progress = (idx + 0.2) / max(1, total_modules)
        # submodule planning (now including planning search) is 15% of overall (55% to 70%)
        overall_progress = 0.55 + (module_progress * 0.15) 
        
        await progress_callback(
            f"Planning submodules for module {idx+1}: {module.title}",
            phase="submodule_planning",
            phase_progress=module_progress,
            overall_progress=overall_progress,
            preview_data={"current_module": {"title": module.title, "index": idx}},
            action="processing"
        )
        
    # Get language from state
    from backend.utils.language_utils import get_full_language_name
    output_language_code = state.get('language', 'en')
    output_language = get_full_language_name(output_language_code)
    
    # Prepare context
    learning_path_context = "\n".join([f"Module {i+1}: {m.title}\n{m.description}"
                                       for i, m in enumerate(state["modules"])])
    
    # Add planning context if available
    planning_context_str = planning_search_context or "(No structural research context available)"

    # Check if a specific number of submodules was requested
    submodule_count_instruction = ""
    if state.get("desired_submodule_count"):
        submodule_count_instruction = f"IMPORTANT: Create EXACTLY {state['desired_submodule_count']} submodules for this module. Not more, not less."
    
    # Modify the prompt to include submodule count and planning context
    base_prompt = SUBMODULE_PLANNING_PROMPT
    prompt_params = {
        "user_topic": escape_curly_braces(state["user_topic"]),
        "module_title": escape_curly_braces(module.title),
        "module_description": escape_curly_braces(module.description),
        "learning_path_context": learning_path_context,
        "language": output_language,
        "planning_search_context": escape_curly_braces(planning_context_str),
        "format_instructions": submodule_parser.get_format_instructions() # Ensure format instructions are passed
    }
    
    # Insert the submodule count instruction if specified
    if submodule_count_instruction:
        base_prompt = base_prompt.replace(
            "## INSTRUCTIONS & REQUIREMENTS",
            f"## INSTRUCTIONS & REQUIREMENTS\n\n{submodule_count_instruction}"
        )

    prompt = ChatPromptTemplate.from_template(base_prompt)

    try:
        result = await run_chain(prompt, lambda: get_llm_with_search(key_provider=state.get("google_key_provider"), user=state.get('user')), submodule_parser, prompt_params)
        submodules = result.submodules
        
        # Validate and adjust submodule count if necessary
        desired_count = state.get("desired_submodule_count")
        if desired_count and len(submodules) != desired_count:
            logging.warning(f"Requested {desired_count} submodules but got {len(submodules)} for module {idx+1}: '{module.title}'. Adjusting...")
            if len(submodules) > desired_count:
                submodules = submodules[:desired_count]
            else:
                # If too few, log it, but proceed with what we have.
                # Trying to regenerate might be complex and slow down the process.
                logging.warning(f"Proceeding with {len(submodules)} submodules for '{module.title}' despite requesting {desired_count}.")

        # Set order for each submodule
        for i, sub in enumerate(submodules):
            sub.order = i + 1

        # Create the enhanced module
        try:
            # If 'module' is already an EnhancedModule, copy it
            enhanced_module = module.model_copy(update={"submodules": submodules})
        except AttributeError:
            # If 'module' is likely a basic Module (e.g., from initial state)
            from backend.models.models import EnhancedModule
            enhanced_module = EnhancedModule(
                title=module.title,
                description=module.description,
                submodules=submodules
            )
            
        logging.info(f"Planned {len(submodules)} submodules for module {idx+1}")
        
        # Send progress update for completed module submodule planning
        if progress_callback:
            submodule_previews = []
            for submodule_idx, submodule in enumerate(submodules): # Added submodule_idx
                submodule_previews.append({
                    "id": submodule_idx, # Added id for keying
                    "title": submodule.title,
                    "order": submodule_idx, # Added order
                    "description_preview": submodule.description[:100] + "..." if len(submodule.description) > 100 else submodule.description,
                    "status": "planned" # Initial status
                })
                
            # Calculate slightly more progress
            module_progress = (idx + 1) / max(1, total_modules)
            overall_progress = 0.55 + (module_progress * 0.05)
            
            await progress_callback(
                f"Planned {len(submodules)} submodules for module {idx+1}: {module.title}",
                phase="submodule_planning", 
                phase_progress=module_progress,
                overall_progress=overall_progress,
                preview_data={
                    "type": "module_submodules_planned", # Specific type
                    "data": { # Wrapped in data
                        "module_id": idx, # Identify parent module
                        "module_title": module.title, 
                        "submodules": submodule_previews
                    }
                },
                action="processing" # This is still part of an ongoing process
            )
        
        return enhanced_module

    except Exception as e:
        logging.exception(f"Error planning submodules for module {idx+1}: {str(e)}")
        if progress_callback:
             # Use the earlier calculated progress for the error update
             await progress_callback(
                 f"Error planning submodules for module {idx+1}: {str(e)}",
                 phase="submodule_planning",
                 phase_progress=module_progress, 
                 overall_progress=overall_progress,
                 action="error"
             )
        raise # Propagate the exception

async def plan_and_research_module_submodules(state: LearningPathState, module_id: int, module) -> EnhancedModule:
    """Combines planning search and submodule planning for a single module."""
    logger = logging.getLogger("learning_path.planner")
    logger.info(f"Starting combined planning and research for module {module_id+1}: {module.title}")
    
    # 1. Generate planning queries
    planning_queries = await generate_module_specific_planning_queries(state, module_id, module)
    
    # 2. Execute planning searches
    planning_search_results = await execute_module_specific_planning_searches(state, module_id, module, planning_queries)
    
    # 3. Format planning search context
    planning_context_parts = []
    MAX_CONTEXT_CHARS = 5000 # Limit total context size
    current_chars = 0
    
    for report in planning_search_results:
        query = escape_curly_braces(report.query)
        planning_context_parts.append(f"\n## Research for Planning Query: \"{query}\"\n")
        results_included = 0
        for res in report.results:
            if current_chars >= MAX_CONTEXT_CHARS:
                 planning_context_parts.append("... (Context truncated due to length)")
                 break
            
            title = escape_curly_braces(res.title or 'N/A')
            url = res.url
            planning_context_parts.append(f"### Source: {url} (Title: {title})")
            
            content_snippet = ""
            if res.scraped_content:
                content_snippet = f"Scraped Content Snippet:\n{escape_curly_braces(res.scraped_content)[:1000]}" # Limit snippet length
            elif res.search_snippet: # Fallback # Renamed tavily_snippet
                error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                content_snippet = f"Search Snippet:{error_info}\n{escape_curly_braces(res.search_snippet)[:1000]}" # Renamed tavily_snippet
            else:
                error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                content_snippet = f"Content: Not available.{error_info}"
                
            planning_context_parts.append(content_snippet)
            current_chars += len(content_snippet)
            results_included += 1
            planning_context_parts.append("---")
        
        if results_included == 0:
             planning_context_parts.append("(No usable content found for this planning query)")
             
        if current_chars >= MAX_CONTEXT_CHARS:
            break
            
    planning_search_context = "\n".join(planning_context_parts)

    # 4. Plan submodules using the context
    enhanced_module = await plan_module_submodules(state, module_id, module, planning_search_context)

    return enhanced_module

# =========================================================================
# Submodule Research Evaluation Loop (Google Style)
# =========================================================================

async def evaluate_submodule_research_sufficiency(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    search_results: List[SearchServiceResult],
) -> ResearchEvaluation:
    """Evaluate if gathered research is sufficient to write the submodule."""

    from backend.utils.language_utils import get_full_language_name
    from backend.prompts.learning_path_prompts import SUBMODULE_RESEARCH_EVALUATION_PROMPT
    from backend.parsers.parsers import research_evaluation_parser
    logger = logging.getLogger("learning_path.submodule_research_eval")

    search_summary = _build_enhanced_search_context(search_results)
    output_language = get_full_language_name(state.get("language", "en"))

    prompt = ChatPromptTemplate.from_template(SUBMODULE_RESEARCH_EVALUATION_PROMPT)

    result = await run_chain(
        prompt,
        lambda: get_llm_for_evaluation(key_provider=state.get("google_key_provider"), user=state.get("user")),
        research_evaluation_parser,
        {
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "submodule_title": submodule.title,
            "submodule_description": submodule.description,
            "language": output_language,
            "search_results_summary": search_summary,
            "format_instructions": research_evaluation_parser.get_format_instructions(),
        },
    )

    logger.info(
        f"Submodule research evaluation {module_id+1}.{sub_id+1}: sufficient={result.is_sufficient}, confidence={result.confidence_score:.2f}"
    )
    return result


async def generate_submodule_refinement_queries(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    knowledge_gaps: List[str],
    existing_queries: List[SearchQuery],
) -> List[SearchQuery]:
    """Generate follow-up queries to fill knowledge gaps."""

    from backend.utils.language_utils import get_full_language_name
    from backend.prompts.learning_path_prompts import SUBMODULE_REFINEMENT_QUERY_GENERATION_PROMPT
    from backend.parsers.parsers import refinement_query_parser

    output_language = get_full_language_name(state.get("language", "en"))
    search_language = get_full_language_name(state.get("search_language", "en"))

    prompt = ChatPromptTemplate.from_template(SUBMODULE_REFINEMENT_QUERY_GENERATION_PROMPT)

    result = await run_chain(
        prompt,
        lambda: get_llm_for_evaluation(key_provider=state.get("google_key_provider"), user=state.get("user")),
        refinement_query_parser,
        {
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "submodule_title": submodule.title,
            "submodule_description": submodule.description,
            "knowledge_gaps": "\n".join([f"- {gap}" for gap in knowledge_gaps]),
            "existing_queries": "\n".join([f"- {q.keywords}" for q in existing_queries]),
            "language": output_language,
            "search_language": search_language,
            "format_instructions": refinement_query_parser.get_format_instructions(),
        },
    )

    return result.queries


async def gather_research_until_sufficient(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    initial_queries: List[SearchQuery],
    initial_results: List[SearchServiceResult],
    progress_callback=None,
) -> Tuple[List[SearchQuery], List[SearchServiceResult]]:
    """Iteratively gather research until deemed sufficient."""

    local_queries = list(initial_queries)
    local_results = list(initial_results)
    loop_count = 0
    max_loops = 2

    while loop_count < max_loops:
        loop_count += 1

        if progress_callback:
            await progress_callback(
                f"Evaluating research sufficiency for {module.title} > {submodule.title} (Loop {loop_count})",
                phase="submodule_research",
                phase_progress=0.9,
                overall_progress=0.65,
                action="processing",
            )

        evaluation = await evaluate_submodule_research_sufficiency(
            state, module_id, sub_id, module, submodule, local_results
        )

        if evaluation.is_sufficient:
            break

        follow_up = await generate_submodule_refinement_queries(
            state,
            module_id,
            sub_id,
            module,
            submodule,
            evaluation.knowledge_gaps,
            local_queries,
        )

        if not follow_up:
            break

        new_results = await execute_submodule_specific_searches(
            state, module_id, sub_id, module, submodule, follow_up
        )

        local_queries.extend(follow_up)
        local_results.extend(new_results)

    return local_queries, local_results

# =========================================================================
# Content Refinement Loop Functions (Following Google Pattern)
# =========================================================================

async def develop_submodule_content_with_refinement_loop(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    sub_queries: List[SearchQuery],
    sub_search_results: List[SearchServiceResult],
    progress_callback = None
) -> str:
    """
    Develops submodule content with refinement loop following Google pattern.
    
    Flow: develop_content → evaluate_content → check_adequacy → {finalize | generate_refinement_queries → execute_refinement_searches → enhance_content → loop}
    """
    logger = logging.getLogger("learning_path.content_refinement")
    logger.info(f"Starting content development with refinement loop for submodule {module_id+1}.{sub_id+1}: {submodule.title}")
    
    try:
        # Create local loop control state for this specific submodule
        # This prevents interference between parallel submodule processing
        local_loop_state = {
            "content_loop_count": 0,
            "max_content_loops": 2,  # Allow up to 2 refinement iterations
            "is_content_sufficient": False,
            "content_gaps": [],
            "content_confidence_score": 0.0,
            "content_refinement_queries": [],
            "content_search_queries": list(sub_queries),  # Start with initial queries
            "content_search_results": list(sub_search_results)  # Start with initial results
        }
        
        # STEP 1: Initial content development
        submodule_content = await develop_submodule_specific_content(
            state, module_id, sub_id, module, submodule, sub_queries, sub_search_results
        )
        
        # Content refinement loop following Google pattern
        while local_loop_state["content_loop_count"] < local_loop_state["max_content_loops"]:
            current_loop = local_loop_state["content_loop_count"] + 1
            local_loop_state["content_loop_count"] = current_loop
            
            logger.info(f"Content refinement loop {current_loop}/{local_loop_state['max_content_loops']} for submodule {module_id+1}.{sub_id+1}")
            
            if progress_callback:
                await progress_callback(
                    f"Evaluating content quality for {module.title} > {submodule.title} (Loop {current_loop})",
                    phase="content_evaluation",
                    phase_progress=0.1,
                    overall_progress=0.65 + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                    preview_data={
                        "type": "submodule_status_update",
                        "data": {
                            "module_id": module_id,
                            "submodule_id": sub_id,
                            "status_detail": f"content_evaluation_loop_{current_loop}"
                        }
                    },
                    action="processing"
                )
            
            # STEP 2: Evaluate content sufficiency
            content_evaluation = await evaluate_content_sufficiency(
                state, module_id, sub_id, module, submodule, submodule_content
            )
            
            # Update local state with evaluation results
            local_loop_state["is_content_sufficient"] = content_evaluation.is_sufficient
            local_loop_state["content_gaps"] = content_evaluation.content_gaps
            local_loop_state["content_confidence_score"] = content_evaluation.confidence_score
            
            # STEP 3: Check if content is sufficient using local state
            if check_content_adequacy_local(local_loop_state, content_evaluation):
                logger.info(f"Content deemed sufficient for submodule {module_id+1}.{sub_id+1} after {current_loop} loops")
                break
            
            # STEP 4: Generate refinement queries for content improvement
            if progress_callback:
                await progress_callback(
                    f"Generating content enhancement queries for {module.title} > {submodule.title}",
                    phase="content_refinement",
                    phase_progress=0.3,
                    overall_progress=0.66 + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                    action="processing"
                )
            
            content_refinement_queries = await generate_content_refinement_queries_local(
                state, module_id, sub_id, module, submodule, content_evaluation, submodule_content, local_loop_state
            )
            
            # STEP 5: Execute refinement searches with accumulation
            if progress_callback:
                await progress_callback(
                    f"Searching for content enhancement information for {module.title} > {submodule.title}",
                    phase="content_refinement",
                    phase_progress=0.5,
                    overall_progress=0.67 + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                    action="processing"
                )
            
            refinement_search_results = await execute_content_refinement_searches(
                state, module_id, sub_id, module, submodule, content_refinement_queries
            )
            
            # Add new queries and results to local accumulative state
            local_loop_state["content_search_queries"].extend(content_refinement_queries)
            local_loop_state["content_search_results"].extend(refinement_search_results)
            
            # STEP 6: Enhance content with new information
            if progress_callback:
                await progress_callback(
                    f"Enhancing content for {module.title} > {submodule.title}",
                    phase="content_enhancement",
                    phase_progress=0.7,
                    overall_progress=0.68 + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                    action="processing"
                )
            
            submodule_content = await develop_enhanced_content(
                state, module_id, sub_id, module, submodule, submodule_content, refinement_search_results
            )
        
        logger.info(f"Content development completed for submodule {module_id+1}.{sub_id+1} after {local_loop_state['content_loop_count']} loops")
        return submodule_content
        
    except Exception as e:
        logger.exception(f"Error in content refinement loop for submodule {module_id+1}.{sub_id+1}: {str(e)}")
        # Fallback to original content development
        logger.info(f"Falling back to original content development for submodule {module_id+1}.{sub_id+1}")
        return await develop_submodule_specific_content(
            state, module_id, sub_id, module, submodule, sub_queries, sub_search_results
        )

def check_content_adequacy_local(local_loop_state: Dict[str, Any], content_evaluation: Any) -> bool:
    """
    Determines whether content refinement should continue or finalize, using local state.
    This prevents interference between parallel submodule processing.
    """
    logger = logging.getLogger("learning_path.content_adequacy")
    
    # Extract evaluation results
    is_sufficient = content_evaluation.is_sufficient
    confidence_score = content_evaluation.confidence_score
    current_loop = local_loop_state["content_loop_count"]
    max_loops = local_loop_state["max_content_loops"]
    
    # Decision logic following Google pattern
    if is_sufficient and confidence_score >= 0.7:
        logger.info(f"Content is sufficient (confidence: {confidence_score:.2f}) - finalizing")
        return True
    elif current_loop >= max_loops:
        logger.info(f"Maximum content loops reached ({max_loops}) - finalizing with current content")
        return True
    else:
        logger.info(f"Content needs refinement (confidence: {confidence_score:.2f}, loop: {current_loop}/{max_loops}) - continuing")
        return False

async def generate_content_refinement_queries_local(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    content_evaluation: Any,
    current_content: str,
    local_loop_state: Dict[str, Any]
) -> List[SearchQuery]:
    """
    Generates targeted search queries to address specific content gaps and improvements.
    Uses local state to avoid interference between parallel submodules.
    """
    logger = logging.getLogger("learning_path.content_refinement_queries")
    logger.info(f"Generating content refinement queries for submodule {module_id+1}.{sub_id+1}: {submodule.title}")
    
    # Get key providers and language settings
    from backend.utils.language_utils import get_full_language_name
    google_key_provider = state.get("google_key_provider")
    output_language_code = state.get('language', 'en')
    search_language_code = state.get('search_language', 'en')
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)
    
    # Import necessary components
    from backend.prompts.learning_path_prompts import CONTENT_REFINEMENT_QUERY_GENERATION_PROMPT
    from backend.parsers.parsers import content_refinement_query_parser
    from backend.core.graph_nodes.helpers import escape_curly_braces, run_chain
    from langchain.prompts import ChatPromptTemplate
    
    # Prepare context with escaped content
    user_topic = escape_curly_braces(state["user_topic"])
    module_title = escape_curly_braces(module.title)
    submodule_title = escape_curly_braces(submodule.title)
    
    # Extract evaluation details
    content_gaps_text = "\n".join([f"- {gap}" for gap in content_evaluation.content_gaps])
    improvement_areas_text = "\n".join([f"- {area}" for area in content_evaluation.improvement_areas])
    
    # Summarize existing research using local state
    existing_queries = local_loop_state["content_search_queries"]
    existing_queries_text = "\n".join([f"- {query.keywords}" for query in existing_queries[-5:]])  # Last 5 queries
    
    current_loop = local_loop_state["content_loop_count"]
    max_loops = local_loop_state["max_content_loops"]
    
    prompt = ChatPromptTemplate.from_template(CONTENT_REFINEMENT_QUERY_GENERATION_PROMPT)
    
    try:
        refinement_result = await run_chain(prompt, lambda: get_llm_for_evaluation(key_provider=google_key_provider, user=state.get('user')), content_refinement_query_parser, {
            "user_topic": user_topic,
            "module_title": module_title,
            "submodule_title": submodule_title,
            "content_status": "insufficient" if not content_evaluation.is_sufficient else "needs_improvement",
            "current_loop": current_loop,
            "max_loops": max_loops,
            "content_gaps": content_gaps_text,
            "improvement_areas": improvement_areas_text,
            "depth_assessment": escape_curly_braces(content_evaluation.depth_assessment),
            "clarity_assessment": escape_curly_braces(content_evaluation.clarity_assessment),
            "quality_issues": escape_curly_braces(content_evaluation.rationale),
            "existing_queries": existing_queries_text,
            "current_research_summary": f"Content loop {current_loop} - targeting gaps in educational effectiveness",
            "search_language": search_language,
            "output_language": output_language,
            "format_instructions": content_refinement_query_parser.get_format_instructions()
        })
        
        # Store refinement queries in local state instead of global state
        local_loop_state["content_refinement_queries"] = refinement_result.queries
        
        logger.info(f"Generated {len(refinement_result.queries)} content refinement queries for submodule {module_id+1}.{sub_id+1}")
        
        return refinement_result.queries
        
    except Exception as e:
        logger.exception(f"Error generating content refinement queries for submodule {module_id+1}.{sub_id+1}: {str(e)}")
        # Return fallback queries
        from backend.models.models import SearchQuery
        fallback_queries = [
            SearchQuery(
                keywords=f"{submodule.title} detailed explanation examples",
                rationale="Fallback query for content enhancement due to query generation error"
            ),
            SearchQuery(
                keywords=f"{submodule.title} practical applications tutorial",
                rationale="Fallback query for practical examples due to query generation error"
            )
        ]
        return fallback_queries

async def execute_content_refinement_searches(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    refinement_queries: List[SearchQuery]
) -> List[SearchServiceResult]:
    """
    Executes content refinement searches with accumulation in state following Google pattern.
    """
    logger = logging.getLogger("learning_path.content_refinement_search")
    logger.info(f"Executing {len(refinement_queries)} content refinement searches for submodule {module_id+1}.{sub_id+1}")
    
    if not refinement_queries:
        logger.warning(f"No refinement queries provided for submodule {module_id+1}.{sub_id+1}")
        return []
    
    # Get search configuration
    brave_key_provider = state.get("brave_key_provider")
    if not brave_key_provider:
        raise ValueError(f"Brave Search key provider not found in state for content refinement")
    
    max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS", 3))  # Reduced for refinement
    scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))
    
    results = []
    
    # Import search utilities
    from backend.core.graph_nodes.search_utils import execute_search_with_llm_retry
    import asyncio
    
    # Create semaphore for controlled concurrency
    sem = asyncio.Semaphore(2)  # Reduced concurrency for refinement searches
    
    async def bounded_refinement_search(query_obj: SearchQuery):
        async with sem:
            provider = brave_key_provider.set_operation("content_refinement_search")
            
            return await execute_search_with_llm_retry(
                state=state,
                initial_query=query_obj,
                regenerate_query_func=regenerate_content_refinement_query,
                search_provider_key_provider=provider,
                search_config={
                    "max_results": max_results_per_query,
                    "scrape_timeout": scrape_timeout
                },
                regenerate_args={
                    "module_id": module_id,
                    "sub_id": sub_id,
                    "module": module,
                    "submodule": submodule
                }
            )
    
    try:
        tasks = [bounded_refinement_search(query) for query in refinement_queries]
        results_or_excs = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, res_or_exc in enumerate(results_or_excs):
            if isinstance(res_or_exc, Exception):
                logger.error(f"Content refinement search error for submodule {module_id+1}.{sub_id+1}: {str(res_or_exc)}")
                # Create error result
                from backend.models.models import SearchServiceResult
                error_result = SearchServiceResult(
                    query=refinement_queries[i].keywords,
                    search_provider_error=f"Content refinement search error: {str(res_or_exc)}"
                )
                results.append(error_result)
            else:
                results.append(res_or_exc)
        
        # NOTE: No longer adding to global state as we now use local state per submodule
        # This prevents interference between parallel submodule processing
        # Local state accumulation is handled in develop_submodule_content_with_refinement_loop
        
        logger.info(f"Completed {len(results)} content refinement searches for submodule {module_id+1}.{sub_id+1}")
        return results
        
    except Exception as e:
        logger.exception(f"Error executing content refinement searches for submodule {module_id+1}.{sub_id+1}: {str(e)}")
        from backend.models.models import SearchServiceResult
        return [SearchServiceResult(
            query=f"Error: {str(e)}",
            search_provider_error=f"Failed to execute content refinement searches: {str(e)}"
        )]

async def regenerate_content_refinement_query(
    state: LearningPathState,
    failed_query: SearchQuery,
    module_id: int = None,
    sub_id: int = None,
    module: EnhancedModule = None,
    submodule: Submodule = None
) -> Optional[SearchQuery]:
    """
    Regenerates a failed content refinement query with simpler terms.
    """
    logger = logging.getLogger("learning_path.content_refinement_retry")
    logger.info(f"Regenerating failed content refinement query: {failed_query.keywords}")
    
    try:
        # Get Google key provider for query regeneration
        google_key_provider = state.get("google_key_provider")
        
        # Import necessary components
        from backend.core.graph_nodes.helpers import escape_curly_braces, run_chain
        from langchain.prompts import ChatPromptTemplate
        
        # Create a simplified regeneration prompt
        regeneration_prompt = """
# CONTENT REFINEMENT QUERY REGENERATION

The following search query returned no results:
"{failed_query}"

Generate a SIMPLER, broader query for finding content enhancement information about: {submodule_title}

Requirements:
- Use fewer, more common keywords
- Remove technical jargon if present
- Make the query broader to ensure results
- Focus on educational/tutorial content
- Maximum 4-5 keywords

New Query: """
        
        prompt = ChatPromptTemplate.from_template(regeneration_prompt)
        
        # Simple string-based regeneration
        llm = get_llm_for_evaluation(key_provider=google_key_provider, user=state.get('user'))
        
        response = await llm.ainvoke(prompt.format(
            failed_query=failed_query.keywords,
            submodule_title=submodule.title if submodule else "educational content"
        ))
        
        # Extract the new query from response
        new_query_text = response.content.strip()
        if new_query_text.startswith("New Query:"):
            new_query_text = new_query_text.replace("New Query:", "").strip()
        
        from backend.models.models import SearchQuery
        new_query = SearchQuery(
            keywords=new_query_text,
            rationale=f"Regenerated simpler query for content refinement (original: {failed_query.keywords})"
        )
        
        logger.info(f"Regenerated content refinement query: {new_query.keywords}")
        return new_query
        
    except Exception as e:
        logger.exception(f"Error regenerating content refinement query: {str(e)}")
        return None

async def develop_enhanced_content(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    current_content: str,
    refinement_search_results: List[SearchServiceResult]
) -> str:
    """
    Enhances existing content with new information from refinement searches.
    This performs ENHANCEMENT rather than complete regeneration.
    """
    logger = logging.getLogger("learning_path.content_enhancer")
    logger.info(f"Enhancing content for submodule {module_id+1}.{sub_id+1}: {submodule.title}")
    
    # Get key providers and language settings
    from backend.utils.language_utils import get_full_language_name
    google_key_provider = state.get("google_key_provider")
    output_language_code = state.get('language', 'en')
    output_language = get_full_language_name(output_language_code)
    explanation_style = state.get('explanation_style', 'standard')
    
    # Import necessary components
    from backend.core.graph_nodes.helpers import escape_curly_braces, run_chain
    from langchain.prompts import ChatPromptTemplate
    
    # Prepare refinement search context
    refinement_context = ""
    for result in refinement_search_results:
        if result.search_provider_error:
            continue
        
        for item in result.results:
            refinement_context += f"Title: {item.title}\n"
            refinement_context += f"Content: {item.content[:500]}...\n"  # Limit content length
            refinement_context += f"URL: {item.url}\n\n"
    
    if not refinement_context.strip():
        logger.warning(f"No useful refinement information found for submodule {module_id+1}.{sub_id+1}, returning original content")
        return current_content
    
    # Content enhancement prompt
    enhancement_prompt = """# EDUCATIONAL CONTENT ENHANCEMENT SPECIALIST

Your task is to ENHANCE existing educational content by incorporating new information from refinement research.

## ENHANCEMENT CONTEXT
- Subject Topic: {user_topic}
- Module: {module_title}
- Submodule: {submodule_title}
- Target Style: {explanation_style}
- Language: {output_language}

## CURRENT CONTENT (TO BE ENHANCED)
{current_content}

## REFINEMENT INFORMATION (FOR ENHANCEMENT)
{refinement_context}

## ENHANCEMENT INSTRUCTIONS

### 1. PRESERVE STRUCTURE AND CORE CONTENT
- Keep the existing content structure and organization
- Preserve all correct information already present
- Maintain the original educational flow and progression

### 2. STRATEGIC ENHANCEMENT APPROACH
- **ENHANCE** rather than rewrite completely
- Add new information that fills gaps or improves explanations
- Integrate better examples, analogies, or practical applications
- Improve clarity where needed without losing technical accuracy

### 3. ENHANCEMENT PRIORITIES
- Add missing key concepts or details
- Improve explanations that were unclear or incomplete
- Insert better examples or real-world applications
- Enhance technical accuracy with updated information
- Add practical insights or methodologies

### 4. INTEGRATION GUIDELINES
- Seamlessly weave new information into existing content
- Ensure enhanced content flows naturally
- Maintain consistent tone and style throughout
- Preserve the educational objectives and learning outcomes

### 5. QUALITY ENHANCEMENT
- Improve content depth without overwhelming the reader
- Add clarifying details where concepts were too brief
- Include practical examples that illustrate key points
- Enhance pedagogical effectiveness for better learning

## CONTENT STYLE REQUIREMENTS
{style_description}

## OUTPUT REQUIREMENTS
Provide the ENHANCED content that:
- Incorporates the most valuable refinement information
- Maintains the original structure while improving quality
- Addresses content gaps identified in evaluation
- Remains focused on the submodule learning objectives
- Is more comprehensive, clear, and educationally effective than the original

## IMPORTANT: OUTPUT ONLY THE ENHANCED CONTENT
Do not include meta-commentary, explanations of changes, or section headers describing the enhancement process.
"""
    
    # Define style descriptions
    style_descriptions = {
        "standard": "",  # No specific style instructions for standard
        "simple": "Use simple vocabulary and sentence structure. Incorporate basic analogies if helpful. Prioritize clarity over technical precision.",
        "technical": "Use correct technical terms and formal language. Include specific details, mechanisms, and underlying principles.",
        "example": "Illustrate every key concept with concrete, practical examples. Include relevant code snippets or pseudocode where applicable.",
        "conceptual": "Emphasize core principles, relationships between ideas, and mental models. Focus on the 'why' behind concepts.",
        "grumpy_genius": "Adopt a comedic reluctant expert persona while providing clear explanations. Use phrases showing mild intellectual impatience but always follow with correct information."
    }
    
    style_description = style_descriptions.get(explanation_style, "")
    
    prompt = ChatPromptTemplate.from_template(enhancement_prompt)
    
    try:
        # Simple string output parser for content enhancement
        llm = get_llm_for_evaluation(key_provider=google_key_provider, user=state.get('user'))
        
        enhanced_content_response = await llm.ainvoke(prompt.format(
            user_topic=escape_curly_braces(state["user_topic"]),
            module_title=escape_curly_braces(module.title),
            submodule_title=escape_curly_braces(submodule.title),
            explanation_style=explanation_style,
            output_language=output_language,
            current_content=escape_curly_braces(current_content),
            refinement_context=escape_curly_braces(refinement_context),
            style_description=style_description
        ))
        
        enhanced_content = enhanced_content_response.content.strip()
        
        # Ensure we have valid enhanced content
        if len(enhanced_content) < len(current_content) * 0.8:  # Enhanced content should not be significantly shorter
            logger.warning(f"Enhanced content seems too short for submodule {module_id+1}.{sub_id+1}, using original content")
            return current_content
        
        logger.info(f"Content successfully enhanced for submodule {module_id+1}.{sub_id+1} (original: {len(current_content)} chars, enhanced: {len(enhanced_content)} chars)")
        return enhanced_content
        
    except Exception as e:
        logger.exception(f"Error enhancing content for submodule {module_id+1}.{sub_id+1}: {str(e)}")
        logger.info(f"Returning original content due to enhancement error")
        return current_content

async def evaluate_content_sufficiency(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    submodule_content: str
) -> Any:  # Returns ContentEvaluation
    """
    Evaluates content quality across multiple dimensions following Google pattern.
    Note: This function no longer modifies the global state to prevent interference 
    between parallel submodule processing.
    """
    logger = logging.getLogger("learning_path.content_evaluator")
    logger.info(f"Evaluating content sufficiency for submodule {module_id+1}.{sub_id+1}: {submodule.title}")
    
    # Get key providers and language settings
    from backend.utils.language_utils import get_full_language_name
    google_key_provider = state.get("google_key_provider")
    output_language_code = state.get('language', 'en')
    output_language = get_full_language_name(output_language_code)
    explanation_style = state.get('explanation_style', 'standard')
    
    # Import necessary components
    from backend.prompts.learning_path_prompts import CONTENT_EVALUATION_PROMPT
    from backend.parsers.parsers import content_evaluation_parser
    from backend.core.graph_nodes.helpers import escape_curly_braces, run_chain
    from langchain.prompts import ChatPromptTemplate
    
    # Prepare context with escaped content
    user_topic = escape_curly_braces(state["user_topic"])
    module_title = escape_curly_braces(module.title)
    submodule_title = escape_curly_braces(submodule.title)
    submodule_description = escape_curly_braces(submodule.description)
    depth_level = escape_curly_braces(submodule.depth_level)
    content_to_evaluate = escape_curly_braces(submodule_content)
    
    prompt = ChatPromptTemplate.from_template(CONTENT_EVALUATION_PROMPT)
    
    try:
        evaluation_result = await run_chain(prompt, lambda: get_llm_for_evaluation(key_provider=google_key_provider, user=state.get('user')), content_evaluation_parser, {
            "user_topic": user_topic,
            "module_title": module_title,
            "submodule_title": submodule_title,
            "submodule_description": submodule_description,
            "depth_level": depth_level,
            "explanation_style": explanation_style,
            "submodule_content": content_to_evaluate,
            "format_instructions": content_evaluation_parser.get_format_instructions()
        })
        
        # DO NOT update global state - let the calling function handle local state
        # This prevents interference between parallel submodule processing
        
        logger.info(f"Content evaluation completed for submodule {module_id+1}.{sub_id+1}: sufficient={evaluation_result.is_sufficient}, confidence={evaluation_result.confidence_score:.2f}")
        
        return evaluation_result
        
    except Exception as e:
        logger.exception(f"Error evaluating content for submodule {module_id+1}.{sub_id+1}: {str(e)}")
        # Return default insufficient evaluation to trigger refinement
        from backend.models.models import ContentEvaluation
        fallback_evaluation = ContentEvaluation(
            is_sufficient=False,
            content_gaps=["Content evaluation failed - requires refinement"],
            confidence_score=0.1,
            improvement_areas=["Overall content enhancement needed"],
            depth_assessment="Unable to assess depth due to evaluation error",
            clarity_assessment="Unable to assess clarity due to evaluation error",
            rationale=f"Content evaluation failed with error: {str(e)}"
        )
        return fallback_evaluation

async def check_content_adequacy(state: LearningPathState, content_evaluation: Any) -> bool:
    """
    Legacy function maintained for compatibility.
    Note: This function should not be used with parallel processing as it uses global state.
    Use check_content_adequacy_local instead for parallel submodule processing.
    """
    logger = logging.getLogger("learning_path.content_adequacy")
    logger.warning("Using legacy check_content_adequacy function - consider using check_content_adequacy_local for parallel processing")
    
    # Extract evaluation results
    is_sufficient = content_evaluation.is_sufficient
    confidence_score = content_evaluation.confidence_score
    current_loop = state.get("content_loop_count", 0)
    max_loops = state.get("max_content_loops", 2)
    
    # Decision logic following Google pattern
    if is_sufficient and confidence_score >= 0.7:
        logger.info(f"Content is sufficient (confidence: {confidence_score:.2f}) - finalizing")
        return True
    elif current_loop >= max_loops:
        logger.info(f"Maximum content loops reached ({max_loops}) - finalizing with current content")
        return True
    else:
        logger.info(f"Content needs refinement (confidence: {confidence_score:.2f}, loop: {current_loop}/{max_loops}) - continuing")
        return False

async def generate_content_refinement_queries(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    content_evaluation: Any,
    current_content: str
) -> List[SearchQuery]:
    """
    Legacy function maintained for compatibility.
    Note: This function should not be used with parallel processing as it uses global state.
    Use generate_content_refinement_queries_local instead for parallel submodule processing.
    """
    logger = logging.getLogger("learning_path.content_refinement_queries")
    logger.warning("Using legacy generate_content_refinement_queries function - consider using generate_content_refinement_queries_local for parallel processing")
    logger.info(f"Generating content refinement queries for submodule {module_id+1}.{sub_id+1}: {submodule.title}")
    
    # Get key providers and language settings
    from backend.utils.language_utils import get_full_language_name
    google_key_provider = state.get("google_key_provider")
    output_language_code = state.get('language', 'en')
    search_language_code = state.get('search_language', 'en')
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)
    
    # Import necessary components
    from backend.prompts.learning_path_prompts import CONTENT_REFINEMENT_QUERY_GENERATION_PROMPT
    from backend.parsers.parsers import content_refinement_query_parser
    from backend.core.graph_nodes.helpers import escape_curly_braces, run_chain
    from langchain.prompts import ChatPromptTemplate
    
    # Prepare context with escaped content
    user_topic = escape_curly_braces(state["user_topic"])
    module_title = escape_curly_braces(module.title)
    submodule_title = escape_curly_braces(submodule.title)
    
    # Extract evaluation details
    content_gaps_text = "\n".join([f"- {gap}" for gap in content_evaluation.content_gaps])
    improvement_areas_text = "\n".join([f"- {area}" for area in content_evaluation.improvement_areas])
    
    # Summarize existing research using global state (legacy behavior)
    existing_queries = state.get("content_search_queries", [])
    existing_queries_text = "\n".join([f"- {query.keywords}" for query in existing_queries[-5:]])  # Last 5 queries
    
    current_loop = state.get("content_loop_count", 0)
    max_loops = state.get("max_content_loops", 2)
    
    prompt = ChatPromptTemplate.from_template(CONTENT_REFINEMENT_QUERY_GENERATION_PROMPT)
    
    try:
        refinement_result = await run_chain(prompt, lambda: get_llm_for_evaluation(key_provider=google_key_provider, user=state.get('user')), content_refinement_query_parser, {
            "user_topic": user_topic,
            "module_title": module_title,
            "submodule_title": submodule_title,
            "content_status": "insufficient" if not content_evaluation.is_sufficient else "needs_improvement",
            "current_loop": current_loop,
            "max_loops": max_loops,
            "content_gaps": content_gaps_text,
            "improvement_areas": improvement_areas_text,
            "depth_assessment": escape_curly_braces(content_evaluation.depth_assessment),
            "clarity_assessment": escape_curly_braces(content_evaluation.clarity_assessment),
            "quality_issues": escape_curly_braces(content_evaluation.rationale),
            "existing_queries": existing_queries_text,
            "current_research_summary": f"Content loop {current_loop} - targeting gaps in educational effectiveness",
            "search_language": search_language,
            "output_language": output_language,
            "format_instructions": content_refinement_query_parser.get_format_instructions()
        })
        
        # Store refinement queries in global state (legacy behavior)
        state["content_refinement_queries"] = refinement_result.queries
        
        logger.info(f"Generated {len(refinement_result.queries)} content refinement queries for submodule {module_id+1}.{sub_id+1}")
        
        return refinement_result.queries
        
    except Exception as e:
        logger.exception(f"Error generating content refinement queries for submodule {module_id+1}.{sub_id+1}: {str(e)}")
        # Return fallback queries
        from backend.models.models import SearchQuery
        fallback_queries = [
            SearchQuery(
                keywords=f"{submodule.title} detailed explanation examples",
                rationale="Fallback query for content enhancement due to query generation error"
            ),
            SearchQuery(
                keywords=f"{submodule.title} practical applications tutorial",
                rationale="Fallback query for practical examples due to query generation error"
            )
        ]
        return fallback_queries

# =========================================================================
# Enhanced Content Development Helper Functions
# =========================================================================

def _build_learning_path_context(state: LearningPathState, current_module_id: int) -> str:
    """
    Builds comprehensive learning path context highlighting course structure and progression.
    """
    try:
        modules = state.get("enhanced_modules", [])
        if not modules:
            return "No course structure available."
        
        context_parts = ["# COMPLETE COURSE STRUCTURE\n"]
        
        for i, mod in enumerate(modules):
            is_current = i == current_module_id
            status_indicator = " **← CURRENT MODULE**" if is_current else ""
            
            mod_title = escape_curly_braces(getattr(mod, 'title', f'Module {i+1}'))
            mod_desc = escape_curly_braces(getattr(mod, 'description', 'No description'))
            
            context_parts.append(f"## Module {i+1}: {mod_title}{status_indicator}")
            context_parts.append(f"**Description**: {mod_desc}")
            
            # Add submodule preview if available
            if hasattr(mod, 'submodules') and mod.submodules:
                context_parts.append("**Submodules**:")
                for j, sub in enumerate(mod.submodules):
                    sub_title = escape_curly_braces(getattr(sub, 'title', f'Submodule {j+1}'))
                    context_parts.append(f"  {j+1}. {sub_title}")
            
            context_parts.append("")  # Add spacing
        
        return "\n".join(context_parts)
        
    except Exception as e:
        logging.error(f"Error building learning path context: {str(e)}")
        return f"Error building course context: {str(e)}"

def _build_module_context(module: EnhancedModule, current_sub_id: int) -> str:
    """
    Builds detailed module context showing submodule structure and relationships.
    """
    try:
        module_title = escape_curly_braces(getattr(module, 'title', 'Current Module'))
        module_desc = escape_curly_braces(getattr(module, 'description', 'No description'))
        
        context_parts = [
            f"# CURRENT MODULE DETAILS",
            f"**Title**: {module_title}",
            f"**Description**: {module_desc}",
            "",
            "## Module Submodules Structure:"
        ]
        
        if hasattr(module, 'submodules') and module.submodules:
            for i, sub in enumerate(module.submodules):
                is_current = i == current_sub_id
                status_indicator = " **← CURRENT SUBMODULE**" if is_current else ""
                
                sub_title = escape_curly_braces(getattr(sub, 'title', f'Submodule {i+1}'))
                sub_desc = escape_curly_braces(getattr(sub, 'description', 'No description'))
                
                context_parts.append(f"### {i+1}. {sub_title}{status_indicator}")
                context_parts.append(f"**Description**: {sub_desc}")
                
                # Add key components if available
                if hasattr(sub, 'key_components') and sub.key_components:
                    components = ', '.join([escape_curly_braces(comp) for comp in sub.key_components])
                    context_parts.append(f"**Key Components**: {components}")
                
                # Add learning objective if available
                if hasattr(sub, 'learning_objective'):
                    objective = escape_curly_braces(getattr(sub, 'learning_objective', ''))
                    if objective:
                        context_parts.append(f"**Learning Objective**: {objective}")
                
                context_parts.append("")  # Add spacing
        else:
            context_parts.append("No submodules defined for this module.")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        logging.error(f"Error building module context: {str(e)}")
        return f"Error building module context: {str(e)}"

def _build_adjacent_context(module: EnhancedModule, current_sub_id: int) -> str:
    """
    Builds context for adjacent submodules to show learning progression.
    """
    try:
        if not hasattr(module, 'submodules') or not module.submodules:
            return "No adjacent submodules available."
        
        context_parts = ["# LEARNING PROGRESSION CONTEXT\n"]
        
        # Previous submodule
        if current_sub_id > 0:
            prev_sub = module.submodules[current_sub_id - 1]
            prev_title = escape_curly_braces(getattr(prev_sub, 'title', f'Previous Submodule'))
            prev_desc = escape_curly_braces(getattr(prev_sub, 'description', 'No description'))
            
            context_parts.append(f"## Previous Submodule ({current_sub_id}): {prev_title}")
            context_parts.append(f"**Description**: {prev_desc}")
            
            # Add key concepts from previous submodule
            if hasattr(prev_sub, 'core_concept'):
                prev_concept = escape_curly_braces(getattr(prev_sub, 'core_concept', ''))
                if prev_concept:
                    context_parts.append(f"**Core Concept**: {prev_concept}")
            
            context_parts.append("*This provides the foundation for the current submodule.*")
            context_parts.append("")
        else:
            context_parts.append("## Previous Submodule: None (This is the first submodule)")
            context_parts.append("")
        
        # Next submodule
        if current_sub_id < len(module.submodules) - 1:
            next_sub = module.submodules[current_sub_id + 1]
            next_title = escape_curly_braces(getattr(next_sub, 'title', f'Next Submodule'))
            next_desc = escape_curly_braces(getattr(next_sub, 'description', 'No description'))
            
            context_parts.append(f"## Next Submodule ({current_sub_id + 2}): {next_title}")
            context_parts.append(f"**Description**: {next_desc}")
            
            # Add key concepts from next submodule
            if hasattr(next_sub, 'core_concept'):
                next_concept = escape_curly_braces(getattr(next_sub, 'core_concept', ''))
                if next_concept:
                    context_parts.append(f"**Core Concept**: {next_concept}")
            
            context_parts.append("*The current submodule should prepare learners for this next step.*")
        else:
            context_parts.append("## Next Submodule: None (This is the final submodule)")
            context_parts.append("*This submodule should provide comprehensive closure for the module.*")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        logging.error(f"Error building adjacent context: {str(e)}")
        return f"Error building adjacent context: {str(e)}"

def _build_enhanced_search_context(search_results: List[SearchServiceResult]) -> str:
    """
    Builds comprehensive, well-organized search context from research materials.
    Places resources at the end as requested by the user.
    """
    try:
        if not search_results:
            return "No research materials available for this submodule."
        
        context_parts = []
        total_sources = 0
        max_results_per_query = 4  # Increased for enhanced context
        
        for result_group in search_results:
            if result_group.search_provider_error:
                # Skip failed searches but log them
                logging.warning(f"Skipping failed search: {result_group.search_provider_error}")
                continue
            
            query = escape_curly_braces(result_group.query)
            context_parts.append(f"\n## Research Query: \"{query}\"")
            context_parts.append(f"*This search aimed to gather information relevant to the submodule development.*")
            context_parts.append("")
            
            valid_results = 0
            for i, result_item in enumerate(result_group.results):
                if valid_results >= max_results_per_query:
                    break
                
                # Check if we have usable content
                has_content = bool(result_item.scraped_content or result_item.search_snippet)
                if not has_content:
                    continue
                
                valid_results += 1
                total_sources += 1
                
                # Build source header
                title = escape_curly_braces(result_item.title or 'Untitled Source')
                url = result_item.url or 'No URL'
                
                context_parts.append(f"### Source {valid_results}: {title}")
                context_parts.append(f"**URL**: {url}")
                
                # Add content with preference for scraped content
                if result_item.scraped_content:
                    content = escape_curly_braces(result_item.scraped_content)
                    # Use enhanced length for comprehensive context
                    truncated_content = content[:MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT * 2]  # Double the usual limit
                    if len(content) > MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT * 2:
                        truncated_content += "\n\n*(Content truncated for brevity)*"
                    
                    context_parts.append(f"**Content Summary**:")
                    context_parts.append(truncated_content)
                
                elif result_item.search_snippet:
                    snippet = escape_curly_braces(result_item.search_snippet)
                    error_info = ""
                    if result_item.scrape_error:
                        error_info = f" *(Note: Full content scraping failed - {escape_curly_braces(result_item.scrape_error)})*"
                    
                    # Use enhanced length for search snippets too
                    truncated_snippet = snippet[:MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT]
                    if len(snippet) > MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT:
                        truncated_snippet += "\n\n*(Snippet truncated)*"
                    
                    context_parts.append(f"**Search Snippet**:{error_info}")
                    context_parts.append(truncated_snippet)
                
                context_parts.append("")  # Add spacing between sources
            
            if valid_results == 0:
                context_parts.append("*No usable content was found for this research query.*")
                context_parts.append("")
            else:
                context_parts.append(f"*Found {valid_results} relevant sources for this query.*")
                context_parts.append("")
        
        # Add summary header
        summary_header = [
            f"# COMPREHENSIVE RESEARCH MATERIALS",
            f"*The following {total_sources} sources provide research context and information to enhance submodule content development.*",
            ""
        ]
        
        return "\n".join(summary_header + context_parts)
        
    except Exception as e:
        logging.error(f"Error building enhanced search context: {str(e)}")
        return f"Error building research context: {str(e)}"
