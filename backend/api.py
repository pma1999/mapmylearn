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
import sys
from typing import Optional, List, Dict, Any, Callable, Awaitable, Union
from datetime import datetime
import uuid
import time
import httpx
import traceback

# Database imports
from backend.config.database import engine, Base, get_db
from backend.routes.auth import router as auth_router
from backend.routes.learning_paths import router as learning_paths_router
from backend.routes.admin import router as admin_router
from backend.routes.chatbot import router as chatbot_router
from backend.models.auth_models import User, CreditTransaction
from backend.utils.auth import decode_access_token

# Import rate limiter
from backend.utils.rate_limiter import rate_limiting_middleware

# Initialize startup time for health check and uptime reporting
startup_time = time.time()

# Add proper path handling for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# First try with relative imports (when run directly)
try:
    # Import the backend functionality - try both approaches
    try:
        from main import generate_learning_path
        from services.services import validate_google_key, validate_perplexity_key
        from services.key_management import ApiKeyManager
        from services.key_provider import GoogleKeyProvider, PerplexityKeyProvider
    except ImportError:
        # If that fails, try with backend prefix (when run as a package)
        from backend.main import generate_learning_path
        from backend.services.services import validate_google_key, validate_perplexity_key
        from backend.services.key_management import ApiKeyManager
        from backend.services.key_provider import GoogleKeyProvider, PerplexityKeyProvider
except ImportError as e:
    # If all import approaches fail, log the error
    logging.error(f"Import error: {str(e)}")
    # Re-raise to fail fast with a clear error
    raise

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
    title="MapMyLearn API",
    description="API for MapMyLearn Learning Path Generator",
    version="0.1.0"
)

