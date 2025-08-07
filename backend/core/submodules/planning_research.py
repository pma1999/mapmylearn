import os
import asyncio
import logging
from typing import List, Optional, Tuple

from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

from backend.models.models import (
    LearningPathState,
    EnhancedModule,
    SearchQuery,
    SearchServiceResult,
)
from backend.services.services import get_llm, get_llm_for_evaluation
from backend.core.graph_nodes.helpers import escape_curly_braces, run_chain
from backend.core.graph_nodes.search_utils import execute_search_with_llm_retry
from backend.core.submodules.context_builders import build_enhanced_search_context
from backend.prompts.learning_path_prompts import (
    MODULE_SUBMODULE_PLANNING_QUERY_GENERATION_PROMPT,
    SUBMODULE_PLANNING_RESEARCH_EVALUATION_PROMPT,
    SUBMODULE_PLANNING_REFINEMENT_QUERY_GENERATION_PROMPT,
)
from backend.parsers.parsers import (
    search_queries_parser,
    research_evaluation_parser,
    refinement_query_parser,
)


async def generate_module_specific_planning_queries(
    state: LearningPathState, module_id: int, module: EnhancedModule
) -> List[SearchQuery]:
    logger = logging.getLogger("learning_path.submodule_planner")
    logger.info(
        f"Generating structural planning queries for module {module_id+1}: {module.title}"
    )

    from backend.utils.language_utils import get_full_language_name

    google_key_provider = state.get("google_key_provider")
    output_language_code = state.get("language", "en")
    search_language_code = state.get("search_language", "en")
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)

    user_topic = escape_curly_braces(state["user_topic"])
    module_title = escape_curly_braces(
        module.title if hasattr(module, "title") else module.get("title", f"Module {module_id+1}")
    )
    module_description = escape_curly_braces(
        module.description if hasattr(module, "description") else module.get("description", "No description")
    )
    module_count = len(state.get("modules", []))

    learning_path_context = "\n".join(
        [
            f"Module {i+1}: {escape_curly_braces(mod.title if hasattr(mod, 'title') else mod.get('title', f'Module {i+1}'))}\n{escape_curly_braces(mod.description if hasattr(mod, 'description') else mod.get('description', 'No description'))}"
            for i, mod in enumerate(state.get("modules", []))
        ]
    )

    prompt = ChatPromptTemplate.from_template(
        MODULE_SUBMODULE_PLANNING_QUERY_GENERATION_PROMPT
    )

    try:
        result = await run_chain(
            prompt,
            lambda: get_llm(
                key_provider=google_key_provider, user=state.get("user")
            ),
            search_queries_parser,
            {
                "module_title": module_title,
                "module_description": module_description,
                "module_order": module_id + 1,
                "module_count": module_count,
                "user_topic": user_topic,
                "learning_path_context": learning_path_context,
                "language": output_language,
                "search_language": search_language,
                "format_instructions": search_queries_parser.get_format_instructions(),
            },
        )
        search_queries = result.queries
        logger.info(
            f"Generated {len(search_queries)} planning queries for module {module_id+1}"
        )
        return search_queries
    except Exception as e:
        logger.error(
            f"Error generating module planning queries for module {module_id+1}: {str(e)}"
        )
        return []


