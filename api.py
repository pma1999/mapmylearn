from fastapi import FastAPI, BackgroundTasks, Request, HTTPException, Depends, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
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
import traceback

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
# Global exception handler middleware
# --------------------------------------------------------------------------------
@app.middleware("http")
async def global_exception_middleware(request: Request, call_next):
    """
    Global middleware to catch and handle unhandled exceptions.
    Ensures all errors are properly logged and return consistent JSON responses.
    """
    try:
        # Process the request through the normal flow
        return await call_next(request)
    except Exception as e:
        # Get detailed exception information for logging
        exc_info = traceback.format_exc()
        
        # Generate a unique error reference ID
        error_id = str(uuid.uuid4())
        
        # Log the detailed error with reference ID
        logger.exception(f"Unhandled exception in request {request.url.path} [Error ID: {error_id}]: {str(e)}\n{exc_info}")
        
        # Create a sanitized error response that doesn't expose internal details
        error_response = {
            "status": "failed",
            "error": {
                "message": "An unexpected error occurred while processing your request. Please try again later.",
                "error_id": error_id,
                "type": "server_error"
            }
        }
        
        # Return a consistent JSON response with an appropriate HTTP status code
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )

# Add a custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors.
    Returns user-friendly error messages for input validation failures.
    """
    # Extract error details from the validation exception
    errors = []
    for error in exc.errors():
        error_location = " -> ".join([str(loc) for loc in error["loc"] if loc != "body"])
        errors.append({
            "field": error_location,
            "message": error["msg"]
        })
    
    # Log the validation error
    logger.warning(f"Validation error in request {request.url.path}: {errors}")
    
    # Return a structured response
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "failed", 
            "error": {
                "message": "Invalid input data. Please check your request parameters.",
                "type": "validation_error",
                "details": errors
            }
        }
    )

# Add a custom exception handler for HTTP exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom handler for HTTP exceptions.
    Ensures all HTTP exceptions follow a consistent error response format.
    """
    # Create a formatted error response
    error_response = {
        "status": "failed",
        "error": {
            "message": exc.detail,
            "type": "http_error"
        }
    }
    
    # Add headers from the exception if present
    headers = getattr(exc, "headers", None)
    
    # Log the HTTP exception
    logger.warning(f"HTTP exception in request {request.url.path}: {exc.status_code} - {exc.detail}")
    
    # Return a structured JSON response
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=headers
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

