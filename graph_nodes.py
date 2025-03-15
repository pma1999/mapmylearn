import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Callable, Tuple

from models import SearchQuery, Module, Submodule, EnhancedModule, ModuleContent, SubmoduleContent, LearningPathState
from parsers import search_queries_parser, modules_parser, module_queries_parser, submodule_parser
from services import get_llm, get_search_tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from operator import add

# -----------------------------
# Node Functions for the Initial Flow
# -----------------------------

async def execute_single_search(query: SearchQuery) -> Dict[str, Any]:
    """
    Execute a single web search for a given query.
    Returns a dict with the original query, rationale and the results.
    """
    try:
        search_tool = get_search_tool()
        logging.info(f"Searching for: {query.keywords}")
        result = await search_tool.ainvoke({"query": query.keywords})
        return {
            "query": query.keywords,
            "rationale": query.rationale,
            "results": result
        }
    except Exception as e:
        logging.error(f"Error searching for '{query.keywords}': {str(e)}")
        return {
            "query": query.keywords,
            "rationale": query.rationale,
            "results": f"Error performing search: {str(e)}"
        }

async def generate_search_queries(state: LearningPathState) -> Dict[str, Any]:
    """
    Generate optimal search queries for the user topic.
    """
    logging.info(f"Generating search queries for topic: {state['user_topic']}")
    prompt = ChatPromptTemplate.from_template("""
You are an expert research assistant. Your task is to generate 5 search queries that 
will gather comprehensive information for creating a learning path about {user_topic}.

For each search query:
1. Make it specific and targeted
2. Ensure it covers a different aspect of the topic
3. Design it to return high-quality educational content
4. Explain why this search is important for understanding the topic

Your response should be exactly 5 search queries, each with its rationale.

{format_instructions}
""")
    try:
        llm = get_llm()
        chain = prompt | llm | search_queries_parser
        search_query_list = await chain.ainvoke({
            "user_topic": state["user_topic"],
            "format_instructions": search_queries_parser.get_format_instructions()
        })
        search_queries = search_query_list.queries
        logging.info(f"Generated {len(search_queries)} search queries")
        return {
            "search_queries": search_queries,
            "steps": [f"Generated {len(search_queries)} search queries for topic: {state['user_topic']}"]
        }
    except Exception as e:
        logging.error(f"Error generating search queries: {str(e)}")
        return {
            "search_queries": [],
            "steps": [f"Error generating search queries: {str(e)}"]
        }

async def execute_web_searches(state: LearningPathState) -> Dict[str, Any]:
    """
    Execute web searches using the generated queries in parallel.
    """
    logging.info("Executing web searches in parallel")
    if not state["search_queries"]:
        logging.warning("No search queries available to execute")
        return {
            "search_results": [],
            "steps": ["No search queries available to execute"]
        }
    
    search_parallel_count = state.get("search_parallel_count", 3)
    queries = state["search_queries"]
    query_batches = [queries[i:i + search_parallel_count] for i in range(0, len(queries), search_parallel_count)]
    
    logging.info(f"Executing {len(queries)} searches in {len(query_batches)} batches with parallelism of {search_parallel_count}")
    search_results = []
    
    try:
        for batch_index, batch in enumerate(query_batches):
            logging.info(f"Processing search batch {batch_index + 1}/{len(query_batches)} with {len(batch)} queries")
            tasks = [execute_single_search(query) for query in batch]
            batch_results = await asyncio.gather(*tasks)
            search_results.extend(batch_results)
            if batch_index < len(query_batches) - 1:
                await asyncio.sleep(0.5)
        logging.info(f"Completed {len(search_results)} web searches in parallel")
        if state.get("progress_callback"):
            await state["progress_callback"](f"Executed {len(search_results)} web searches in {len(query_batches)} parallel batches")
        return {
            "search_results": search_results,
            "steps": [f"Executed {len(search_results)} web searches in parallel batches"]
        }
    except Exception as e:
        logging.error(f"Error executing web searches: {str(e)}")
        return {
            "search_results": [],
            "steps": [f"Error executing web searches: {str(e)}"]
        }

async def create_learning_path(state: LearningPathState) -> Dict[str, Any]:
    """
    Create a structured learning path based on the search results.
    """
    logging.info("Creating learning path")
    if not state["search_results"]:
        logging.warning("No search results available to create learning path")
        return {
            "modules": [],
            "steps": ["No search results available to create learning path"]
        }
    
    formatted_results = ""
    for result in state["search_results"]:
        formatted_results += f"Search Query: {result['query']}\n"
        formatted_results += f"Rationale: {result['rationale']}\nResults:\n"
        if isinstance(result['results'], str):
            formatted_results += f"  {result['results']}\n\n"
        else:
            for item in result['results']:
                formatted_results += f"  - {item.get('title', 'No title')}: {item.get('content', 'No content')}\n"
                formatted_results += f"    URL: {item.get('url', 'No URL')}\n"
            formatted_results += "\n"
    
    prompt = ChatPromptTemplate.from_template("""
You are an expert education specialist. Your task is to create a comprehensive learning path 
for {user_topic}.

Use the following research information:
{search_results}

Design a logical sequence of learning modules. For each module, provide:
1. A clear, informative title
2. A detailed description of what will be covered in the module

Structure your response as a series of modules that build upon each other.

{format_instructions}
""")
    try:
        llm = get_llm()
        chain = prompt | llm | modules_parser
        module_list = await chain.ainvoke({
            "user_topic": state["user_topic"],
            "search_results": formatted_results,
            "format_instructions": modules_parser.get_format_instructions()
        })
        modules = module_list.modules
        logging.info(f"Created learning path with {len(modules)} modules")
        return {
            "modules": modules,
            "steps": [f"Created learning path with {len(modules)} modules"]
        }
    except Exception as e:
        logging.error(f"Error creating learning path: {str(e)}")
        return {
            "modules": [],
            "steps": [f"Error creating learning path: {str(e)}"]
        }

