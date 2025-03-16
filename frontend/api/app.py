from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Callable
import json
import asyncio
import os
import sys
import logging
from asyncio import Queue

# Add parent directory to path to access main application modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import required modules from existing application
from main import generate_learning_path
from history import history_service as hs
from models.models import SearchQuery

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# Define models for API endpoints

class LearningPathRequest(BaseModel):
    topic: str
    parallel_count: int = 2
    search_parallel_count: int = 3
    submodule_parallel_count: int = 2
    save_to_history: bool = True

class TagUpdateRequest(BaseModel):
    tags: List[str]

class FavoriteUpdateRequest(BaseModel):
    favorite: bool

# NEW: Modelo para actualización de settings
class SettingsUpdate(BaseModel):
    darkMode: Optional[bool] = None
    parallelCount: Optional[int] = None
    searchParallelCount: Optional[int] = None
    submoduleParallelCount: Optional[int] = None
    saveToHistory: Optional[bool] = None
    openaiApiKey: Optional[str] = None
    tavilyApiKey: Optional[str] = None

# Create FastAPI app
app = FastAPI(title="Learning Path Generator API")

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
connections = {}

# Main routes
@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Learning Path Generator API is running"}

@app.post("/api/learning-path")
async def create_learning_path(request: LearningPathRequest, background_tasks: BackgroundTasks):
    try:
        # Check if API keys are available
        if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("TAVILY_API_KEY"):
            return JSONResponse(
                status_code=400,
                content={"error": "Missing API keys. Please set OPENAI_API_KEY and TAVILY_API_KEY."}
            )
        
        # Create connection ID for WebSocket
        connection_id = f"task_{id(request)}"
        connections[connection_id] = Queue()
        
        # Return connection ID immediately
        return {"status": "processing", "connection_id": connection_id}
    except Exception as e:
        logger.error(f"Error starting learning path generation: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to start generation: {str(e)}"}
        )

@app.websocket("/ws/{connection_id}")
async def websocket_endpoint(websocket: WebSocket, connection_id: str):
    await websocket.accept()
    
    if connection_id not in connections:
        await websocket.send_json({"status": "error", "message": "Invalid connection ID"})
        await websocket.close()
        return
    
    queue = connections[connection_id]
    
    try:
        # Send initial message
        await websocket.send_json({"status": "connected", "message": "WebSocket connection established"})
        
        async def progress_callback(message: str):
            await queue.put({"type": "progress", "message": message})
        
        # Get parameters from the queue
        params = await queue.get()
        topic = params.get("topic")
        parallel_count = params.get("parallel_count", 2)
        search_parallel_count = params.get("search_parallel_count", 3)
        submodule_parallel_count = params.get("submodule_parallel_count", 2)
        save_to_history = params.get("save_to_history", True)
        
        # Send starting message
        await websocket.send_json({
            "type": "progress", 
            "message": f"Starting learning path generation for: {topic}"
        })
        
        # Generate learning path
        result = await generate_learning_path(
            topic=topic,
            parallel_count=parallel_count,
            search_parallel_count=search_parallel_count,
            submodule_parallel_count=submodule_parallel_count,
            progress_callback=progress_callback
        )
        
        # Save to history if needed
        if save_to_history and result:
            hs.add_learning_path(result)
        
        # Send completed result
        await websocket.send_json({
            "type": "complete",
            "result": result
        })
        
        # Process messages from the queue
        while True:
            message = await queue.get()
            if message.get("type") == "progress":
                await websocket.send_json(message)
            elif message.get("type") == "error":
                await websocket.send_json(message)
                break
            elif message.get("type") == "complete":
                await websocket.send_json(message)
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {connection_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        # Clean up
        if connection_id in connections:
            del connections[connection_id]

@app.post("/api/start-generation/{connection_id}")
async def start_generation(
    connection_id: str, 
    request: LearningPathRequest
):
    if connection_id not in connections:
        raise HTTPException(status_code=400, detail="Invalid connection ID")
    
    queue = connections[connection_id]
    await queue.put({
        "topic": request.topic,
        "parallel_count": request.parallel_count,
        "search_parallel_count": request.search_parallel_count,
        "submodule_parallel_count": request.submodule_parallel_count,
        "save_to_history": request.save_to_history
    })
    
    return {"status": "started", "connection_id": connection_id}

# History routes
@app.get("/api/history")
async def get_history():
    try:
        preview = hs.get_history_preview()
        return preview
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to retrieve history: {str(e)}"}
        )

