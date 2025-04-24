import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage
import os

from backend.models.models import SearchQuery, LearningPathState, SearchServiceResult, ScrapedResult
from backend.parsers.parsers import search_queries_parser, enhanced_modules_parser
from backend.services.services import get_llm, perform_search_and_scrape
from langchain_core.prompts import ChatPromptTemplate

from backend.core.graph_nodes.helpers import run_chain, batch_items, format_search_results, escape_curly_braces, MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT
from backend.core.graph_nodes.search_utils import execute_search_with_llm_retry

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
# EXPERT LEARNING PATH ARCHITECT INSTRUCTIONS

Your task is to design optimal search queries that will retrieve information specifically for structuring a comprehensive learning path on "{user_topic}".

## LEARNING PATH DESIGN FOCUS

These searches are NOT for content development, but specifically for determining the optimal STRUCTURE and ORGANIZATION of the learning path.

## TOPIC ANALYSIS

Analyze the topic "{user_topic}" to identify key structural components:

### STRUCTURAL ELEMENTS
- Essential knowledge domains and sub-domains
- Natural progression and prerequisites 
- Critical learning milestones
- Logical teaching sequence
- Different skill/proficiency levels (beginner to expert)

### EDUCATIONAL FRAMEWORK
- Pedagogical approaches specific to this topic
- Standard curriculum structures in this field
- Expert-recommended learning sequences
- Typical module organization in courses/tutorials
- Academic vs practical learning progressions

### SCOPE AND BOUNDARIES
- Core vs peripheral concepts
- Essential vs optional topics
- Foundational prerequisites
- Advanced specializations
- Interdisciplinary connections

## LANGUAGE INSTRUCTIONS
- Generate all of your analysis and responses in {output_language}.
- For search queries, use {search_language} to maximize retrieving high-quality curriculum design information.

## SEARCH STRATEGY

Design EXACTLY 5 search queries that will:
1. Retrieve information about optimal learning path structures for this topic
2. Discover how experts organize curriculum on this subject
3. Identify standard modules and their sequencing
4. Find information about pedagogical progressions specific to this topic
5. Uncover recommended learning sequences and prerequisites

For each search query:
- Make it specific to retrieving STRUCTURAL and ORGANIZATIONAL information. These queries should NOT search for HOW TO DO {user_topic}, but HOW TO STRUCTURE THE LEARNING of {user_topic}.
- Focus on curriculum design, learning path structure, and module organization.
- Target educational resources, discussions, or examples that reveal how knowledge in this domain is best structured (e.g., syllabi, course outlines, pedagogical guides).
- Consider terms like: 'curriculum design {user_topic}', 'learning path structure {user_topic}', 'module sequence {user_topic}', 'pedagogical framework {user_topic}', 'skill progression {user_topic}', 'example syllabus {user_topic}', '{user_topic} prerequisites'.
- CRITICAL: Ensure each query balances specificity (finding CURRICULUM STRUCTURE info) with breadth (getting actual results). Avoid terms so specific they describe only a hypothetical course.
- QUOTE USAGE RULE: NEVER use more than ONE quoted phrase per query. Quotes are ONLY for essential multi-word concepts that MUST be searched together (e.g., "machine learning" if the topic is broad, or a specific framework name). DO NOT put quotes around every keyword. Combine specific structural terms without quotes.
    - BAD Example (Too many quotes): `"curriculum design" "machine learning" "module sequence" "prerequisites"`
    - GOOD Example (One quote): `"machine learning" curriculum design syllabus example`
    - GOOD Example (No quotes): `machine learning curriculum design module sequence prerequisites`
- Getting *some* relevant structural examples/discussions is ALWAYS better than getting *zero* results from excessive quoting.
- Explain precisely how this query will help determine the optimal modules and their sequence.

Your response should be exactly 5 search queries, each with a detailed rationale explaining how it contributes to creating the perfect learning path STRUCTURE.

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

