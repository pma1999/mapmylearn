import asyncio
import logging
import os
from typing import Any, Dict, List

from backend.models.models import (
    LearningPathState,
    EnhancedModule,
    Submodule,
    SubmoduleContent,
    SearchServiceResult,
)
from backend.core.graph_nodes.helpers import batch_items, escape_curly_braces, MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT
from backend.core.submodules.research import (
    generate_submodule_specific_queries,
    execute_submodule_specific_searches,
)
from backend.core.submodules.content import develop_submodule_specific_content
from backend.core.submodules.quiz import generate_submodule_quiz
from backend.core.submodules.refinement import gather_research_until_sufficient


async def initialize_submodule_processing(state: LearningPathState) -> Dict[str, Any]:
    logging.info(
        "Initializing submodule batch processing with LangGraph-optimized distribution"
    )

    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback(
            "Preparing to enhance modules with targeted research and content development...",
            phase="submodule_research",
            phase_progress=0.0,
            overall_progress=0.6,
            action="started",
        )

    enhanced_modules = state.get("enhanced_modules")
    if not enhanced_modules:
        logging.warning("No enhanced modules available")
        return {
            "submodule_batches": [],
            "current_submodule_batch_index": 0,
            "submodules_in_process": {},
            "developed_submodules": [],
            "quiz_generation_enabled": True,
            "quiz_questions_by_submodule": {},
            "quiz_generation_in_progress": {},
            "quiz_generation_errors": {},
            "steps": ["No enhanced modules available"],
        }

    submodule_parallel_count = state.get("submodule_parallel_count", 2)

    all_submodules = []
    for module_id, module in enumerate(enhanced_modules):
        if module.submodules:
            for sub_id in range(len(module.submodules)):
                all_submodules.append(
                    {
                        "module_id": module_id,
                        "sub_id": sub_id,
                        "module_title": module.title,
                        "submodule_title": module.submodules[sub_id].title,
                        "module_idx": module_id,
                        "total_submodules": len(module.submodules),
                    }
                )

    if not all_submodules:
        logging.warning("No valid submodules found")
        return {
            "submodule_batches": [],
            "current_submodule_batch_index": 0,
            "submodules_in_process": {},
            "developed_submodules": [],
            "quiz_generation_enabled": True,
            "quiz_questions_by_submodule": {},
            "quiz_generation_in_progress": {},
            "quiz_generation_errors": {},
            "steps": ["No valid submodules found"],
        }

    def distribution_key(item):
        relative_position = item["sub_id"] / max(1, item["total_submodules"])
        module_id = item["module_id"]
        return (relative_position, module_id)

    all_submodules.sort(key=distribution_key)

    all_pairs = [(item["module_id"], item["sub_id"]) for item in all_submodules]

    submodule_batches = batch_items(all_pairs, submodule_parallel_count)

    total_submodules = len(all_submodules)
    total_batches = len(submodule_batches)

    logging.info(
        f"Using LangGraph map-reduce pattern: Organized {total_submodules} submodules into {total_batches} batches with parallelism of {submodule_parallel_count}"
    )

    module_to_submodules: Dict[int, Dict[str, Any]] = {}
    for item in all_submodules:
        module_id = item["module_id"]
        if module_id not in module_to_submodules:
            module_to_submodules[module_id] = {"title": item["module_title"], "submodules": []}
        module_to_submodules[module_id]["submodules"].append(
            {"title": item["submodule_title"], "sub_id": item["sub_id"]}
        )

    preview_data = {
        "modules": [
            {"title": data["title"], "submodule_count": len(data["submodules"])}
            for module_id, data in module_to_submodules.items()
        ],
        "total_submodules": total_submodules,
        "total_batches": total_batches,
        "parallel_processing": submodule_parallel_count,
    }

    quiz_generation_enabled = state.get("quiz_generation_enabled", True)

    if progress_callback:
        quiz_info = (
            "with quiz generation enabled" if quiz_generation_enabled else "without quiz generation"
        )
        await progress_callback(
            f"Preparing to process {total_submodules} submodules in {total_batches} batches with {submodule_parallel_count} submodules in parallel ({quiz_info})",
            phase="submodule_research",
            phase_progress=0.1,
            overall_progress=0.6,
            preview_data=preview_data,
            action="processing",
        )

    return {
        "submodule_batches": submodule_batches,
        "current_submodule_batch_index": 0,
        "submodules_in_process": {},
        "developed_submodules": [],
        "quiz_generation_enabled": quiz_generation_enabled,
        "quiz_questions_by_submodule": {},
        "quiz_generation_in_progress": {},
        "quiz_generation_errors": {},
        "steps": [
            f"Initialized LangGraph-optimized submodule processing with batch size {submodule_parallel_count} and quiz generation {'enabled' if quiz_generation_enabled else 'disabled'}"
        ],
    }


