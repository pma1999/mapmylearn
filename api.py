from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncio
import uvicorn
import logging
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Import the backend functionality
from main import generate_learning_path
from history.history_models import LearningPathHistory, LearningPathHistoryEntry
from services.services import validate_openai_key, validate_tavily_key

# Import the database configuration
from history.db_config import get_history_file_path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# Create FastAPI app
app = FastAPI(title="Learning Path Generator API")
# Define allowed origins for both local development and production
allowed_origins = [
    "http://localhost:3000",  # Local development
    "https://learny-peach.vercel.app",  # Vercel production domain
    "https://learny-*.vercel.app",      # Any Vercel deployment with learny- prefix
]

# Add any custom domain from environment variable (used in production)
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request and response models
class LearningPathRequest(BaseModel):
    topic: str
    parallel_count: Optional[int] = 2
    search_parallel_count: Optional[int] = 3
    submodule_parallel_count: Optional[int] = 2
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key for LLM operations")
    tavily_api_key: Optional[str] = Field(None, description="Tavily API key for search operations")

class ApiKeyValidationRequest(BaseModel):
    openai_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None

class ProgressUpdate(BaseModel):
    message: str
    timestamp: str

class HistoryEntryUpdate(BaseModel):
    favorite: Optional[bool] = None
    tags: Optional[List[str]] = None

class ImportPathRequest(BaseModel):
    json_data: str

# Store for active generation tasks with lock for thread safety
active_generations = {}
active_generations_lock = asyncio.Lock()

# Progress callback queue for each generation with lock for thread safety
progress_queues = {}
progress_queues_lock = asyncio.Lock()

# Custom class for handling datetime object serialization
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Helper functions for history management
def load_history() -> LearningPathHistory:
    try:
        history_file = get_history_file_path()
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                entries = []
                for entry_data in data.get("entries", []):
                    entries.append(LearningPathHistoryEntry(**entry_data))
                return LearningPathHistory(entries=entries)
        return LearningPathHistory()
    except Exception as e:
        logger.error(f"Error loading history: {str(e)}")
        return LearningPathHistory()