# Create the database tables if they don't exist
# We'll use alembic for proper migrations in production
@app.on_event("startup")
async def startup_db_client():
    logger.info("Creating database tables if they don't exist...")
    try:
        # Create base tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
        
        # Apply migrations for schema updates
        from backend.config.database import apply_migrations
        logger.info("Applying database migrations...")
        apply_migrations()
        logger.info("Database migrations applied successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        # Don't raise the exception - we'll let the app start anyway and fail on actual db operations
        # This allows the app to run without a database for development

# Include the auth, learning path, and admin routers
app.include_router(auth_router, prefix="/api")
app.include_router(learning_paths_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")

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
# Configuración automática de CORS y seguridad de endpoints 
# --------------------------------------------------------------------------------
# Se configuran los orígenes permitidos de forma automática según el entorno:
# - En producción se permiten los dominios específicos de Vercel y Railway.
# - En desarrollo, se permite únicamente el origen local.
environment = os.getenv("ENVIRONMENT", "development")
is_production = environment == "production"

if is_production:
    # Entorno de producción - usar lista explícita de dominios permitidos
    allowed_origins = [
        "https://mapmylearn.vercel.app",               # Producción principal
        "https://mapmylearn-pablos-projects-d80d0b2f.vercel.app",       # Despliegue específico
        "https://mapmylearn-git-main-pablos-projects-d80d0b2f.vercel.app",  # Rama principal
        "https://web-production-62f88.up.railway.app",     # Backend (para posibles solicitudes cross-origin)
        "https://mapmylearn.com"                     # Nuevo front (Removed trailing slash)
    ]
    
    # Añadir orígenes adicionales desde la variable de entorno si existe
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url and frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)
        
    # Registrar los dominios permitidos
    logger.info(f"Running in PRODUCTION mode with allowed origins: {allowed_origins}")
else:
    # Entorno de desarrollo local
    allowed_origins = ["http://localhost:3000"]
    logger.info("Running in DEVELOPMENT mode with local origins only")

# Add rate limiting middleware before CORS middleware
@app.middleware("http")
async def apply_rate_limiting(request: Request, call_next):
    """Apply rate limiting to protect against abuse"""
    if os.getenv("ENABLE_RATE_LIMITING", "false").lower() == "true":
        return await rate_limiting_middleware(request, call_next)
    return await call_next(request)

# Añadir middleware CORS con la configuración apropiada
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,  # Cachear resultados de pre-vuelo por 24 horas
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
    language: Optional[str] = Field("en", description="ISO language code for content generation (e.g., 'en', 'es')")

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

# Enhanced structured progress update model
class PreviewData(BaseModel):
    """Preview data for modules and submodules during generation"""
    modules: Optional[List[Dict[str, Any]]] = None
    search_queries: Optional[List[str]] = None
    current_module: Optional[Dict[str, Any]] = None
    current_submodule: Optional[Dict[str, Any]] = None

class ProgressUpdate(BaseModel):
    """Enhanced progress update with structured information"""
    message: str
    timestamp: str
    phase: Optional[str] = None  # e.g., "search_queries", "web_searches", "modules", "submodules", "content"
    phase_progress: Optional[float] = None  # 0.0 to 1.0 indicating progress within current phase
    overall_progress: Optional[float] = None  # 0.0 to 1.0 estimated overall progress
    preview_data: Optional[PreviewData] = None  # Early preview data
    action: Optional[str] = None  # e.g., "started", "processing", "completed", "error"

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
                # Only store the key if validation passed
                response.google_key_token = key_manager.store_key(
                    key_manager.KEY_TYPE_GOOGLE, 
                    request.google_api_key,
                    ip_address=client_ip
                )
                logger.info(f"Generated token for Google API key from {client_ip}")
            except Exception as e:
                # In case of storage error
                response.google_key_valid = False
                response.google_key_error = "Error generating token: " + str(e)
                logger.error(f"Error storing Google API key: {str(e)}")
        else:
            response.google_key_error = error_message
            logger.info(f"Invalid Google API key from {client_ip}: {error_message}")
    
    # Validate and store Perplexity API key if provided
    if request.pplx_api_key:
        is_valid, error_message = validate_perplexity_key(request.pplx_api_key)
        response.pplx_key_valid = is_valid
        if is_valid:
            try:
                # Only store the key if validation passed
                response.pplx_key_token = key_manager.store_key(
                    key_manager.KEY_TYPE_PERPLEXITY, 
                    request.pplx_api_key,
                    ip_address=client_ip
                )
                logger.info(f"Generated token for Perplexity API key from {client_ip}")
            except Exception as e:
                # In case of storage error
                response.pplx_key_valid = False
                response.pplx_key_error = "Error generating token: " + str(e)
                logger.error(f"Error storing Perplexity API key: {str(e)}")
        else:
            response.pplx_key_error = error_message
            logger.info(f"Invalid Perplexity API key from {client_ip}: {error_message}")
    
    return response

@app.post("/api/generate-learning-path")
async def api_generate_learning_path(request: LearningPathRequest, background_tasks: BackgroundTasks, req: Request):
    """
    Generate a learning path for the specified topic.
    
    This endpoint starts a background task to generate the learning path.
    API keys are now provided by the server - no need for user-provided keys.
    User API key tokens are still accepted for backward compatibility.
    
    The task ID can be used to retrieve the result or track progress.
    """
    client_ip = req.client.host if req.client else None
    
    # Get current user if authenticated
    user = None
    user_id = None
    try:
        if req.headers.get("Authorization"):
            # Get db session
            db = next(get_db())
            # Get user from auth token
            auth_header = req.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                token_data = decode_access_token(token)
                if token_data:
                    user = db.query(User).filter(User.id == token_data.user_id).first()
                    if user:
                        user_id = user.id
                        
                        # Check if user has sufficient credits
                        if user.credits <= 0:
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="Insufficient credits. Please contact the administrator to add credits to your account."
                            )
                        
                        # Deduct one credit for the generation and record the transaction
                        user.credits -= 1
                        
                        # Create credit transaction record
                        transaction = CreditTransaction(
                            user_id=user.id,
                            amount=-1,  # Negative amount for usage
                            action_type="generation_use",
                            notes=f"Used 1 credit to generate learning path for topic: {request.topic}"
                        )
                        db.add(transaction)
                        db.commit()
                        logger.info(f"Deducted 1 credit from user {user.id}, remaining credits: {user.credits}")
    except Exception as e:
        logger.warning(f"Error getting user or checking credits: {str(e)}")
        if isinstance(e, HTTPException):
            raise
    
    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # Create a queue for progress updates
    progress_queue = asyncio.Queue()
    async with progress_queues_lock:
        progress_queues[task_id] = progress_queue
        
    # Initialize the task in active_generations dictionary
    async with active_generations_lock:
        active_generations[task_id] = {"status": "running", "result": None, "user_id": user_id}

    # Define a progress callback that puts messages into the queue
    async def progress_callback(update: Union[str, ProgressUpdate]):
        if isinstance(update, str):
            # Legacy string format - convert to ProgressUpdate
            timestamp = datetime.now().isoformat()
            update = ProgressUpdate(message=update, timestamp=timestamp)
        
        await progress_queue.put(update)
        
    # Create key providers with server API keys (prioritized) 
    # but accept user tokens for backward compatibility
    google_provider = GoogleKeyProvider(
        token_or_key=request.google_key_token, 
        user_id=user_id
    ).set_operation("generate_learning_path")
    
    pplx_provider = PerplexityKeyProvider(
        token_or_key=request.pplx_key_token,
        user_id=user_id
    ).set_operation("generate_learning_path")
    
    # Start a background task to generate the learning path
    background_tasks.add_task(
        generate_learning_path_task,
        task_id=task_id,
        topic=request.topic,
        parallelCount=request.parallel_count,
        searchParallelCount=request.search_parallel_count,
        submoduleParallelCount=request.submodule_parallel_count,
        desiredModuleCount=request.desired_module_count,
        desiredSubmoduleCount=request.desired_submodule_count,
        googleKeyProvider=google_provider,
        pplxKeyProvider=pplx_provider,
        progressCallback=progress_callback,
        language=request.language,
        user_id=user_id
    )
    
    # Include information that API keys are provided by the server now
    return {
        "task_id": task_id,
        "status": "running",
        "api_key_info": {
            "server_provided": True,
            "message": "API keys are now provided by the server. You don't need to provide your own keys."
        }
    }