# -----------------------------
# Node Functions for Submodule Planning and Processing
# -----------------------------

async def plan_submodules(state: LearningPathState) -> Dict[str, Any]:
    """
    Plan detailed submodules for each module in the learning path.
    """
    logging.info("Planning submodules for each module in the learning path")
    if not state["modules"]:
        logging.warning("No modules available to plan submodules")
        return {
            "enhanced_modules": [],
            "steps": ["No modules available to plan submodules"]
        }
    
    enhanced_modules = []
    for module_index, module in enumerate(state["modules"]):
        logging.info(f"Planning submodules for module {module_index + 1}: {module.title}")
        learning_path_context = ""
        for i, mod in enumerate(state["modules"]):
            learning_path_context += f"Module {i+1}: {mod.title}\nDescription: {mod.description}\n\n"
        
        prompt = ChatPromptTemplate.from_template("""
You are an expert education content planner. Your task is to break down a learning module 
into logical submodules that provide a detailed, comprehensive coverage of the topic.

The module you need to break down is:
Title: {module_title}
Description: {module_description}

This module is part of a learning path about "{user_topic}".

Here is the context of the entire learning path:
{learning_path_context}

For this module, create 3-5 logical submodules that:
1. Cover different aspects of the module topic
2. Build upon each other in a logical sequence
3. Are comprehensive yet focused
4. Together completely fulfill the module's description

For each submodule provide:
1. A clear, descriptive title
2. A detailed description explaining what this submodule will cover
3. Ensure the submodules follow a logical order for learning

Your submodules MUST create a complete, cohesive learning experience for this module.

{format_instructions}
""")
        try:
            llm = get_llm()
            chain = prompt | llm | submodule_parser
            submodule_list = await chain.ainvoke({
                "user_topic": state["user_topic"],
                "module_title": module.title,
                "module_description": module.description,
                "learning_path_context": learning_path_context,
                "format_instructions": submodule_parser.get_format_instructions()
            })
            submodules = submodule_list.submodules
            for i, sub in enumerate(submodules):
                sub.order = i + 1
            enhanced_module = EnhancedModule(
                title=module.title,
                description=module.description,
                submodules=submodules
            )
            enhanced_modules.append(enhanced_module)
            logging.info(f"Created {len(submodules)} submodules for module {module_index + 1}")
        except Exception as e:
            logging.error(f"Error planning submodules for module {module_index + 1}: {str(e)}")
            enhanced_modules.append(EnhancedModule(
                title=module.title,
                description=module.description,
                submodules=[]
            ))
    if state.get("progress_callback"):
        total_submodules = sum(len(m.submodules) for m in enhanced_modules)
        await state["progress_callback"](f"Planned {total_submodules} submodules across {len(enhanced_modules)} modules")
    return {
        "enhanced_modules": enhanced_modules,
        "steps": [f"Planned submodules for {len(enhanced_modules)} modules"]
    }

async def initialize_parallel_processing(state: LearningPathState) -> Dict[str, Any]:
    """
    Initialize the parallel module development process.
    """
    logging.info(f"Initializing parallel module development process with {state.get('parallel_count',1)} modules at once")
    if not state.get("modules"):
        logging.warning("No modules to develop")
        return {
            "developed_modules": [],
            "steps": ["No modules to develop"]
        }
    parallel_count = state.get("parallel_count", 1)
    modules = state.get("modules", [])
    module_batches = [list(range(i, min(i + parallel_count, len(modules)))) for i in range(0, len(modules), parallel_count)]
    logging.info(f"Created {len(module_batches)} batches of modules for parallel processing")
    return {
        "module_batches": module_batches,
        "current_batch_index": 0,
        "modules_in_process": {},
        "developed_modules": [],
        "steps": [f"Initialized parallel processing with {parallel_count} modules at once"]
    }

