import os
import asyncio
import logging
from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from backend.models.models import SearchQuery, LearningPathState, EnhancedModule, Submodule, SearchServiceResult
from backend.services.services import get_llm
from backend.core.graph_nodes.helpers import run_chain, escape_curly_braces
from backend.core.graph_nodes.search_utils import execute_search_with_llm_retry


async def regenerate_submodule_content_query(
    state: LearningPathState,
    failed_query: SearchQuery,
    module_id: int = None,
    sub_id: int = None,
    module: EnhancedModule = None,
    submodule: Submodule = None,
) -> Optional[SearchQuery]:
    logger = logging.getLogger("learning_path.submodule_processor")
    logger.info(
        f"Regenerating submodule content query after no results for: {failed_query.keywords}"
    )

    from backend.utils.language_utils import get_full_language_name

    output_language_code = state.get("language", "en")
    search_language_code = state.get("search_language", "en")
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)

    google_key_provider = state.get("google_key_provider")
    if not google_key_provider:
        logger.warning(
            "Google key provider not found in state for submodule query regeneration"
        )
        return None

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
        parser = PydanticOutputParser(pydantic_object=SearchQuery)

        prompt = ChatPromptTemplate.from_template(prompt_text)

        result = await run_chain(
            prompt,
            lambda: get_llm(
                key_provider=google_key_provider, user=state.get("user")
            ),
            parser,
            {
                "failed_query": failed_query.keywords,
                "submodule_context": submodule_context,
                "output_language": output_language,
                "search_language": search_language,
                "format_instructions": parser.get_format_instructions(),
            },
        )

        if result and isinstance(result, SearchQuery):
            logger.info(
                f"Successfully regenerated submodule content query: Keywords='{result.keywords}', Rationale='{result.rationale}'"
            )
            return result
        else:
            logger.error(
                f"Submodule query regeneration returned empty or invalid result type: {type(result)}"
            )
            return None
    except Exception as e:
        logger.exception(
            f"Error regenerating submodule content query: {str(e)}"
        )
        return None


async def generate_submodule_specific_queries(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
) -> List[SearchQuery]:
    logger = logging.getLogger("learning_path.query_generator")
    logger.info(
        f"Generating search query for submodule {module_id}.{sub_id}: {submodule.title}"
    )

    google_key_provider = state.get("google_key_provider")

    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback(
            f"Generating targeted search query for {module.title} > {submodule.title}",
            phase="submodule_research",
            phase_progress=0.2,
            overall_progress=0.61,
            action="processing",
        )

    from backend.utils.language_utils import get_full_language_name

    output_language_code = state.get("language", "en")
    search_language_code = state.get("search_language", "en")
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)

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
        "depth_level": submodule_depth,
    }

    other_modules = []
    for i, m in enumerate(state.get("enhanced_modules", [])):
        other_modules.append(
            {
                "title": escape_curly_braces(m.title),
                "description": escape_curly_braces(
                    m.description[:200] + "..." if len(m.description) > 200 else m.description
                ),
                "is_current": i == module_id,
            }
        )

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
        learning_path_context += (
            f"- {'[Current] ' if m['is_current'] else ''}{m['title']}: {m['description']}\n"
        )

    module_context = f"Current Module: {module_title}\nDescription: {module_description}"
    module_count = len(state.get("enhanced_modules", []))
    submodule_count = len(module.submodules)

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
        rationale: str = Field(
            description="Explanation of why this query is optimal for this submodule"
        )

    single_query_parser = PydanticOutputParser(
        pydantic_object=SingleSearchQueryOutput
    )

    try:
        result = await run_chain(
            prompt,
            lambda: get_llm(
                key_provider=google_key_provider, user=state.get("user")
            ),
            single_query_parser,
            {
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
                "format_instructions": single_query_parser.get_format_instructions(),
            },
        )

        query = SearchQuery(keywords=result.query, rationale=result.rationale)
        logging.info(
            f"Generated optimal search query for submodule {sub_id+1}: {query.keywords}"
        )
        return [query]
    except Exception as e:
        logging.error(f"Error generating submodule search query: {str(e)}")
        fallback_query = SearchQuery(
            keywords=f"{module_title} {submodule_title} tutorial comprehensive guide",
            rationale="Fallback query due to error in query generation",
        )
        return [fallback_query]


async def execute_submodule_specific_searches(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    sub_queries: List[SearchQuery],
) -> List[SearchServiceResult]:
    logging.info(
        f"Executing web searches for submodule {module_id+1}.{sub_id+1}: {submodule.title}"
    )

    if not sub_queries:
        logging.warning(
            f"No search queries provided for submodule {module_id+1}.{sub_id+1}"
        )
        return []

    brave_key_provider = state.get("brave_key_provider")
    if not brave_key_provider:
        raise ValueError(
            f"Brave Search key provider not found in state for submodule {module_id+1}.{sub_id+1}"
        )

    max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS", 5))
    scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))

    results: List[SearchServiceResult] = []
    sem = asyncio.Semaphore(3)

    async def bounded_search_with_retry(query_obj: SearchQuery):
        async with sem:
            provider = brave_key_provider.set_operation("submodule_content_search")
            return await execute_search_with_llm_retry(
                state=state,
                initial_query=query_obj,
                regenerate_query_func=regenerate_submodule_content_query,
                search_provider_key_provider=provider,
                search_config={
                    "max_results": max_results_per_query,
                    "scrape_timeout": scrape_timeout,
                },
                regenerate_args={
                    "module_id": module_id,
                    "sub_id": sub_id,
                    "module": module,
                    "submodule": submodule,
                },
            )

    try:
        tasks = [bounded_search_with_retry(query) for query in sub_queries]
        results_or_excs = await asyncio.gather(*tasks, return_exceptions=True)

        for i, res_or_exc in enumerate(results_or_excs):
            if isinstance(res_or_exc, Exception):
                logging.error(
                    f"Search error for submodule {module_id+1}.{sub_id+1}: {str(res_or_exc)}"
                )
                error_result = SearchServiceResult(
                    query=sub_queries[i].keywords,
                    search_provider_error=f"Search task error: {str(res_or_exc)}",
                )
                results.append(error_result)
            else:
                results.append(res_or_exc)
                if res_or_exc.search_provider_error:
                    logging.warning(
                        f"Search provider error for submodule query '{sub_queries[i].keywords}': {res_or_exc.search_provider_error}"
                    )

        return results

    except Exception as e:
        logging.exception(
            f"Error executing searches for submodule {module_id+1}.{sub_id+1}: {str(e)}"
        )
        return [
            SearchServiceResult(
                query=f"Error: {str(e)}",
                search_provider_error=f"Failed to execute submodule searches: {str(e)}",
            )
        ]