async def regenerate_initial_structure_query(
    state: LearningPathState, 
    failed_query: SearchQuery
) -> SearchQuery:
    """
    Regenerates a search query for learning path structure after a "no results found" error.
    
    This function uses an LLM to create an alternative search query when the original
    structure-focused query returns no results. It provides the failed query as context
    and instructs the LLM to broaden or rephrase the search while maintaining focus on
    finding structural/organizational information.
    
    Args:
        state: The current LearningPathState with user_topic.
        failed_query: The SearchQuery object that failed to return results.
        
    Returns:
        A new SearchQuery object with an alternative query.
    """
    logging.info(f"Regenerating structure query after no results for: {failed_query.keywords}")
    
    # Get language information from state
    output_language = state.get('language', 'en')
    search_language = state.get('search_language', 'en')
    
    # Get Google key provider from state
    google_key_provider = state.get("google_key_provider")
    if not google_key_provider:
        logging.warning("Google key provider not found in state for query regeneration")
    
    prompt_text = """
# SEARCH QUERY RETRY SPECIALIST INSTRUCTIONS

The following search query returned NO RESULTS when searching for information about how to structure a learning path on "{user_topic}":

FAILED QUERY: {failed_query}

I need you to generate a DIFFERENT search query that is more likely to find results but still focused on retrieving STRUCTURAL and ORGANIZATIONAL information about learning this topic.

## ANALYSIS OF FAILED QUERY

Analyze why the previous query might have failed:
- Was it too specific with too many quoted terms?
- Did it use uncommon terminology or jargon?
- Was it too long or complex?
- Did it combine too many concepts that rarely appear together?

## NEW QUERY REQUIREMENTS

Create ONE alternative search query that:
1. Is BROADER or uses more common terminology
2. Maintains focus on curriculum design, learning path structure, and module organization
3. Uses fewer quoted phrases (one at most)
4. Is more likely to match existing educational content
5. Balances specificity (finding curriculum structure info) with generality (getting actual results)

## LANGUAGE INSTRUCTIONS
- Generate your analysis and response in {output_language}.
- For the search query, use {search_language} to maximize retrieving high-quality curriculum design information.

## QUERY FORMAT RULES
- CRITICAL: Ensure your new query is DIFFERENT from the failed one
- Fewer keywords is better than too many
- QUOTE USAGE RULE: NEVER use more than ONE quoted phrase. Quotes are ONLY for essential multi-word concepts
- Getting some relevant results is BETTER than getting zero results
- The query should still target STRUCTURAL information (how to organize learning), NOT just content about the topic

Your response should include just ONE search query and a brief rationale for why this query might work better.

{format_instructions}
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    try:
        result = await run_chain(prompt, lambda: get_llm(key_provider=google_key_provider), search_queries_parser, {
            "user_topic": state["user_topic"],
            "failed_query": failed_query.keywords,
            "output_language": output_language,
            "search_language": search_language,
            "format_instructions": search_queries_parser.get_format_instructions()
        })
        
        # Return just the first query from the result
        if result.queries and len(result.queries) > 0:
            logging.info(f"Successfully regenerated structure query: {result.queries[0].keywords}")
            return result.queries[0]
        else:
            logging.error("Query regeneration returned empty result")
            return None
    except Exception as e:
        logging.error(f"Error regenerating structure query: {str(e)}")
        return None

async def execute_web_searches(state: LearningPathState) -> Dict[str, Any]:
    """
    Execute web searches using Tavily and scrape results for each search query in parallel.
    """
    if not state.get("search_queries"):
        logging.info("No search queries to execute")
        return {
            "search_results": [],
            "steps": state.get("steps", []) + ["No search queries to execute"]
        }
    
    search_queries: List[SearchQuery] = state["search_queries"]
    
    # Get the Tavily key provider from state
    tavily_key_provider = state.get("tavily_key_provider")
    if not tavily_key_provider:
        # Critical error if no key provider is found for searching
        error_msg = "Tavily key provider not found in state. Cannot execute web searches."
        logging.error(error_msg)
        # Optionally send error progress update
        progress_callback = state.get('progress_callback')
        if progress_callback:
             await progress_callback(error_msg, phase="web_searches", action="error")
        # Return empty results or raise an exception depending on desired graph behavior
        return { 
            "search_results": [], 
            "steps": state.get("steps", []) + [error_msg] 
        } 
    else:
        logging.debug("Found Tavily key provider in state, using for web searches")
    
    # Set up parallel processing based on user configuration
    search_parallel_count = state.get("search_parallel_count", 3)
    # Get scrape timeout from env or default
    scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))
    # Get max results from env or default
    max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS", 5))
    
    logging.info(f"Executing {len(search_queries)} web searches (Tavily+Scrape) with parallelism={search_parallel_count}, max_results={max_results_per_query}, scrape_timeout={scrape_timeout}")
    
    # Send progress update if callback is available
    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Executing {len(search_queries)} web searches in parallel (max {search_parallel_count} at a time)...",
            phase="web_searches",
            phase_progress=0.0,
            overall_progress=0.25,
            preview_data={"search_queries": [query.keywords for query in search_queries]},
            action="started"
        )
    
    all_search_service_results: List[SearchServiceResult] = [] # Store results of the new type
    
    try:
        # Create a semaphore to limit concurrency
        sem = asyncio.Semaphore(search_parallel_count)
        
        async def bounded_search_with_retry(query_obj: SearchQuery):
            async with sem:
                # Set operation name for tracking
                provider = tavily_key_provider.set_operation("initial_web_search")
                
                # Use the new function with retry capability
                return await execute_search_with_llm_retry(
                    state=state,
                    initial_query=query_obj,
                    regenerate_query_func=regenerate_initial_structure_query,
                    max_retries=1,
                    tavily_key_provider=provider,
                    search_config={
                        "max_results": max_results_per_query,
                        "scrape_timeout": scrape_timeout
                    }
                )
        
        # Create tasks for all searches
        tasks = [bounded_search_with_retry(query) for query in search_queries]
        
        if progress_callback and len(tasks) > 0:
            await progress_callback(
                f"Searching & scraping for: '{search_queries[0].keywords}'...",
                phase="web_searches",
                phase_progress=0.1,
                overall_progress=0.27,
                action="processing"
            )
        
        # Run all tasks in parallel with bounded concurrency
        completed = 0
        total = len(tasks)
        
        for i, future in enumerate(asyncio.as_completed(tasks)):
            scrape_errors = [] # Initialize scrape_errors before try block
            try:
                # Get the result (SearchServiceResult object)
                result: SearchServiceResult = await future
                all_search_service_results.append(result)
                completed += 1
                current_query_keywords = search_queries[i].keywords # Get keywords from original list by index
                
                # Log search provider errors if any
                if result.search_provider_error:
                    logging.error(f"Search provider error for query '{current_query_keywords}': {result.search_provider_error}")
                # Log summary of scrape errors
                scrape_errors = [r.scrape_error for r in result.results if r.scrape_error]
                if scrape_errors:
                    logging.warning(f"Scraping issues for query '{current_query_keywords}': {len(scrape_errors)}/{len(result.results)} URLs failed. Errors: {scrape_errors[:2]}...") # Log first few errors
                
            except Exception as e:
                # Handle potential errors from the await future itself (e.g., task cancellation)
                query_keywords = search_queries[i].keywords
                logging.exception(f"Error processing search task for query '{query_keywords}': {e}")
                # Append a placeholder result indicating the task error
                all_search_service_results.append(
                    SearchServiceResult(
                        query=query_keywords,
                        results=[],
                        search_provider_error=f"Task execution error: {type(e).__name__} - {str(e)}"
                    )
                )
                # We count it as completed for progress purposes, even though it failed
                completed += 1
            
            # Send incremental progress updates
            if progress_callback and i < len(search_queries):
                phase_progress = min(1.0, completed / total)
                overall_progress = 0.25 + (phase_progress * 0.15) # web searches are 15% of overall process
                
                # Create preview data (show completed query)
                preview_data = {
                    "search_queries": [q.keywords for q in search_queries[:i+1]],
                    "current_search": {
                        "query": search_queries[i].keywords,
                        "completed": completed,
                        "total": total,
                        # Add info about scrape success/failure?
                        "scrape_status": f"{len(all_search_service_results[-1].results) - len(scrape_errors)}/{len(all_search_service_results[-1].results)} scraped" if all_search_service_results else "N/A"
                    }
                }
                
                # Throttle detailed updates
                if i % 2 == 0 or i == len(search_queries) - 1:
                    next_idx = min(i + 1, len(search_queries) - 1)
                    next_message = f"Completed {completed}/{total} searches. "
                    if completed < total and next_idx < len(search_queries):
                         next_message += f"Searching & scraping for '{search_queries[next_idx].keywords}'..."
                    
                    await progress_callback(
                        next_message,
                        phase="web_searches",
                        phase_progress=phase_progress,
                        overall_progress=overall_progress,
                        preview_data=preview_data,
                        action="processing"
                    )
        
        logging.info(f"Completed {len(all_search_service_results)} web searches (Tavily+Scrape)")
        
        if progress_callback:
            await progress_callback(
                f"Completed all {len(all_search_service_results)} web searches",
                phase="web_searches",
                phase_progress=1.0,
                overall_progress=0.4,
                preview_data={"search_queries": [q.keywords for q in search_queries]},
                action="completed"
            )
        
        return {
            "search_results": all_search_service_results, # Return the list of SearchServiceResult objects
            "steps": state.get("steps", []) + [f"Executed {len(all_search_service_results)} web searches (Tavily+Scrape)"]
        }
    except Exception as e:
        # Catch errors during task setup or semaphore handling
        logging.exception(f"Error setting up or running web search tasks: {str(e)}")
        if progress_callback:
            await progress_callback(
                f"Error during web searches setup: {str(e)}",
                phase="web_searches",
                phase_progress=0.5,
                overall_progress=0.3,
                action="error"
            )
        return {
            "search_results": all_search_service_results, # Return whatever was collected
            "steps": state.get("steps", []) + [f"Error executing web searches setup: {str(e)}"]
        }

async def create_learning_path(state: LearningPathState) -> Dict[str, Any]:
    """
    Create a structured learning path from the scraped search results.
    """
    # Type hint for clarity
    search_service_results: Optional[List[SearchServiceResult]] = state.get("search_results")

    if not search_service_results or len(search_service_results) == 0:
        logging.info("No search results available to create learning path")
        return {
            "modules": [],
            "final_learning_path": {
                "topic": state["user_topic"],
                "modules": []
            },
            "steps": state.get("steps", []) + ["No search results available to create learning path"]
        }

    # Get Google key provider from state
    google_key_provider = state.get("google_key_provider")
    if not google_key_provider:
        logging.warning("Google key provider not found in state, using env fallback if available for LLM")
    else:
        logging.debug("Found Google key provider in state, using for learning path creation")

    # Get language information from state
    output_language = state.get('language', 'en')

    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Creating initial learning path structure for '{state['user_topic']}'...",
            phase="modules",
            phase_progress=0.0,
            overall_progress=0.4,
            action="started"
        )

    try:
        # Process the new search results structure for the LLM prompt
        context_parts = []
        max_context_per_query = 5 # Limit number of results per query used in context

        for report in search_service_results:
            query = escape_curly_braces(report.query)
            context_parts.append(f"\n## Search Results for Query: \"{query}\"\n")

            results_included = 0
            for res in report.results:
                if results_included >= max_context_per_query:
                    break

                title = escape_curly_braces(res.title or 'N/A')
                url = res.url # URLs are usually safe
                context_parts.append(f"### Result from: {url} (Title: {title})")

                if res.scraped_content:
                    content = escape_curly_braces(res.scraped_content)
                    truncated_content = content[:MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT]
                    if len(content) > MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT:
                        truncated_content += "... (truncated)"
                    context_parts.append(f"Scraped Content Snippet:\n{truncated_content}")
                    results_included += 1
                elif res.tavily_snippet:
                    snippet = escape_curly_braces(res.tavily_snippet)
                    error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                    truncated_snippet = snippet[:MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT]
                    if len(snippet) > MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT:
                         truncated_snippet += "... (truncated)"
                    context_parts.append(f"Tavily Snippet:{error_info}\n{truncated_snippet}")
                    results_included += 1
                else:
                     # If scrape failed and no snippet, mention the failure
                     error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                     context_parts.append(f"Content: Not available.{error_info}")
                     # Optionally decide if this counts towards max_context_per_query

                context_parts.append("---")
            if results_included == 0:
                 context_parts.append("(No usable content found for this query)")

        results_text = "\n".join(context_parts)

        # Check if a specific number of modules was requested
        module_count_instruction = ""
        if state.get("desired_module_count"):
            module_count_instruction = f"\nIMPORTANT: Create EXACTLY {state['desired_module_count']} modules for this learning path. Not more, not less."
        else:
            module_count_instruction = "\nCreate a structured learning path with 3-7 modules."

        # Add language instruction
        language_instruction = f"\nIMPORTANT: Create all content in {output_language}. All titles, descriptions, and content must be written in {output_language}."

        if progress_callback:
            await progress_callback(
                "Analyzing search results and scraped content to identify key concepts and learning structure...",
                phase="modules",
                phase_progress=0.3,
                overall_progress=0.45,
                action="processing"
            )

        escaped_topic = escape_curly_braces(state["user_topic"])

        # Update prompt to mention scraped content
        prompt_text = f"""
