import logging
from typing import Any, List

from langchain_core.prompts import ChatPromptTemplate

from backend.models.models import LearningPathState, EnhancedModule, Submodule, SearchServiceResult, SearchQuery
from backend.services.services import get_llm_for_evaluation
from backend.core.graph_nodes.helpers import run_chain, escape_curly_braces
from backend.prompts.learning_path_prompts import CONTENT_EVALUATION_PROMPT, SUBMODULE_RESEARCH_EVALUATION_PROMPT, CONTENT_REFINEMENT_QUERY_GENERATION_PROMPT
from backend.parsers.parsers import content_evaluation_parser, research_evaluation_parser, content_refinement_query_parser


async def evaluate_content_sufficiency(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    submodule_content: str,
) -> Any:
    logger = logging.getLogger("learning_path.content_evaluator")
    logger.info(
        f"Evaluating content sufficiency for submodule {module_id+1}.{sub_id+1}: {submodule.title}"
    )

    from backend.utils.language_utils import get_full_language_name

    google_key_provider = state.get("google_key_provider")
    output_language_code = state.get("language", "en")
    output_language = get_full_language_name(output_language_code)
    explanation_style = state.get("explanation_style", "standard")

    user_topic = escape_curly_braces(state["user_topic"])
    module_title = escape_curly_braces(module.title)
    submodule_title = escape_curly_braces(submodule.title)
    submodule_description = escape_curly_braces(submodule.description)
    depth_level = escape_curly_braces(submodule.depth_level)
    content_to_evaluate = escape_curly_braces(submodule_content)

    prompt = ChatPromptTemplate.from_template(CONTENT_EVALUATION_PROMPT)

    try:
        evaluation_result = await run_chain(
            prompt,
            lambda: get_llm_for_evaluation(
                key_provider=google_key_provider, user=state.get("user")
            ),
            content_evaluation_parser,
            {
                "user_topic": user_topic,
                "module_title": module_title,
                "submodule_title": submodule_title,
                "submodule_description": submodule_description,
                "depth_level": depth_level,
                "explanation_style": explanation_style,
                "submodule_content": content_to_evaluate,
                "format_instructions": content_evaluation_parser.get_format_instructions(),
            },
        )

        logger.info(
            f"Content evaluation completed for submodule {module_id+1}.{sub_id+1}: sufficient={evaluation_result.is_sufficient}, confidence={evaluation_result.confidence_score:.2f}"
        )

        return evaluation_result

    except Exception as e:
        logger.exception(
            f"Error evaluating content for submodule {module_id+1}.{sub_id+1}: {str(e)}"
        )
        from backend.models.models import ContentEvaluation

        fallback_evaluation = ContentEvaluation(
            is_sufficient=False,
            content_gaps=["Content evaluation failed - requires refinement"],
            confidence_score=0.1,
            improvement_areas=["Overall content enhancement needed"],
            depth_assessment="Unable to assess depth due to evaluation error",
            clarity_assessment="Unable to assess clarity due to evaluation error",
            rationale=f"Content evaluation failed with error: {str(e)}",
        )
        return fallback_evaluation


def check_content_adequacy_local(local_loop_state: dict, content_evaluation: Any) -> bool:
    logger = logging.getLogger("learning_path.content_adequacy")

    is_sufficient = content_evaluation.is_sufficient
    confidence_score = content_evaluation.confidence_score
    current_loop = local_loop_state["content_loop_count"]
    max_loops = local_loop_state["max_content_loops"]

    if is_sufficient and confidence_score >= 0.7:
        logger.info(
            f"Content is sufficient (confidence: {confidence_score:.2f}) - finalizing"
        )
        return True
    elif current_loop >= max_loops:
        logger.info(
            f"Maximum content loops reached ({max_loops}) - finalizing with current content"
        )
        return True
    else:
        logger.info(
            f"Content needs refinement (confidence: {confidence_score:.2f}, loop: {current_loop}/{max_loops}) - continuing"
        )
        return False


