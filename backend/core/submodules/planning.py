import asyncio
import logging
from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate

from backend.models.models import LearningPathState, EnhancedModule
from backend.parsers.parsers import submodule_parser
from backend.services.services import get_llm_with_search
from backend.core.graph_nodes.helpers import run_chain, escape_curly_braces
from backend.prompts.learning_path_prompts import SUBMODULE_PLANNING_PROMPT
from backend.core.submodules.planning_research import (
    generate_module_specific_planning_queries,
    execute_module_specific_planning_searches,
    gather_planning_research_until_sufficient,
)


async def plan_and_research_module_submodules(
    state: LearningPathState, module_id: int, module
) -> EnhancedModule:
    logger = logging.getLogger("learning_path.planner")
    logger.info(
        f"Starting combined planning and research for module {module_id+1}: {module.title}"
    )

    planning_queries = await generate_module_specific_planning_queries(
        state, module_id, module
    )

    initial_planning_results = await execute_module_specific_planning_searches(
        state, module_id, module, planning_queries
    )

    planning_queries, planning_search_results = await gather_planning_research_until_sufficient(
        state, module_id, module, planning_queries, initial_planning_results
    )

    planning_context_parts = []
    MAX_CONTEXT_CHARS = 5000
    current_chars = 0

    for report in planning_search_results:
        query = escape_curly_braces(report.query)
        planning_context_parts.append(
            f"\n## Research for Planning Query: \"{query}\"\n"
        )
        results_included = 0
        for res in report.results:
            if current_chars >= MAX_CONTEXT_CHARS:
                planning_context_parts.append("... (Context truncated due to length)")
                break

            title = escape_curly_braces(res.title or "N/A")
            url = res.url
            planning_context_parts.append(f"### Source: {url} (Title: {title})")

            content_snippet = ""
            if res.scraped_content:
                content_snippet = (
                    f"Scraped Content Snippet:\n{escape_curly_braces(res.scraped_content)[:1000]}"
                )
            elif res.search_snippet:
                error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                content_snippet = (
                    f"Search Snippet:{error_info}\n{escape_curly_braces(res.search_snippet)[:1000]}"
                )
            else:
                error_info = f" (Scraping failed: {escape_curly_braces(res.scrape_error or 'Unknown error')})"
                content_snippet = f"Content: Not available.{error_info}"

            planning_context_parts.append(content_snippet)
            current_chars += len(content_snippet)
            results_included += 1
            planning_context_parts.append("---")

        if results_included == 0:
            planning_context_parts.append(
                "(No usable content found for this planning query)"
            )

        if current_chars >= MAX_CONTEXT_CHARS:
            break

    planning_search_context = "\n".join(planning_context_parts)

    enhanced_module = await plan_module_submodules(
        state, module_id, module, planning_search_context
    )

    return enhanced_module


async def plan_module_submodules(
    state: LearningPathState,
    idx: int,
    module,
    planning_search_context: Optional[str] = None,
) -> EnhancedModule:
    logging.info(f"Planning submodules for module {idx+1}: {module.title}")

    progress_callback = state.get("progress_callback")

    if progress_callback:
        total_modules = len(state.get("modules", []))
        module_progress = (idx + 0.2) / max(1, total_modules)
        overall_progress = 0.55 + (module_progress * 0.15)

        await progress_callback(
            f"Planning submodules for module {idx+1}: {module.title}",
            phase="submodule_planning",
            phase_progress=module_progress,
            overall_progress=overall_progress,
            preview_data={"current_module": {"title": module.title, "index": idx}},
            action="processing",
        )

    from backend.utils.language_utils import get_full_language_name

    output_language_code = state.get("language", "en")
    output_language = get_full_language_name(output_language_code)

    learning_path_context = "\n".join(
        [f"Module {i+1}: {m.title}\n{m.description}" for i, m in enumerate(state["modules"])])

    planning_context_str = (
        planning_search_context or "(No structural research context available)"
    )

    submodule_count_instruction = ""
    if state.get("desired_submodule_count"):
        submodule_count_instruction = (
            f"IMPORTANT: Create EXACTLY {state['desired_submodule_count']} submodules for this module. Not more, not less."
        )

    base_prompt = SUBMODULE_PLANNING_PROMPT
    prompt_params = {
        "user_topic": escape_curly_braces(state["user_topic"]),
        "module_title": escape_curly_braces(module.title),
        "module_description": escape_curly_braces(module.description),
        "learning_path_context": learning_path_context,
        "language": output_language,
        "planning_search_context": escape_curly_braces(planning_context_str),
        "format_instructions": submodule_parser.get_format_instructions(),
    }

    if submodule_count_instruction:
        base_prompt = base_prompt.replace(
            "## INSTRUCTIONS & REQUIREMENTS",
            f"## INSTRUCTIONS & REQUIREMENTS\n\n{submodule_count_instruction}",
        )

    prompt = ChatPromptTemplate.from_template(base_prompt)

    try:
        result = await run_chain(
            prompt,
            lambda: get_llm_with_search(
                key_provider=state.get("google_key_provider"), user=state.get("user")
            ),
            submodule_parser,
            prompt_params,
        )
        submodules = result.submodules

        desired_count = state.get("desired_submodule_count")
        if desired_count and len(submodules) != desired_count:
            logging.warning(
                f"Requested {desired_count} submodules but got {len(submodules)} for module {idx+1}: '{module.title}'. Adjusting..."
            )
            if len(submodules) > desired_count:
                submodules = submodules[:desired_count]
            else:
                logging.warning(
                    f"Proceeding with {len(submodules)} submodules for '{module.title}' despite requesting {desired_count}."
                )

        for i, sub in enumerate(submodules):
            sub.order = i + 1

        try:
            enhanced_module = module.model_copy(update={"submodules": submodules})
        except AttributeError:
            enhanced_module = EnhancedModule(
                title=module.title, description=module.description, submodules=submodules
            )

        logging.info(f"Planned {len(submodules)} submodules for module {idx+1}")

        if progress_callback:
            submodule_previews = []
            for submodule_idx, submodule in enumerate(submodules):
                submodule_previews.append(
                    {
                        "id": submodule_idx,
                        "title": submodule.title,
                        "order": submodule_idx,
                        "description_preview": submodule.description[:100] + "..."
                        if len(submodule.description) > 100
                        else submodule.description,
                        "status": "planned",
                    }
                )

            module_progress = (idx + 1) / max(1, total_modules)
            overall_progress = 0.55 + (module_progress * 0.05)

            await progress_callback(
                f"Planned {len(submodules)} submodules for module {idx+1}: {module.title}",
                phase="submodule_planning",
                phase_progress=module_progress,
                overall_progress=overall_progress,
                preview_data={
                    "type": "module_submodules_planned",
                    "data": {
                        "module_id": idx,
                        "module_title": module.title,
                        "submodules": submodule_previews,
                    },
                },
                action="processing",
            )

        return enhanced_module

    except Exception as e:
        logging.exception(
            f"Error planning submodules for module {idx+1}: {str(e)}"
        )
        if progress_callback:
            await progress_callback(
                f"Error planning submodules for module {idx+1}: {str(e)}",
                phase="submodule_planning",
                phase_progress=module_progress,
                overall_progress=overall_progress,
                action="error",
            )
        raise