async def generate_learning_path_task(
    task_id: str,
    topic: str,
    parallelCount: int = 2,
    searchParallelCount: int = 3,
    submoduleParallelCount: int = 2,
    progressCallback = None,
    googleKeyProvider = None,
    pplxKeyProvider = None,
    desiredModuleCount: Optional[int] = None,
    desiredSubmoduleCount: Optional[int] = None,
    language: str = "en",
    user_id: Optional[int] = None
):
    """
    Execute the learning path generation task with comprehensive error handling.
    Ensures all exceptions are caught, logged, and reported through progress updates.
    
    Now using server-provided API keys by default, with backward compatibility
    for user-provided keys.
    """
    # Define a wrapper progress callback to ensure messages are logged and structured
    async def enhanced_progress_callback(message: str, 
                                         phase: Optional[str] = None, 
                                         phase_progress: Optional[float] = None, 
                                         overall_progress: Optional[float] = None,
                                         preview_data: Optional[Dict[str, Any]] = None,
                                         action: Optional[str] = None):
        """
        Enhanced progress callback that supports structured progress updates.
        
        Args:
            message: The progress message
            phase: Current generation phase (search_queries, web_searches, modules, submodules, content)
            phase_progress: Progress within the current phase (0.0 to 1.0)
            overall_progress: Estimated overall progress (0.0 to 1.0)
            preview_data: Preview data for modules and submodules
            action: Action being performed (started, processing, completed, error)
        """
        timestamp = datetime.now().isoformat()
        
        # Create the enhanced progress update
        preview_data_model = None
        if preview_data:
            preview_data_model = PreviewData(**preview_data)
            
        update = ProgressUpdate(
            message=message, 
            timestamp=timestamp,
            phase=phase,
            phase_progress=phase_progress,
            overall_progress=overall_progress,
            preview_data=preview_data_model,
            action=action
        )
        
        logging.info(f"Progress update for task {task_id}: {message} (Phase: {phase}, Progress: {phase_progress})")
        
        if progressCallback:
            await progressCallback(update)
    
    try:
        logging.info(f"Starting learning path generation for: {topic} in language: {language}")
        
        # Send initial progress message
        await enhanced_progress_callback(
            f"Starting learning path generation for: {topic} in language: {language}",
            phase="initialization",
            phase_progress=0.0,
            overall_progress=0.0,
            action="started"
        )
        
        # Verify that we have valid key providers
        if not googleKeyProvider:
            googleKeyProvider = GoogleKeyProvider()
            
        if not pplxKeyProvider:
            pplxKeyProvider = PerplexityKeyProvider()
        
        await enhanced_progress_callback(
            "API keys ready. Using server-provided API keys.",
            phase="initialization",
            phase_progress=0.6,
            overall_progress=0.1,
            action="processing"
        )
        
        await enhanced_progress_callback(
            f"Preparing to generate learning path for '{topic}' with {parallelCount} modules in parallel",
            phase="search_queries",
            phase_progress=0.0,
            overall_progress=0.15,
            action="started"
        )
        
        # Pass callback to update front-end with progress
        try:
            result = await generate_learning_path(
                topic,
                parallel_count=parallelCount,
                search_parallel_count=searchParallelCount, 
                submodule_parallel_count=submoduleParallelCount,
                progress_callback=enhanced_progress_callback,
                google_key_provider=googleKeyProvider,
                pplx_key_provider=pplxKeyProvider,
                desired_module_count=desiredModuleCount,
                desired_submodule_count=desiredSubmoduleCount,
                language=language
            )
        except Exception as e:
            # This is an unexpected error in the learning path generation process
            # Log the detailed error but provide a sanitized message to the user
            error_message = f"Unexpected error during learning path generation: {str(e)}"
            logging.exception(error_message)
            
            # Create a sanitized user-facing error message
            user_error_msg = "An error occurred during learning path generation. Please try again later."
            
            # Send error message to frontend
            await enhanced_progress_callback(
                f"Error: {user_error_msg}",
                phase="unknown",
                action="error"
            )
            
            # Restore credit to user if the generation failed and record the transaction
            if user_id is not None:
                try:
                    # Get a new DB session
                    from backend.config.database import get_db
                    db = next(get_db())
                    
                    # Find the user and restore credit
                    user = db.query(User).filter(User.id == user_id).first()
                    if user is not None:
                        user.credits += 1
                        
                        # Create credit transaction record for the refund
                        transaction = CreditTransaction(
                            user_id=user.id,
                            amount=1,  # Positive amount for refund
                            action_type="refund",
                            notes=f"Refunded 1 credit due to failed generation for topic: {topic}"
                        )
                        db.add(transaction)
                        db.commit()
                        logger.info(f"Restored 1 credit to user {user_id} due to generation error")
                except Exception as credit_error:
                    logger.error(f"Failed to restore credit to user {user_id}: {str(credit_error)}")
            
            # Update task status with sanitized error info - this is an unexpected error
            async with active_generations_lock:
                active_generations[task_id]["status"] = "failed"
                active_generations[task_id]["error"] = {
                    "message": user_error_msg,
                    "type": "unexpected_error"
                }
            return
        
        # Send completion message
        await enhanced_progress_callback(
            "Learning path generation completed successfully!",
            phase="completion",
            phase_progress=1.0,
            overall_progress=1.0,
            action="completed"
        )
        
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
            
        # Restore credit to user if the generation failed and record the transaction
        if user_id is not None:
            try:
                # Get a new DB session
                from backend.config.database import get_db
                db = next(get_db())
                
                # Find the user and restore credit
                user = db.query(User).filter(User.id == user_id).first()
                if user is not None:
                    user.credits += 1
                    
                    # Create credit transaction record for the refund
                    transaction = CreditTransaction(
                        user_id=user.id,
                        amount=1,  # Positive amount for refund
                        action_type="refund",
                        notes=f"Refunded 1 credit due to failed generation for topic: {topic}"
                    )
                    db.add(transaction)
                    db.commit()
                    logger.info(f"Restored 1 credit to user {user_id} due to generation error")
            except Exception as credit_error:
                logger.error(f"Failed to restore credit to user {user_id}: {str(credit_error)}")
    except Exception as e:
        # Catch any other unexpected exceptions
        error_message = f"Unexpected error during learning path generation: {str(e)}"
        logging.exception(error_message)
        
        # Create a sanitized user-facing error message
        user_error_msg = "An unexpected error occurred while generating your learning path. Please try again later."
        
        # Send error message to frontend
        await enhanced_progress_callback(
            f"Error: {user_error_msg}",
            phase="unknown",
            action="error"
        )
        
        # Restore credit to user if the generation failed and record the transaction
        if user_id is not None:
            try:
                # Get a new DB session
                from backend.config.database import get_db
                db = next(get_db())
                
                # Find the user and restore credit
                user = db.query(User).filter(User.id == user_id).first()
                if user is not None:
                    user.credits += 1
                    
                    # Create credit transaction record for the refund
                    transaction = CreditTransaction(
                        user_id=user.id,
                        amount=1,  # Positive amount for refund
                        action_type="refund",
                        notes=f"Refunded 1 credit due to failed generation for topic: {topic}"
                    )
                    db.add(transaction)
                    db.commit()
                    logger.info(f"Restored 1 credit to user {user_id} due to generation error")
            except Exception as credit_error:
                logger.error(f"Failed to restore credit to user {user_id}: {str(credit_error)}")
        
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
    Validate API keys without storing them.
    This endpoint is used to check if keys are valid before submitting a full request.
    """
    response = {
        "google_key_valid": False, 
        "pplx_key_valid": False,
        "google_key_error": None,
        "pplx_key_error": None
    }
    
    # Validate Google API key if provided
    if request.google_api_key:
        is_valid, error_message = validate_google_key(request.google_api_key)
        response["google_key_valid"] = is_valid
        if not is_valid:
            response["google_key_error"] = error_message
            logger.info(f"Google API key validation failed: {error_message}")
    
    # Validate Perplexity API key if provided
    if request.pplx_api_key:
        is_valid, error_message = validate_perplexity_key(request.pplx_api_key)
        response["pplx_key_valid"] = is_valid
        if not is_valid:
            response["pplx_key_error"] = error_message
            logger.info(f"Perplexity API key validation failed: {error_message}")
    
    return response

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
    Returns structured progress data including phase information, completion percentages,
    and early preview data.
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
                initial_update = ProgressUpdate(
                    message="Connection established", 
                    timestamp=datetime.now().isoformat(),
                    phase="connection",
                    phase_progress=0.0,
                    overall_progress=0.0,
                    action="connected"
                )
                yield f"data: {json.dumps(initial_update.dict())}\n\n"
                
                while True:
                    update = await queue.get()
                    if update is None:  # Sentinel to indicate completion
                        yield "data: {\"complete\": true}\n\n"
                        break
                    
                    # Convert ProgressUpdate model to dict before sending
                    if hasattr(update, 'dict'):
                        update_dict = update.dict()
                    else:
                        # For backward compatibility with simple string messages
                        if isinstance(update, str):
                            update_dict = {
                                "message": update,
                                "timestamp": datetime.now().isoformat()
                            }
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

@app.get("/api/admin/api-usage", response_model=Dict[str, Any])
async def get_api_usage_stats(request: Request):
    """
    Get API usage statistics.
    This is an admin-only endpoint for monitoring API key usage.
    In a production system, this would include authentication checks.
    """
    # In a real system, we would check authentication and authorization here
    # For now, just check if the request seems to be coming from an admin IP
    client_ip = request.client.host if request.client else None
    
    # This is a placeholder check and should be replaced with proper auth
    if client_ip != "127.0.0.1" and not os.environ.get("ADMIN_MODE"):
        # For security in production, we don't reveal this endpoint exists
        raise HTTPException(
            status_code=404,
            detail="Resource not found"
        )
    
    try:
        from backend.services.usage_tracker import UsageTracker
        
        # Get usage summary
        usage_summary = await UsageTracker.get_usage_summary()
        
        # Get per-user statistics (in production, this would be paginated)
        user_stats = {}
        for user_id in ["anonymous"]:  # In production, this would be a list of users
            user_usage = await UsageTracker.get_user_usage(user_id)
            if user_usage["total_calls"] > 0:
                user_stats[user_id] = user_usage
        
        # Return all stats
        return {
            "summary": usage_summary,
            "user_stats": user_stats,
            "server_time": datetime.now().isoformat(),
            "api_keys_mode": "server_provided",
            "future_credits_system": "in_development"
        }
    except Exception as e:
        logger.exception(f"Error retrieving API usage stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve API usage statistics"
        )

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
