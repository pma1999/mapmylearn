import asyncio
import logging
import os
from typing import Optional, Callable, Dict, Any
from core.graph_builder import build_graph
from models.models import LearningPathState
from config.log_config import setup_logging, log_debug_data, log_info_data, get_log_level

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

async def generate_learning_path(
    topic: str, 
    parallel_count: int = 1, 
    search_parallel_count: int = 3,
    submodule_parallel_count: int = 2,
    progress_callback: Optional[Callable] = None
) -> dict:
    logger = logging.getLogger("learning_path_generator")
    logger.info(f"Generating learning path for topic: {topic} with {parallel_count} parallel modules, " +
                f"{submodule_parallel_count} parallel submodules, and {search_parallel_count} parallel searches")
    learning_graph = build_graph()
    initial_state: LearningPathState = {
        "user_topic": topic,
        "search_queries": None,
        "search_results": None,
        "modules": None,
        "steps": [],
        "current_module_index": None,
        "module_search_queries": None,
        "module_search_results": None,
        "developed_modules": None,
        "final_learning_path": None,
        "parallel_count": parallel_count,
        "module_batches": None,
        "current_batch_index": None,
        "modules_in_process": None,
        "progress_callback": progress_callback,
        "search_parallel_count": search_parallel_count,
        "enhanced_modules": None,
        "submodule_parallel_count": submodule_parallel_count,
        "submodule_batches": None,
        "current_submodule_batch_index": None,
        "submodules_in_process": None,
        "developed_submodules": None
    }
    logger.debug("Initialized learning path state")
    log_debug_data(logger, "Initial state", initial_state)
    try:
        result = await learning_graph.ainvoke(initial_state)
        logger.info(f"Graph execution completed successfully for topic: {topic}")
        log_info_data(logger, "Raw graph result", result)
        formatted_output = result["final_learning_path"] if result.get("final_learning_path") else {
            "topic": topic,
            "modules": result.get("modules", []),
            "execution_steps": result["steps"]
        }
        logger.info(f"Successfully generated learning path for {topic}")
        log_info_data(logger, "Final formatted output", formatted_output)
        return formatted_output
    except Exception as e:
        logger.exception(f"Error in graph execution: {str(e)}")
        return {
            "topic": topic,
            "modules": [],
            "execution_steps": [f"Error: {str(e)}"]
        }

# For testing purposes when run as a script
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Learning Path Generator")
    parser.add_argument("topic", nargs="?", default="Quantum computing for beginners", help="Topic to generate learning path for")
    parser.add_argument("--parallel", type=int, default=2, help="Number of modules to process in parallel")
    parser.add_argument("--search-parallel", type=int, default=3, help="Number of searches to execute in parallel")
    parser.add_argument("--submodule-parallel", type=int, default=2, help="Number of submodules to process in parallel")
    parser.add_argument("--log-level", choices=["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Set logging level")
    parser.add_argument("--log-file", default="learning_path.log", help="Log file path")
    parser.add_argument("--disable-json", action="store_true", help="Disable JSON formatting in logs")
    parser.add_argument("--disable-data-logging", action="store_true", help="Disable detailed data logging")
    args = parser.parse_args()
    
    setup_logging(
        log_file=args.log_file,
        console_level=get_log_level(args.log_level),
        file_level=logging.DEBUG,
        enable_json_logs=not args.disable_json,
        data_logging=not args.disable_data_logging
    )
    
    logger = logging.getLogger("main")
    logger.info(f"Starting Learning Path Generator with topic: {args.topic}")
    result = asyncio.run(generate_learning_path(
        topic=args.topic,
        parallel_count=args.parallel,
        search_parallel_count=args.search_parallel,
        submodule_parallel_count=args.submodule_parallel
    ))
    
    logger.info("Learning path generation completed")
    print(f"Learning Path for: {result['topic']}")
    print("\nExecution Steps:")
    for step in result.get("execution_steps", []):
        print(f"- {step}")
    print("\nModules:")
    for i, module in enumerate(result.get("modules", []), 1):
        print(f"\nModule {i}: {module.get('title')}")
        print(f"Description: {module.get('description')}")
        submodules = module.get("submodules", [])
        if submodules:
            print(f"Number of submodules: {len(submodules)}")
            for j, submodule in enumerate(submodules, 1):
                print(f"  Submodule {j}: {submodule.get('title')}")
                print(f"    Description: {submodule.get('description')}")
                content = submodule.get("content", "")
                if content:
                    print(f"    Content length: {len(content)} characters")
                    print(f"    Preview: {content[:100]}..." if len(content) > 100 else content)
                else:
                    print("    WARNING: No content available!")
        elif "content" in module:
            content = module["content"]
            print("\nContent:")
            print(content[:500] + "..." if len(content) > 500 else content)
    print(f"\nLog file: {args.log_file}")
    print("To analyze logs, run:")
    print(f"python diagnostic.py {args.log_file} --summary")
