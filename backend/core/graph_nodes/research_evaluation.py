"""
Research evaluation functionality for the learning path generation process.

This module implements a self-reflection loop following the Google research pattern,
allowing the system to evaluate the quality and completeness of initial research
and iteratively refine it until sufficient information is gathered for course creation.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional

from backend.models.models import (
    LearningPathState, 
    SearchQuery, 
    SearchServiceResult,
    ResearchEvaluation,
    RefinementQueryList
)
from backend.parsers.parsers import research_evaluation_parser, refinement_query_parser
from backend.services.services import get_llm, get_llm_for_evaluation, execute_search_with_router
from langchain_core.prompts import ChatPromptTemplate
from backend.core.graph_nodes.helpers import run_chain, escape_curly_braces, MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT
from backend.core.graph_nodes.search_utils import execute_search_with_llm_retry

# Configure logger
logger = logging.getLogger("learning_path.research_evaluation")

async def evaluate_research_sufficiency(state: LearningPathState) -> Dict[str, Any]:
    """
    Evaluates if the current research is sufficient for generating a high-quality course.
    
    This function implements the core self-reflection mechanism following the Google pattern.
    It analyzes existing search results to determine if they provide adequate foundation
    for creating comprehensive learning modules.
    
    Args:
        state: Current LearningPathState containing search results and topic information
        
    Returns:
        Dictionary with evaluation results and updated loop tracking
    """
    # Increment research loop counter
    current_count = state.get('research_loop_count', 0) + 1
    logger.info(f"Starting research evaluation iteration {current_count} for topic: {state['user_topic']}")
    
    # Send progress update if callback is available
    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Evaluating research quality and completeness (iteration {current_count})...",
            phase="research_evaluation",
            phase_progress=0.1,
            overall_progress=0.35,
            action="processing"
        )
    
    try:
        # Analyze research completeness using LLM
        evaluation = await analyze_research_completeness(state)
        
        # Log evaluation results
        logger.info(f"Research evaluation {current_count} complete: sufficient={evaluation.is_sufficient}, "
                   f"confidence={evaluation.confidence_score:.2f}, gaps={len(evaluation.knowledge_gaps)}")
        
        # Prepare preview data for frontend
        preview_data = {
            "type": "research_evaluation",
            "data": {
                "iteration": current_count,
                "is_sufficient": evaluation.is_sufficient,
                "confidence_score": evaluation.confidence_score,
                "knowledge_gaps": evaluation.knowledge_gaps,
                "gap_count": len(evaluation.knowledge_gaps)
            }
        }
        
        # Send progress update with results
        if progress_callback:
            status_message = "Research deemed sufficient" if evaluation.is_sufficient else f"Identified {len(evaluation.knowledge_gaps)} knowledge gaps"
            await progress_callback(
                f"Research evaluation {current_count}: {status_message}",
                phase="research_evaluation",
                phase_progress=1.0,
                overall_progress=0.38,
                preview_data=preview_data,
                action="completed"
            )
        
        return {
            'research_loop_count': current_count,
            'is_research_sufficient': evaluation.is_sufficient,
            'research_knowledge_gaps': evaluation.knowledge_gaps,
            'research_confidence_score': evaluation.confidence_score,
            'steps': [f"Research evaluation {current_count}: {'Sufficient' if evaluation.is_sufficient else f'Needs refinement - {len(evaluation.knowledge_gaps)} gaps identified'}"]
        }
        
    except Exception as e:
        logger.exception(f"Error during research evaluation {current_count}: {str(e)}")
        
        # Send error progress update
        if progress_callback:
            await progress_callback(
                f"Error in research evaluation: {str(e)}",
                phase="research_evaluation",
                phase_progress=0.5,
                overall_progress=0.37,
                action="error"
            )
        
        # Return conservative result (not sufficient) to continue with fallback
        return {
            'research_loop_count': current_count,
            'is_research_sufficient': False,
            'research_knowledge_gaps': ["Error in evaluation - proceeding with additional research as precaution"],
            'research_confidence_score': 0.3,
            'steps': [f"Research evaluation {current_count} failed: {str(e)} - assuming insufficient"]
        }

async def generate_refinement_queries(state: LearningPathState) -> Dict[str, Any]:
    """
    Generates targeted search queries to address identified knowledge gaps.
    
    This function creates specific, focused queries designed to fill the gaps
    identified during research evaluation, following the Google refinement pattern.
    
    Args:
        state: Current LearningPathState with identified knowledge gaps
        
    Returns:
        Dictionary with generated refinement queries
    """
    knowledge_gaps = state.get('research_knowledge_gaps', [])
    current_count = state.get('research_loop_count', 0)
    
    logger.info(f"Generating refinement queries for {len(knowledge_gaps)} knowledge gaps")
    
    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Generating targeted queries to address {len(knowledge_gaps)} knowledge gaps...",
            phase="query_refinement",
            phase_progress=0.1,
            overall_progress=0.38,
            action="processing"
        )
    
    try:
        # Generate refinement queries using LLM
        refinement_result = await create_targeted_queries(
            state=state,
            knowledge_gaps=knowledge_gaps
        )
        
        generated_queries = refinement_result.queries
        logger.info(f"Generated {len(generated_queries)} refinement queries targeting knowledge gaps")
        
        # Prepare preview data
        preview_data = {
            "type": "refinement_queries",
            "data": {
                "query_count": len(generated_queries),
                "queries": [query.keywords for query in generated_queries],
                "targeting_strategy": refinement_result.targeting_strategy,
                "addressing_gaps": knowledge_gaps
            }
        }
        
        # Send progress update
        if progress_callback:
            await progress_callback(
                f"Generated {len(generated_queries)} targeted refinement queries",
                phase="query_refinement",
                phase_progress=1.0,
                overall_progress=0.39,
                preview_data=preview_data,
                action="completed"
            )
        
        return {
            'refinement_queries': generated_queries,
            'steps': [f"Generated {len(generated_queries)} refinement queries to address knowledge gaps"]
        }
        
    except Exception as e:
        logger.exception(f"Error generating refinement queries: {str(e)}")
        
        # Send error progress update
        if progress_callback:
            await progress_callback(
                f"Error generating refinement queries: {str(e)}",
                phase="query_refinement",
                phase_progress=0.5,
                overall_progress=0.385,
                action="error"
            )
        
        # Generate fallback queries based on gaps
        fallback_queries = await generate_fallback_refinement_queries(state, knowledge_gaps)
        
        return {
            'refinement_queries': fallback_queries,
            'steps': [f"Generated {len(fallback_queries)} fallback refinement queries due to error: {str(e)}"]
        }

async def execute_refinement_searches(state: LearningPathState) -> Dict[str, Any]:
    """
    Executes the refinement search queries to gather additional information.
    
    This function performs web searches using the generated refinement queries,
    following the same patterns as the initial search but focused on filling
    specific knowledge gaps.
    
    Args:
        state: Current LearningPathState with refinement queries to execute
        
    Returns:
        Dictionary with new search results (will be accumulated with existing ones)
    """
    refinement_queries = state.get('refinement_queries', [])
    current_count = state.get('research_loop_count', 0)
    
    if not refinement_queries:
        logger.warning("No refinement queries to execute")
        return {
            "search_results": [],
            "steps": ["No refinement queries to execute"]
        }
    
    logger.info(f"Executing {len(refinement_queries)} refinement searches (iteration {current_count})")
    
    # Get search configuration
    brave_key_provider = state.get("brave_key_provider")
    if not brave_key_provider:
        error_msg = "Brave key provider not found in state for refinement searches"
        logger.error(error_msg)
        return {
            "search_results": [],
            "steps": [error_msg]
        }
    
    search_parallel_count = state.get("search_parallel_count", 3)
    max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS", 5))
    scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))
    
    logger.info(f"Executing refinement searches with parallelism={search_parallel_count}, "
               f"max_results={max_results_per_query}, timeout={scrape_timeout}")
    
    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Executing {len(refinement_queries)} refinement searches to fill knowledge gaps...",
            phase="refinement_searches",
            phase_progress=0.0,
            overall_progress=0.39,
            preview_data={"refinement_queries": [q.keywords for q in refinement_queries]},
            action="started"
        )
    
    try:
        # Create semaphore for controlled concurrency
        sem = asyncio.Semaphore(search_parallel_count)
        
        async def bounded_refinement_search(query_obj: SearchQuery):
            async with sem:
                # Set operation name for tracking
                provider = brave_key_provider.set_operation("refinement_search")
                
                # Use the same retry mechanism as initial searches
                return await execute_search_with_llm_retry(
                    state=state,
                    initial_query=query_obj,
                    regenerate_query_func=regenerate_refinement_query,
                    search_provider_key_provider=provider,
                    search_config={
                        "max_results": max_results_per_query,
                        "scrape_timeout": scrape_timeout
                    }
                )
        
        # Execute all refinement searches in parallel
        tasks = [bounded_refinement_search(query) for query in refinement_queries]
        refinement_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        successful_results = []
        error_count = 0
        
        for i, result in enumerate(refinement_results):
            if isinstance(result, Exception):
                error_count += 1
                logger.error(f"Refinement search failed for query '{refinement_queries[i].keywords}': {str(result)}")
                # Create error placeholder result
                successful_results.append(SearchServiceResult(
                    query=refinement_queries[i].keywords,
                    results=[],
                    search_provider_error=f"Refinement search error: {str(result)}"
                ))
            else:
                successful_results.append(result)
                # Log any search provider errors
                if result.search_provider_error:
                    logger.warning(f"Search provider error for refinement query '{refinement_queries[i].keywords}': {result.search_provider_error}")
        
        success_count = len(successful_results) - error_count
        logger.info(f"Refinement searches completed: {success_count}/{len(refinement_queries)} successful")
        
        # Send progress update
        if progress_callback:
            preview_data = {
                "type": "refinement_search_results",
                "data": {
                    "successful_searches": success_count,
                    "total_searches": len(refinement_queries),
                    "error_count": error_count
                }
            }
            
            await progress_callback(
                f"Completed {success_count}/{len(refinement_queries)} refinement searches successfully",
                phase="refinement_searches",
                phase_progress=1.0,
                overall_progress=0.4,
                preview_data=preview_data,
                action="completed"
            )
        
        return {
            "search_results": successful_results,  # Will be accumulated with existing results
            "steps": [f"Executed {success_count}/{len(refinement_queries)} refinement searches successfully"]
        }
        
    except Exception as e:
        logger.exception(f"Error executing refinement searches: {str(e)}")
        
        if progress_callback:
            await progress_callback(
                f"Error executing refinement searches: {str(e)}",
                phase="refinement_searches",
                phase_progress=0.5,
                overall_progress=0.395,
                action="error"
            )
        
        return {
            "search_results": [],
            "steps": [f"Error executing refinement searches: {str(e)}"]
        }

def check_research_adequacy(state: LearningPathState) -> str:
    """
    Conditional function that determines whether to continue research loop or proceed to course creation.
    
    This function implements the decision logic following the Google pattern, checking both
    the sufficiency assessment and loop limits to prevent infinite iterations.
    
    Args:
        state: Current LearningPathState with evaluation results and loop tracking
        
    Returns:
        String indicating next node: "create_learning_path" or "generate_refinement_queries"
    """
    # Get loop control parameters
    max_loops = state.get('max_research_loops', 3)  # Default maximum loops
    current_count = state.get('research_loop_count', 0)
    is_sufficient = state.get('is_research_sufficient', False)
    confidence_score = state.get('research_confidence_score', 0.0)
    
    # Log decision factors
    logger.info(f"Research adequacy check: sufficient={is_sufficient}, confidence={confidence_score:.2f}, "
               f"iteration={current_count}/{max_loops}")
    
    # Decision logic following Google pattern
    if is_sufficient or current_count >= max_loops:
        if is_sufficient:
            logger.info(f"Research deemed sufficient after {current_count} iteration(s) - proceeding to course creation")
        else:
            logger.info(f"Research loop limit reached ({current_count}/{max_loops}) - proceeding to course creation with available information")
        
        return "create_learning_path"  # Continue with normal flow
    else:
        logger.info(f"Research insufficient - continuing to iteration {current_count + 1}/{max_loops}")
        return "generate_refinement_queries"  # Continue research loop

# Helper Functions

async def analyze_research_completeness(state: LearningPathState) -> ResearchEvaluation:
    """
    Analyzes the completeness and quality of current research using LLM evaluation.
    
    This function implements the core research evaluation logic, examining search results
    to determine if they provide sufficient foundation for course creation.
    """
    # Prepare context from search results
    search_results = state.get('search_results', [])
    search_context = format_search_results_for_evaluation(search_results)
    
    # Get language settings
    from backend.utils.language_utils import get_full_language_name
    output_language_code = state.get('language', 'en')
    output_language = get_full_language_name(output_language_code)
    
    # Import the prompt (will be defined in prompts file)
    from backend.prompts.learning_path_prompts import RESEARCH_EVALUATION_PROMPT
    
    prompt = ChatPromptTemplate.from_template(RESEARCH_EVALUATION_PROMPT)
    
    # Execute evaluation using LLM
    result = await run_chain(
        prompt,
        lambda: get_llm_for_evaluation(key_provider=state.get("google_key_provider"), user=state.get('user')),
        research_evaluation_parser,
        {
            "user_topic": escape_curly_braces(state["user_topic"]),
            "search_results_summary": search_context,
            "language": output_language,
            "format_instructions": research_evaluation_parser.get_format_instructions()
        }
    )
    
    return result

async def create_targeted_queries(state: LearningPathState, knowledge_gaps: List[str]) -> RefinementQueryList:
    """
    Creates targeted search queries to address specific knowledge gaps.
    
    This function generates focused queries designed to fill the identified gaps
    in the current research coverage.
    """
    # Get existing queries to avoid redundancy
    existing_queries = []
    if state.get('search_queries'):
        existing_queries = [q.keywords for q in state['search_queries']]
    
    # Get language settings
    from backend.utils.language_utils import get_full_language_name
    output_language_code = state.get('language', 'en')
    search_language_code = state.get('search_language', 'en')
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)
    
    # Import the prompt
    from backend.prompts.learning_path_prompts import REFINEMENT_QUERY_GENERATION_PROMPT
    
    prompt = ChatPromptTemplate.from_template(REFINEMENT_QUERY_GENERATION_PROMPT)
    
    # Generate refinement queries
    result = await run_chain(
        prompt,
        lambda: get_llm_for_evaluation(key_provider=state.get("google_key_provider"), user=state.get('user')),
        refinement_query_parser,
        {
            "user_topic": escape_curly_braces(state["user_topic"]),
            "knowledge_gaps": "\n".join([f"- {escape_curly_braces(gap)}" for gap in knowledge_gaps]),
            "existing_queries": "\n".join([f"- {escape_curly_braces(q)}" for q in existing_queries]),
            "language": output_language,
            "search_language": search_language,
            "format_instructions": refinement_query_parser.get_format_instructions()
        }
    )
    
    return result

async def generate_fallback_refinement_queries(state: LearningPathState, knowledge_gaps: List[str]) -> List[SearchQuery]:
    """
    Generates simple fallback refinement queries when the main generation fails.
    """
    user_topic = state.get("user_topic", "")
    
    # Create basic refinement queries targeting common knowledge areas
    fallback_queries = []
    
    for i, gap in enumerate(knowledge_gaps[:3]):  # Limit to first 3 gaps
        # Create simple queries based on gap and topic
        if "practical" in gap.lower() or "example" in gap.lower():
            query = SearchQuery(
                keywords=f"{user_topic} practical examples applications",
                rationale=f"Find practical examples to address gap: {gap}"
            )
        elif "advanced" in gap.lower() or "expert" in gap.lower():
            query = SearchQuery(
                keywords=f"{user_topic} advanced concepts expert level",
                rationale=f"Find advanced information to address gap: {gap}"
            )
        elif "fundamental" in gap.lower() or "basic" in gap.lower():
            query = SearchQuery(
                keywords=f"{user_topic} fundamentals basic concepts",
                rationale=f"Find fundamental concepts to address gap: {gap}"
            )
        else:
            query = SearchQuery(
                keywords=f"{user_topic} comprehensive overview detailed",
                rationale=f"Find comprehensive information to address gap: {gap}"
            )
        
        fallback_queries.append(query)
    
    # Add a general refinement query if no specific gaps
    if not fallback_queries:
        fallback_queries.append(SearchQuery(
            keywords=f"{user_topic} comprehensive guide detailed information",
            rationale="General refinement query for additional comprehensive information"
        ))
    
    logger.info(f"Generated {len(fallback_queries)} fallback refinement queries")
    return fallback_queries

async def regenerate_refinement_query(state: LearningPathState, failed_query: SearchQuery) -> Optional[SearchQuery]:
    """
    Regenerates a refinement query when the original fails to return results.
    
    This provides a backup mechanism for refinement queries that don't yield results.
    """
    logger.info(f"Regenerating refinement query after no results for: {failed_query.keywords}")
    
    user_topic = state.get("user_topic", "")
    
    # Create a simpler, broader version of the failed query
    original_keywords = failed_query.keywords.split()
    
    # Take the most important keywords and make them broader
    if len(original_keywords) > 3:
        # Use first few keywords with broader terms
        new_keywords = f"{user_topic} {' '.join(original_keywords[:2])} guide overview"
    else:
        # Make the entire query broader
        new_keywords = f"{user_topic} {original_keywords[0]} comprehensive information"
    
    regenerated_query = SearchQuery(
        keywords=new_keywords,
        rationale=f"Regenerated broader query from failed refinement search: {failed_query.keywords}"
    )
    
    logger.info(f"Regenerated refinement query: {regenerated_query.keywords}")
    return regenerated_query

def format_search_results_for_evaluation(search_results: List[SearchServiceResult]) -> str:
    """
    Formats search results into a structured context for LLM evaluation.
    
    This function creates a comprehensive summary of all search results
    that can be analyzed for completeness and quality.
    """
    if not search_results:
        return "No search results available for evaluation."
    
    context_parts = []
    
    for i, result in enumerate(search_results, 1):
        query = escape_curly_braces(result.query)
        context_parts.append(f"\n## Search Query {i}: \"{query}\"\n")
        
        if result.search_provider_error:
            context_parts.append(f"**Error**: {result.search_provider_error}\n")
            continue
        
        if not result.results:
            context_parts.append("**No results found for this query**\n")
            continue
        
        # Process up to 3 results per query for evaluation
        results_included = 0
        for res in result.results:
            if results_included >= 3:  # Limit for evaluation context
                break
                
            title = escape_curly_braces(res.title or 'N/A')
            url = res.url
            context_parts.append(f"### Result {results_included + 1}: {title}")
            context_parts.append(f"**URL**: {url}")
            
            if res.scraped_content:
                content = escape_curly_braces(res.scraped_content)
                # Use a reasonable limit for evaluation context
                truncated_content = content[:MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT]  # Use constant
                if len(content) > MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT:
                    truncated_content += "... (truncated)"
                context_parts.append(f"**Content**: {truncated_content}")
                results_included += 1
            elif res.search_snippet:
                snippet = escape_curly_braces(res.search_snippet)
                truncated_snippet = snippet[:MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT] # Use constant
                if len(snippet) > MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT:
                    truncated_snippet += "... (truncated)"
                context_parts.append(f"**Snippet**: {truncated_snippet}")
                results_included += 1
            else:
                context_parts.append(f"**Content**: Not available (scraping failed)")
            
            context_parts.append("---")
        
        if results_included == 0:
            context_parts.append("(No usable content found for this query)")
    
    return "\n".join(context_parts) 