# Custom error class for learning path generation errors
class LearningPathGenerationError(Exception):
    """Custom exception for learning path generation errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

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
                logger.exception(f"Error storing Google API key: {str(e)}")
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
                logger.exception(f"Error storing Perplexity API key: {str(e)}")
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
    try:
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
    except Exception as e:
        # Clean up the queue and task entry if background task setup fails
        async with progress_queues_lock:
            if task_id in progress_queues:
                del progress_queues[task_id]
                
        async with active_generations_lock:
            if task_id in active_generations:
                del active_generations[task_id]
                
        logger.exception(f"Failed to start learning path generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start learning path generation task. Please try again later."
        )

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
    Execute the learning path generation task with comprehensive error handling.
    Ensures all exceptions are caught, logged, and reported through progress updates.
    """
    # Define a wrapper progress callback to ensure messages are logged
    async def enhanced_progress_callback(message: str):
        logging.info(f"Progress update for task {task_id}: {message}")
        if progress_callback:
            await progress_callback(message)
    
    google_api_key = None
    pplx_api_key = None
    
    try:
        logging.info(f"Starting learning path generation for: {topic}")
        
        # Send initial progress message
        await enhanced_progress_callback(f"Starting learning path generation for: {topic}")
        
        # Retrieve Google API key with proper error handling
        try:
            if google_key_token:
                try:
                    google_api_key = key_manager.get_key(google_key_token, key_manager.KEY_TYPE_GOOGLE, ip_address=client_ip)
                    logging.info("Successfully retrieved Google API key from token")
                    await enhanced_progress_callback("Successfully retrieved Google API key")
                except Exception as e:
                    logging.warning(f"Failed to retrieve Google API key from token: {str(e)}")
                    await enhanced_progress_callback("Using default Google API key from environment")
                    # Try fallback to environment variable
                    google_api_key = key_manager.get_env_key(key_manager.KEY_TYPE_GOOGLE)
                    
                    if not google_api_key:
                        raise LearningPathGenerationError(
                            "Failed to retrieve Google API key and no fallback key available",
                            {"source": "google_key_retrieval"}
                        )
            else:
                # Try environment variable
                google_api_key = key_manager.get_env_key(key_manager.KEY_TYPE_GOOGLE)
                if google_api_key:
                    await enhanced_progress_callback("Using default Google API key from environment")
                else:
                    raise LearningPathGenerationError(
                        "No Google API key provided and no fallback key available",
                        {"source": "google_key_retrieval"}
                    )
        except Exception as e:
            # Log the detailed error but provide a sanitized message to the user
            logging.exception(f"Error retrieving Google API key: {str(e)}")
            error_msg = "Failed to retrieve Google API key. Please provide a valid key."
            await enhanced_progress_callback(f"Error: {error_msg}")
            raise LearningPathGenerationError(error_msg, {"source": "google_key_retrieval"})
            
        # Retrieve Perplexity API key with proper error handling
        try:
            if pplx_key_token:
                try:
                    pplx_api_key = key_manager.get_key(pplx_key_token, key_manager.KEY_TYPE_PERPLEXITY, ip_address=client_ip)
                    logging.info("Successfully retrieved Perplexity API key from token")
                    await enhanced_progress_callback("Successfully retrieved Perplexity API key")
                except Exception as e:
                    logging.warning(f"Failed to retrieve Perplexity API key from token: {str(e)}")
                    await enhanced_progress_callback("Using default Perplexity API key from environment")
                    # Try fallback to environment variable
                    pplx_api_key = key_manager.get_env_key(key_manager.KEY_TYPE_PERPLEXITY)
                    
                    if not pplx_api_key:
                        raise LearningPathGenerationError(
                            "Failed to retrieve Perplexity API key and no fallback key available",
                            {"source": "perplexity_key_retrieval"}
                        )
            else:
                # Try environment variable
                pplx_api_key = key_manager.get_env_key(key_manager.KEY_TYPE_PERPLEXITY)
                if pplx_api_key:
                    await enhanced_progress_callback("Using default Perplexity API key from environment")
                else:
                    raise LearningPathGenerationError(
                        "No Perplexity API key provided and no fallback key available",
                        {"source": "perplexity_key_retrieval"}
                    )
        except Exception as e:
            # Log the detailed error but provide a sanitized message to the user
            logging.exception(f"Error retrieving Perplexity API key: {str(e)}")
            error_msg = "Failed to retrieve Perplexity API key. Please provide a valid key."
            await enhanced_progress_callback(f"Error: {error_msg}")
            raise LearningPathGenerationError(error_msg, {"source": "perplexity_key_retrieval"})
        
        # Create key providers with direct keys instead of tokens
        try:
            google_provider = GoogleKeyProvider(google_api_key)
            pplx_provider = PerplexityKeyProvider(pplx_api_key)
        except Exception as e:
            logging.exception(f"Error creating key providers: {str(e)}")
            error_msg = "Failed to initialize API key providers. Please try again with valid keys."
            await enhanced_progress_callback(f"Error: {error_msg}")
            raise LearningPathGenerationError(error_msg, {"source": "key_provider_initialization"})
        
        await enhanced_progress_callback(f"Preparing to generate learning path for '{topic}' with {parallel_count} modules in parallel")
        
        # Pass callback to update front-end with progress
        try:
            result = await generate_learning_path(
                topic,
                parallel_count=parallel_count,
                search_parallel_count=search_parallel_count, 
                submodule_parallel_count=submodule_parallel_count,
                progress_callback=enhanced_progress_callback,
                google_key_provider=google_provider,
                pplx_key_provider=pplx_provider,
                desired_module_count=desired_module_count,
                desired_submodule_count=desired_submodule_count
            )
        except Exception as e:
            # This is an unexpected error in the learning path generation process
            # Log the detailed error but provide a sanitized message to the user
            error_message = f"Unexpected error during learning path generation: {str(e)}"
            logging.exception(error_message)
            
            # Create a sanitized user-facing error message
            user_error_msg = "An error occurred during learning path generation. Please try again later."
            
            # Send error message to frontend
            await enhanced_progress_callback(f"Error: {user_error_msg}")
            
            # Update task status with sanitized error info - this is an unexpected error
            async with active_generations_lock:
                active_generations[task_id]["status"] = "failed"
                active_generations[task_id]["error"] = {
                    "message": user_error_msg,
                    "type": "unexpected_error"
                }
            return
        
        # Send completion message
        await enhanced_progress_callback("Learning path generation completed successfully!")
        
        # Store result in active_generations
        async with active_generations_lock:
            active_generations[task_id]["result"] = result
            active_generations[task_id]["status"] = "completed"
            
        logging.info(f"Learning path generation completed for: {topic}")
        
    except LearningPathGenerationError as e:
        # These errors have already been logged and reported through the progress callback
        async with active_generations_lock:
            active_generations[task_id]["status"] = "failed"
            active_generations[task_id]["error"] = {
                "message": e.message,
                "type": "learning_path_generation_error",
                "details": e.details
            }
    except Exception as e:
        # Catch any other unexpected exceptions
        error_message = f"Unexpected error during learning path generation: {str(e)}"
        logging.exception(error_message)
        
        # Create a sanitized user-facing error message
        user_error_msg = "An unexpected error occurred while generating your learning path. Please try again later."
        
        # Send error message to frontend
        await enhanced_progress_callback(f"Error: {user_error_msg}")
        
        # Update status to failed with sanitized error info
        async with active_generations_lock:
            active_generations[task_id]["status"] = "failed"
            active_generations[task_id]["error"] = {
                "message": user_error_msg,
                "type": "unexpected_error"
            }

