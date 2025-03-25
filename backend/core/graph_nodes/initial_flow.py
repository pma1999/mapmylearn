import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import HumanMessage

from backend.models.models import SearchQuery, LearningPathState
from backend.parsers.parsers import search_queries_parser, enhanced_modules_parser
from backend.services.services import get_llm, get_search_tool
from langchain_core.prompts import ChatPromptTemplate

from backend.core.graph_nodes.helpers import run_chain, batch_items, format_search_results, escape_curly_braces

async def execute_single_search(query: SearchQuery, key_provider = None) -> Dict[str, Any]:
    """
    Executes a single web search using the Perplexity LLM.
    
    Args:
        query: A SearchQuery instance with keywords and rationale.
        key_provider: Optional key provider for Perplexity search.
        
    Returns:
        A dictionary with the query, rationale, and search results.
    """
    try:
        # Properly await the async function
        search_model = await get_search_tool(key_provider=key_provider)
        logging.info(f"Searching for: {query.keywords}")
        
        # Create a prompt that asks for web search results
        search_prompt = f"{query.keywords}"
        
        # Invoke the Perplexity model with the search prompt as a string
        # Use ainvoke instead of invoke to properly leverage async execution
        result = await search_model.ainvoke(search_prompt)
        
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

async def generate_search_queries(state: LearningPathState) -> Dict[str, Any]:
    """
    Generates optimal search queries for the user topic using an LLM chain.
    
    Args:
        state: The current LearningPathState with 'user_topic'.
        
    Returns:
        A dictionary containing the generated search queries and a list of execution steps.
    """
    logging.info(f"Generating search queries for topic: {state['user_topic']}")
    
    # Send progress update if callback is available
    progress_callback = state.get('progress_callback')
    if progress_callback:
        # Use enhanced progress update with phase information
        await progress_callback(
            f"Analyzing topic '{state['user_topic']}' to generate optimal search queries...",
            phase="search_queries",
            phase_progress=0.1,
            overall_progress=0.2,
            action="processing"
        )
    
    # Get language information from state
    output_language = state.get('language', 'en')
    search_language = state.get('search_language', 'en')
    
    prompt_text = """
# EXPERT TEACHING ASSISTANT INSTRUCTIONS

Your task is to analyze a learning topic and generate optimal search queries to gather comprehensive information.

## TOPIC ANALYSIS

Please analyze the topic "{user_topic}" thoroughly:

### CORE CONCEPT IDENTIFICATION
- Primary concepts that form the foundation
- Supporting concepts necessary for understanding
- Advanced concepts that build on the basics
- Practical applications and implications
- Tools, methodologies, or frameworks involved

### KNOWLEDGE STRUCTURE MAPPING
- Fundamental principles and theories
- Key relationships and dependencies
- Historical or contextual elements
- Current state and developments
- Future implications or trends

### COMPLEXITY LAYERS
- Basic principles and definitions
- Intermediate concepts and applications
- Advanced theories and implementations
- Expert-level considerations
- Cross-domain connections

## LANGUAGE INSTRUCTIONS
- Generate all of your analysis and responses in {output_language}.
- For search queries, use {search_language} to maximize the quality and quantity of information retrieved.

## SEARCH STRATEGY

Based on this analysis, generate 5 search queries that will:
1. Cover different critical aspects of the topic
2. Address various complexity levels
3. Explore diverse perspectives and applications
4. Ensure comprehensive understanding
5. Target high-quality educational content

For each search query:
- Make it specific and targeted
- Explain why this search is essential for understanding the topic
- Ensure it addresses a different aspect of the topic
- Design it to return high-quality educational content

Your response should be exactly 5 search queries, each with its detailed rationale.

{format_instructions}
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    try:
        # Get Google key provider from state
        google_key_provider = state.get("google_key_provider")
        if not google_key_provider:
            logging.warning("Google key provider not found in state, this may cause errors")
        else:
            logging.debug("Found Google key provider in state, using for search query generation")
            
        # Send progress update with more details
        if progress_callback:
            await progress_callback(
                "Analyzing topic with AI to identify key concepts, knowledge structure, and complexity layers...",
                phase="search_queries",
                phase_progress=0.3, 
                overall_progress=0.22,
                action="processing"
            )
            
        result = await run_chain(prompt, lambda: get_llm(key_provider=google_key_provider), search_queries_parser, {
            "user_topic": state["user_topic"],
            "output_language": output_language,
            "search_language": search_language,
            "format_instructions": search_queries_parser.get_format_instructions()
        })
        search_queries = result.queries
        logging.info(f"Generated {len(search_queries)} search queries")
        
        # Prepare preview data for frontend display
        preview_data = {
            "search_queries": [query.keywords for query in search_queries]
        }
        
        # Send progress update about completion with preview data
        if progress_callback:
            await progress_callback(
                f"Generated {len(search_queries)} search queries for topic '{state['user_topic']}'",
                phase="search_queries",
                phase_progress=1.0,
                overall_progress=0.25,
                preview_data=preview_data,
                action="completed"
            )
        
        return {
            "search_queries": search_queries,
            "steps": [f"Generated {len(search_queries)} search queries for topic: {state['user_topic']}"]
        }
    except Exception as e:
        logging.error(f"Error generating search queries: {str(e)}")
        
        # Send error progress update
        if progress_callback:
            await progress_callback(
                f"Error generating search queries: {str(e)}",
                phase="search_queries",
                phase_progress=0.5,
                overall_progress=0.2,
                action="error"
            )
            
        return {"search_queries": [], "steps": [f"Error: {str(e)}"]}

async def execute_web_searches(state: LearningPathState) -> Dict[str, Any]:
    """
    Execute web searches for each search query in parallel.
    """
    if not state.get("search_queries"):
        logging.info("No search queries to execute")
        return {
            "search_results": [],
            "steps": state.get("steps", []) + ["No search queries to execute"]
        }
    
    search_queries = state["search_queries"]
    
    # Get the Perplexity key provider from state
    pplx_key_provider = state.get("pplx_key_provider")
    if not pplx_key_provider:
        logging.warning("Perplexity key provider not found in state, this may cause errors")
    else:
        logging.debug("Found Perplexity key provider in state, using for web searches")
    
    # Set up parallel processing based on user configuration
    search_parallel_count = state.get("search_parallel_count", 3)
    logging.info(f"Executing {len(search_queries)} web searches with parallelism of {search_parallel_count}")
    
    # Send progress update if callback is available
    progress_callback = state.get('progress_callback')
    if progress_callback:
        # Enhanced progress update with phase information
        await progress_callback(
            f"Executing {len(search_queries)} web searches in parallel (max {search_parallel_count} at a time)...",
            phase="web_searches",
            phase_progress=0.0,
            overall_progress=0.25,
            preview_data={"search_queries": [query.keywords for query in search_queries]},
            action="started"
        )
    
    all_results = []
    
    try:
        # Create a semaphore to limit concurrency based on search_parallel_count
        sem = asyncio.Semaphore(search_parallel_count)
        
        async def bounded_search(query):
            async with sem:  # This ensures we only run search_parallel_count queries at a time
                return await execute_single_search(query, key_provider=pplx_key_provider)
        
        # Create tasks for all searches but bounded by the semaphore
        tasks = [bounded_search(query) for query in search_queries]
        
        # Send additional progress update
        if progress_callback and len(tasks) > 0:
            await progress_callback(
                f"Searching for information on '{search_queries[0].keywords}'...",
                phase="web_searches",
                phase_progress=0.1,
                overall_progress=0.27,
                action="processing"
            )
        
        # Run all the searches in parallel with bounded concurrency
        completed = 0
        total = len(tasks)
        
        for i, future in enumerate(asyncio.as_completed(tasks)):
            result = await future
            all_results.append(result)
            completed += 1
            
            # Send incremental progress updates
            if progress_callback and i < len(search_queries):
                phase_progress = min(1.0, completed / total)
                overall_progress = 0.25 + (phase_progress * 0.15)  # web searches are 15% of overall process
                
                # Create preview data from the first result
                preview_data = {}
                if result and "query" in result:
                    preview_data = {
                        "search_queries": [q.keywords for q in search_queries[:i+1]],
                        "current_search": {
                            "query": result.get("query", ""),
                            "completed": completed,
                            "total": total
                        }
                    }
                
                # Only send detailed updates for every other completion to avoid flooding
                if i % 2 == 0 or i == len(search_queries) - 1:
                    next_idx = min(i + 1, len(search_queries) - 1)
                    next_message = f"Completed {completed}/{total} searches. "
                    if next_idx < len(search_queries):
                        next_message += f"Searching for '{search_queries[next_idx].keywords}'..."
                    
                    await progress_callback(
                        next_message,
                        phase="web_searches",
                        phase_progress=phase_progress,
                        overall_progress=overall_progress,
                        preview_data=preview_data,
                        action="processing"
                    )
        
        # Process results and handle any exceptions
        for i, result in enumerate(all_results):
            if isinstance(result, Exception):
                logging.error(f"Error executing search: {str(result)}")
                # Add a placeholder for failed searches
                all_results[i] = {
                    "query": search_queries[i].keywords,
                    "rationale": search_queries[i].rationale,
                    "results": [{"source": "Error", "content": f"Error executing search: {str(result)}"}],
                    "error": str(result)
                }
        
        logging.info(f"Completed {len(all_results)} web searches in parallel")
        
        # Send progress update with completion information
        if progress_callback:
            await progress_callback(
                f"Completed all {len(all_results)} web searches in parallel",
                phase="web_searches",
                phase_progress=1.0,
                overall_progress=0.4,
                preview_data={"search_queries": [q.keywords for q in search_queries]},
                action="completed"
            )
        
        return {
            "search_results": all_results,
            "steps": state.get("steps", []) + [f"Executed {len(all_results)} web searches in parallel"]
        }
    except Exception as e:
        logging.exception(f"Error executing web searches: {str(e)}")
        
        # Send error progress update
        if progress_callback:
            await progress_callback(
                f"Error executing web searches: {str(e)}",
                phase="web_searches",
                phase_progress=0.5,  # partial progress
                overall_progress=0.3,
                action="error"
            )
            
        return {
            "search_results": all_results,
            "steps": state.get("steps", []) + [f"Error executing web searches: {str(e)}"]
        }

async def create_learning_path(state: LearningPathState) -> Dict[str, Any]:
    """
    Create a structured learning path from search results.
    """
    if not state.get("search_results") or len(state["search_results"]) == 0:
        logging.info("No search results available")
        return {
            "modules": [],
            "final_learning_path": {
                "topic": state["user_topic"],
                "modules": []
            },
            "steps": state.get("steps", []) + ["No search results available"]
        }
    
    # Get the Google key provider from state
    google_key_provider = state.get("google_key_provider")
    if not google_key_provider:
        logging.warning("Google key provider not found in state, this may cause errors")
    else:
        logging.debug("Found Google key provider in state, using for learning path creation")
    
    # Get language information from state
    output_language = state.get('language', 'en')
    
    # Send progress update if callback is available
    progress_callback = state.get('progress_callback')
    if progress_callback:
        # Enhanced progress update with phase information
        await progress_callback(
            f"Creating initial learning path structure for '{state['user_topic']}'...",
            phase="modules",
            phase_progress=0.0,
            overall_progress=0.4,
            action="started"
        )
    
    try:
        # Procesar los resultados de búsqueda para generar módulos
        processed_results = []
        for result in state["search_results"]:
            # Escapar las llaves en la consulta
            query = escape_curly_braces(result.get("query", "Unknown query"))
            raw_results = result.get("results", [])
            # Comprobar que raw_results es una lista
            if not isinstance(raw_results, list):
                logging.warning(f"Search results for query '{query}' is not a list; skipping this result.")
                continue
            if not raw_results:
                continue
                
            relevant_info = []
            for item in raw_results[:3]:  # Limitar a los 3 mejores resultados por búsqueda
                # Escapar las llaves en la fuente y el contenido
                source = escape_curly_braces(item.get('source', 'Unknown'))
                content = escape_curly_braces(item.get('content', 'No content'))
                relevant_info.append(f"Source: {source}\n{content}")
            
            processed_results.append({
                "query": query,
                "relevant_information": "\n\n".join(relevant_info)
            })
        
        # Update progress after processing search results
        if progress_callback:
            await progress_callback(
                "Analyzing search results to identify key concepts and learning structure...",
                phase="modules",
                phase_progress=0.3,
                overall_progress=0.45,
                action="processing"
            )
            
        # Convertir los resultados procesados a texto para incluir en el prompt
        results_text = ""
        for i, result in enumerate(processed_results, 1):
            results_text += f"""
