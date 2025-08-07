import os
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.prompts import ChatPromptTemplate

from backend.models.models import (
    LearningPathState,
    EnhancedModule,
    Submodule,
    SearchQuery,
    SearchServiceResult,
)
from backend.services.services import get_llm_for_evaluation
from backend.core.graph_nodes.helpers import run_chain, escape_curly_braces
from backend.core.graph_nodes.search_utils import execute_search_with_llm_retry
from backend.prompts.learning_path_prompts import (
    SUBMODULE_REFINEMENT_QUERY_GENERATION_PROMPT,
    CONTENT_REFINEMENT_QUERY_GENERATION_PROMPT,
)
from backend.parsers.parsers import refinement_query_parser, content_refinement_query_parser
from backend.core.submodules.evaluation import (
    evaluate_submodule_research_sufficiency,
    evaluate_content_sufficiency,
    check_content_adequacy_local,
)
from backend.core.submodules.content import develop_submodule_specific_content, develop_enhanced_content


async def generate_submodule_refinement_queries(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    knowledge_gaps: List[str],
    existing_queries: List[SearchQuery],
) -> List[SearchQuery]:
    from backend.utils.language_utils import get_full_language_name

    output_language = get_full_language_name(state.get("language", "en"))
    search_language = get_full_language_name(state.get("search_language", "en"))

    prompt = ChatPromptTemplate.from_template(SUBMODULE_REFINEMENT_QUERY_GENERATION_PROMPT)

    result = await run_chain(
        prompt,
        lambda: get_llm_for_evaluation(
            key_provider=state.get("google_key_provider"), user=state.get("user")
        ),
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


async def generate_content_refinement_queries_local(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    content_evaluation: Any,
    current_content: str,
    local_loop_state: Dict[str, Any],
) -> List[SearchQuery]:
    logger = logging.getLogger("learning_path.content_refinement_queries")
    logger.info(
        f"Generating content refinement queries for submodule {module_id+1}.{sub_id+1}: {submodule.title}"
    )

    from backend.utils.language_utils import get_full_language_name

    google_key_provider = state.get("google_key_provider")
    output_language_code = state.get("language", "en")
    search_language_code = state.get("search_language", "en")
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)

    prompt = ChatPromptTemplate.from_template(CONTENT_REFINEMENT_QUERY_GENERATION_PROMPT)

    try:
        refinement_result = await run_chain(
            prompt,
            lambda: get_llm_for_evaluation(
                key_provider=google_key_provider, user=state.get("user")
            ),
            content_refinement_query_parser,
            {
                "user_topic": escape_curly_braces(state["user_topic"]),
                "module_title": escape_curly_braces(module.title),
                "submodule_title": escape_curly_braces(submodule.title),
                "content_status": "insufficient"
                if not content_evaluation.is_sufficient
                else "needs_improvement",
                "current_loop": local_loop_state["content_loop_count"],
                "max_loops": local_loop_state["max_content_loops"],
                "content_gaps": "\n".join([f"- {gap}" for gap in content_evaluation.content_gaps]),
                "improvement_areas": "\n".join(
                    [f"- {area}" for area in content_evaluation.improvement_areas]
                ),
                "depth_assessment": escape_curly_braces(
                    content_evaluation.depth_assessment
                ),
                "clarity_assessment": escape_curly_braces(
                    content_evaluation.clarity_assessment
                ),
                "quality_issues": escape_curly_braces(content_evaluation.rationale),
                "existing_queries": "\n".join(
                    [
                        f"- {query.keywords}"
                        for query in local_loop_state["content_search_queries"][-5:]
                    ]
                ),
                "current_research_summary": f"Content loop {local_loop_state['content_loop_count']} - targeting gaps in educational effectiveness",
                "search_language": search_language,
                "output_language": output_language,
                "format_instructions": content_refinement_query_parser.get_format_instructions(),
            },
        )

        local_loop_state["content_refinement_queries"] = refinement_result.queries

        logger.info(
            f"Generated {len(refinement_result.queries)} content refinement queries for submodule {module_id+1}.{sub_id+1}"
        )

        return refinement_result.queries

    except Exception as e:
        logger.exception(
            f"Error generating content refinement queries for submodule {module_id+1}.{sub_id+1}: {str(e)}"
        )
        from backend.models.models import SearchQuery

        fallback_queries = [
            SearchQuery(
                keywords=f"{submodule.title} detailed explanation examples",
                rationale="Fallback query for content enhancement due to query generation error",
            ),
            SearchQuery(
                keywords=f"{submodule.title} practical applications tutorial",
                rationale="Fallback query for practical examples due to query generation error",
            ),
        ]
        return fallback_queries


