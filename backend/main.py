import asyncio
import logging
import os
import json
import uuid
from typing import Optional, Callable, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Import APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.tasks.credit_tasks import grant_monthly_credits # Import the task

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from backend.core.graph_builder import build_graph
from backend.models.models import LearningPathState
from backend.config.log_config import setup_logging, log_debug_data, log_info_data, get_log_level
from backend.services.key_provider import KeyProvider, GoogleKeyProvider, PerplexityKeyProvider, BraveKeyProvider
# Importa el decorador traceable de LangSmith
from langsmith import traceable

# Import FastAPI and Rate Limiter
from fastapi import FastAPI, Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

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

# Initialize Scheduler
scheduler = AsyncIOScheduler(timezone="UTC") # Use UTC

# Define FastAPI app (assuming it's defined elsewhere or needs to be added)
# If 'app' is defined in api.py or another file, this part needs adjustment
# For now, assuming 'app' is defined here or imported
# from backend.api import app # Example if defined in api.py

# --- TEMPORARY Placeholder for FastAPI app instance ---
# Replace this with the actual FastAPI app instance from your project structure
app = FastAPI()
# --- END TEMPORARY Placeholder ---

@app.on_event("startup")
async def startup_event():
    # Schedule the job
    # Run daily at 1:00 UTC
    scheduler.add_job(grant_monthly_credits, 'cron', hour=1, minute=0, misfire_grace_time=3600) # Added grace time
    # Start the scheduler
    scheduler.start()
    logger.info("APScheduler started and 'grant_monthly_credits' job scheduled.")

@app.on_event("shutdown")
async def shutdown_event():
    # Shut down the scheduler
    scheduler.shutdown()
    logger.info("APScheduler shut down.")

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
        
        # Add a unique, persistent path_id to the result
        if formatted_output: # Only add if we have a valid path structure
            formatted_output["path_id"] = str(uuid.uuid4())
        
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
    google_key_provider: Optional[GoogleKeyProvider] = None,
    brave_key_provider: Optional[BraveKeyProvider] = None,
    desired_module_count: Optional[int] = None,
    desired_submodule_count: Optional[int] = None,
    language: str = "en",
    explanation_style: str = "standard",
    user: Optional[Any] = None  # Add user parameter for model selection
) -> Dict[str, Any]:
    """
    Asynchronous interface for course generation.
    
    Args:
        topic: The topic to generate a course for
        parallel_count: Number of modules to process in parallel
        search_parallel_count: Number of search queries to process in parallel
        submodule_parallel_count: Number of submodules to process in parallel
        progress_callback: Callback function for progress updates
        google_key_provider: Provider for Google API key
        brave_key_provider: Provider for Brave Search API key
        desired_module_count: Desired number of modules
        desired_submodule_count: Desired number of submodules per module
        language: ISO language code for content generation (e.g., 'en', 'es')
        explanation_style: Style for content explanations (e.g., 'standard', 'simple')
        user: Optional user parameter for model selection
        
    Returns:
        Dictionary with the course data
    """
    logger.info(f"Generating course for topic: {topic} with {parallel_count} parallel modules, " +
                f"{submodule_parallel_count} parallel submodules, {search_parallel_count} parallel searches, " +
                f"and language: {language}")
    
    # Create default key providers if none provided
    if not google_key_provider:
        google_key_provider = GoogleKeyProvider()
        logger.info("Using default Google key provider (from environment)")
    else:
        logger.info("Using provided Google key provider")
        
    # Use Brave provider
    if not brave_key_provider:
        brave_key_provider = BraveKeyProvider()
        logger.info("Using default Brave Search key provider (from environment)")
    else:
        logger.info("Using provided Brave Search key provider")
    
    # Initialize with English as the search language by default
    search_language = "en"
    
    # For now, use a simple heuristic: if the topic contains words specific to a region/language,
    # we could use that language for search as well
    # This can be expanded with more sophisticated detection
    spanish_indicators = ["españa", "español", "latinoamerica", "méxico", "méxico", "argentina", "colombia", "chile"]
    if any(indicator in topic.lower() for indicator in spanish_indicators) and language == "es":
        search_language = "es"
        logger.info(f"Detected topic may have more resources in Spanish. Setting search language to Spanish.")
    
    # Initialize the state with the user topic and configuration
    initial_state = {
        "user_topic": topic,
        "user": user,  # Add user for model selection
        "steps": [],
        "parallel_count": parallel_count,
        "search_parallel_count": search_parallel_count,
        "submodule_parallel_count": submodule_parallel_count,
        "progress_callback": progress_callback,
        "google_key_provider": google_key_provider,
        "brave_key_provider": brave_key_provider,
        "desired_module_count": desired_module_count,
        "desired_submodule_count": desired_submodule_count,
        "language": language,
        "search_language": search_language,
        "explanation_style": explanation_style,
    }
    
    # Configure and run the graph
    return await run_graph(initial_state)

