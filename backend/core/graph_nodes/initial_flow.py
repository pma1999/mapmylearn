import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage
import os

from backend.models.models import SearchQuery, LearningPathState, SearchServiceResult, ScrapedResult
from backend.parsers.parsers import search_queries_parser, enhanced_modules_parser
from backend.services.services import get_llm, perform_search_and_scrape, get_llm_with_search
from langchain_core.prompts import ChatPromptTemplate

from backend.core.graph_nodes.helpers import run_chain, batch_items, format_search_results, escape_curly_braces, MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT, extract_json_from_markdown
from backend.core.graph_nodes.search_utils import execute_search_with_llm_retry

async def generate_search_queries(state: LearningPathState) -> Dict[str, Any]:
    """
    Generates optimal search queries for the user topic using an LLM chain.
    Enhanced with better error handling and JSON extraction.
    Also initializes research loop control parameters.
    
    Args:
        state: The current LearningPathState with 'user_topic'.
        
    Returns:
        A dictionary containing the generated search queries, research loop initialization, and execution steps.
    """
    logging.info(f"Generating search queries for topic: {state['user_topic']}")
    
    # Initialize research loop control parameters (following Google pattern)
    research_loop_initialization = {
        'research_loop_count': 0,  # Start at 0, will be incremented in evaluation
        'max_research_loops': 3,   # Default maximum research iterations
        'is_research_sufficient': False,  # Initial assumption
        'research_knowledge_gaps': [],    # Will be populated by evaluation
        'research_confidence_score': 0.0, # Will be set by evaluation
        'refinement_queries': []          # Will be populated by refinement generation
    }
    
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
    
    # Improved prompt template with better structure and formatting
    prompt_text = """# EXPERT LEARNING PATH ARCHITECT & CURRICULUM DESIGNER

Your task is to generate 5 diverse search queries that will gather the necessary information to DESIGN an optimal and comprehensive course for the topic: {user_topic}.

## INFORMATION GATHERING FOR DESIGN

These searches are NOT just for finding pre-existing course structures, but for collecting the essential building blocks and insights needed to CREATE a well-structured path. Your goal is to gather information covering various facets required for effective curriculum design.

## TARGET INFORMATION CATEGORIES

Analyze the topic and design queries to gather information relevant to these aspects:

1. **Fundamental Concepts & Prerequisites:** What are the absolute foundational ideas? What knowledge is assumed before starting?
2. **Core Sub-domains & Key Topics:** What are the major distinct areas within this topic? What specific subjects must be covered?
3. **Logical Sequencing & Dependencies:** How do concepts typically build upon each other? What's a natural progression for learning? Are there critical paths or dependencies?
4. **Practical Applications & Skills:** What can learners *do* with this knowledge? What are the key practical skills to develop at different stages?
5. **Common Challenges & Advanced Concepts:** Where do learners often get stuck? What are typical difficulties? What constitutes advanced knowledge or specialization in this area?

## LANGUAGE INSTRUCTIONS
- Generate all of your analysis and responses in {output_language}.
- For the search queries themselves, use {search_language} to maximize retrieving high-quality information relevant to curriculum design.

## SEARCH STRATEGY & QUERY DESIGN

Design EXACTLY 5 distinct search queries. Each query should ideally target a DIFFERENT aspect or category from the list above to ensure comprehensive information gathering.

For each search query:
- Frame it to retrieve information that INFORMS the design process. Focus on gathering the raw materials for curriculum design, rather than just finding finished examples.
- Combine the core concepts with terms related to the TARGET INFORMATION CATEGORIES listed above.
- Target educational resources, expert discussions, syllabi, textbooks, or technical documentation that reveal how knowledge in this domain is structured, taught, and applied.
- CRITICAL: Ensure each query balances specificity (finding relevant design information) with breadth (getting actual results).
- QUOTE USAGE RULE: NEVER use more than ONE quoted phrase per query. Quotes are ONLY for essential multi-word concepts that MUST be searched together.
- Getting *some* relevant information across *different* categories is ALWAYS better than getting *zero* results or redundant results.
- Explain precisely how the information retrieved by this specific query will contribute to DESIGNING the optimal course structure.

Your response must be valid JSON with this exact format:
{{
  "queries": [
    {{
      "keywords": "search query text here",
      "rationale": "explanation of why this query helps with curriculum design"
    }}
  ]
}}

Do not wrap your response in markdown code blocks. Return only the JSON object."""

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
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_template(prompt_text)
        
        # Prepare parameters - carefully escape any user input
        escaped_user_topic = escape_curly_braces(state["user_topic"])
        
        # Use the enhanced run_chain with better error handling
        result = await run_chain(
            prompt, 
            lambda: get_llm(key_provider=google_key_provider, user=state.get('user')), 
            search_queries_parser, 
            {
                "user_topic": escaped_user_topic,
                "output_language": output_language,
                "search_language": search_language,
            },
            max_retries=3,
            retry_parsing_errors=True,
            max_parsing_retries=3
        )
        
        search_queries = result.queries
        logging.info(f"Generated {len(search_queries)} search queries")
        
        # Prepare preview data for frontend display
        preview_data = {
            "type": "search_queries_generated",
            "data": {
                "queries": [query.keywords for query in search_queries]
            }
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
        
        # Combine research loop initialization with search query results
        result = {
            "search_queries": search_queries,
            "steps": [f"Generated {len(search_queries)} search queries for topic: {state['user_topic']}"]
        }
        result.update(research_loop_initialization)
        
        return result
        
    except Exception as e:
        logging.error(f"Error generating search queries: {str(e)}")
        
        # Try fallback approach with simpler queries
        try:
            logging.info("Attempting fallback search query generation")
            fallback_queries = await generate_fallback_queries(state)
            
            if progress_callback:
                await progress_callback(
                    f"Generated {len(fallback_queries)} fallback search queries",
                    phase="search_queries",
                    phase_progress=1.0,
                    overall_progress=0.25,
                    action="completed"
                )
            
            # Include research loop initialization even for fallback
            result = {
                "search_queries": fallback_queries,
                "steps": [f"Generated {len(fallback_queries)} fallback search queries due to error: {str(e)}"]
            }
            result.update(research_loop_initialization)
            
            return result
            
        except Exception as fallback_error:
            logging.error(f"Fallback query generation also failed: {str(fallback_error)}")
            
            # Send error progress update
            if progress_callback:
                await progress_callback(
                    f"Error generating search queries: {str(e)}",
                    phase="search_queries",
                    phase_progress=0.5,
                    overall_progress=0.2,
                    action="error"
                )
            
            # Include research loop initialization even for errors
            result = {"search_queries": [], "steps": [f"Error: {str(e)}"]}
            result.update(research_loop_initialization)
            
            return result

async def generate_fallback_queries(state: LearningPathState) -> List[SearchQuery]:
    """
    Generate simple fallback search queries when the main generation fails.
    """
    user_topic = state.get("user_topic", "")
    search_language = state.get("search_language", "en")
    
    # Create basic queries that are likely to work
    fallback_queries = [
        SearchQuery(
            keywords=f"{user_topic} introduction tutorial basics",
            rationale="Find introductory materials and basic concepts"
        ),
        SearchQuery(
            keywords=f"{user_topic} course curriculum syllabus outline",
            rationale="Find existing course structures and curricula"
        ),
        SearchQuery(
            keywords=f"{user_topic} learning path guide",
            rationale="Find structured learning approaches"
        ),
        SearchQuery(
            keywords=f"{user_topic} concepts fundamentals",
            rationale="Find core concepts and fundamentals"
        ),
        SearchQuery(
            keywords=f"{user_topic} advanced topics applications",
            rationale="Find advanced topics and practical applications"
        )
    ]
    
    logging.info(f"Generated {len(fallback_queries)} fallback queries")
    return fallback_queries

async def regenerate_initial_structure_query(
    state: LearningPathState, 
    failed_query: SearchQuery
) -> SearchQuery:
    """
    Regenerates a search query for course structure after a "no results found" error.
    Enhanced with better error handling.
    """
    logging.info(f"Regenerating structure query after no results for: {failed_query.keywords}")
    
    # Get language information from state
    output_language = state.get('language', 'en')
    search_language = state.get('search_language', 'en')
    
    # Get Google key provider from state
    google_key_provider = state.get("google_key_provider")
    if not google_key_provider:
        logging.warning("Google key provider not found in state for query regeneration")
        # Return a simple regenerated query
        return SearchQuery(
            keywords=f"{state['user_topic']} curriculum structure",
            rationale="Simplified query for course structure information"
        )
    
    prompt_text = """# SEARCH QUERY RETRY SPECIALIST

The following search query returned NO RESULTS when searching for information about how to structure a course:

FAILED QUERY: {failed_query}
TOPIC: {user_topic}

I need you to generate a DIFFERENT search query that is more likely to find results but still focused on retrieving STRUCTURAL and ORGANIZATIONAL information about learning this topic.

## NEW QUERY REQUIREMENTS

Create ONE alternative search query that:
1. Is BROADER or uses more common terminology
2. Maintains focus on curriculum design, course structure, and module organization
3. Uses fewer quoted phrases (one at most)
4. Is more likely to match existing educational content
5. Balances specificity with generality

## LANGUAGE INSTRUCTIONS
- Generate your response in {output_language}.
- For the search query, use {search_language} to maximize retrieving high-quality information.

Your response must be valid JSON with this exact format:
{{
  "keywords": "new search query here",
  "rationale": "brief explanation why this query might work better"
}}

Do not wrap your response in markdown code blocks. Return only the JSON object."""

    try:
        prompt = ChatPromptTemplate.from_template(prompt_text)
        
        # Use a simpler approach that directly gets the LLM response
        llm = await get_llm(key_provider=google_key_provider, user=state.get('user'))
        chain = prompt | llm
        
        response = await chain.ainvoke({
            "failed_query": failed_query.keywords,
            "user_topic": state["user_topic"],
            "output_language": output_language,
            "search_language": search_language,
        })
        
        # Extract JSON from response
        response_text = response.content if hasattr(response, 'content') else str(response)
        json_data = extract_json_from_markdown(response_text)
        
        if json_data and "keywords" in json_data:
            regenerated_query = SearchQuery(
                keywords=json_data["keywords"],
                rationale=json_data.get("rationale", "Regenerated query")
            )
            logging.info(f"Successfully regenerated structure query: {regenerated_query.keywords}")
            return regenerated_query
        else:
            raise Exception("Could not extract valid JSON from regeneration response")
            
    except Exception as e:
        logging.error(f"Error regenerating structure query: {str(e)}")
        # Return a simple fallback
        return SearchQuery(
            keywords=f"{state['user_topic']} learning guide tutorial",
            rationale="Fallback query due to regeneration error"
        )

# Rest of the functions remain the same as in the original file...
async def execute_web_searches(state: LearningPathState) -> Dict[str, Any]:
    """
    Execute web searches using Brave and scrape results for each search query in parallel.
    """
    if not state.get("search_queries"):
        logging.info("No search queries to execute")
        return {
            "search_results": [],
            "steps": state.get("steps", []) + ["No search queries to execute"]
        }
    
    search_queries: List[SearchQuery] = state["search_queries"]
    
    # Get the Brave key provider from state
    brave_key_provider = state.get("brave_key_provider")
    if not brave_key_provider:
        # Critical error if no key provider is found for searching
        error_msg = "Brave key provider not found in state. Cannot execute web searches."
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
        logging.debug("Found Brave key provider in state, using for web searches")
    
    # Set up parallel processing based on user configuration
    search_parallel_count = state.get("search_parallel_count", 3)
    # Get scrape timeout from env or default
    scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))
    # Get max results from env or default
    max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS", 5))
    
    logging.info(f"Executing {len(search_queries)} web searches (Brave+Scrape) with parallelism={search_parallel_count}, max_results={max_results_per_query}, scrape_timeout={scrape_timeout}")
    
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
                provider = brave_key_provider.set_operation("initial_web_search")
                
                # Use the new function with retry capability
                return await execute_search_with_llm_retry(
                    state=state,
                    initial_query=query_obj,
                    regenerate_query_func=regenerate_initial_structure_query,
                    search_provider_key_provider=provider,
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
        
        logging.info(f"Completed {len(all_search_service_results)} web searches (Brave+Scrape)")
        
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
            "steps": state.get("steps", []) + [f"Executed {len(all_search_service_results)} web searches (Brave+Scrape)"]
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
    Create a structured course from the scraped search results.
    Enhanced with better error handling.
    """
    # Type hint for clarity
    search_service_results: Optional[List[SearchServiceResult]] = state.get("search_results")

    if not search_service_results or len(search_service_results) == 0:
        logging.info("No search results available to create course")
        return {
            "modules": [],
            "final_learning_path": {
                "topic": state["user_topic"],
                "modules": []
            },
            "steps": state.get("steps", []) + ["No search results available to create course"]
        }

    # Get Google key provider from state
    google_key_provider = state.get("google_key_provider")
    if not google_key_provider:
        logging.warning("Google key provider not found in state, using env fallback if available for LLM")
    else:
        logging.debug("Found Google key provider in state, using for course creation")

    # Get language information from state
    output_language = state.get('language', 'en')

    # Get explanation style
    style = state.get('explanation_style', 'standard')

    # Define style descriptions (can reuse from submodules or define here)
    style_descriptions = {
        "standard": "Provide a balanced, clear, and informative explanation suitable for a general audience. Use standard terminology and provide sufficient detail without oversimplification or excessive jargon. Assume general intelligence but not deep prior knowledge.",
        "simple": "Explain like you're talking to someone smart but new to the topic. Prioritize clarity and understanding over technical precision. Use simple vocabulary and sentence structure. Incorporate basic analogies if helpful.",
        "technical": "Be precise and detailed. Use correct technical terms and formal language. Dive into specifics, mechanisms, and underlying principles. Assume the reader has prerequisite knowledge.",
        "example": "Illustrate every key concept with concrete, practical examples. If the topic is technical, provide relevant code snippets or pseudocode where applicable. Focus on application and real-world scenarios.",
        "conceptual": "Emphasize the core principles, the 'why' behind concepts, relationships between ideas, and the overall context. Focus on mental models. De-emphasize specific implementation steps unless critical to the concept.",
        "grumpy_genius": "Adopt the persona of an incredibly smart expert who finds it slightly tedious to explain this topic *yet again*. Write clear and accurate explanations, but frame them with comedic reluctance and mild intellectual impatience. Use phrases like 'Okay, *fine*, let\'s break down this supposedly \"difficult\" concept...', 'The surprisingly straightforward reason for this is (though most get it wrong)...', 'Look, pay attention, this part is actually important...', or '*Sigh*... Why they make this so complicated, I\'ll never know, but here\'s the deal...'. Inject relatable (and slightly exaggerated) sighs or comments about the inherent (or perceived) difficulty/complexity, but always follow through immediately with a correct and clear explanation. The humor comes from the grumpy-but-brilliant persona."
    }
    explanation_style_description = style_descriptions.get(style, style_descriptions["standard"])

    # If the style is standard, use an empty description
    if style == 'standard':
        explanation_style_description = ""

    progress_callback = state.get('progress_callback')
    if progress_callback:
        await progress_callback(
            f"Creating initial course structure for '{state['user_topic']}'...",
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
                elif res.search_snippet:
                    snippet = escape_curly_braces(res.search_snippet)
                    error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                    truncated_snippet = snippet[:MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT]
                    if len(snippet) > MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT:
                         truncated_snippet += "... (truncated)"
                    context_parts.append(f"Search Snippet:{error_info}\n{truncated_snippet}")
                    results_included += 1
                else:
                     # If scrape failed and no snippet, mention the failure
                     error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                     # context_parts.append(f"Content: Not available.{error_info}") # Let's omit results with no content at all for this prompt
                     # Optionally decide if this counts towards max_context_per_query

                context_parts.append("---")
            if results_included == 0:
                 context_parts.append("(No usable content found for this query)")

        results_text = "\n".join(context_parts)

        # Check if a specific number of modules was requested
        module_count_instruction = ""
        if state.get("desired_module_count"):
            module_count_instruction = f"\nIMPORTANT: Create EXACTLY {state['desired_module_count']} modules for this course. Not more, not less."
        else:
            module_count_instruction = "\nCreate a structured course with 3-7 modules."

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

        # Conditionally add the style instruction part to the prompt
        style_instruction_part = ""
        if explanation_style_description:
            style_instruction_part = f"\n\n**Style Requirement:** Write all module titles and descriptions using the following style: **{explanation_style_description}**"

        # Improved prompt text with proper template variables and escaping
        prompt_text = """# EXPERT CURRICULUM ARCHITECT INSTRUCTIONS

You are a world-class curriculum architect with expertise in educational design. Transform the following search results into a cohesive, comprehensive course on {topic}.

## SEARCH CONTEXT
{search_results}

## CURRICULUM REQUIREMENTS
- Language: {language_instruction}
- Module Count: {module_count_instruction}
{style_instruction_part}

## DESIGN PRINCIPLES
1. **Evidence-Based Structure**: Analyze the search results to identify key concepts, standard approaches, and natural divisions within this subject.
2. **Progressive Complexity**: Arrange modules in a sequence that builds knowledge systematically from foundations to advanced concepts.
3. **Conceptual Independence**: Each module must cover a distinct aspect of the topic with minimal overlap.
4. **Collective Completeness**: Together, all modules must comprehensively cover the entire subject.

## MODULE CREATION INSTRUCTIONS
For each module, provide:

1. **Title**: A clear, descriptive title reflecting the module's core focus (8-10 words maximum)
2. **Overview**: A comprehensive explanation of the module's content and scope (100-200 words)
3. **Primary Objective**: ONE specific, measurable learning outcome expressed as: "After completing this module, learners will be able to..." (1 sentence)
4. **Strategic Relevance**: Explain this module's importance in the overall learning journey and how it connects to other modules (2-3 sentences)

## RESPONSE FORMAT
Your response must be valid JSON with this exact structure:
{{{{
  "modules": [
    {{{{
      "title": "Module title here",
      "description": "Comprehensive overview here",
      "learning_objective": "After completing this module, learners will be able to...",
      "strategic_relevance": "Explanation of importance and connections"
    }}}}
  ]
}}}}

Do not wrap your response in markdown code blocks. Return only the JSON object."""

        prompt = ChatPromptTemplate.from_template(prompt_text)

        result = await run_chain(
            prompt,
            lambda: get_llm_with_search(key_provider=google_key_provider, user=state.get('user')),
            enhanced_modules_parser,
            {
                "topic": escaped_topic,
                "search_results": results_text,
                "language_instruction": language_instruction,
                "module_count_instruction": module_count_instruction,
                "style_instruction_part": style_instruction_part,
            },
            max_retries=3,
            retry_parsing_errors=True,
            max_parsing_retries=3
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

        logging.info(f"Created course structure with {len(modules)} modules")

        preview_modules = []
        for module_index, module in enumerate(modules):
            preview_modules.append({
                "id": module_index,
                "title": module.title,
                "order": module_index,
                "description_preview": module.description[:150] + "..." if len(module.description) > 150 else module.description,
                "status": "defined"
            })

        preview_data = {
            "type": "modules_defined",
            "data": {
                "modules": preview_modules
            }
        }

        if progress_callback and 'modules' in final_learning_path:
            module_count = len(final_learning_path['modules'])
            await progress_callback(
                f"Created initial course with {module_count} modules",
                phase="modules",
                phase_progress=1.0,
                overall_progress=0.55,
                preview_data=preview_data,
                action="completed"
            )

        return {
            "modules": modules,
            "final_learning_path": final_learning_path,
            "steps": state.get("steps", []) + [f"Created course structure with {len(modules)} modules"]
        }
    except Exception as e:
        logging.exception(f"Error creating course: {str(e)}")
        if progress_callback:
            await progress_callback(
                f"Error creating course: {str(e)}",
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
            "steps": state.get("steps", []) + [f"Error creating course: {str(e)}"]
        }