async def process_module_batch(state: LearningPathState) -> Dict[str, Any]:
    """
    Process the current batch of modules in parallel.
    """
    logging.info("Processing a batch of modules in parallel")
    if state.get("current_batch_index", 0) >= len(state.get("module_batches", [])):
        logging.info("All module batches have been processed")
        return {
            "steps": ["All module batches have been processed"]
        }
    current_batch = state["module_batches"][state["current_batch_index"]]
    modules = state["modules"]
    modules_in_process = state.get("modules_in_process", {})
    tasks = []
    for module_index in current_batch:
        if module_index not in modules_in_process:
            modules_in_process[module_index] = {
                "status": "starting",
                "search_queries": None,
                "search_results": None,
                "content": None
            }
            task = process_single_module(state, module_index, modules[module_index])
            tasks.append(task)
    progress_msg = f"Started processing batch {state['current_batch_index'] + 1} with {len(tasks)} modules"
    logging.info(progress_msg)
    if tasks:
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, module_index in enumerate(current_batch):
                if i < len(results):
                    result = results[i]
                    if isinstance(result, Exception):
                        logging.error(f"Error processing module {module_index}: {str(result)}")
                        modules_in_process[module_index]["status"] = "error"
                        modules_in_process[module_index]["error"] = str(result)
                    else:
                        modules_in_process[module_index] = result
            logging.info(f"Completed processing batch {state['current_batch_index'] + 1}")
        except Exception as e:
            logging.error(f"Error in parallel processing batch: {str(e)}")
    next_batch_index = state["current_batch_index"] + 1
    developed_modules = state.get("developed_modules", [])
    for module_index in current_batch:
        module_data = modules_in_process.get(module_index, {})
        if module_data.get("status") == "completed":
            developed_modules.append(ModuleContent(
                module_id=module_index,
                title=modules[module_index].title,
                description=modules[module_index].description,
                search_queries=module_data.get("search_queries", []),
                search_results=module_data.get("search_results", []),
                content=module_data.get("content", "")
            ))
    return {
        "modules_in_process": modules_in_process,
        "current_batch_index": next_batch_index,
        "developed_modules": developed_modules,
        "steps": [f"Processed batch {state['current_batch_index'] + 1} of modules in parallel"]
    }