async def plan_submodules(state: LearningPathState) -> Dict[str, Any]:
    logging.info(
        "Planning submodules for each module in parallel with structural research"
    )
    basic_modules = state.get("modules")
    if not basic_modules:
        logging.warning("No basic modules available from create_learning_path")
        return {"enhanced_modules": [], "steps": ["No basic modules available"]}

    parallel_count = state.get("parallel_count", 2)
    logging.info(f"Planning submodules with parallelism of {parallel_count}")

    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback(
            f"Planning submodules for {len(basic_modules)} modules (with research) using parallelism={parallel_count}...",
            phase="submodule_planning",
            phase_progress=0.0,
            overall_progress=0.55,
            action="started",
        )

    sem = asyncio.Semaphore(parallel_count)

    async def plan_and_research_module_submodules_bounded(idx, module):
        async with sem:
            return await plan_and_research_module_submodules(state, idx, module)

    tasks = [
        plan_and_research_module_submodules_bounded(idx, module)
        for idx, module in enumerate(basic_modules)
    ]

    enhanced_modules_results = await asyncio.gather(*tasks, return_exceptions=True)

    processed_modules = []

    for idx, result in enumerate(enhanced_modules_results):
        if isinstance(result, Exception):
            module_title = (
                basic_modules[idx].title
                if hasattr(basic_modules[idx], "title")
                else basic_modules[idx].get("title", f"Module {idx+1}")
            )
            module_desc = (
                basic_modules[idx].description
                if hasattr(basic_modules[idx], "description")
                else basic_modules[idx].get("description", "No description")
            )
            logging.error(
                f"Error processing module {idx+1} ('{module_title}'): {str(result)}"
            )
            processed_modules.append(
                EnhancedModule(title=module_title, description=module_desc, submodules=[])
            )
        elif isinstance(result, EnhancedModule):
            processed_modules.append(result)
        else:
            module_title = (
                basic_modules[idx].title
                if hasattr(basic_modules[idx], "title")
                else basic_modules[idx].get("title", f"Module {idx+1}")
            )
            module_desc = (
                basic_modules[idx].description
                if hasattr(basic_modules[idx], "description")
                else basic_modules[idx].get("description", "No description")
            )
            logging.error(
                f"Unexpected result type for module {idx+1} ('{module_title}'): {type(result)}"
            )
            processed_modules.append(
                EnhancedModule(title=module_title, description=module_desc, submodules=[])
            )

    preview_modules = []
    total_submodules = 0

    for module in processed_modules:
        if isinstance(module, EnhancedModule):
            submodule_previews = []
            if hasattr(module, "submodules") and module.submodules:
                for submodule in module.submodules:
                    sub_title = getattr(submodule, "title", "Untitled Submodule")
                    sub_desc = getattr(submodule, "description", "")
                    submodule_previews.append(
                        {
                            "title": sub_title,
                            "description": sub_desc[:100] + "..."
                            if len(sub_desc) > 100
                            else sub_desc,
                        }
                    )
                    total_submodules += 1

            preview_modules.append(
                {"title": getattr(module, "title", "Untitled Module"), "submodules": submodule_previews}
            )
        else:
            preview_modules.append(
                {
                    "title": getattr(module, "title", "Error Processing Module"),
                    "submodules": [],
                }
            )

    if progress_callback:
        await progress_callback(
            f"Planned {total_submodules} submodules across {len(processed_modules)} modules (with research)",
            phase="submodule_planning",
            phase_progress=1.0,
            overall_progress=0.6,
            preview_data={
                "type": "all_submodules_planned",
                "data": {
                    "modules": preview_modules,
                    "total_submodules_planned": total_submodules,
                },
            },
            action="completed",
        )

    return {
        "enhanced_modules": processed_modules,
        "steps": state.get("steps", [])
        + [
            f"Planned submodules for {len(processed_modules)} modules with structural research using {parallel_count} parallel processes"
        ],
    }