async def process_single_submodule(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
) -> Dict[str, Any]:
    logger = logging.getLogger("learning_path.submodule_processor")
    logger.info(
        f"Processing submodule {sub_id+1} in module {module_id+1}: {submodule.title}"
    )

    progress_callback = state.get("progress_callback")

    try:
        import time

        start_time = time.time()

        if progress_callback:
            await progress_callback(
                f"Processing: Module {module_id+1} > Submodule {sub_id+1}: {submodule.title}",
                phase="submodule_research",
                phase_progress=0.1,
                overall_progress=0.6
                + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                preview_data={
                    "type": "submodule_processing_started",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "submodule_title": submodule.title,
                        "status_detail": "research_started",
                    },
                },
                action="processing",
            )

        step_start = time.time()
        submodule_search_queries = await generate_submodule_specific_queries(
            state, module_id, sub_id, module, submodule
        )
        query_gen_time = time.time() - step_start
        logger.debug(
            f"Generated {len(submodule_search_queries)} queries for submodule in {query_gen_time:.2f}s"
        )

        if progress_callback:
            await progress_callback(
                f"Generated search query for {module.title} > {submodule.title}",
                phase="submodule_research",
                phase_progress=0.3,
                overall_progress=0.61
                + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                preview_data={
                    "type": "submodule_status_update",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "status_detail": "query_generated",
                        "queries": [q.keywords for q in submodule_search_queries]
                        if submodule_search_queries
                        else [],
                    },
                },
                action="processing",
            )

        step_start = time.time()
        submodule_search_results = await execute_submodule_specific_searches(
            state, module_id, sub_id, module, submodule, submodule_search_queries
        )
        search_time = time.time() - step_start
        logger.debug(
            f"Completed {len(submodule_search_results)} searches in {search_time:.2f}s"
        )

        if progress_callback:
            await progress_callback(
                f"Completed research for {module.title} > {submodule.title}",
                phase="submodule_research",
                phase_progress=0.8,
                overall_progress=0.65
                + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                preview_data={
                    "type": "submodule_status_update",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "status_detail": "research_completed",
                        "search_result_count": len(submodule_search_results)
                        if submodule_search_results
                        else 0,
                    },
                },
                action="completed",
            )

        step_start = time.time()

        if progress_callback:
            await progress_callback(
                f"Developing content for {module.title} > {submodule.title}",
                phase="content_development",
                phase_progress=0.2,
                overall_progress=0.67
                + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                preview_data={
                    "type": "submodule_status_update",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "status_detail": "content_development_started",
                    },
                },
                action="processing",
            )

        submodule_search_queries, submodule_search_results = (
            await gather_research_until_sufficient(
                state,
                module_id,
                sub_id,
                module,
                submodule,
                submodule_search_queries,
                submodule_search_results,
                progress_callback,
            )
        )

        submodule_content = await develop_submodule_specific_content(
            state,
            module_id,
            sub_id,
            module,
            submodule,
            submodule_search_queries,
            submodule_search_results,
        )
        content_time = time.time() - step_start

        step_start = time.time()

        if progress_callback:
            await progress_callback(
                f"Generating quiz questions for {module.title} > {submodule.title}",
                phase="quiz_generation",
                phase_progress=0.0,
                overall_progress=0.75
                + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                preview_data={
                    "type": "submodule_status_update",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "status_detail": "quiz_generation_started",
                    },
                },
                action="started",
            )

        quiz_questions = []
        if submodule_content and not submodule_content.startswith("Error:"):
            quiz_questions = await generate_submodule_quiz(
                state, module_id, sub_id, module, submodule, submodule_content
            )
        else:
            logger.warning(
                f"Skipping quiz generation for submodule {module_id}.{sub_id} due to content generation failure"
            )

            if progress_callback:
                await progress_callback(
                    f"Skipped quiz generation for {module.title} > {submodule.title} due to content generation failure",
                    phase="quiz_generation",
                    phase_progress=0.0,
                    overall_progress=0.75
                    + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                    preview_data={
                        "type": "submodule_status_update",
                        "data": {
                            "module_id": module_id,
                            "submodule_id": sub_id,
                            "status_detail": "quiz_generation_skipped",
                        },
                    },
                    action="skipped",
                )

        quiz_time = time.time() - step_start

        step_start = time.time()

        initial_result: Dict[str, Any] = {
            "status": "completed",
            "module_id": module_id,
            "sub_id": sub_id,
            "search_queries": submodule_search_queries,
            "search_results": submodule_search_results,
            "content": submodule_content,
            "quiz_questions": quiz_questions,
            "processing_time": {
                "total": 0,
                "query_generation": query_gen_time,
                "search": search_time,
                "content_development": content_time,
                "quiz_generation": quiz_time,
                "resource_generation": 0,
            },
        }

        if submodule_content and not submodule_content.startswith("Error:"):
            from backend.core.graph_nodes.resources import (
                integrate_resources_with_submodule_processing,
            )

            result = await integrate_resources_with_submodule_processing(
                state,
                module_id,
                sub_id,
                module,
                submodule,
                submodule_content,
                initial_result,
                submodule_search_results,
            )
        else:
            logger.warning(
                f"Skipping resource generation for submodule {module_id}.{sub_id} due to content generation failure"
            )
            result = initial_result

        resource_time = time.time() - step_start
        total_time = time.time() - start_time

        result["processing_time"]["resource_generation"] = resource_time
        result["processing_time"]["total"] = total_time

        logger.info(
            f"Completed submodule {module_id+1}.{sub_id+1} in {total_time:.2f}s (Query: {query_gen_time:.2f}s, Search: {search_time:.2f}s, Content: {content_time:.2f}s, Quiz: {quiz_time:.2f}s, Resources: {resource_time:.2f}s)"
        )

        if progress_callback:
            await progress_callback(
                f"Completed development for {module.title} > {submodule.title} in {total_time:.2f}s",
                phase="content_development",
                phase_progress=0.5,
                overall_progress=0.7
                + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                preview_data={
                    "type": "submodule_completed",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "status_detail": "fully_processed",
                        "quiz_question_count": len(quiz_questions) if quiz_questions else 0,
                        "resource_count": len(result.get("resources", [])),
                    },
                },
                action="completed",
            )

        return result
    except Exception as e:
        logger.exception(
            f"Error processing submodule {sub_id+1} of module {module_id+1}: {str(e)}"
        )
        if progress_callback:
            await progress_callback(
                f"Error in {module.title} > {submodule.title}: {str(e)}",
                phase="content_development",
                phase_progress=0.3,
                overall_progress=0.65
                + ((module_id * 0.1 + sub_id * 0.02) / state.get("total_submodules_estimate", 10)),
                preview_data={
                    "type": "submodule_error",
                    "data": {
                        "module_id": module_id,
                        "submodule_id": sub_id,
                        "error_message": str(e),
                    },
                },
                action="error",
            )

        return {"status": "error", "module_id": module_id, "sub_id": sub_id, "error": str(e)}