async def execute_content_refinement_searches(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    refinement_queries: List[SearchQuery],
) -> List[SearchServiceResult]:
    logger = logging.getLogger("learning_path.content_refinement_search")
    logger.info(
        f"Executing {len(refinement_queries)} content refinement searches for submodule {module_id+1}.{sub_id+1}"
    )

    if not refinement_queries:
        logger.warning(
            f"No refinement queries provided for submodule {module_id+1}.{sub_id+1}"
        )
        return []

    brave_key_provider = state.get("brave_key_provider")
    if not brave_key_provider:
        raise ValueError(
            f"Brave Search key provider not found in state for content refinement"
        )

    max_results_per_query = int(os.environ.get("SEARCH_MAX_RESULTS", 3))
    scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))

    results: List[SearchServiceResult] = []
    sem = asyncio.Semaphore(2)

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
        tasks = [bounded_refinement_search(query) for query in refinement_queries]
        results_or_excs = await asyncio.gather(*tasks, return_exceptions=True)

        for i, res_or_exc in enumerate(results_or_excs):
            if isinstance(res_or_exc, Exception):
                logger.error(
                    f"Content refinement search error for submodule {module_id+1}.{sub_id+1}: {str(res_or_exc)}"
                )
                from backend.models.models import SearchServiceResult

                error_result = SearchServiceResult(
                    query=refinement_queries[i].keywords,
                    search_provider_error=f"Content refinement search error: {str(res_or_exc)}",
                )
                results.append(error_result)
            else:
                results.append(res_or_exc)

        return results

    except Exception as e:
        logger.exception(
            f"Error executing content refinement searches for submodule {module_id+1}.{sub_id+1}: {str(e)}"
        )
        from backend.models.models import SearchServiceResult

        return [
            SearchServiceResult(
                query=f"Error: {str(e)}",
                search_provider_error=f"Failed to execute content refinement searches: {str(e)}",
            )
        ]


async def regenerate_content_refinement_query(
    state: LearningPathState,
    failed_query: SearchQuery,
    module_id: int = None,
    sub_id: int = None,
    module: EnhancedModule = None,
    submodule: Submodule = None,
) -> Optional[SearchQuery]:
    logger = logging.getLogger("learning_path.content_refinement_retry")
    logger.info(
        f"Regenerating failed content refinement query: {failed_query.keywords}"
    )

    try:
        google_key_provider = state.get("google_key_provider")

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

        llm = get_llm_for_evaluation(key_provider=google_key_provider, user=state.get("user"))

        response = await llm.ainvoke(
            prompt.format(
                failed_query=failed_query.keywords,
                submodule_title=submodule.title if submodule else "educational content",
            )
        )

        new_query_text = response.content.strip()
        if new_query_text.startswith("New Query:"):
            new_query_text = new_query_text.replace("New Query:", "").strip()

        from backend.models.models import SearchQuery

        new_query = SearchQuery(
            keywords=new_query_text,
            rationale=f"Regenerated simpler query for content refinement (original: {failed_query.keywords})",
        )

        logger.info(f"Regenerated content refinement query: {new_query.keywords}")
        return new_query

    except Exception as e:
        logger.exception(f"Error regenerating content refinement query: {str(e)}")
        return None


