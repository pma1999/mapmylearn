from fastapi import FastAPI, BackgroundTasks, Request, HTTPException, Depends, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import asyncio
import uvicorn
import logging
import json
import os
from typing import Optional, List, Dict, Any, Callable, Awaitable, Union
from datetime import datetime
import uuid
import time
import httpx

# Initialize startup time for health check and uptime reporting
startup_time = time.time()

# Import the backend functionality
from main import generate_learning_path
from services.services import validate_google_key, validate_perplexity_key

# Import the new API key management services
from services.key_management import ApiKeyManager
from services.key_provider import GoogleKeyProvider, PerplexityKeyProvider

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
    datefmt="%Y-%m-%dT%H:%M:%S.%f"
)
logger = logging.getLogger(__name__)

# Initialize the API Key Manager singleton
key_manager = ApiKeyManager()

# Create FastAPI app
app = FastAPI(
    title="Learny API",
    description="API for Learny Learning Path Generator",
    version="0.1.0"
)

# --------------------------------------------------------------------------------
# Configuración automática de CORS y seguridad de endpoints (Mejora 1)
# --------------------------------------------------------------------------------
# Se configuran los orígenes permitidos de forma automática según el entorno:
# - En producción (cuando existe la variable "RAILWAY_STATIC_URL") se permiten
#   los dominios de los despliegues de Vercel y Railway.
# - En desarrollo, se permite únicamente el origen local.
if os.getenv("RAILWAY_STATIC_URL"):
    # Entorno de producción
    allowed_origins = [
        "https://learny-peach.vercel.app",
        "https://learny-pablos-projects-d80d0b2f.vercel.app",
        "https://learny-git-main-pablos-projects-d80d0b2f.vercel.app",
        "https://web-production-62f88.up.railway.app"
    ]
    if os.getenv("FRONTEND_URL"):
        allowed_origins.append(os.getenv("FRONTEND_URL"))
else:
    # Entorno de desarrollo local
    allowed_origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------------------------------------------------------------
# Fin de configuración automática de CORS
# --------------------------------------------------------------------------------

# Request and response models
class LearningPathRequest(BaseModel):
    topic: str
    parallel_count: Optional[int] = 2
    search_parallel_count: Optional[int] = 3
    submodule_parallel_count: Optional[int] = 2
    desired_module_count: Optional[int] = None
    desired_submodule_count: Optional[int] = None
    google_key_token: Optional[str] = Field(None, description="Token for Google API key")
    pplx_key_token: Optional[str] = Field(None, description="Token for Perplexity API key")

class ApiKeyAuthRequest(BaseModel):
    google_api_key: Optional[str] = Field(None, description="Google API key for LLM operations")
    pplx_api_key: Optional[str] = Field(None, description="Perplexity API key for search operations")
    
class ApiKeyAuthResponse(BaseModel):
    google_key_token: Optional[str] = None
    pplx_key_token: Optional[str] = None
    google_key_valid: bool = False
    pplx_key_valid: bool = False
    google_key_error: Optional[str] = None
    pplx_key_error: Optional[str] = None

class ApiKeyValidationRequest(BaseModel):
    google_api_key: Optional[str] = None
    pplx_api_key: Optional[str] = None

class ProgressUpdate(BaseModel):
    message: str
    timestamp: str

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

@app.post("/api/auth/api-keys")
async def authenticate_api_keys(request: ApiKeyAuthRequest, req: Request):
    """
    Validate API keys and generate secure tokens for them.
    This endpoint creates short-lived tokens to reference the API keys securely.
    """
    response = ApiKeyAuthResponse()
    client_ip = req.client.host if req.client else None
    
    # Validate and store Google API key if provided
    if request.google_api_key:
        is_valid, error_message = validate_google_key(request.google_api_key)
        response.google_key_valid = is_valid
        if is_valid:
            try:
                # Store key securely and get token
                google_token = key_manager.store_key(
                    key_manager.KEY_TYPE_GOOGLE, 
                    request.google_api_key,
                    ip_address=client_ip
                )
                response.google_key_token = google_token
                logger.info(f"Generated token for Google API key from {client_ip}")
            except Exception as e:
                response.google_key_valid = False
                response.google_key_error = f"Error storing API key: {str(e)}"
        else:
            response.google_key_error = error_message
    
    # Validate and store Perplexity API key if provided
    if request.pplx_api_key:
        is_valid, error_message = validate_perplexity_key(request.pplx_api_key)
        response.pplx_key_valid = is_valid
        if is_valid:
            try:
                # Store key securely and get token
                pplx_token = key_manager.store_key(
                    key_manager.KEY_TYPE_PERPLEXITY, 
                    request.pplx_api_key,
                    ip_address=client_ip
                )
                response.pplx_key_token = pplx_token
                logger.info(f"Generated token for Perplexity API key from {client_ip}")
            except Exception as e:
                response.pplx_key_valid = False
                response.pplx_key_error = f"Error storing API key: {str(e)}"
        else:
            response.pplx_key_error = error_message
    
    return response

