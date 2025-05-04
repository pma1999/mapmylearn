"""
LangGraph nodes for course generation.

This package contains all the nodes used in the course generation graph,
organized by their function in the generation process.
"""

from .initial_flow import (
    generate_search_queries,
    execute_web_searches,
    create_learning_path,
)
from .submodules import (
    plan_submodules,
    initialize_submodule_processing,
    process_submodule_batch,
    process_single_submodule,
    generate_submodule_specific_queries,
    execute_submodule_specific_searches,
    develop_submodule_specific_content,
    finalize_enhanced_learning_path,
    check_submodule_batch_processing
)
from .resources import (
    initialize_resource_generation,
    generate_topic_resources,
    process_module_resources,
    integrate_resources_with_submodule_processing,
    add_resources_to_final_learning_path
)