async def develop_submodule_content_with_refinement_loop(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    sub_queries: List[SearchQuery],
    sub_search_results: List[SearchServiceResult],
    progress_callback=None,
) -> str:
    logger = logging.getLogger("learning_path.content_refinement")
    logger.info(
        f"Starting content development with refinement loop for submodule {module_id+1}.{sub_id+1}: {submodule.title}"
    )

    try:
        local_loop_state: Dict[str, Any] = {
            "content_loop_count": 0,
            "max_content_loops": 2,
            "is_content_sufficient": False,
            "content_gaps": [],
            "content_confidence_score": 0.0,
            "content_refinement_queries": [],
            "content_search_queries": list(sub_queries),
            "content_search_results": list(sub_search_results),
        }

        submodule_content = await develop_submodule_specific_content(
            state, module_id, sub_id, module, submodule, sub_queries, sub_search_results
        )

        while local_loop_state["content_loop_count"] < local_loop_state["max_content_loops"]:
            current_loop = local_loop_state["content_loop_count"] + 1
            local_loop_state["content_loop_count"] = current_loop

            logger.info(
                f"Content refinement loop {current_loop}/{local_loop_state['max_content_loops']} for submodule {module_id+1}.{sub_id+1}"
            )

            if progress_callback:
                await progress_callback(
                    f"Evaluating content quality for {module.title} > {submodule.title} (Loop {current_loop})",
                    phase="content_evaluation",
                    phase_progress=0.1,
                    overall_progress=0.65
                    + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                    preview_data={
                        "type": "submodule_status_update",
                        "data": {
                            "module_id": module_id,
                            "submodule_id": sub_id,
                            "status_detail": f"content_evaluation_loop_{current_loop}",
                        },
                    },
                    action="processing",
                )

            content_evaluation = await evaluate_content_sufficiency(
                state, module_id, sub_id, module, submodule, submodule_content
            )

            local_loop_state["is_content_sufficient"] = content_evaluation.is_sufficient
            local_loop_state["content_gaps"] = content_evaluation.content_gaps
            local_loop_state["content_confidence_score"] = (
                content_evaluation.confidence_score
            )

            if check_content_adequacy_local(local_loop_state, content_evaluation):
                logger.info(
                    f"Content deemed sufficient for submodule {module_id+1}.{sub_id+1} after {current_loop} loops"
                )
                break

            if progress_callback:
                await progress_callback(
                    f"Generating content enhancement queries for {module.title} > {submodule.title}",
                    phase="content_refinement",
                    phase_progress=0.3,
                    overall_progress=0.66
                    + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                    action="processing",
                )

            content_refinement_queries = await generate_content_refinement_queries_local(
                state,
                module_id,
                sub_id,
                module,
                submodule,
                content_evaluation,
                submodule_content,
                local_loop_state,
            )

            if progress_callback:
                await progress_callback(
                    f"Searching for content enhancement information for {module.title} > {submodule.title}",
                    phase="content_refinement",
                    phase_progress=0.5,
                    overall_progress=0.67
                    + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                    action="processing",
                )

            refinement_search_results = await execute_content_refinement_searches(
                state, module_id, sub_id, module, submodule, content_refinement_queries
            )

            local_loop_state["content_search_queries"].extend(content_refinement_queries)
            local_loop_state["content_search_results"].extend(refinement_search_results)

            if progress_callback:
                await progress_callback(
                    f"Enhancing content for {module.title} > {submodule.title}",
                    phase="content_enhancement",
                    phase_progress=0.7,
                    overall_progress=0.68
                    + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                    action="processing",
                )

            submodule_content = await develop_enhanced_content(
                state, module_id, sub_id, module, submodule, submodule_content, refinement_search_results
            )

        logger.info(
            f"Content development completed for submodule {module_id+1}.{sub_id+1} after {local_loop_state['content_loop_count']} loops"
        )
        return submodule_content

    except Exception as e:
        logger.exception(
            f"Error in content refinement loop for submodule {module_id+1}.{sub_id+1}: {str(e)}"
        )
        return await develop_submodule_specific_content(
            state, module_id, sub_id, module, submodule, sub_queries, sub_search_results
        )


# Import placed at end to avoid circular import during function definitions
from backend.core.submodules.research import execute_submodule_specific_searches