Search {i}: "{result['query']}"
{result['relevant_information']}
---
"""
        # Check if a specific number of modules was requested
        module_count_instruction = ""
        if state.get("desired_module_count"):
            module_count_instruction = f"\nIMPORTANT: Create EXACTLY {state['desired_module_count']} modules for this learning path. Not more, not less."
        else:
            module_count_instruction = "\nCreate a structured learning path with 3-7 modules."
        
        # Add language instruction
        language_instruction = f"\nIMPORTANT: Create all content in {output_language}. All titles, descriptions, and content must be written in {output_language}."
        
        # Update progress with AI generation status
        if progress_callback:
            await progress_callback(
                "Designing logical learning progression and module structure based on topic analysis...",
                phase="modules",
                phase_progress=0.6,
                overall_progress=0.5,
                action="processing"
            )
        
        # Escapar las llaves en el tema del usuario
        escaped_topic = escape_curly_braces(state["user_topic"])
        
        # Preparar el prompt con un placeholder para format_instructions
        prompt_text = f"""
You are an expert curriculum designer. Create a comprehensive learning path for the topic: {escaped_topic}.

Based on the following search results, organize the learning into logical modules:

{results_text}
{module_count_instruction}{language_instruction} For each module:
1. Give it a clear, descriptive title
2. Write a comprehensive overview (100-200 words)
3. Identify 3-5 key learning objectives
4. Explain why this module is important in the overall learning journey