def save_history(history: LearningPathHistory) -> bool:
    try:
        history_file = get_history_file_path()
        with open(history_file, "w", encoding="utf-8") as f:
            # Use the to_dict method which properly converts datetime objects to ISO strings
            history_dict = history.to_dict()
            json.dump(history_dict, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving history: {str(e)}")
        return False

@app.post("/api/generate-learning-path")
async def api_generate_learning_path(request: LearningPathRequest, background_tasks: BackgroundTasks):
    """
    Generate a learning path for the specified topic.
    This endpoint starts a background task to generate the learning path.
    The task ID can be used to retrieve the result or track progress.
    """
    # Validate required API keys
    if not request.openai_api_key or not request.tavily_api_key:
        raise HTTPException(
            status_code=400,
            detail="Both OpenAI API key and Tavily API key are required. Please provide both keys."
        )
    
    # Validate the API keys format
    if not request.openai_api_key.startswith("sk-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid OpenAI API key format. API key should start with 'sk-'."
        )
    
    if not request.tavily_api_key.startswith("tvly-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid Tavily API key format. API key should start with 'tvly-'."
        )
    
    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # Create a queue for progress updates
    progress_queue = asyncio.Queue()
    async with progress_queues_lock:
        progress_queues[task_id] = progress_queue

    # Define a progress callback that puts messages into the queue
    async def progress_callback(message: str):
        timestamp = datetime.now().isoformat()
        update = ProgressUpdate(message=message, timestamp=timestamp)
        async with progress_queues_lock:
            if task_id in progress_queues:
                await progress_queues[task_id].put(update)
    
    # Start the learning path generation as a background task
    background_tasks.add_task(
        generate_learning_path_task,
        task_id=task_id,
        topic=request.topic,
        parallel_count=request.parallel_count,
        search_parallel_count=request.search_parallel_count,
        submodule_parallel_count=request.submodule_parallel_count,
        progress_callback=progress_callback,
        openai_api_key=request.openai_api_key,
        tavily_api_key=request.tavily_api_key
    )
    
    logger.info(f"Started learning path generation for topic '{request.topic}' with task_id: {task_id}")
    return {"task_id": task_id, "status": "started"}

async def generate_learning_path_task(
    task_id: str,
    topic: str,
    parallel_count: int = 2,
    search_parallel_count: int = 3,
    submodule_parallel_count: int = 2,
    progress_callback = None,
    openai_api_key: Optional[str] = None,
    tavily_api_key: Optional[str] = None
):
    """Background task to generate learning path."""
    try:
        # Safely update active_generations
        async with active_generations_lock:
            active_generations[task_id] = {"status": "running", "result": None}
        
        # Generate the learning path
        result = await generate_learning_path(
            topic=topic,
            parallel_count=parallel_count,
            search_parallel_count=search_parallel_count,
            submodule_parallel_count=submodule_parallel_count,
            progress_callback=progress_callback,
            openai_api_key=openai_api_key,
            tavily_api_key=tavily_api_key
        )
        
        # Safely update active_generations with result
        async with active_generations_lock:
            active_generations[task_id] = {"status": "completed", "result": result}
        
        logger.info(f"Learning path generation completed for task_id: {task_id}")
        
    except Exception as e:
        logger.exception(f"Error generating learning path for task_id {task_id}: {str(e)}")
        async with active_generations_lock:
            active_generations[task_id] = {"status": "error", "error": str(e)}
    finally:
        # Close the progress queue with proper locking
        async with progress_queues_lock:
            if task_id in progress_queues:
                await progress_queues[task_id].put(None)  # Sentinel to indicate completion

@app.post("/api/validate-api-keys")
async def validate_api_keys(request: ApiKeyValidationRequest):
    """
    Validate the provided API keys
    """
    response = {"openai": None, "tavily": None}
    
    if request.openai_api_key:
        valid, error_msg = validate_openai_key(request.openai_api_key)
        response["openai"] = {"valid": valid, "error": error_msg if not valid else None}
    
    if request.tavily_api_key:
        valid, error_msg = validate_tavily_key(request.tavily_api_key)
        response["tavily"] = {"valid": valid, "error": error_msg if not valid else None}
    
    return response

@app.get("/api/learning-path/{task_id}")
async def get_learning_path(task_id: str):
    """
    Get the status and result of a learning path generation task.
    """
    async with active_generations_lock:
        if task_id not in active_generations:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task_data = active_generations[task_id].copy()  # Create a copy to avoid race conditions
    
    return {
        "task_id": task_id,
        "status": task_data["status"],
        "result": task_data.get("result"),
        "error": task_data.get("error")
    }

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """
    Get progress updates for a learning path generation task using Server-Sent Events.
    """
    # Safely check if task exists
    async with progress_queues_lock:
        if task_id not in progress_queues:
            raise HTTPException(status_code=404, detail="Task not found")
        
        queue = progress_queues[task_id]
    
    async def event_generator():
        while True:
            update = await queue.get()
            if update is None:  # Sentinel to indicate completion
                yield f"data: {JSONResponse(content={'complete': True}).body.decode()}\n\n"
                break
            # Convert ProgressUpdate model to dict before sending
            update_dict = update.dict() if hasattr(update, 'dict') else update
            yield f"data: {JSONResponse(content=update_dict).body.decode()}\n\n"
    
    from starlette.responses import StreamingResponse
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.delete("/api/learning-path/{task_id}")
async def delete_learning_path(task_id: str):
    """
    Delete a completed learning path task to free up resources.
    """
    async with active_generations_lock:
        if task_id not in active_generations:
            raise HTTPException(status_code=404, detail="Task not found")
        
        del active_generations[task_id]
    
    async with progress_queues_lock:
        if task_id in progress_queues:
            del progress_queues[task_id]
    
    return {"status": "deleted"}

# History API endpoints (no locking needed as they don't modify the global state)
@app.get("/api/history")
async def get_history_preview(sort_by: str = "creation_date", filter_source: Optional[str] = None, search: Optional[str] = None):
    """
    Get list of learning path history entries with optional filtering and sorting.
    """
    history = load_history()
    entries = history.get_sorted_entries(sort_by=sort_by)
    
    # Apply filtering
    filtered_entries = entries
    if filter_source:
        if filter_source.lower() == "generated":
            filtered_entries = [e for e in filtered_entries if e.source == "generated"]
        elif filter_source.lower() == "imported":
            filtered_entries = [e for e in filtered_entries if e.source == "imported"]
    
    # Apply search
    if search and search.strip():
        search_term = search.lower().strip()
        filtered_entries = [e for e in filtered_entries if search_term in e.topic.lower()]
    
    # Convert to preview format
    preview_data = [entry.to_preview_dict() for entry in filtered_entries]
    return {"entries": preview_data}

@app.get("/api/history/{entry_id}")
async def get_history_entry(entry_id: str):
    """
    Get complete learning path data for a specific entry.
    """
    history = load_history()
    entry = history.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="History entry not found")
    
    return {"entry": entry.model_dump()}

