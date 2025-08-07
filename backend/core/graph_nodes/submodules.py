# Facade module re-exporting submodule orchestration functions
# to preserve public API and import paths while delegating to
# cohesive submodules for implementation.

from typing import Any, Dict, List, Tuple, Optional

# Planning APIs (effective versions with research integration)
from backend.core.submodules.planning import (
    plan_submodules,
    plan_module_submodules,
    plan_and_research_module_submodules,
)

# Pipeline/batch processing and finalization
from backend.core.submodules.pipeline import (
    initialize_submodule_processing,
    process_submodule_batch,
    process_single_submodule,
    finalize_enhanced_learning_path,
    check_submodule_batch_processing,
)

# Research and search execution for submodules
from backend.core.submodules.research import (
    generate_submodule_specific_queries,
    execute_submodule_specific_searches,
    regenerate_submodule_content_query,
)

# Content development
from backend.core.submodules.content import (
    develop_submodule_specific_content,
    develop_enhanced_content,
)

# Quiz generation
from backend.core.submodules.quiz import generate_submodule_quiz

# Refinement loops and utilities
from backend.core.submodules.refinement import (
    generate_submodule_refinement_queries,
    gather_research_until_sufficient,
    generate_content_refinement_queries_local,
    execute_content_refinement_searches,
    regenerate_content_refinement_query,
    develop_submodule_content_with_refinement_loop,
)

# Evaluation and legacy shims
from backend.core.submodules.evaluation import (
    evaluate_submodule_research_sufficiency,
    evaluate_content_sufficiency,
    check_content_adequacy_local,
    check_content_adequacy,
    generate_content_refinement_queries,
)

# Context builders and utils (if other modules import them from here)
from backend.core.submodules.context_builders import (
    build_learning_path_context as _build_learning_path_context,
    build_module_context as _build_module_context,
    build_adjacent_context as _build_adjacent_context,
    build_enhanced_search_context as _build_enhanced_search_context,
)
from backend.core.submodules.utils import extract_json_from_markdown

__all__ = [
    # Planning
    "plan_submodules",
    "plan_module_submodules",
    "plan_and_research_module_submodules",
    # Pipeline
    "initialize_submodule_processing",
    "process_submodule_batch",
    "process_single_submodule",
    "finalize_enhanced_learning_path",
    "check_submodule_batch_processing",
    # Research
    "generate_submodule_specific_queries",
    "execute_submodule_specific_searches",
    "regenerate_submodule_content_query",
    # Content
    "develop_submodule_specific_content",
    "develop_enhanced_content",
    # Quiz
    "generate_submodule_quiz",
    # Refinement
    "generate_submodule_refinement_queries",
    "gather_research_until_sufficient",
    "generate_content_refinement_queries_local",
    "execute_content_refinement_searches",
    "regenerate_content_refinement_query",
    "develop_submodule_content_with_refinement_loop",
    # Evaluation
    "evaluate_submodule_research_sufficiency",
    "evaluate_content_sufficiency",
    "check_content_adequacy_local",
    "check_content_adequacy",
    "generate_content_refinement_queries",
    # Helpers
    "_build_learning_path_context",
    "_build_module_context",
    "_build_adjacent_context",
    "_build_enhanced_search_context",
    "extract_json_from_markdown",
]