@app.post("/api/validate-api-keys")
async def validate_api_keys(request: ApiKeyValidationRequest):
    """
    Validate the format and functionality of API keys.
    """
    try:
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
    except Exception as e:
        logger.exception(f"Error validating API keys: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to validate API keys. Please try again later."
        )

@app.get("/api/learning-path/{task_id}")
async def get_learning_path(task_id: str):
    """
    Get the status and result of a learning path generation task.
    """
    try:
        async with active_generations_lock:
            if task_id not in active_generations:
                raise HTTPException(
                    status_code=404, 
                    detail="Learning path task not found. The task ID may be invalid or the task has been deleted."
                )
            
            task_data = active_generations[task_id].copy()  # Create a copy to avoid race conditions
        
        return {
            "task_id": task_id,
            "status": task_data["status"],
            "result": task_data.get("result"),
            "error": task_data.get("error")
        }
    except HTTPException:
        # Re-raise HTTP exceptions to be handled by our custom handler
        raise
    except Exception as e:
        logger.exception(f"Error retrieving learning path for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve learning path data. Please try again later."
        )

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """
    Get progress updates for a learning path generation task using Server-Sent Events.
    """
    try:
        # Safely check if task exists
        async with progress_queues_lock:
            if task_id not in progress_queues:
                raise HTTPException(
                    status_code=404, 
                    detail="Progress updates not available. The task ID may be invalid or the task has been completed."
                )
            
            queue = progress_queues[task_id]
        
        async def event_generator():
            try:
                # Send initial message to establish connection
                yield "data: {\"message\": \"Connection established\", \"timestamp\": \"" + datetime.now().isoformat() + "\"}\n\n"
                
                while True:
                    update = await queue.get()
                    if update is None:  # Sentinel to indicate completion
                        yield "data: {\"complete\": true}\n\n"
                        break
                    
                    # Convert ProgressUpdate model to dict before sending
                    if hasattr(update, 'dict'):
                        update_dict = update.dict()
                    else:
                        update_dict = update
                    
                    # Format as SSE data line with proper line endings
                    yield f"data: {json.dumps(update_dict)}\n\n"
            except asyncio.CancelledError:
                logger.info(f"SSE connection for task {task_id} was cancelled")
                raise
            except Exception as e:
                logger.error(f"Error in SSE stream for task {task_id}: {str(e)}")
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions to be handled by our custom handler
        raise
    except Exception as e:
        logger.exception(f"Error setting up progress stream for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to set up progress updates stream. Please try again later."
        )

@app.delete("/api/learning-path/{task_id}")
async def delete_learning_path(task_id: str):
    """
    Delete a learning path generation task and its progress queue.
    """
    try:
        # Check if the task exists
        task_existed = False
        async with active_generations_lock:
            if task_id in active_generations:
                del active_generations[task_id]
                task_existed = True
        
        # Clean up the progress queue if it exists
        async with progress_queues_lock:
            if task_id in progress_queues:
                await progress_queues[task_id].put(None)  # Signal completion
                del progress_queues[task_id]
                task_existed = True
        
        if not task_existed:
            raise HTTPException(
                status_code=404,
                detail="Learning path task not found. The task ID may be invalid or the task has already been deleted."
            )
        
        logger.info(f"Deleted learning path task: {task_id}")
        return {"status": "success", "message": "Learning path task deleted successfully."}
    except HTTPException:
        # Re-raise HTTP exceptions to be handled by our custom handler
        raise
    except Exception as e:
        logger.exception(f"Error deleting learning path task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete learning path task. Please try again later."
        )

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