async def process_submodule_batch(state: LearningPathState) -> Dict[str, Any]:
    submodule_parallel_count = state.get("submodule_parallel_count", 2)
    progress_callback = state.get("progress_callback")
    sub_batches = state.get("submodule_batches") or []
    current_index = state.get("current_submodule_batch_index", 0)
    batch_progress = 0
    overall_progress = 0.6

    logging.info(
        f"Processing submodule batch {current_index+1}/{len(sub_batches)} with parallelism of {submodule_parallel_count}"
    )

    if progress_callback:
        total_batches = len(sub_batches)
        batch_progress = current_index / max(1, total_batches)
        overall_progress = 0.6 + (batch_progress * 0.1)

        await progress_callback(
            f"Processing batch {current_index+1} of {len(sub_batches)} with {submodule_parallel_count} parallel tasks...",
            phase="submodule_research",
            phase_progress=batch_progress,
            overall_progress=overall_progress,
            action="processing",
        )

    if current_index >= len(sub_batches):
        logging.info("All submodule batches processed")
        return {"steps": ["All submodule batches processed"]}

    current_batch = sub_batches[current_index]

    enhanced_modules = state.get("enhanced_modules", [])
    if not enhanced_modules:
        logging.error("No enhanced modules found in state")
        return {"steps": ["Error: No enhanced modules found"]}

    submodules_in_process = state.get("submodules_in_process", {}) or {}

    tasks = []
    success_count = 0
    error_count = 0
    processed_submodules: List[Dict[str, Any]] = []
    next_index = current_index + 1

    if current_batch:
        for module_id, sub_id in current_batch:
            if module_id < len(enhanced_modules):
                module = enhanced_modules[module_id]
                if sub_id < len(module.submodules):
                    submodule = module.submodules[sub_id]
                    key = f"{module_id}:{sub_id}"
                    if key not in submodules_in_process or submodules_in_process[key].get("status") not in [
                        "completed",
                        "processing",
                    ]:
                        submodules_in_process[key] = {"status": "processing"}
                        tasks.append(
                            process_single_submodule(
                                state, module_id, sub_id, module, submodule
                            )
                        )

        if tasks:
            try:
                import time

                start_time = time.time()

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        error_count += 1
                        logging.error(f"Task error: {str(result)}")
                        continue

                    if isinstance(result, dict):
                        module_id = result.get("module_id")
                        sub_id = result.get("sub_id")
                        status = result.get("status")

                        if module_id is not None and sub_id is not None:
                            key = f"{module_id}:{sub_id}"
                            submodules_in_process[key] = result

                            if status == "completed":
                                success_count += 1
                                if module_id < len(enhanced_modules):
                                    processed_submodules.append(
                                        {
                                            "module_title": enhanced_modules[module_id].title,
                                            "submodule_title": enhanced_modules[module_id].submodules[
                                                sub_id
                                            ].title,
                                            "status": "completed",
                                        }
                                    )
                            elif status == "error":
                                error_count += 1

                elapsed_time = time.time() - start_time

                batch_progress = (current_index + 1) / max(1, total_batches)
                overall_progress = 0.7 + (batch_progress * 0.25)

                if progress_callback:
                    await progress_callback(
                        f"Completed batch {current_index+1}/{len(sub_batches)}: {success_count} successful, {error_count} failed in {elapsed_time:.2f} seconds",
                        phase="content_development",
                        phase_progress=batch_progress,
                        overall_progress=overall_progress,
                        preview_data={"processed_submodules": processed_submodules},
                        action="processing",
                    )

                logging.info(
                    f"Batch {current_index+1} results: {success_count} successful, {error_count} failed"
                )
            except Exception as e:
                logging.error(f"Error in processing submodule batch: {str(e)}")
                if progress_callback:
                    await progress_callback(
                        f"Error processing batch: {str(e)}",
                        phase="content_development",
                        phase_progress=batch_progress,
                        overall_progress=overall_progress,
                        action="error",
                    )
        else:
            logging.info(f"No tasks to process in batch {current_index+1}")
            if progress_callback:
                await progress_callback(
                    f"No tasks to process in batch {current_index+1}",
                    phase="content_development",
                    phase_progress=batch_progress,
                    overall_progress=overall_progress,
                    action="processing",
                )

    developed_submodules = state.get("developed_submodules", [])

    for module_id, sub_id in current_batch:
        key = f"{module_id}:{sub_id}"
        data = submodules_in_process.get(key, {})

        if data.get("status") == "completed" and module_id < len(enhanced_modules):
            module = enhanced_modules[module_id]
            if sub_id < len(module.submodules):
                search_results_raw = data.get("search_results", [])
                search_results_dicts: List[Dict[str, Any]] = []
                if isinstance(search_results_raw, list):
                    for res in search_results_raw:
                        if hasattr(res, "model_dump"):
                            search_results_dicts.append(res.model_dump())
                        elif isinstance(res, dict):
                            search_results_dicts.append(res)
                elif search_results_raw:
                    if hasattr(search_results_raw, "model_dump"):
                        search_results_dicts.append(search_results_raw.model_dump())
                    elif isinstance(search_results_raw, dict):
                        search_results_dicts.append(search_results_raw)

                developed_submodules.append(
                    SubmoduleContent(
                        module_id=module_id,
                        submodule_id=sub_id,
                        title=module.submodules[sub_id].title,
                        description=module.submodules[sub_id].description,
                        search_queries=data.get("search_queries", []),
                        search_results=search_results_dicts,
                        content=data.get("content", ""),
                        quiz_questions=data.get("quiz_questions", None),
                        resources=data.get("resources", []),
                    )
                )

    if progress_callback:
        processed_count = current_index + 1
        total_count = len(sub_batches)
        percentage = min(100, int((processed_count / total_count) * 100))

        if next_index >= len(sub_batches):
            await progress_callback(
                f"Completed all {total_count} batches of submodule processing ({percentage}% complete)",
                phase="content_development",
                phase_progress=1.0,
                overall_progress=0.95,
                action="completed",
            )
        else:
            await progress_callback(
                f"Completed batch {current_index+1}/{len(sub_batches)} ({percentage}% of submodules processed)",
                phase="content_development",
                phase_progress=batch_progress,
                overall_progress=overall_progress,
                action="processing",
            )

    return {
        "current_submodule_batch_index": next_index,
        "submodules_in_process": submodules_in_process,
        "developed_submodules": developed_submodules,
        "steps": [
            f"Processed submodule batch {current_index+1} with {len(tasks)} parallel tasks using LangGraph pattern"
        ],
    }