async def evaluate_submodule_research_sufficiency(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    search_results: List[SearchServiceResult],
):
    from backend.utils.language_utils import get_full_language_name
    logger = logging.getLogger("learning_path.submodule_research_eval")

    from backend.core.submodules.context_builders import build_enhanced_search_context

    search_summary = build_enhanced_search_context(search_results)
    output_language = get_full_language_name(state.get("language", "en"))

    prompt = ChatPromptTemplate.from_template(SUBMODULE_RESEARCH_EVALUATION_PROMPT)

    result = await run_chain(
        prompt,
        lambda: get_llm_for_evaluation(
            key_provider=state.get("google_key_provider"), user=state.get("user")
        ),
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


# Legacy shims (maintain behavior and warnings)
async def check_content_adequacy(state: LearningPathState, content_evaluation: Any) -> bool:
    logger = logging.getLogger("learning_path.content_adequacy")
    logger.warning(
        "Using legacy check_content_adequacy function - consider using check_content_adequacy_local for parallel processing"
    )

    is_sufficient = content_evaluation.is_sufficient
    confidence_score = content_evaluation.confidence_score
    current_loop = state.get("content_loop_count", 0)
    max_loops = state.get("max_content_loops", 2)

    if is_sufficient and confidence_score >= 0.7:
        logger.info(
            f"Content is sufficient (confidence: {confidence_score:.2f}) - finalizing"
        )
        return True
    elif current_loop >= max_loops:
        logger.info(
            f"Maximum content loops reached ({max_loops}) - finalizing with current content"
        )
        return True
    else:
        logger.info(
            f"Content needs refinement (confidence: {confidence_score:.2f}, loop: {current_loop}/{max_loops}) - continuing"
        )
        return False


async def generate_content_refinement_queries(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    content_evaluation: Any,
    current_content: str,
) -> List[SearchQuery]:
    """
    Legacy function maintained for compatibility.
    Note: This function should not be used with parallel processing as it uses global state.
    Use generate_content_refinement_queries_local instead for parallel submodule processing.
    """
    logger = logging.getLogger("learning_path.content_refinement_queries")
    logger.warning(
        "Using legacy generate_content_refinement_queries function - consider using generate_content_refinement_queries_local for parallel processing"
    )
    logger.info(
        f"Generating content refinement queries for submodule {module_id+1}.{sub_id+1}: {submodule.title}"
    )

    from backend.utils.language_utils import get_full_language_name

    google_key_provider = state.get("google_key_provider")
    output_language_code = state.get("language", "en")
    search_language_code = state.get("search_language", "en")
    output_language = get_full_language_name(output_language_code)
    search_language = get_full_language_name(search_language_code)

    user_topic = escape_curly_braces(state["user_topic"])
    module_title = escape_curly_braces(module.title)
    submodule_title = escape_curly_braces(submodule.title)

    content_gaps_text = "\n".join([f"- {gap}" for gap in content_evaluation.content_gaps])
    improvement_areas_text = "\n".join(
        [f"- {area}" for area in content_evaluation.improvement_areas]
    )

    existing_queries = state.get("content_search_queries", [])
    existing_queries_text = "\n".join(
        [f"- {query.keywords}" for query in existing_queries[-5:]]
    )

    current_loop = state.get("content_loop_count", 0)
    max_loops = state.get("max_content_loops", 2)

    prompt = ChatPromptTemplate.from_template(CONTENT_REFINEMENT_QUERY_GENERATION_PROMPT)

    try:
        refinement_result = await run_chain(
            prompt,
            lambda: get_llm_for_evaluation(
                key_provider=google_key_provider, user=state.get("user")
            ),
            content_refinement_query_parser,
            {
                "user_topic": user_topic,
                "module_title": module_title,
                "submodule_title": submodule_title,
                "content_status": "insufficient"
                if not content_evaluation.is_sufficient
                else "needs_improvement",
                "current_loop": current_loop,
                "max_loops": max_loops,
                "content_gaps": content_gaps_text,
                "improvement_areas": improvement_areas_text,
                "depth_assessment": escape_curly_braces(
                    content_evaluation.depth_assessment
                ),
                "clarity_assessment": escape_curly_braces(
                    content_evaluation.clarity_assessment
                ),
                "quality_issues": escape_curly_braces(content_evaluation.rationale),
                "existing_queries": existing_queries_text,
                "current_research_summary": f"Content loop {current_loop} - targeting gaps in educational effectiveness",
                "search_language": search_language,
                "output_language": output_language,
                "format_instructions": content_refinement_query_parser.get_format_instructions(),
            },
        )

        state["content_refinement_queries"] = refinement_result.queries

        logger.info(
            f"Generated {len(refinement_result.queries)} content refinement queries for submodule {module_id+1}.{sub_id+1}"
        )

        return refinement_result.queries

    except Exception as e:
        logger.exception(
            f"Error generating content refinement queries for submodule {module_id+1}.{sub_id+1}: {str(e)}"
        )
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
