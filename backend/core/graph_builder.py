import logging
from langgraph.graph import StateGraph, START, END
from backend.models.models import LearningPathState
from backend.core.graph_nodes import (
    generate_search_queries,
    execute_web_searches,
    create_learning_path,
    plan_submodules,
    initialize_submodule_processing,
    process_submodule_batch,
    finalize_enhanced_learning_path,
    check_submodule_batch_processing,
    initialize_resource_generation,
    generate_topic_resources,
    process_module_resources,
    add_resources_to_final_learning_path
)

def build_graph():
    """
    Constructs and returns the LangGraph with hierarchical submodule processing and resource generation.
    """
    logging.info("Building graph with hierarchical submodule processing and resource generation")
    graph = StateGraph(LearningPathState)
    
    # Initial learning path generation nodes
    graph.add_node("generate_search_queries", generate_search_queries)
    graph.add_node("execute_web_searches", execute_web_searches)
    graph.add_node("create_learning_path", create_learning_path)
    
    # Submodule planning and development nodes
    graph.add_node("plan_submodules", plan_submodules)
    graph.add_node("initialize_submodule_processing", initialize_submodule_processing)
    graph.add_node("process_submodule_batch", process_submodule_batch)
    graph.add_node("finalize_enhanced_learning_path", finalize_enhanced_learning_path)
    
    # Resource generation nodes
    graph.add_node("initialize_resource_generation", initialize_resource_generation)
    graph.add_node("generate_topic_resources", generate_topic_resources)
    graph.add_node("process_module_resources", process_module_resources)
    graph.add_node("add_resources_to_final_learning_path", add_resources_to_final_learning_path)
    
    # Connect initial flow
    graph.add_edge(START, "generate_search_queries")
    graph.add_edge("generate_search_queries", "execute_web_searches")
    graph.add_edge("execute_web_searches", "create_learning_path")
    
    # Connect submodule flow with resource generation
    graph.add_edge("create_learning_path", "plan_submodules")
    graph.add_edge("plan_submodules", "initialize_resource_generation")  # Initialize resources after planning modules
    graph.add_edge("initialize_resource_generation", "generate_topic_resources")  # Generate topic resources first
    graph.add_edge("generate_topic_resources", "initialize_submodule_processing")  # Then start submodule processing
    graph.add_edge("initialize_submodule_processing", "process_submodule_batch")
    graph.add_conditional_edges(
        "process_submodule_batch",
        check_submodule_batch_processing,
        {
            "all_batches_processed": "process_module_resources",  # Process module resources after all submodules
            "continue_processing": "process_submodule_batch"
        }
    )
    graph.add_edge("process_module_resources", "finalize_enhanced_learning_path")  # Then finalize the path
    graph.add_edge("finalize_enhanced_learning_path", "add_resources_to_final_learning_path")  # Add resources to final path
    graph.add_edge("add_resources_to_final_learning_path", END)
    return graph.compile()