def build_learning_path(
    topic: str,
    parallel_count: int = 2,
    search_parallel_count: int = 3,
    submodule_parallel_count: int = 2,
    progress_callback = None,
    google_key_token: Optional[str] = None,
    brave_key_token: Optional[str] = None,
    desired_module_count: Optional[int] = None,
    desired_submodule_count: Optional[int] = None,
    language: str = "en",
    explanation_style: str = "standard"
) -> Dict[str, Any]:
    """
    Build a course for the given topic using a submodule-enhanced approach.
    
    Args:
        topic: The user's learning topic
        parallel_count: Number of modules to process in parallel
        search_parallel_count: Number of search queries to execute in parallel
        submodule_parallel_count: Number of submodules to process in parallel
        progress_callback: Optional callback for reporting progress
        google_key_token: Optional token for Google API key
        brave_key_token: Optional token for Brave Search API key
        desired_module_count: Optional desired number of modules
        desired_submodule_count: Optional desired number of submodules per module
        language: ISO language code for content generation (e.g., 'en', 'es')
        explanation_style: Style for content explanations (e.g., 'standard', 'simple')
        
    Returns:
        Dictionary with the course data
    """
    logger.info(f"Generating course for topic: {topic} with {parallel_count} parallel modules, " +
                f"{submodule_parallel_count} parallel submodules, {search_parallel_count} parallel searches, " +
                f"and language: {language}")
    
    # Create key providers
    google_provider = GoogleKeyProvider(google_key_token)
    brave_provider = BraveKeyProvider(brave_key_token)
    
    # Run async version
    result = asyncio.run(generate_learning_path(
        topic=topic,
        parallel_count=parallel_count,
        search_parallel_count=search_parallel_count,
        submodule_parallel_count=submodule_parallel_count,
        progress_callback=progress_callback,
        google_key_provider=google_provider,
        brave_key_provider=brave_provider,
        desired_module_count=desired_module_count,
        desired_submodule_count=desired_submodule_count,
        language=language,
        explanation_style=explanation_style
    ))
    return result

# For testing purposes when run as a script
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate a course for a given topic")
    parser.add_argument("topic", type=str, help="The topic to create a course for")
    parser.add_argument("--parallel", type=int, default=2, help="Number of modules to process in parallel")
    parser.add_argument("--search-parallel", type=int, default=3, help="Number of search queries to execute in parallel")
    parser.add_argument("--submodule-parallel", type=int, default=2, help="Number of submodules to process in parallel")
    parser.add_argument("--google-key-token", type=str, help="Google API key token")
    parser.add_argument("--brave-key-token", type=str, help="Brave Search API key token")
    parser.add_argument("--modules", type=int, help="Desired number of modules")
    parser.add_argument("--submodules", type=int, help="Desired number of submodules per module")
    parser.add_argument("--language", type=str, default="en", help="ISO language code for content generation (e.g., 'en', 'es')")
    parser.add_argument("--style", type=str, default="standard", help="Explanation style (standard, simple, technical, example, conceptual)")
    args = parser.parse_args()
    
    result = build_learning_path(
        topic=args.topic,
        parallel_count=args.parallel,
        search_parallel_count=args.search_parallel,
        submodule_parallel_count=args.submodule_parallel,
        google_key_token=args.google_key_token,
        brave_key_token=args.brave_key_token,
        desired_module_count=args.modules,
        desired_submodule_count=args.submodules,
        language=args.language,
        explanation_style=args.style
    )
    
    # Print the course
    print(json.dumps(result, indent=2))