async def finalize_enhanced_learning_path(state: LearningPathState) -> Dict[str, Any]:
    logging.info("Finalizing enhanced course")

    progress_callback = state.get("progress_callback")
    if progress_callback:
        await progress_callback(
            "Finalizing your course with all enhanced content...",
            phase="final_assembly",
            phase_progress=0.0,
            overall_progress=0.95,
            action="started",
        )

    logger = logging.getLogger("learning_path.finalizer")
    logger.info("Finalizing enhanced course with submodules")
    try:
        if not state.get("developed_submodules"):
            logger.warning("No developed submodules available")
            return {
                "final_learning_path": {"topic": state["user_topic"], "modules": []},
                "steps": ["No submodules developed"],
            }

        module_to_subs: Dict[int, List[SubmoduleContent]] = {}
        for sub in state["developed_submodules"]:
            module_to_subs.setdefault(sub.module_id, []).append(sub)

        for module_id in module_to_subs:
            module_to_subs[module_id].sort(key=lambda s: s.submodule_id)

        if progress_callback:
            await progress_callback(
                "Organizing all developed content into final structure...",
                phase="final_assembly",
                phase_progress=0.5,
                overall_progress=0.97,
                action="processing",
            )

        final_modules = []
        total_quiz_questions = 0

        for module_id, module in enumerate(state.get("enhanced_modules") or []):
            subs = module_to_subs.get(module_id, [])
            submodule_data: List[Dict[str, Any]] = []

            for sub in subs:
                summary = (
                    sub.summary
                    if hasattr(sub, "summary")
                    else (sub.content[:200].strip() + "..." if sub.content else "")
                )

                quiz_data = None
                if hasattr(sub, "quiz_questions") and sub.quiz_questions:
                    quiz_data = []
                    for quiz in sub.quiz_questions:
                        quiz_data.append(
                            {
                                "question": quiz.question,
                                "options": [
                                    {"text": opt.text, "is_correct": opt.is_correct}
                                    for opt in quiz.options
                                ],
                                "explanation": quiz.explanation,
                            }
                        )
                    total_quiz_questions += len(quiz_data)

                research_parts: List[str] = []
                for res in getattr(sub, "search_results", []):
                    if isinstance(res, dict):
                        text = (
                            res.get("scraped_content")
                            or res.get("search_snippet")
                            or ""
                        )
                        if text:
                            snippet = text[:3000]
                            research_parts.append(f"Source: {res.get('url')}\n{snippet}")
                    else:
                        logging.warning(
                            f"Unexpected type for search result item in finalization: {type(res)}"
                        )
                research_context = "\n\n".join(research_parts)[:10000]

                submodule_data.append(
                    {
                        "id": sub.submodule_id,
                        "title": sub.title,
                        "description": sub.description,
                        "content": sub.content,
                        "order": sub.submodule_id + 1,
                        "summary": summary,
                        "connections": getattr(sub, "connections", {}),
                        "quiz_questions": quiz_data,
                        "resources": getattr(sub, "resources", []),
                        "research_context": research_context,
                    }
                )

            module_data = {
                "id": module_id,
                "title": module.title,
                "description": module.description,
                "core_concept": getattr(module, "core_concept", ""),
                "learning_objective": getattr(module, "learning_objective", ""),
                "prerequisites": getattr(module, "prerequisites", []),
                "key_components": getattr(module, "key_components", []),
                "expected_outcomes": getattr(module, "expected_outcomes", []),
                "submodules": submodule_data,
                "resources": [],
            }

            final_modules.append(module_data)

        final_learning_path = {
            "topic": state["user_topic"],
            "modules": final_modules,
            "execution_steps": state["steps"],
            "metadata": {
                "total_modules": len(final_modules),
                "total_submodules": sum(
                    len(module["submodules"]) for module in final_modules
                ),
                "total_quiz_questions": total_quiz_questions,
                "has_quizzes": total_quiz_questions > 0,
            },
        }

        logger.info(
            f"Finalized course with {len(final_modules)} modules and {total_quiz_questions} quiz questions"
        )

        preview_modules = []
        total_submodules = 0

        for module in final_modules:
            module_preview = {
                "title": module["title"],
                "submodule_count": len(module["submodules"]),
                "description": module["description"][:150] + "..."
                if len(module["description"]) > 150
                else module["description"],
                "quiz_count": sum(1 for sub in module["submodules"] if sub.get("quiz_questions")),
            }
            preview_modules.append(module_preview)
            total_submodules += len(module["submodules"])

        preview_data = {
            "modules": preview_modules,
            "total_modules": len(final_modules),
            "total_submodules": total_submodules,
            "total_quiz_questions": total_quiz_questions,
        }

        if progress_callback:
            await progress_callback(
                f"Learning path complete with {len(final_modules)} modules, {total_submodules} detailed submodules, and {total_quiz_questions} quiz questions",
                phase="final_assembly",
                phase_progress=1.0,
                overall_progress=1.0,
                preview_data=preview_data,
                action="completed",
            )

        return {"final_learning_path": final_learning_path, "steps": ["Finalized enhanced course"]}
    except Exception as e:
        logger.exception(f"Error finalizing course: {str(e)}")

        if progress_callback:
            await progress_callback(
                f"Error finalizing course: {str(e)}",
                phase="final_assembly",
                phase_progress=0.5,
                overall_progress=0.97,
                action="error",
            )

        return {
            "final_learning_path": {
                "topic": state["user_topic"],
                "modules": [],
                "error": str(e),
            },
            "steps": [f"Error: {str(e)}"],
        }