@app.get("/api/history/{entry_id}")
async def get_history_entry(entry_id: str):
    try:
        entry = hs.get_learning_path(entry_id)
        if not entry:
            return JSONResponse(
                status_code=404,
                content={"error": "Entry not found"}
            )
        return entry
    except Exception as e:
        logger.error(f"Error getting history entry: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to retrieve history entry: {str(e)}"}
        )

@app.delete("/api/history/{entry_id}")
async def delete_history_entry(entry_id: str):
    try:
        success = hs.delete_learning_path(entry_id)
        if not success:
            return JSONResponse(
                status_code=404,
                content={"error": "Failed to delete entry or entry not found"}
            )
        return {"status": "success", "message": "Entry deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting history entry: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to delete history entry: {str(e)}"}
        )

@app.put("/api/history/{entry_id}/favorite")
async def update_favorite(entry_id: str, request: FavoriteUpdateRequest):
    try:
        success = hs.update_learning_path_metadata(entry_id, favorite=request.favorite)
        if not success:
            return JSONResponse(
                status_code=404,
                content={"error": "Failed to update entry or entry not found"}
            )
        return {"status": "success", "message": "Favorite status updated successfully"}
    except Exception as e:
        logger.error(f"Error updating favorite status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to update favorite status: {str(e)}"}
        )

@app.put("/api/history/{entry_id}/tags")
async def update_tags(entry_id: str, request: TagUpdateRequest):
    try:
        success = hs.update_learning_path_metadata(entry_id, tags=request.tags)
        if not success:
            return JSONResponse(
                status_code=404,
                content={"error": "Failed to update entry or entry not found"}
            )
        return {"status": "success", "message": "Tags updated successfully"}
    except Exception as e:
        logger.error(f"Error updating tags: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to update tags: {str(e)}"}
        )

@app.post("/api/import")
async def import_learning_path(file: UploadFile = File(...)):
    try:
        content = await file.read()
        string_data = content.decode("utf-8")
        
        success, message = hs.import_learning_path(string_data)
        if not success:
            return JSONResponse(
                status_code=400,
                content={"error": message}
            )
        return {"status": "success", "message": message}
    except Exception as e:
        logger.error(f"Error importing learning path: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to import learning path: {str(e)}"}
        )

@app.get("/api/export")
async def export_history():
    try:
        history_data = hs.export_history()
        return JSONResponse(content=json.loads(history_data))
    except Exception as e:
        logger.error(f"Error exporting history: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to export history: {str(e)}"}
        )

@app.delete("/api/history")
async def clear_history():
    try:
        success = hs.clear_history()
        if not success:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to clear history"}
            )
        return {"status": "success", "message": "History cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to clear history: {str(e)}"}
        )

# --- Updated Settings Endpoint ---
@app.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    try:
        # Update API keys if provided
        if settings.openaiApiKey:
            os.environ["OPENAI_API_KEY"] = settings.openaiApiKey
        if settings.tavilyApiKey:
            os.environ["TAVILY_API_KEY"] = settings.tavilyApiKey
        # For other settings, simply return them as updated (simulate persistencia)
        updated = settings.dict(exclude_unset=True)
        return {
            "status": "success",
            "message": "Settings updated successfully",
            **updated
        }
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to update settings: {str(e)}"}
        )

@app.get("/api/settings")
async def get_settings():
    return {
        "openaiApiKeySet": bool(os.environ.get("OPENAI_API_KEY")),
        "tavilyApiKeySet": bool(os.environ.get("TAVILY_API_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    # Run the FastAPI app
    uvicorn.run("frontend.api.app:app", host="0.0.0.0", port=8000, reload=True)
