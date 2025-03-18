import asyncio
import logging
from typing import Dict, Any, List, Tuple

from core.graph_nodes.initial_flow import execute_single_search
from models.models import SearchQuery, EnhancedModule, Submodule, SubmoduleContent, LearningPathState
from parsers.parsers import submodule_parser, module_queries_parser
from services.services import get_llm, get_search_tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import the extracted prompts
from prompts.learning_path_prompts import (
    SUBMODULE_PLANNING_PROMPT,
    SUBMODULE_QUERY_GENERATION_PROMPT,
    SUBMODULE_CONTENT_DEVELOPMENT_PROMPT
)
# Optional: Import the prompt registry for more advanced prompt management
# from prompts.prompt_registry import registry

from core.graph_nodes.helpers import run_chain, batch_items

async def plan_submodules(state: LearningPathState) -> Dict[str, Any]:
    """
    Breaks down each module into 3-5 detailed submodules using an LLM chain.
    
    Args:
        state: The current LearningPathState containing basic modules.
        
    Returns:
        A dictionary with enhanced modules (each including planned submodules) and a list of steps.
    """
    logging.info("Planning submodules for each module")
    if not state.get("modules"):
        logging.warning("No modules available")
        return {"enhanced_modules": [], "steps": ["No modules available"]}
    
    enhanced_modules = []
    for idx, module in enumerate(state["modules"]):
        logging.info(f"Planning submodules for module {idx+1}: {module.title}")
        learning_path_context = "\n".join([f"Module {i+1}: {mod.title}\n{mod.description}" for i, mod in enumerate(state["modules"])])
        
        # Check if a specific number of submodules was requested
        submodule_count_instruction = ""
        if state.get("desired_submodule_count"):
            submodule_count_instruction = f"IMPORTANT: Create EXACTLY {state['desired_submodule_count']} submodules for this module. Not more, not less."
        
        # Modify the prompt to include the submodule count instruction if specified
        base_prompt = SUBMODULE_PLANNING_PROMPT
        if submodule_count_instruction:
            # Insert the instruction before the format_instructions placeholder
            base_prompt = base_prompt.replace("{format_instructions}", f"{submodule_count_instruction}\n\n{{format_instructions}}")
        
        # Using the extracted prompt template instead of an inline string
        prompt = ChatPromptTemplate.from_template(base_prompt)
        try:
            result = await run_chain(prompt, lambda: get_llm(key_provider=state.get("google_key_provider")), submodule_parser, {
                "user_topic": state["user_topic"],
                "module_title": module.title,
                "module_description": module.description,
                "learning_path_context": learning_path_context,
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
            
            for i, sub in enumerate(submodules):
                sub.order = i + 1
            try:
                enhanced_module = module.model_copy(update={"submodules": submodules})
            except Exception:
                from models.models import EnhancedModule
                enhanced_module = EnhancedModule(
                    title=module.title,
                    description=module.description,
                    submodules=submodules
                )
            enhanced_modules.append(enhanced_module)
            logging.info(f"Planned {len(submodules)} submodules for module {idx+1}")
        except Exception as e:
            logging.error(f"Error planning submodules for module {idx+1}: {str(e)}")
            from models.models import EnhancedModule
            enhanced_module = EnhancedModule(
                title=module.title,
                description=module.description,
                submodules=[]
            )
            enhanced_modules.append(enhanced_module)
    if state.get("progress_callback"):
        total_submodules = sum(len(m.submodules) for m in enhanced_modules)
        await state["progress_callback"](f"Planned {total_submodules} submodules across {len(enhanced_modules)} modules")
    return {"enhanced_modules": enhanced_modules, "steps": [f"Planned submodules for {len(enhanced_modules)} modules"]}

async def initialize_submodule_processing(state: LearningPathState) -> Dict[str, Any]:
    """
    Initializes parallel processing for submodules by organizing them into batches.
    
    Args:
        state: The current LearningPathState with enhanced modules.
        
    Returns:
        A dictionary containing submodule batches, current batch index, and related tracking data.
    """
    logging.info("Initializing submodule parallel processing")
    enhanced_modules = state.get("enhanced_modules")
    if not enhanced_modules:
        logging.warning("No enhanced modules available")
        return {
            "submodule_batches": [],
            "current_submodule_batch_index": 0,
            "submodules_in_process": {},
            "developed_submodules": [],
            "steps": ["No enhanced modules available"]
        }
    submodule_parallel_count = state.get("submodule_parallel_count", 2)
    all_pairs = []
    for module_id, module in enumerate(enhanced_modules):
        if module.submodules:
            for sub_id in range(len(module.submodules)):
                all_pairs.append((module_id, sub_id))
    if not all_pairs:
        logging.warning("No valid submodules found")
        return {
            "submodule_batches": [],
            "current_submodule_batch_index": 0,
            "submodules_in_process": {},
            "developed_submodules": [],
            "steps": ["No valid submodules found"]
        }
    submodule_batches = batch_items(all_pairs, submodule_parallel_count)
    logging.info(f"Organized {len(all_pairs)} submodules into {len(submodule_batches)} batches")
    if state.get("progress_callback"):
        await state["progress_callback"](f"Organized {len(all_pairs)} submodules into {len(submodule_batches)} batches")
    return {
        "submodule_batches": submodule_batches,
        "current_submodule_batch_index": 0,
        "submodules_in_process": {},
        "developed_submodules": [],
        "steps": [f"Initialized submodule processing with batch size {submodule_parallel_count}"]
    }

async def process_submodule_batch(state: LearningPathState) -> Dict[str, Any]:
    """
    Processes the current batch of submodules concurrently.
    
    Args:
        state: The current LearningPathState containing submodule batches.
        
    Returns:
        A dictionary with updated submodule processing information and a list of steps.
    """
    logging.info("Processing a batch of submodules in parallel")
    sub_batches = state.get("submodule_batches") or []
    current_index = state.get("current_submodule_batch_index", 0)
    if current_index >= len(sub_batches):
        logging.info("All submodule batches processed")
        return {"steps": ["All submodule batches processed"]}
    current_batch = sub_batches[current_index]
    enhanced_modules = state.get("enhanced_modules", [])
    submodules_in_process = state.get("submodules_in_process", {})
    tasks = []
    task_to_submodule_map = []  # Track which task corresponds to which submodule
    for module_id, sub_id in current_batch:
        key = (module_id, sub_id)
        if key not in submodules_in_process:
            submodules_in_process[key] = {"status": "starting", "search_queries": None, "search_results": None, "content": None}
            if module_id < len(enhanced_modules) and sub_id < len(enhanced_modules[module_id].submodules):
                module = enhanced_modules[module_id]
                submodule = module.submodules[sub_id]
                task = process_single_submodule(state, module_id, sub_id, module, submodule)
                tasks.append(task)
                task_to_submodule_map.append(key)  # Record which submodule this task is for
            else:
                logging.warning(f"Invalid submodule indices: module {module_id}, submodule {sub_id}")
    if state.get("progress_callback"):
        await state["progress_callback"](f"Processing submodule batch {current_index+1} with {len(tasks)} tasks")
    if tasks:
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if i < len(task_to_submodule_map):
                    module_id, sub_id = task_to_submodule_map[i]
                    key = (module_id, sub_id)
                    if isinstance(result, Exception):
                        logging.error(f"Error in submodule {module_id}.{sub_id}: {str(result)}")
                        submodules_in_process[key]["status"] = "error"
                        submodules_in_process[key]["error"] = str(result)
                    else:
                        submodules_in_process[key] = result
            logging.info(f"Completed submodule batch {current_index+1}")
        except Exception as e:
            logging.error(f"Error in processing submodule batch: {str(e)}")
    next_index = current_index + 1
    developed_submodules = state.get("developed_submodules", [])
    for module_id, sub_id in current_batch:
        key = (module_id, sub_id)
        data = submodules_in_process.get(key, {})
        if data.get("status") == "completed" and module_id < len(enhanced_modules):
            module = enhanced_modules[module_id]
            if sub_id < len(module.submodules):
                developed_submodules.append(SubmoduleContent(
                    module_id=module_id,
                    submodule_id=sub_id,
                    title=module.submodules[sub_id].title,
                    description=module.submodules[sub_id].description,
                    search_queries=data.get("search_queries", []),
                    search_results=data.get("search_results", []),
                    content=data.get("content", "")
                ))
    if state.get("progress_callback"):
        await state["progress_callback"](f"Completed batch {current_index+1} of submodules")
    return {
        "submodules_in_process": submodules_in_process,
        "current_submodule_batch_index": next_index,
        "developed_submodules": developed_submodules,
        "steps": [f"Processed submodule batch {current_index+1}"]
    }

async def process_single_submodule(
    state: LearningPathState, 
    module_id: int, 
    sub_id: int, 
    module: EnhancedModule, 
    submodule: Submodule
) -> Dict[str, Any]:
    """
    Processes a single submodule from generating queries to developing content.
    
    Args:
        state: The current LearningPathState.
        module_id: Index of the parent module.
        sub_id: Index of the submodule.
        module: The EnhancedModule instance.
        submodule: The Submodule instance.
        
    Returns:
        A dictionary with the submodule processing result.
    """
    logger = logging.getLogger("learning_path.submodule_processor")
    logger.info(f"Processing submodule {sub_id+1} of module {module_id+1}: {submodule.title}")
    try:
        from config.log_config import log_debug_data
        submodule_search_queries = await generate_submodule_specific_queries(state, module_id, sub_id, module, submodule)
        logger.debug(f"Generated {len(submodule_search_queries)} queries for submodule")
        if state.get("progress_callback"):
            await state["progress_callback"](f"Generated queries for submodule {sub_id+1} of module {module_id+1}")
        submodule_search_results = await execute_submodule_specific_searches(state, module_id, sub_id, module, submodule, submodule_search_queries)
        logger.debug(f"Obtained {len(submodule_search_results)} search results for submodule")
        if state.get("progress_callback"):
            await state["progress_callback"](f"Completed research for submodule {sub_id+1} of module {module_id+1}")
        submodule_content = await develop_submodule_specific_content(state, module_id, sub_id, module, submodule, submodule_search_queries, submodule_search_results)
        logger.info(f"Developed content for submodule {sub_id+1} (length: {len(submodule_content)})")
        if state.get("progress_callback"):
            await state["progress_callback"](f"Completed development for submodule {sub_id+1} of module {module_id+1}")
        return {"status": "completed", "search_queries": submodule_search_queries, "search_results": submodule_search_results, "content": submodule_content}
    except Exception as e:
        logger.exception(f"Error processing submodule {sub_id+1} of module {module_id+1}: {str(e)}")
        if state.get("progress_callback"):
            await state["progress_callback"](f"Error in submodule {sub_id+1} of module {module_id+1}: {str(e)}")
        return {"status": "error", "error": str(e)}

async def generate_submodule_specific_queries(
    state: LearningPathState, 
    module_id: int, 
    sub_id: int, 
    module: EnhancedModule, 
    submodule: Submodule
) -> List[SearchQuery]:
    """
    Generates search queries specific to a submodule.
    
    Args:
        state: The current LearningPathState.
        module_id: Index of the parent module.
        sub_id: Index of the submodule.
        module: The EnhancedModule instance.
        submodule: The Submodule instance.
        
    Returns:
        A list of SearchQuery instances.
    """
    logger = logging.getLogger("learning_path.query_generator")
    logger.info(f"Generating search queries for submodule {module_id}.{sub_id}: {submodule.title}")
    
    # Get the Google key provider from state
    google_key_provider = state.get("google_key_provider")
    
    # Prepare context about the module and submodule
    learning_context = {
        "topic": state["user_topic"],
        "module_title": module.title,
        "module_description": module.description,
        "submodule_title": submodule.title,
        "submodule_description": submodule.description,
        "depth_level": submodule.depth_level
    }
    
    # Create context about other modules and submodules
    other_modules = []
    for i, m in enumerate(state.get("enhanced_modules", [])):
        other_modules.append({
            "title": m.title,
            "description": m.description[:200] + "..." if len(m.description) > 200 else m.description,
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

Other Modules in Learning Path:
"""
    for m in other_modules:
        learning_path_context += f"- {'[Current] ' if m['is_current'] else ''}{m['title']}: {m['description']}\n"
    
    # Set up module context and counts
    module_context = f"Current Module: {module.title}\nDescription: {module.description}"
    module_count = len(state.get("enhanced_modules", []))
    submodule_count = len(module.submodules)
    
    prompt = ChatPromptTemplate.from_template(SUBMODULE_QUERY_GENERATION_PROMPT)
    try:
        result = await run_chain(prompt, lambda: get_llm(key_provider=google_key_provider), module_queries_parser, {
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "submodule_title": submodule.title,
            "submodule_description": submodule.description,
            "module_order": module_id + 1,
            "module_count": module_count,
            "submodule_order": sub_id + 1,
            "submodule_count": submodule_count,
            "module_context": module_context,
            "learning_path_context": learning_path_context,
            "format_instructions": module_queries_parser.get_format_instructions()
        })
        
        queries = result.queries if hasattr(result, 'queries') else []
        logging.info(f"Generated {len(queries)} search queries for submodule {sub_id+1}")
        return queries
    except Exception as e:
        logging.error(f"Error generating submodule search queries: {str(e)}")
        # Create a fallback query
        fallback_query = SearchQuery(
            keywords=f"{module.title} {submodule.title}",
            rationale="Fallback query due to error in query generation"
        )
        return [fallback_query]

async def execute_single_search_for_submodule(query: SearchQuery, key_provider=None) -> Dict[str, Any]:
    """
    Executes a single web search for a submodule using the Perplexity LLM.
    
    Args:
        query: A SearchQuery instance with keywords and rationale.
        key_provider: Optional key provider for Perplexity search.
        
    Returns:
        A dictionary with the query, rationale, and search results.
    """
    try:
        # Properly await the search_model coroutine
        search_model = await get_search_tool(key_provider=key_provider)
        logging.info(f"Searching for: {query.keywords}")
        
        # Create a prompt that asks for web search results
        search_prompt = f"{query.keywords}"
        
        # Invoke the Perplexity model with the search prompt as a string
        result = search_model.invoke(search_prompt)
        
        # Process the response into the expected format
        formatted_result = [
            {
                "source": f"Perplexity Search Result for '{query.keywords}'",
                "content": result.content
            }
        ]
        
        return {
            "query": query.keywords,
            "rationale": query.rationale,
            "results": formatted_result
        }
    except Exception as e:
        logging.error(f"Error searching for '{query.keywords}': {str(e)}")
        return {
            "query": query.keywords,
            "rationale": query.rationale,
            "results": [{"source": "Error", "content": f"Error performing search: {str(e)}"}]
        }

async def execute_submodule_specific_searches(
    state: LearningPathState, 
    module_id: int, 
    sub_id: int, 
    module: EnhancedModule, 
    submodule: Submodule,
    sub_queries: List[SearchQuery]
) -> List[Dict[str, Any]]:
    """
    Execute web searches for submodule-specific queries.
    
    Args:
        state: The current LearningPathState.
        module_id: Index of the parent module.
        sub_id: Index of the submodule.
        module: The EnhancedModule instance.
        submodule: The Submodule instance.
        sub_queries: List of search queries for the submodule.
        
    Returns:
        A list of search result dictionaries.
    """
    logging.info(f"Executing searches for submodule {sub_id+1} of module {module_id+1}: {submodule.title}")
    if not sub_queries:
        logging.warning("No search queries available for submodule")
        return []
    search_parallel_count = state.get("search_parallel_count", 3)
    batches = batch_items(sub_queries, search_parallel_count)
    search_results = []
    try:
        for idx, batch in enumerate(batches):
            tasks = [execute_single_search_for_submodule(query, key_provider=state.get("pplx_key_provider")) for query in batch]
            results = await asyncio.gather(*tasks)
            search_results.extend(results)
            if idx < len(batches) - 1:
                await asyncio.sleep(0.5)
        logging.info(f"Completed {len(search_results)} searches for submodule {sub_id+1}")
        return search_results
    except Exception as e:
        logging.error(f"Error executing submodule searches: {str(e)}")
        return []

async def develop_submodule_specific_content(
    state: LearningPathState, 
    module_id: int, 
    sub_id: int, 
    module: EnhancedModule, 
    submodule: Submodule,
    sub_queries: List[SearchQuery],
    sub_search_results: List[Dict[str, Any]]
) -> str:
    """
    Develops comprehensive content for a submodule using research data.
    
    Args:
        state: The current LearningPathState.
        module_id: Index of the parent module.
        sub_id: Index of the submodule.
        module: The EnhancedModule instance.
        submodule: The Submodule instance.
        sub_queries: List of search queries used.
        sub_search_results: List of search results obtained.
        
    Returns:
        A string containing the developed submodule content.
    """
    logger = logging.getLogger("learning_path.content_developer")
    logger.info(f"Developing content for submodule {sub_id+1} of module {module_id+1}: {submodule.title}")
    if not sub_search_results:
        logger.warning("No search results available for content development")
        return "No content generated due to missing search results."
    
    formatted_results = ""
    for result in sub_search_results:
        formatted_results += f"Query: {result.get('query', '')}\n"
        formatted_results += f"Rationale: {result.get('rationale', '')}\nResults:\n"
        results = result.get("results", "")
        if isinstance(results, str):
            formatted_results += f"  {results}\n\n"
        else:
            for item in results:
                formatted_results += f"  - {item.get('title', 'No title')}: {item.get('content', 'No content')}\n    URL: {item.get('url', 'No URL')}\n"
            formatted_results += "\n"
    
    learning_path_context = ""
    for i, mod in enumerate(state.get("enhanced_modules") or []):
        indicator = " (CURRENT)" if i == module_id else ""
        learning_path_context += f"Module {i+1}: {mod.title}{indicator}\n{mod.description}\n"
    module_context = f"Current Module: {module.title}\nDescription: {module.description}\nAll Submodules:\n"
    for i, s in enumerate(module.submodules):
        indicator = " (CURRENT)" if i == sub_id else ""
        module_context += f"  {i+1}. {s.title}{indicator}\n  {s.description}\n"
    adjacent_context = "Adjacent Submodules:\n"
    if sub_id > 0:
        prev = module.submodules[sub_id-1]
        adjacent_context += f"Previous: {prev.title}\n{prev.description}\n"
    else:
        adjacent_context += "No previous submodule.\n"
    if sub_id < len(module.submodules) - 1:
        nxt = module.submodules[sub_id+1]
        adjacent_context += f"Next: {nxt.title}\n{nxt.description}\n"
    else:
        adjacent_context += "No next submodule.\n"
    
    # Using the extracted prompt template
    prompt = ChatPromptTemplate.from_template(SUBMODULE_CONTENT_DEVELOPMENT_PROMPT)
    try:
        # Properly await the LLM coroutine
        llm = await get_llm(key_provider=state.get("google_key_provider"))
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser
        sub_content = await chain.ainvoke({
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "module_description": module.description,
            "submodule_title": submodule.title,
            "submodule_description": submodule.description,
            "module_order": module_id + 1,
            "module_count": len(state.get("enhanced_modules") or []),
            "submodule_order": sub_id + 1,
            "submodule_count": len(module.submodules),
            "module_context": module_context,
            "adjacent_context": adjacent_context,
            "learning_path_context": learning_path_context,
            "search_results": formatted_results,
            "format_instructions": ""
        })
        if not sub_content:
            logger.error("LLM returned empty content")
            sub_content = f"Error: No content generated for {submodule.title}"
        elif not isinstance(sub_content, str):
            logger.warning("Content not a string; converting")
            sub_content = str(sub_content)
        return sub_content
    except Exception as e:
        logger.exception(f"Error developing submodule content: {str(e)}")
        return f"Error developing content: {str(e)}"

async def finalize_enhanced_learning_path(state: LearningPathState) -> Dict[str, Any]:
    """
    Assembles all developed submodules into a final learning path structure.
    
    Args:
        state: The current LearningPathState.
        
    Returns:
        A dictionary with the final learning path structure and execution steps.
    """
    logger = logging.getLogger("learning_path.finalizer")
    logger.info("Finalizing enhanced learning path with submodules")
    try:
        if not state.get("developed_submodules"):
            logger.warning("No developed submodules available")
            return {"final_learning_path": {"topic": state["user_topic"], "modules": []}, "steps": ["No submodules developed"]}
        module_to_subs = {}
        for sub in state["developed_submodules"]:
            module_to_subs.setdefault(sub.module_id, []).append(sub)
        for module_id in module_to_subs:
            module_to_subs[module_id].sort(key=lambda s: s.submodule_id)
        final_modules = []
        for module_id, module in enumerate(state.get("enhanced_modules") or []):
            subs = module_to_subs.get(module_id, [])
            submodule_data = []
            for sub in subs:
                summary = sub.summary if hasattr(sub, 'summary') else (sub.content[:200].strip() + "..." if sub.content else "")
                submodule_data.append({
                    "id": sub.submodule_id,
                    "title": sub.title,
                    "description": sub.description,
                    "content": sub.content,
                    "order": sub.submodule_id + 1,
                    "summary": summary,
                    "connections": getattr(sub, 'connections', {})
                })
            module_data = {
                "id": module_id,
                "title": module.title,
                "description": module.description,
                "core_concept": getattr(module, 'core_concept', ""),
                "learning_objective": getattr(module, 'learning_objective', ""),
                "prerequisites": getattr(module, 'prerequisites', []),
                "key_components": getattr(module, 'key_components', []),
                "expected_outcomes": getattr(module, 'expected_outcomes', []),
                "submodules": submodule_data
            }
            final_modules.append(module_data)
        final_learning_path = {"topic": state["user_topic"], "modules": final_modules, "execution_steps": state["steps"]}
        logger.info(f"Finalized learning path with {len(final_modules)} modules")
        return {"final_learning_path": final_learning_path, "steps": ["Finalized enhanced learning path"]}
    except Exception as e:
        logger.exception(f"Error finalizing learning path: {str(e)}")
        return {"final_learning_path": {"topic": state["user_topic"], "modules": [], "error": str(e)}, "steps": [f"Error: {str(e)}"]}

def check_submodule_batch_processing(state: LearningPathState) -> str:
    """
    Checks if all submodule batches have been processed.
    
    Args:
        state: The current LearningPathState.
        
    Returns:
        "all_batches_processed" if all batches are done, otherwise "continue_processing".
    """
    current_index = state.get("current_submodule_batch_index")
    batches = state.get("submodule_batches")
    if current_index is None or batches is None:
        logging.warning("Submodule batch processing state is not set properly")
        return "all_batches_processed"
    if current_index >= len(batches):
        logging.info(f"All {len(batches)} submodule batches processed")
        return "all_batches_processed"
    else:
        logging.info(f"Continue processing: batch {current_index+1} of {len(batches)}")
        return "continue_processing"