async def process_single_module(state: LearningPathState, module_index: int, module: Module) -> Dict[str, Any]:
    """
    Process a single module from research to content development.
    """
    logging.info(f"Processing module {module_index + 1}: {module.title}")
    try:
        module_search_queries = await generate_module_specific_queries(state, module_index, module)
        if state.get("progress_callback"):
            await state["progress_callback"](f"Generated search queries for module {module_index + 1}: {module.title}")
        module_search_results = await execute_module_specific_searches(state, module_index, module, module_search_queries)
        if state.get("progress_callback"):
            await state["progress_callback"](f"Completed research for module {module_index + 1}: {module.title}")
        module_content = await develop_module_specific_content(state, module_index, module, module_search_queries, module_search_results)
        if state.get("progress_callback"):
            await state["progress_callback"](f"Completed development of module {module_index + 1}: {module.title}")
        return {
            "status": "completed",
            "search_queries": module_search_queries,
            "search_results": module_search_results,
            "content": module_content
        }
    except Exception as e:
        logging.error(f"Error processing module {module_index}: {str(e)}")
        if state.get("progress_callback"):
            await state["progress_callback"](f"Error processing module {module_index + 1}: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

async def generate_module_specific_queries(state: LearningPathState, module_index: int, module: Module) -> List[SearchQuery]:
    """
    Generate targeted search queries for a specific module.
    """
    logging.info(f"Generating search queries for module {module_index + 1}: {module.title}")
    learning_path_context = ""
    for i, mod in enumerate(state["modules"]):
        learning_path_context += f"Module {i+1}: {mod.title}\nDescription: {mod.description}\n\n"
    
    prompt = ChatPromptTemplate.from_template("""
You are an expert research assistant. Your task is to generate 5 search queries that 
will gather comprehensive information for developing the module titled "{module_title}" 
which is part of a learning path about "{user_topic}".

Here is the description of this module:
{module_description}

Here is the context of the entire learning path:
{learning_path_context}

For each search query:
1. Make it specific and targeted to this particular module
2. Ensure it covers different aspects needed to develop this module
3. Design it to return high-quality educational content
4. Explain why this search is important for developing this module

Your response should be exactly 5 search queries, each with its rationale.

{format_instructions}
""")
    try:
        llm = get_llm()
        chain = prompt | llm | module_queries_parser
        search_query_list = await chain.ainvoke({
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "module_description": module.description,
            "learning_path_context": learning_path_context,
            "format_instructions": module_queries_parser.get_format_instructions()
        })
        module_search_queries = search_query_list.queries
        logging.info(f"Generated {len(module_search_queries)} search queries for module: {module.title}")
        return module_search_queries
    except Exception as e:
        logging.error(f"Error generating module search queries: {str(e)}")
        return []

async def execute_module_specific_searches(
    state: LearningPathState, 
    module_index: int, 
    module: Module, 
    module_search_queries: List[SearchQuery]
) -> List[Dict[str, Any]]:
    """
    Execute web searches for a specific module's queries in parallel.
    """
    logging.info(f"Executing web searches for module {module_index + 1}: {module.title}")
    if not module_search_queries:
        logging.warning(f"No search queries available for module {module_index + 1}")
        return []
    
    search_parallel_count = state.get("search_parallel_count", 3)
    query_batches = [module_search_queries[i:i+search_parallel_count] for i in range(0, len(module_search_queries), search_parallel_count)]
    
    logging.info(f"Executing {len(module_search_queries)} module searches in {len(query_batches)} batches with parallelism of {search_parallel_count}")
    search_results = []
    
    try:
        for batch_index, batch in enumerate(query_batches):
            logging.info(f"Processing module search batch {batch_index + 1}/{len(query_batches)} with {len(batch)} queries")
            tasks = [execute_single_search(query) for query in batch]
            batch_results = await asyncio.gather(*tasks)
            search_results.extend(batch_results)
            if batch_index < len(query_batches) - 1:
                await asyncio.sleep(0.5)
        logging.info(f"Completed {len(search_results)} web searches for module {module_index + 1}")
        return search_results
    except Exception as e:
        logging.error(f"Error executing module web searches: {str(e)}")
        return []

async def develop_module_specific_content(
    state: LearningPathState, 
    module_index: int, 
    module: Module, 
    module_search_queries: List[SearchQuery],
    module_search_results: List[Dict[str, Any]]
) -> str:
    """
    Develop comprehensive content for a specific module.
    """
    logging.info(f"Developing content for module {module_index + 1}: {module.title}")
    if not module_search_results:
        logging.warning(f"No search results available for module {module_index + 1}")
        return "No content could be developed due to missing search results."
    
    formatted_results = ""
    for result in module_search_results:
        formatted_results += f"Search Query: {result['query']}\n"
        formatted_results += f"Rationale: {result['rationale']}\nResults:\n"
        if isinstance(result['results'], str):
            formatted_results += f"  {result['results']}\n\n"
        else:
            for item in result['results']:
                formatted_results += f"  - {item.get('title', 'No title')}: {item.get('content', 'No content')}\n"
                formatted_results += f"    URL: {item.get('url', 'No URL')}\n"
            formatted_results += "\n"
    
    learning_path_context = ""
    for i, mod in enumerate(state["modules"]):
        indicator = " (CURRENT MODULE)" if i == module_index else ""
        learning_path_context += f"Module {i+1}: {mod.title}{indicator}\nDescription: {mod.description}\n\n"
    
    prompt = ChatPromptTemplate.from_template("""
You are an expert education content developer. Your task is to create comprehensive
educational content for a module titled "{module_title}" which is part of a learning 
path about "{user_topic}".

Module description: {module_description}

The position of this module in the learning path: Module {module_index} of {total_modules}

Context of the entire learning path:
{learning_path_context}

Use the following research information to develop this module:
{search_results}

Your content should:
1. Be comprehensive and educational
2. Include clear explanations of concepts
3. Provide examples where appropriate
4. Reference authoritative sources
5. Build upon prior modules in the learning path
6. Prepare the learner for subsequent modules

Structure your content with appropriate sections and markdown formatting.
""")
    try:
        llm = get_llm()
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser
        module_content = await chain.ainvoke({
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "module_description": module.description,
            "module_index": module_index + 1,
            "total_modules": len(state["modules"]),
            "learning_path_context": learning_path_context,
            "search_results": formatted_results
        })
        logging.info(f"Developed content for module {module_index + 1}: {module.title}")
        return module_content
    except Exception as e:
        logging.error(f"Error developing module content: {str(e)}")
        return f"Error developing content: {str(e)}"

async def finalize_learning_path(state: LearningPathState) -> Dict[str, Any]:
    """
    Create the final learning path with all developed modules.
    """
    logging.info("Finalizing learning path")
    if not state.get("developed_modules"):
        logging.warning("No developed modules available")
        return {
            "final_learning_path": {
                "topic": state["user_topic"],
                "modules": []
            },
            "steps": ["No modules were developed"]
        }
    final_learning_path = {
        "topic": state["user_topic"],
        "modules": [
            {
                "id": module.module_id,
                "title": module.title,
                "description": module.description,
                "content": module.content
            }
            for module in state["developed_modules"]
        ],
        "execution_steps": state["steps"]
    }
    logging.info(f"Finalized comprehensive learning path with {len(final_learning_path['modules'])} modules")
    return {
        "final_learning_path": final_learning_path,
        "steps": ["Finalized comprehensive learning path"]
    }

# -----------------------------
# Node Functions for Submodule Parallel Processing
# -----------------------------

async def initialize_submodule_processing(state: LearningPathState) -> Dict[str, Any]:
    """
    Initialize the parallel submodule development process.
    """
    logging.info("Initializing parallel submodule development process")
    if not state.get("enhanced_modules"):
        logging.warning("No enhanced modules with submodules to develop")
        return {
            "developed_submodules": [],
            "steps": ["No enhanced modules with submodules to develop"]
        }
    submodule_parallel_count = state.get("submodule_parallel_count", 2)
    all_submodule_pairs = []
    for module_id, module in enumerate(state["enhanced_modules"]):
        for submodule_id, _ in enumerate(module.submodules):
            all_submodule_pairs.append((module_id, submodule_id))
    submodule_batches = [all_submodule_pairs[i:i+submodule_parallel_count] for i in range(0, len(all_submodule_pairs), submodule_parallel_count)]
    logging.info(f"Created {len(submodule_batches)} batches of submodules for parallel processing")
    if state.get("progress_callback"):
        await state["progress_callback"](f"Organized {len(all_submodule_pairs)} submodules into {len(submodule_batches)} processing batches")
    return {
        "submodule_batches": submodule_batches,
        "current_submodule_batch_index": 0,
        "submodules_in_process": {},
        "developed_submodules": [],
        "steps": [f"Initialized submodule processing with {submodule_parallel_count} submodules at once"]
    }

async def process_submodule_batch(state: LearningPathState) -> Dict[str, Any]:
    """
    Process the current batch of submodules in parallel.
    """
    logging.info("Processing a batch of submodules in parallel")
    if state.get("current_submodule_batch_index", 0) >= len(state.get("submodule_batches", [])):
        logging.info("All submodule batches have been processed")
        return {
            "steps": ["All submodule batches have been processed"]
        }
    current_batch = state["submodule_batches"][state["current_submodule_batch_index"]]
    enhanced_modules = state["enhanced_modules"]
    submodules_in_process = state.get("submodules_in_process", {})
    tasks = []
    for module_id, submodule_id in current_batch:
        sub_key = (module_id, submodule_id)
        if sub_key not in submodules_in_process:
            submodules_in_process[sub_key] = {
                "status": "starting",
                "search_queries": None,
                "search_results": None,
                "content": None
            }
            module = enhanced_modules[module_id]
            submodule = module.submodules[submodule_id]
            task = process_single_submodule(state, module_id, submodule_id, module, submodule)
            tasks.append(task)
    progress_msg = f"Started processing submodule batch {state['current_submodule_batch_index'] + 1} with {len(tasks)} submodules"
    logging.info(progress_msg)
    if state.get("progress_callback"):
        await state["progress_callback"](f"Processing batch {state['current_submodule_batch_index'] + 1} of submodules")
    if tasks:
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, (module_id, submodule_id) in enumerate(current_batch):
                sub_key = (module_id, submodule_id)
                if i < len(results):
                    result = results[i]
                    if isinstance(result, Exception):
                        logging.error(f"Error processing submodule {module_id}.{submodule_id}: {str(result)}")
                        submodules_in_process[sub_key]["status"] = "error"
                        submodules_in_process[sub_key]["error"] = str(result)
                    else:
                        submodules_in_process[sub_key] = result
            logging.info(f"Completed processing submodule batch {state['current_submodule_batch_index'] + 1}")
        except Exception as e:
            logging.error(f"Error in parallel processing submodule batch: {str(e)}")
    next_batch_index = state["current_submodule_batch_index"] + 1
    developed_submodules = state.get("developed_submodules", [])
    for module_id, submodule_id in current_batch:
        sub_key = (module_id, submodule_id)
        sub_data = submodules_in_process.get(sub_key, {})
        if sub_data.get("status") == "completed":
            module = enhanced_modules[module_id]
            submodule = module.submodules[submodule_id]
            developed_submodules.append(SubmoduleContent(
                module_id=module_id,
                submodule_id=submodule_id,
                title=submodule.title,
                description=submodule.description,
                search_queries=sub_data.get("search_queries", []),
                search_results=sub_data.get("search_results", []),
                content=sub_data.get("content", "")
            ))
    if state.get("progress_callback") and state.get("submodule_batches"):
        batch_count = len(state["submodule_batches"])
        batch_num = state["current_submodule_batch_index"] + 1
        await state["progress_callback"](f"Completed {batch_num}/{batch_count} submodule batches")
    return {
        "submodules_in_process": submodules_in_process,
        "current_submodule_batch_index": next_batch_index,
        "developed_submodules": developed_submodules,
        "steps": [f"Processed batch {state['current_submodule_batch_index'] + 1} of submodules in parallel"]
    }

async def process_single_submodule(
    state: LearningPathState, 
    module_id: int, 
    submodule_id: int, 
    module: EnhancedModule, 
    submodule: Submodule
) -> Dict[str, Any]:
    """
    Process a single submodule from research to content development.
    """
    logger = logging.getLogger("learning_path.submodule_processor")
    logger.info(f"Processing submodule {submodule_id + 1} of module {module_id + 1}: {submodule.title}")
    
    try:
        # Log del estado recibido
        from log_config import log_debug_data, log_info_data
        log_debug_data(logger, f"Starting submodule processing with state", {
            "module_id": module_id,
            "submodule_id": submodule_id,
            "module_title": module.title,
            "submodule_title": submodule.title,
            "state_keys": list(state.keys())
        })
        
        submodule_search_queries = await generate_submodule_specific_queries(state, module_id, submodule_id, module, submodule)
        logger.debug(f"Generated {len(submodule_search_queries)} search queries for submodule")
        log_debug_data(logger, "Submodule search queries", submodule_search_queries)
        
        if state.get("progress_callback"):
            await state["progress_callback"](f"Generated search queries for submodule {submodule_id + 1} of module {module_id + 1}: {submodule.title}")
        
        submodule_search_results = await execute_submodule_specific_searches(state, module_id, submodule_id, module, submodule, submodule_search_queries)
        logger.debug(f"Executed {len(submodule_search_results)} searches for submodule")
        log_debug_data(logger, "Submodule search results", submodule_search_results)
        
        if state.get("progress_callback"):
            await state["progress_callback"](f"Completed research for submodule {submodule_id + 1} of module {module_id + 1}: {submodule.title}")
        
        submodule_content = await develop_submodule_specific_content(state, module_id, submodule_id, module, submodule, submodule_search_queries, submodule_search_results)
        logger.info(f"Developed content for submodule {submodule_id + 1}. Content length: {len(submodule_content)}")
        
        # Log una muestra del contenido generado para diagnóstico
        content_sample = submodule_content[:500] + "..." if len(submodule_content) > 500 else submodule_content
        logger.debug(f"Content sample for submodule {submodule_id + 1}: {content_sample}")
        
        if state.get("progress_callback"):
            await state["progress_callback"](f"Completed development of submodule {submodule_id + 1} of module {module_id + 1}: {submodule.title}")
        
        result = {
            "status": "completed",
            "search_queries": submodule_search_queries,
            "search_results": submodule_search_results,
            "content": submodule_content
        }
        
        log_debug_data(logger, "Final submodule process result", result)
        return result
    except Exception as e:
        logger.exception(f"Error processing submodule {submodule_id + 1} of module {module_id + 1}: {str(e)}")
        if state.get("progress_callback"):
            await state["progress_callback"](f"Error processing submodule {submodule_id + 1} of module {module_id + 1}: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

async def generate_submodule_specific_queries(
    state: LearningPathState, 
    module_id: int, 
    submodule_id: int, 
    module: EnhancedModule, 
    submodule: Submodule
) -> List[SearchQuery]:
    """
    Generate targeted search queries for a specific submodule.
    """
    logging.info(f"Generating search queries for submodule {submodule_id + 1} of module {module_id + 1}: {submodule.title}")
    learning_path_context = ""
    for i, mod in enumerate(state["enhanced_modules"]):
        learning_path_context += f"Module {i+1}: {mod.title}\nDescription: {mod.description}\n\n"
        for j, sub in enumerate(mod.submodules):
            learning_path_context += f"  Submodule {j+1}: {sub.title}\n  Description: {sub.description}\n\n"
    module_context = f"Current Module: {module.title}\nModule Description: {module.description}\n\nSubmodules in this module:\n"
    for i, sub in enumerate(module.submodules):
        indicator = " (CURRENT SUBMODULE)" if i == submodule_id else ""
        module_context += f"  Submodule {i+1}: {sub.title}{indicator}\n  Description: {sub.description}\n\n"
    
    prompt = ChatPromptTemplate.from_template("""
You are an expert research assistant. Your task is to generate 5 search queries that 
will gather comprehensive information for developing the submodule titled "{submodule_title}" 
which is part of the module "{module_title}" in a learning path about "{user_topic}".

Here is the description of this submodule:
{submodule_description}

This is submodule {submodule_order} of {submodule_count} in this module.
This module is number {module_order} of {module_count} in the learning path.

Context for this module:
{module_context}

Here is the context of the entire learning path:
{learning_path_context}

For each search query:
1. Make it specific and targeted to this particular submodule's content
2. Ensure it covers different aspects needed to develop this submodule thoroughly
3. Design it to return high-quality educational content
4. Explain why this search is important for developing this specific submodule

Your response should be exactly 5 search queries, each with its rationale.

{format_instructions}
""")
    try:
        llm = get_llm()
        chain = prompt | llm | module_queries_parser
        search_query_list = await chain.ainvoke({
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "module_description": module.description,
            "module_order": module_id + 1,
            "module_count": len(state["enhanced_modules"]),
            "submodule_title": submodule.title,
            "submodule_description": submodule.description,
            "submodule_order": submodule_id + 1,
            "submodule_count": len(module.submodules),
            "module_context": module_context,
            "learning_path_context": learning_path_context,
            "format_instructions": module_queries_parser.get_format_instructions()
        })
        submodule_search_queries = search_query_list.queries
        logging.info(f"Generated {len(submodule_search_queries)} search queries for submodule: {submodule.title}")
        return submodule_search_queries
    except Exception as e:
        logging.error(f"Error generating submodule search queries: {str(e)}")
        return []

async def execute_submodule_specific_searches(
    state: LearningPathState, 
    module_id: int, 
    submodule_id: int, 
    module: EnhancedModule, 
    submodule: Submodule,
    submodule_search_queries: List[SearchQuery]
) -> List[Dict[str, Any]]:
    """
    Execute web searches for a specific submodule's queries in parallel.
    """
    logging.info(f"Executing web searches for submodule {submodule_id + 1} of module {module_id + 1}: {submodule.title}")
    if not submodule_search_queries:
        logging.warning(f"No search queries available for submodule {submodule_id + 1} of module {module_id + 1}")
        return []
    search_parallel_count = state.get("search_parallel_count", 3)
    query_batches = [submodule_search_queries[i:i+search_parallel_count] for i in range(0, len(submodule_search_queries), search_parallel_count)]
    logging.info(f"Executing {len(submodule_search_queries)} submodule searches in {len(query_batches)} batches with parallelism of {search_parallel_count}")
    search_results = []
    try:
        for batch_index, batch in enumerate(query_batches):
            logging.info(f"Processing submodule search batch {batch_index + 1}/{len(query_batches)} with {len(batch)} queries")
            tasks = [execute_single_search(query) for query in batch]
            batch_results = await asyncio.gather(*tasks)
            search_results.extend(batch_results)
            if batch_index < len(query_batches) - 1:
                await asyncio.sleep(0.5)
        logging.info(f"Completed {len(search_results)} web searches for submodule {submodule_id + 1} of module {module_id + 1}")
        return search_results
    except Exception as e:
        logging.error(f"Error executing submodule web searches: {str(e)}")
        return []

async def develop_submodule_specific_content(
    state: LearningPathState, 
    module_id: int, 
    submodule_id: int, 
    module: EnhancedModule, 
    submodule: Submodule,
    submodule_search_queries: List[SearchQuery],
    submodule_search_results: List[Dict[str, Any]]
) -> str:
    """
    Develop comprehensive content for a specific submodule.
    """
    logger = logging.getLogger("learning_path.content_developer")
    logger.info(f"Developing content for submodule {submodule_id + 1} of module {module_id + 1}: {submodule.title}")
    
    from log_config import log_debug_data, log_info_data
    
    if not submodule_search_results:
        logger.warning(f"No search results available for submodule {submodule_id + 1} of module {module_id + 1}")
        return "No content could be developed due to missing search results."
    
    # Log input data for debugging
    log_debug_data(logger, "Submodule development input", {
        "module_id": module_id,
        "submodule_id": submodule_id,
        "module_title": module.title,
        "submodule_title": submodule.title,
        "search_queries_count": len(submodule_search_queries),
        "search_results_count": len(submodule_search_results)
    })
    
    formatted_results = ""
    for result in submodule_search_results:
        formatted_results += f"Search Query: {result['query']}\n"
        formatted_results += f"Rationale: {result['rationale']}\nResults:\n"
        if isinstance(result['results'], str):
            formatted_results += f"  {result['results']}\n\n"
        else:
            for item in result['results']:
                formatted_results += f"  - {item.get('title', 'No title')}: {item.get('content', 'No content')}\n"
                formatted_results += f"    URL: {item.get('url', 'No URL')}\n"
            formatted_results += "\n"
    
    learning_path_context = ""
    for i, mod in enumerate(state["enhanced_modules"]):
        indicator = " (CURRENT MODULE)" if i == module_id else ""
        learning_path_context += f"Module {i+1}: {mod.title}{indicator}\nDescription: {mod.description}\n\n"
        if i == module_id:
            for j, sub in enumerate(mod.submodules):
                indicator_sub = " (CURRENT SUBMODULE)" if j == submodule_id else ""
                learning_path_context += f"  Submodule {j+1}: {sub.title}{indicator_sub}\n  Description: {sub.description}\n\n"
        else:
            for j, sub in enumerate(mod.submodules):
                learning_path_context += f"  Submodule {j+1}: {sub.title}\n  Description: {sub.description}\n\n"
    
    module_context = f"Current Module: {module.title}\nModule Description: {module.description}\n\nAll Submodules in this module:\n"
    for i, sub in enumerate(module.submodules):
        indicator_sub = " (CURRENT SUBMODULE)" if i == submodule_id else ""
        module_context += f"  Submodule {i+1}: {sub.title}{indicator_sub}\n  Description: {sub.description}\n\n"
    
    adjacent_context = "Adjacent Submodules:\n"
    if submodule_id > 0:
        prev_sub = module.submodules[submodule_id - 1]
        adjacent_context += f"Previous Submodule: {prev_sub.title}\nDescription: {prev_sub.description}\n\n"
    else:
        adjacent_context += "No previous submodule in this module.\n\n"
    if submodule_id < len(module.submodules) - 1:
        next_sub = module.submodules[submodule_id + 1]
        adjacent_context += f"Next Submodule: {next_sub.title}\nDescription: {next_sub.description}\n"
    else:
        adjacent_context += "No next submodule in this module.\n"
    
    prompt = ChatPromptTemplate.from_template("""
You are an expert education content developer. Your task is to create comprehensive
educational content for a submodule titled "{submodule_title}" which is part of a module
titled "{module_title}" in a learning path about "{user_topic}".

Submodule description: {submodule_description}

Position information:
- This is submodule {submodule_order} of {submodule_count} in the current module
- The parent module is module {module_order} of {module_count} in the learning path

Module context:
{module_context}

Adjacent submodules:
{adjacent_context}

Learning path context:
{learning_path_context}

Use the following research information to develop this submodule:
{search_results}

Your content should:
1. Be comprehensive and educational
2. Include clear explanations of concepts
3. Provide examples where appropriate
4. Reference authoritative sources
5. Build upon prior submodules in the learning path
6. Prepare the learner for subsequent submodules
7. Be coherent with the overall learning path flow
8. Focus ONLY on the topics relevant to this specific submodule

Structure your content with appropriate sections and markdown formatting.
""")
    try:
        llm = get_llm()
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser
        
        # Log the prompt parameters
        log_debug_data(logger, "Content development prompt parameters", {
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "submodule_title": submodule.title,
            "module_order": module_id + 1,
            "module_count": len(state["enhanced_modules"]),
            "submodule_order": submodule_id + 1,
            "submodule_count": len(module.submodules)
        })
        
        logger.info(f"Invoking LLM for content generation for submodule {submodule_id + 1} of module {module_id + 1}")
        
        invoke_params = {
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "module_description": module.description,
            "module_order": module_id + 1,
            "module_count": len(state["enhanced_modules"]),
            "submodule_title": submodule.title,
            "submodule_description": submodule.description,
            "submodule_order": submodule_id + 1,
            "submodule_count": len(module.submodules),
            "module_context": module_context,
            "adjacent_context": adjacent_context,
            "learning_path_context": learning_path_context,
            "search_results": formatted_results
        }
        
        submodule_content = await chain.ainvoke(invoke_params)
        
        # Validar el contenido recibido
        if not submodule_content:
            logger.error(f"LLM returned empty content for submodule {submodule_id + 1} of module {module_id + 1}")
            submodule_content = f"Error: No content was generated for {submodule.title}"
        else:
            logger.info(f"Developed content for submodule {submodule_id + 1} of module {module_id + 1}: {len(submodule_content)} characters")
            
            # Log a preview of the content
            content_preview = submodule_content[:200] + "..." if len(submodule_content) > 200 else submodule_content
            logger.debug(f"Content preview: {content_preview}")
            
            # Ensure the content is stored as a string
            if not isinstance(submodule_content, str):
                logger.warning(f"Content is not a string, converting from {type(submodule_content).__name__}")
                submodule_content = str(submodule_content)
        
        return submodule_content
    except Exception as e:
        logger.exception(f"Error developing submodule content: {str(e)}")
        return f"Error developing content: {str(e)}"

async def finalize_enhanced_learning_path(state: LearningPathState) -> Dict[str, Any]:
    """
    Create the final enhanced learning path with all developed submodules.
    """
    logger = logging.getLogger("learning_path.finalizer")
    logger.info("Finalizing enhanced learning path with submodules")
    
    try:
        from log_config import log_debug_data, log_info_data
        
        log_debug_data(logger, "State at finalization", {
            "state_keys": list(state.keys()),
            "developed_submodules_count": len(state.get("developed_submodules", [])),
            "enhanced_modules_count": len(state.get("enhanced_modules", []))
        })
        
        if not state.get("developed_submodules"):
            logger.warning("No developed submodules available")
            return {
                "final_learning_path": {
                    "topic": state["user_topic"],
                    "modules": []
                },
                "steps": ["No submodules were developed"]
            }
        
        # Log detailed information about developed submodules
        for i, submodule in enumerate(state["developed_submodules"]):
            logger.debug(f"Submodule {i+1} details:")
            logger.debug(f"  Module ID: {submodule.module_id}")
            logger.debug(f"  Submodule ID: {submodule.submodule_id}")
            logger.debug(f"  Title: {submodule.title}")
            logger.debug(f"  Content length: {len(submodule.content) if hasattr(submodule, 'content') and submodule.content else 0}")
        
        # Organize submodules by module_id
        module_to_submodules = {}
        for submodule in state["developed_submodules"]:
            module_to_submodules.setdefault(submodule.module_id, []).append(submodule)
        
        # Sort submodules within each module by submodule_id
        for module_id in module_to_submodules:
            module_to_submodules[module_id].sort(key=lambda s: s.submodule_id)
        
        log_debug_data(logger, "Organized submodules by module", {
            module_id: [sub.submodule_id for sub in subs] 
            for module_id, subs in module_to_submodules.items()
        })
        
        # Build the final modules structure
        final_modules = []
        for module_id, module in enumerate(state["enhanced_modules"]):
            module_submodules = module_to_submodules.get(module_id, [])
            
            # Log detailed information about each submodule in this module
            logger.debug(f"Building final data for module {module_id}: {module.title}")
            logger.debug(f"Found {len(module_submodules)} submodules for this module")
            
            submodule_data = []
            for sub in module_submodules:
                sub_content = sub.content if hasattr(sub, 'content') and sub.content else ""
                
                # Log detailed content info for debugging
                content_preview = sub_content[:100] + "..." if sub_content and len(sub_content) > 100 else sub_content
                logger.debug(f"  Submodule {sub.submodule_id + 1}: {sub.title}")
                logger.debug(f"    Content preview: {content_preview}")
                logger.debug(f"    Content length: {len(sub_content)}")
                
                submodule_data.append({
                    "id": sub.submodule_id,
                    "title": sub.title,
                    "description": sub.description,
                    "content": sub_content,
                    "order": sub.submodule_id + 1
                })
            
            # Check for any issues with submodule data
            for s_data in submodule_data:
                if not s_data.get("content"):
                    logger.warning(f"Missing content in submodule {s_data.get('id')} '{s_data.get('title')}' of module {module_id}")
            
            # Add completed module to final structure
            final_modules.append({
                "id": module_id,
                "title": module.title,
                "description": module.description,
                "submodules": submodule_data
            })
        
        # Create final learning path structure
        final_learning_path = {
            "topic": state["user_topic"],
            "modules": final_modules,
            "execution_steps": state["steps"]
        }
        
        # Log summary information
        total_submodules = sum(len(module.get("submodules", [])) for module in final_modules)
        logger.info(f"Finalized enhanced learning path with {len(final_modules)} modules and {total_submodules} submodules")
        
        # Log the complete structure for debugging
        log_info_data(logger, "Final learning path structure", final_learning_path)
        
        # Special log for monitoring submodule content
        for i, module in enumerate(final_modules):
            for j, submodule in enumerate(module.get("submodules", [])):
                content_length = len(submodule.get("content", ""))
                if content_length == 0:
                    logger.error(f"CONTENT MISSING: Module {i+1}, Submodule {j+1}: {submodule.get('title')}")
                else:
                    logger.info(f"Content available for Module {i+1}, Submodule {j+1}: {content_length} characters")
        
        if state.get("progress_callback"):
            await state["progress_callback"](f"Finalized learning path with {len(final_modules)} modules and {total_submodules} submodules")
        
        return {
            "final_learning_path": final_learning_path,
            "steps": ["Finalized enhanced learning path with submodules"]
        }
    except Exception as e:
        logger.exception(f"Error finalizing learning path: {str(e)}")
        return {
            "final_learning_path": {
                "topic": state["user_topic"],
                "modules": [],
                "error": str(e)
            },
            "steps": [f"Error finalizing learning path: {str(e)}"]
        }

# -----------------------------
# Conditional Helper Functions
# -----------------------------

def check_batch_processing(state: LearningPathState) -> str:
    """
    Check if all module batches are processed.
    """
    if state["current_batch_index"] is not None and state["module_batches"] is not None:
        return "all_batches_processed" if state["current_batch_index"] >= len(state["module_batches"]) else "continue_processing"
    return "continue_processing"

def check_submodule_batch_processing(state: LearningPathState) -> str:
    """
    Check if all submodule batches are processed.
    """
    if state["current_submodule_batch_index"] is not None and state["submodule_batches"] is not None:
        return "all_batches_processed" if state["current_submodule_batch_index"] >= len(state["submodule_batches"]) else "continue_processing"
    return "continue_processing"