def check_submodule_batch_processing(state: LearningPathState) -> str:
    current_index = state.get("current_submodule_batch_index")
    batches = state.get("submodule_batches")

    if current_index is None or batches is None:
        logging.warning("Submodule batch processing state is not properly initialized")
        return "all_batches_processed"

    if current_index >= len(batches):
        total_processed = len(state.get("developed_submodules", []))
        total_batches = len(batches)

        submodules_in_process = state.get("submodules_in_process", {})
        successful_submodules = [
            v for k, v in submodules_in_process.items() if v.get("status") == "completed"
        ]
        error_submodules = [
            v for k, v in submodules_in_process.items() if v.get("status") == "error"
        ]

        timing_stats = "No timing data available"
        if successful_submodules and "processing_time" in successful_submodules[0]:
            total_times = [
                s["processing_time"]["total"] for s in successful_submodules if "processing_time" in s
            ]
            if total_times:
                avg_time = sum(total_times) / len(total_times)
                min_time = min(total_times)
                max_time = max(total_times)
                timing_stats = (
                    f"Average: {avg_time:.2f}s, Min: {min_time:.2f}s, Max: {max_time:.2f}s"
                )

        logger = logging.getLogger("learning_path.batch_processor")
        logger.info(f"All {total_batches} submodule batches processed successfully")
        logger.info(
            f"Completed {total_processed} submodules with {len(error_submodules)} errors"
        )
        logger.info(f"Processing time statistics: {timing_stats}")
        logger.info(f"All {total_processed} submodules across {total_batches} batches completed")

        return "all_batches_processed"
    else:
        progress_pct = int((current_index / len(batches)) * 100)

        processed_count = 0
        total_count = 0
        submodules_in_process = state.get("submodules_in_process", {})
        for batch in batches[:current_index]:
            for module_id, sub_id in batch:
                total_count += 1
                key = f"{module_id}:{sub_id}"
                if key in submodules_in_process:
                    if submodules_in_process[key].get("status") in ["completed", "error"]:
                        processed_count += 1

        remaining = len(batches) - current_index
        logger = logging.getLogger("learning_path.batch_processor")
        logger.info(
            f"Continue processing: batch {current_index+1} of {len(batches)} ({progress_pct}% complete)"
        )
        logger.info(
            f"Processed {processed_count}/{total_count} submodules so far, {remaining} batches remaining"
        )
        logger.info(
            f"Progress: {progress_pct}% - Processing batch {current_index+1} of {len(batches)}"
        )

        return "continue_processing"
