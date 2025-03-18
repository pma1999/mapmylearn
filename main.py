import asyncio
import logging
import os
import json
from typing import Optional, Callable, Dict, Any
from core.graph_builder import build_graph
from models.models import LearningPathState
from config.log_config import setup_logging, log_debug_data, log_info_data, get_log_level
# Importa el decorador traceable de LangSmith
from langsmith import traceable

# Configuration from environment variables
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE = os.environ.get("LOG_FILE", "learning_path.log")
DATA_LOGGING = os.environ.get("DATA_LOGGING", "true").lower() == "true"
JSON_FORMAT = os.environ.get("JSON_FORMAT", "true").lower() == "true"

# Setup logging
setup_logging(
    log_file=LOG_FILE,
    console_level=get_log_level(LOG_LEVEL),
    file_level=logging.DEBUG,
    enable_json_logs=JSON_FORMAT,
    data_logging=DATA_LOGGING
)

logger = logging.getLogger("learning_path_generator")

# Define a function to run the graph
async def run_graph(initial_state):
    """
    Run the workflow graph with the provided initial state.
    
    Args:
        initial_state: The initial state for the graph
        
    Returns:
        The final result after graph execution
    """
    try:
        graph = build_graph()
        result = await graph.ainvoke(initial_state)
        logger.info(f"Graph execution completed successfully")
        
        # Format the output
        formatted_output = result.get("final_learning_path", {})
        if not formatted_output:
            formatted_output = {
                "topic": initial_state["user_topic"],
                "modules": result.get("modules", []),
                "execution_steps": result.get("steps", [])
            }
        
        return formatted_output
    except Exception as e:
        logger.exception(f"Error in graph execution: {str(e)}")
        return {
            "topic": initial_state["user_topic"],
            "modules": [],
            "execution_steps": [f"Error: {str(e)}"]
        }

# Decora la función de generación con @traceable para trazar el flujo completo
@traceable
async def generate_learning_path(
    topic: str,
    parallel_count: int = 2,
    search_parallel_count: int = 3,
    submodule_parallel_count: int = 2,
    progress_callback = None,
    google_api_key: Optional[str] = None,
    pplx_api_key: Optional[str] = None,
    desired_module_count: Optional[int] = None,
    desired_submodule_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Asynchronous interface for learning path generation.
    """
    logger.info(f"Generating learning path for topic: {topic} with {parallel_count} parallel modules, " +
                f"{submodule_parallel_count} parallel submodules, and {search_parallel_count} parallel searches")
    
    # Check API key validity
    if google_api_key:
        logger.info("Using provided Google API key")
    else:
        logger.info("No Google API key provided, using environment variable")
        
    if not pplx_api_key:
        logger.info("No Perplexity API key provided, using environment variable")
    
    initial_state: LearningPathState = {
        "user_topic": topic,
        "google_api_key": google_api_key,
        "pplx_api_key": pplx_api_key,
        "search_parallel_count": search_parallel_count,
        "parallel_count": parallel_count,
        "submodule_parallel_count": submodule_parallel_count,
        "steps": [],
        "progress_callback": progress_callback
    }
    
    # Add desired module count if specified
    if desired_module_count:
        initial_state["desired_module_count"] = desired_module_count
        
    # Add desired submodule count if specified
    if desired_submodule_count:
        initial_state["desired_submodule_count"] = desired_submodule_count
    
    # Configure and run the graph
    return await run_graph(initial_state)

def build_learning_path(
    topic: str,
    parallel_count: int = 2,
    search_parallel_count: int = 3,
    submodule_parallel_count: int = 2,
    progress_callback = None,
    google_api_key: Optional[str] = None,
    pplx_api_key: Optional[str] = None,
    desired_module_count: Optional[int] = None,
    desired_submodule_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Build a learning path for the given topic using a submodule-enhanced approach.
    
    Args:
        topic: The user's learning topic
        parallel_count: Number of modules to process in parallel
        search_parallel_count: Number of search queries to execute in parallel
        submodule_parallel_count: Number of submodules to process in parallel
        progress_callback: Optional callback for reporting progress
        google_api_key: Optional Google API key
        pplx_api_key: Optional Perplexity API key
        desired_module_count: Optional desired number of modules
        desired_submodule_count: Optional desired number of submodules per module
        
    Returns:
        Dictionary with the learning path data
    """
    logger.info(f"Generating learning path for topic: {topic} with {parallel_count} parallel modules, " +
                f"{submodule_parallel_count} parallel submodules, and {search_parallel_count} parallel searches")
    
    # Check API key validity
    if google_api_key:
        logger.info("Using provided Google API key")
    else:
        logger.info("No Google API key provided, using environment variable")
        
    if not pplx_api_key:
        logger.info("No Perplexity API key provided, using environment variable")
    
    initial_state: LearningPathState = {
        "user_topic": topic,
        "google_api_key": google_api_key,
        "pplx_api_key": pplx_api_key,
        "search_parallel_count": search_parallel_count,
        "parallel_count": parallel_count,
        "submodule_parallel_count": submodule_parallel_count,
        "steps": [],
        "progress_callback": progress_callback
    }
    
    # Add desired module count if specified
    if desired_module_count:
        initial_state["desired_module_count"] = desired_module_count
        
    # Add desired submodule count if specified
    if desired_submodule_count:
        initial_state["desired_submodule_count"] = desired_submodule_count
    
    # Configure and run the graph
    result = asyncio.run(run_graph(initial_state))
    return result

# For testing purposes when run as a script
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate a learning path for a given topic")
    parser.add_argument("topic", type=str, help="The topic to create a learning path for")
    parser.add_argument("--parallel", type=int, default=2, help="Number of modules to process in parallel")
    parser.add_argument("--search-parallel", type=int, default=3, help="Number of search queries to execute in parallel")
    parser.add_argument("--submodule-parallel", type=int, default=2, help="Number of submodules to process in parallel")
    parser.add_argument("--google-api-key", type=str, help="Google API key (or use GOOGLE_API_KEY env var)")
    parser.add_argument("--pplx-api-key", type=str, help="Perplexity API key (or use PPLX_API_KEY env var)")
    parser.add_argument("--modules", type=int, help="Desired number of modules")
    parser.add_argument("--submodules", type=int, help="Desired number of submodules per module")
    args = parser.parse_args()
    
    result = build_learning_path(
        topic=args.topic,
        parallel_count=args.parallel,
        search_parallel_count=args.search_parallel,
        submodule_parallel_count=args.submodule_parallel,
        google_api_key=args.google_api_key,
        pplx_api_key=args.pplx_api_key,
        desired_module_count=args.modules,
        desired_submodule_count=args.submodules
    )
    
    # Print the learning path
    print(json.dumps(result, indent=2))
