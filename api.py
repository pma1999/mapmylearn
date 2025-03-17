from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import uvicorn
import logging
from typing import Optional, List, Dict, Any

# Import the backend functionality
from main import generate_learning_path

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

# Store for active generation tasks
active_generations = {}

# Progress callback queue for each generation
progress_queues = {}

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

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 