Format your response as a structured curriculum. Each module should build on previous knowledge.

{{format_instructions}}
"""
        # Crear la plantilla de prompt
        prompt = ChatPromptTemplate.from_template(prompt_text)
        
        # Llamar a la cadena LLM proporcionando el valor para 'format_instructions'
        result = await run_chain(
            prompt,
            lambda: get_llm(key_provider=google_key_provider),
            enhanced_modules_parser,
            { "format_instructions": enhanced_modules_parser.get_format_instructions() }
        )
        modules = result.modules
        
        # If a specific number of modules was requested but not achieved, log a warning
        if state.get("desired_module_count") and len(modules) != state["desired_module_count"]:
            logging.warning(f"Requested {state['desired_module_count']} modules but got {len(modules)}")
            if len(modules) > state["desired_module_count"]:
                # Trim excess modules if we got too many
                modules = modules[:state["desired_module_count"]]
                logging.info(f"Trimmed modules to match requested count of {state['desired_module_count']}")
        
        # Crear la estructura final del learning path
        final_learning_path = {
            "topic": state["user_topic"],
            "modules": modules,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "num_modules": len(modules)
            }
        }
        
        logging.info(f"Created learning path with {len(modules)} modules")
        
        # Prepare preview data for frontend display
        preview_modules = []
        for module in modules:
            preview_modules.append({
                "title": module.title,
                "description": module.description[:150] + "..." if len(module.description) > 150 else module.description
            })
            
        preview_data = {
            "modules": preview_modules
        }
        
        # Send progress update with information about the created modules and preview data
        if progress_callback and 'modules' in final_learning_path:
            module_count = len(final_learning_path['modules'])
            await progress_callback(
                f"Created initial learning path with {module_count} modules",
                phase="modules",
                phase_progress=1.0,
                overall_progress=0.55,
                preview_data=preview_data,
                action="completed"
            )
        
        return {
            "modules": modules,
            "final_learning_path": final_learning_path,
            "steps": state.get("steps", []) + [f"Created learning path with {len(modules)} modules"]
        }
    except Exception as e:
        logging.exception(f"Error creating learning path: {str(e)}")
        
        # Send error progress update
        if progress_callback:
            await progress_callback(
                f"Error creating learning path: {str(e)}",
                phase="modules",
                phase_progress=0.5,
                overall_progress=0.45,
                action="error"
            )
        
        return {
            "modules": [],
            "final_learning_path": {
                "topic": state["user_topic"],
                "modules": []
            },
            "steps": state.get("steps", []) + [f"Error creating learning path: {str(e)}"]
        }