@app.post("/api/history")
async def add_to_history(learning_path: dict, source: str = "generated"):
    """
    Save a new learning path to history.
    """
    try:
        history = load_history()
        entry = LearningPathHistoryEntry(
            topic=learning_path.get("topic", "Untitled"),
            path_data=learning_path,
            source=source
        )
        history.add_entry(entry)
        if save_history(history):
            return {"success": True, "entry_id": entry.id}
        else:
            raise HTTPException(status_code=500, detail="Failed to save history")
    except Exception as e:
        logger.error(f"Error adding to history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/history/{entry_id}")
async def update_history_entry(entry_id: str, update_data: HistoryEntryUpdate):
    """
    Update metadata for an existing history entry.
    """
    history = load_history()
    updates = {}
    if update_data.favorite is not None:
        updates["favorite"] = update_data.favorite
    if update_data.tags is not None:
        updates["tags"] = update_data.tags
    
    if not updates:
        return {"success": True, "message": "No updates provided"}
    
    success = history.update_entry(entry_id, **updates)
    if not success:
        raise HTTPException(status_code=404, detail="History entry not found")
    
    if save_history(history):
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail="Failed to save history updates")

@app.delete("/api/history/{entry_id}")
async def delete_history_entry(entry_id: str):
    """
    Remove a learning path from history.
    """
    history = load_history()
    success = history.remove_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="History entry not found")
    
    if save_history(history):
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail="Failed to save history after deletion")

@app.post("/api/history/import")
async def import_learning_path(request: ImportPathRequest):
    """
    Import a learning path from JSON.
    """
    try:
        learning_path = json.loads(request.json_data)
        if not isinstance(learning_path, dict) or "topic" not in learning_path or "modules" not in learning_path:
            raise HTTPException(status_code=400, detail="Invalid learning path format")
        
        history = load_history()
        entry = LearningPathHistoryEntry(
            topic=learning_path.get("topic", "Untitled"),
            path_data=learning_path,
            source="imported"
        )
        history.add_entry(entry)
        
        if save_history(history):
            return {"success": True, "entry_id": entry.id, "topic": entry.topic}
        else:
            raise HTTPException(status_code=500, detail="Failed to save imported learning path")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    except Exception as e:
        logger.error(f"Error importing learning path: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/export")
async def export_history():
    """
    Export all history entries as JSON.
    """
    history = load_history()
    history_data = history.to_dict()
    
    return history_data

@app.delete("/api/history/clear")
async def clear_history():
    """
    Clear all history entries.
    """
    try:
        if os.path.exists(get_history_file_path()):
            os.remove(get_history_file_path())
        return {"success": True}
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/health")
async def health_check():
    """Health check endpoint for deployment platforms"""
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 