from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import uvicorn
import logging
import json
import os
from typing import Optional, List, Dict, Any

# Import the backend functionality
from main import generate_learning_path
from history.history_models import LearningPathHistory, LearningPathHistoryEntry

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# Create FastAPI app
app = FastAPI(title="Learning Path Generator API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
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

class ProgressUpdate(BaseModel):
    message: str
    timestamp: str

class HistoryEntryUpdate(BaseModel):
    favorite: Optional[bool] = None
    tags: Optional[List[str]] = None

class ImportPathRequest(BaseModel):
    json_data: str

# Store for active generation tasks
active_generations = {}

# Progress callback queue for each generation
progress_queues = {}

# Path for storing history data
HISTORY_FILE = "learning_path_history.json"

# Helper functions for history management
def load_history() -> LearningPathHistory:
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
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
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving history: {str(e)}")
        return False

@app.post("/api/generate-learning-path")
async def api_generate_learning_path(request: LearningPathRequest, background_tasks: BackgroundTasks):
    """
    Start generating a learning path for the given topic.
    Returns a task_id that can be used to check the status and retrieve the result.
    """
    from datetime import datetime
    import uuid
    
    task_id = str(uuid.uuid4())
    progress_queues[task_id] = asyncio.Queue()
    
    # Define async progress callback
    async def progress_callback(message: str):
        await progress_queues[task_id].put({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    # Create background task
    background_tasks.add_task(
        generate_learning_path_task,
        task_id=task_id,
        topic=request.topic,
        parallel_count=request.parallel_count,
        search_parallel_count=request.search_parallel_count,
        submodule_parallel_count=request.submodule_parallel_count,
        progress_callback=progress_callback
    )
    
    logger.info(f"Started learning path generation for topic '{request.topic}' with task_id: {task_id}")
    return {"task_id": task_id, "status": "started"}

async def generate_learning_path_task(
    task_id: str,
    topic: str,
    parallel_count: int = 2,
    search_parallel_count: int = 3,
    submodule_parallel_count: int = 2,
    progress_callback = None
):
    """Background task to generate learning path."""
    try:
        active_generations[task_id] = {"status": "running", "result": None}
        
        # Generate the learning path
        result = await generate_learning_path(
            topic=topic,
            parallel_count=parallel_count,
            search_parallel_count=search_parallel_count,
            submodule_parallel_count=submodule_parallel_count,
            progress_callback=progress_callback
        )
        
        # Store the result
        active_generations[task_id] = {"status": "completed", "result": result}
        logger.info(f"Learning path generation completed for task_id: {task_id}")
        
    except Exception as e:
        logger.exception(f"Error generating learning path for task_id {task_id}: {str(e)}")
        active_generations[task_id] = {"status": "error", "error": str(e)}
    finally:
        # Close the progress queue
        if task_id in progress_queues:
            await progress_queues[task_id].put(None)  # Sentinel to indicate completion

@app.get("/api/learning-path/{task_id}")
async def get_learning_path(task_id: str):
    """
    Get the status and result of a learning path generation task.
    """
    if task_id not in active_generations:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = active_generations[task_id]
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
    if task_id not in progress_queues:
        raise HTTPException(status_code=404, detail="Task not found")
    
    queue = progress_queues[task_id]
    
    async def event_generator():
        while True:
            update = await queue.get()
            if update is None:  # Sentinel to indicate completion
                yield f"data: {JSONResponse(content={'complete': True}).body.decode()}\n\n"
                break
            yield f"data: {JSONResponse(content=update).body.decode()}\n\n"
    
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
    if task_id not in active_generations:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del active_generations[task_id]
    if task_id in progress_queues:
        del progress_queues[task_id]
    
    return {"status": "deleted"}

# History API endpoints
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
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 