async def regenerate_module_planning_query(
    state: LearningPathState,
    failed_query: SearchQuery,
    module_id: int,
    module: EnhancedModule,
) -> Optional[SearchQuery]:
    logger = logging.getLogger("learning_path.submodule_planner")
    logger.info(
        f"Regenerating module planning query for module {module_id+1} after no results for: {failed_query.keywords}"
    )

    from backend.utils.language_utils import get_full_language_name

    output_language_code = state.get("language", "en")
    search_language_code = state.get("search_language", "en")
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)

    google_key_provider = state.get("google_key_provider")
    if not google_key_provider:
        logger.warning(
            "Google key provider not found in state for module planning query regeneration"
        )
        return None

    module_title = escape_curly_braces(module.title)
    module_description = escape_curly_braces(module.description)
    user_topic = escape_curly_braces(state.get("user_topic", "the user's topic"))

    module_context = f"""
Topic: {user_topic}
Module {module_id + 1}: {module_title}
Module Description: {module_description}
Objective: Regenerate a search query suitable for finding curriculum examples or structural guides for this specific module.
    """

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

    parser = PydanticOutputParser(pydantic_object=SearchQuery)

    prompt = ChatPromptTemplate.from_template(prompt_text)
    llm = await get_llm(key_provider=google_key_provider, user=state.get("user"))

    chain = prompt | llm | parser

    try:
        regenerated_query_object = await chain.ainvoke(
            {
                "failed_query": failed_query.keywords,
                "module_context": module_context,
                "output_language": output_language,
                "search_language": search_language,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        if regenerated_query_object and isinstance(regenerated_query_object, SearchQuery):
            logger.info(
                f"Successfully regenerated module planning query: Keywords='{regenerated_query_object.keywords}', Rationale='{regenerated_query_object.rationale}'"
            )
            return regenerated_query_object
        else:
            logger.warning(
                "Query regeneration did not return a valid SearchQuery object."
            )
            return None
    except Exception as e:
        logger.exception(f"Error regenerating module planning query: {str(e)}")
        return None


async def execute_module_specific_planning_searches(
    state: LearningPathState,
    module_id: int,
    module: EnhancedModule,
    planning_queries: List[SearchQuery],
) -> List[SearchServiceResult]:
    logger = logging.getLogger("learning_path.submodule_planner")
    logger.info(f"Executing web searches for module planning: {module.title}")

    if not planning_queries:
        logger.warning(f"No planning queries provided for module {module.title}")
        return []

    brave_key_provider = state.get("brave_key_provider")
    if not brave_key_provider:
        module_title_safe = escape_curly_braces(module.title)
        logger.error(
            f"Brave Search key provider not found for module {module_id+1} ({module_title_safe}) planning search."
        )
        return [
            SearchServiceResult(
                query=q.keywords, search_provider_error="Missing Brave Key Provider"
            )
            for q in planning_queries
        ]

    max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS", 5))
    scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))

    results: List[SearchServiceResult] = []
    sem = asyncio.Semaphore(3)

    async def bounded_search_with_planning_retry(query_obj: SearchQuery):
        async with sem:
            provider = brave_key_provider.set_operation("module_planning_search")
            return await execute_search_with_llm_retry(
                state=state,
                initial_query=query_obj,
                regenerate_query_func=regenerate_module_planning_query,
                search_provider_key_provider=provider,
                search_config={
                    "max_results": max_results_per_query,
                    "scrape_timeout": scrape_timeout,
                },
                regenerate_args={"module_id": module_id, "module": module},
            )

    try:
        tasks = [bounded_search_with_planning_retry(q) for q in planning_queries]
        results_or_excs = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results: List[SearchServiceResult] = []
        for i, res_or_exc in enumerate(results_or_excs):
            if isinstance(res_or_exc, Exception):
                query_keywords = planning_queries[i].keywords
                logger.error(
                    f"Planning search failed for query '{query_keywords}': {str(res_or_exc)}"
                )
                processed_results.append(
                    SearchServiceResult(
                        query=query_keywords,
                        search_provider_error=f"Search task error: {str(res_or_exc)}",
                    )
                )
            elif isinstance(res_or_exc, SearchServiceResult):
                processed_results.append(res_or_exc)
                if res_or_exc.search_provider_error:
                    logger.warning(
                        f"Search provider error for planning query '{res_or_exc.query}': {res_or_exc.search_provider_error}"
                    )
            else:
                query_keywords = planning_queries[i].keywords
                logger.error(
                    f"Unexpected result type for planning query '{query_keywords}': {type(res_or_exc)}"
                )
                processed_results.append(
                    SearchServiceResult(
                        query=query_keywords,
                        search_provider_error=f"Unexpected result type: {type(res_or_exc).__name__}",
                    )
                )

        return processed_results

    except Exception as e:
        logger.exception(
            f"Error executing planning searches for module {module.title}: {str(e)}"
        )
        return [
            SearchServiceResult(
                query=f"Error: {str(e)}",
                search_provider_error=f"Failed to execute planning searches: {str(e)}",
            )
        ]