You are an expert curriculum designer. Create a comprehensive learning path for the topic: {escaped_topic}.

Based on the following search results and scraped web content snippets, organize the learning into logical modules:
{results_text}
{module_count_instruction}{language_instruction}

For each module:
1. Give it a clear, descriptive title.
2. Write a comprehensive overview (100-200 words) summarizing the module's purpose and content.
3. Identify 3-5 key learning objectives (action-oriented).
4. Explain why this module is important in the overall learning journey and how it connects to other modules.

Format your response as a structured curriculum. Each module should build logically on previous knowledge.

{{format_instructions}}
"""
        prompt = ChatPromptTemplate.from_template(prompt_text)

        result = await run_chain(
            prompt,
            lambda: get_llm(key_provider=google_key_provider),
            enhanced_modules_parser,
            { "format_instructions": enhanced_modules_parser.get_format_instructions() }
        )
        modules = result.modules

        if state.get("desired_module_count") and len(modules) != state["desired_module_count"]:
            logging.warning(f"Requested {state['desired_module_count']} modules but got {len(modules)}. Trimming/padding may occur.")
            if len(modules) > state["desired_module_count"]:
                modules = modules[:state["desired_module_count"]]
            # Padding is harder, let the LLM handle it ideally

        final_learning_path = {
            "topic": state["user_topic"],
            "modules": modules,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "num_modules": len(modules)
            }
        }

        logging.info(f"Created learning path structure with {len(modules)} modules")

        preview_modules = []
        for module in modules:
            preview_modules.append({
                "title": module.title,
                "description": module.description[:150] + "..." if len(module.description) > 150 else module.description
            })

        preview_data = {
            "modules": preview_modules
        }

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
            "steps": state.get("steps", []) + [f"Created learning path structure with {len(modules)} modules"]
        }
    except Exception as e:
        logging.exception(f"Error creating learning path: {str(e)}")
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