@app.post("/api/generate-learning-path")
async def api_generate_learning_path(request: LearningPathRequest, background_tasks: BackgroundTasks, req: Request):
    """
    Generate a learning path for the specified topic.
    This endpoint starts a background task to generate the learning path.
    The task ID can be used to retrieve the result or track progress.
    """
    client_ip = req.client.host if req.client else None
    
    # Check if at least one of the key tokens is provided
    if not request.google_key_token and not request.pplx_key_token:
        raise HTTPException(
            status_code=400,
            detail="API key tokens are required. Please provide valid API keys through the /api/auth/api-keys endpoint."
        )
    
    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # Create a queue for progress updates
    progress_queue = asyncio.Queue()
    async with progress_queues_lock:
        progress_queues[task_id] = progress_queue
        
    # Initialize the task in active_generations dictionary
    async with active_generations_lock:
        active_generations[task_id] = {"status": "running", "result": None}

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
        google_key_token=request.google_key_token,
        pplx_key_token=request.pplx_key_token,
        client_ip=client_ip,
        desired_module_count=request.desired_module_count,
        desired_submodule_count=request.desired_submodule_count
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
    google_key_token: Optional[str] = None,
    pplx_key_token: Optional[str] = None,
    client_ip: Optional[str] = None,
    desired_module_count: Optional[int] = None,
    desired_submodule_count: Optional[int] = None
):
    """
    Execute the learning path generation task.
    """
    try:
        logging.info(f"Starting learning path generation for: {topic}")
        
        # Get keys directly from key manager - similar to how validation works
        google_api_key = None
        pplx_api_key = None
        
        # Retrieve the actual API keys using the tokens if available
        if google_key_token:
            try:
                google_api_key = key_manager.get_key(google_key_token, key_manager.KEY_TYPE_GOOGLE, ip_address=client_ip)
                logging.info("Successfully retrieved Google API key from token")
            except Exception as e:
                logging.warning(f"Failed to retrieve Google API key from token: {str(e)}")
                # Try fallback to environment variable
                google_api_key = key_manager.get_env_key(key_manager.KEY_TYPE_GOOGLE)
        else:
            # Try environment variable
            google_api_key = key_manager.get_env_key(key_manager.KEY_TYPE_GOOGLE)
            
        if pplx_key_token:
            try:
                pplx_api_key = key_manager.get_key(pplx_key_token, key_manager.KEY_TYPE_PERPLEXITY, ip_address=client_ip)
                logging.info("Successfully retrieved Perplexity API key from token")
            except Exception as e:
                logging.warning(f"Failed to retrieve Perplexity API key from token: {str(e)}")
                # Try fallback to environment variable
                pplx_api_key = key_manager.get_env_key(key_manager.KEY_TYPE_PERPLEXITY)
        else:
            # Try environment variable
            pplx_api_key = key_manager.get_env_key(key_manager.KEY_TYPE_PERPLEXITY)
        
        # Create key providers with direct keys instead of tokens
        google_provider = GoogleKeyProvider(google_api_key)
        pplx_provider = PerplexityKeyProvider(pplx_api_key)
        
        # Pass callback to update front-end with progress
        result = await generate_learning_path(
            topic,
            parallel_count=parallel_count,
            search_parallel_count=search_parallel_count, 
            submodule_parallel_count=submodule_parallel_count,
            progress_callback=progress_callback,
            google_key_provider=google_provider,
            pplx_key_provider=pplx_provider,
            desired_module_count=desired_module_count,
            desired_submodule_count=desired_submodule_count
        )
        
        # Store result in active_generations
        async with active_generations_lock:
            active_generations[task_id]["result"] = result
            active_generations[task_id]["status"] = "completed"
            
        logging.info(f"Learning path generation completed for: {topic}")
        
    except Exception as e:
        logging.exception(f"Error generating learning path: {str(e)}")
        # Update status to failed
        async with active_generations_lock:
            active_generations[task_id]["status"] = "failed"
            active_generations[task_id]["error"] = str(e)

@app.post("/api/validate-api-keys")
async def validate_api_keys(request: ApiKeyValidationRequest):
    """
    Validate the format and functionality of API keys.
    """
    response = {}
    
    # Validate Google API key if provided
    if request.google_api_key:
        is_valid, error_message = validate_google_key(request.google_api_key)
        response["google_key_valid"] = is_valid
        if not is_valid:
            response["google_key_error"] = error_message
    
    # Validate Perplexity API key if provided
    if request.pplx_api_key:
        is_valid, error_message = validate_perplexity_key(request.pplx_api_key)
        response["pplx_key_valid"] = is_valid
        if not is_valid:
            response["pplx_key_error"] = error_message
    
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

@app.get("/api/health")
async def health_check():
    """
    Basic health check endpoint.
    """
    return {
        "status": "ok",
        "uptime": f"{time.time() - startup_time:.2f} seconds"
    }

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