async def evaluate_module_planning_research_sufficiency(
    state: LearningPathState,
    module_id: int,
    module: EnhancedModule,
    search_results: List[SearchServiceResult],
):
    """Evaluate if planning research for a module is sufficient to design submodules."""
    logger = logging.getLogger("learning_path.submodule_planner")
    from backend.utils.language_utils import get_full_language_name

    search_summary = build_enhanced_search_context(search_results)
    output_language = get_full_language_name(state.get("language", "en"))

    prompt = ChatPromptTemplate.from_template(
        SUBMODULE_PLANNING_RESEARCH_EVALUATION_PROMPT
    )

    result = await run_chain(
        prompt,
        lambda: get_llm_for_evaluation(
            key_provider=state.get("google_key_provider"),
            user=state.get("user"),
        ),
        research_evaluation_parser,
        {
            "user_topic": escape_curly_braces(state["user_topic"]),
            "module_title": escape_curly_braces(module.title),
            "module_description": escape_curly_braces(module.description),
            "language": output_language,
            "search_results_summary": search_summary,
            "format_instructions": research_evaluation_parser.get_format_instructions(),
        },
    )

    logger.info(
        f"Module planning research evaluation for module {module_id+1}: sufficient={result.is_sufficient}, confidence={result.confidence_score:.2f}"
    )
    return result


async def generate_module_planning_refinement_queries(
    state: LearningPathState,
    module_id: int,
    module: EnhancedModule,
    knowledge_gaps: List[str],
    existing_queries: List[SearchQuery],
) -> List[SearchQuery]:
    """Generate follow-up queries to address planning research gaps."""
    logger = logging.getLogger("learning_path.submodule_planner")
    from backend.utils.language_utils import get_full_language_name

    output_language = get_full_language_name(state.get("language", "en"))
    search_language = get_full_language_name(state.get("search_language", "en"))

    prompt = ChatPromptTemplate.from_template(
        SUBMODULE_PLANNING_REFINEMENT_QUERY_GENERATION_PROMPT
    )

    result = await run_chain(
        prompt,
        lambda: get_llm_for_evaluation(
            key_provider=state.get("google_key_provider"),
            user=state.get("user"),
        ),
        refinement_query_parser,
        {
            "user_topic": escape_curly_braces(state["user_topic"]),
            "module_title": escape_curly_braces(module.title),
            "module_description": escape_curly_braces(module.description),
            "knowledge_gaps": "\n".join([f"- {gap}" for gap in knowledge_gaps]),
            "existing_queries": "\n".join([f"- {q.keywords}" for q in existing_queries]),
            "language": output_language,
            "search_language": search_language,
            "format_instructions": refinement_query_parser.get_format_instructions(),
        },
    )

    logger.info(
        f"Generated {len(result.queries)} planning refinement queries for module {module_id+1}"
    )
    return result.queries


async def gather_planning_research_until_sufficient(
    state: LearningPathState,
    module_id: int,
    module: EnhancedModule,
    initial_queries: List[SearchQuery],
    initial_results: List[SearchServiceResult],
) -> Tuple[List[SearchQuery], List[SearchServiceResult]]:
    """Iteratively refine planning research until sufficient for submodule design."""
    queries = list(initial_queries)
    results = list(initial_results)

    loop_count = 0
    max_loops = 2

    while loop_count < max_loops:
        loop_count += 1
        evaluation = await evaluate_module_planning_research_sufficiency(
            state, module_id, module, results
        )

        if evaluation.is_sufficient:
            break

        follow_up = await generate_module_planning_refinement_queries(
            state, module_id, module, evaluation.knowledge_gaps, queries
        )

        if not follow_up:
            break

        new_results = await execute_module_specific_planning_searches(
            state, module_id, module, follow_up
        )

        queries.extend(follow_up)
        results.extend(new_results)

    return queries, results
