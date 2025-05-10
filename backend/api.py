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
from datetime import datetime, timedelta, timezone
import uuid
import time
import httpx
import traceback
# Removed redis import here if no longer needed globally, or kept if used elsewhere.
# import redis.asyncio as redis # Check if still needed
# --- Add redis import back --- 
import redis.asyncio as redis
from sqlalchemy import update

# Database imports
from backend.config.database import engine, Base, get_db, SessionLocal
from backend.routes.auth import router as auth_router
from backend.routes.learning_paths import router as learning_paths_router, public_router as public_learning_paths_router
from backend.routes.admin import router as admin_router
from backend.routes.chatbot import router as chatbot_router
from backend.routes.payments import router as payments_router
from backend.models.auth_models import User, CreditTransaction, TransactionType, GenerationTask, GenerationTaskStatus, LearningPath
from backend.models.models import Resource, EnhancedModule, Submodule, QuizQuestion, LearningPathState, SearchQuery, SearchServiceResult, ScrapedResult
from backend.utils.auth import decode_access_token

# Import rate limiter and backend
from backend.utils.auth_middleware import get_optional_user, get_current_user
# Removed import of old middleware: from backend.utils.rate_limiter import rate_limiting_middleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Import CreditService
from backend.services.credit_service import CreditService, InsufficientCreditsError

# Initialize startup time for health check and uptime reporting
startup_time = time.time()

# Add proper path handling for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# First try with relative imports (when run directly)
try:
    # Import the backend functionality - try both approaches
    try:
        from main import generate_learning_path
        from services.services import validate_google_key, validate_brave_key
        from services.key_management import ApiKeyManager
        from services.key_provider import GoogleKeyProvider, PerplexityKeyProvider, BraveKeyProvider
    except ImportError:
        # If that fails, try with backend prefix (when run as a package)
        from backend.main import generate_learning_path
        from backend.services.services import validate_google_key, validate_brave_key
        from backend.services.key_management import ApiKeyManager
        from backend.services.key_provider import GoogleKeyProvider, PerplexityKeyProvider, BraveKeyProvider
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

def make_path_data_serializable(data: Any) -> Any:
    """Recursively converts Pydantic models within data to dictionaries."""
    if isinstance(data, list):
        return [make_path_data_serializable(item) for item in data]
    elif isinstance(data, dict):
        return {k: make_path_data_serializable(v) for k, v in data.items()}
    # Add explicit checks for your known Pydantic models
    elif isinstance(data, (Resource, EnhancedModule, Submodule, QuizQuestion, LearningPathState, ProgressUpdate, SearchQuery, SearchServiceResult, ScrapedResult, CreditTransaction, User, GenerationTask, LearningPath)):
        # Check for LearningPathState, ProgressUpdate, SearchQuery, SearchServiceResult, ScrapedResult as well, if they can be part of 'result'
        # Also added CreditTransaction, User, GenerationTask, LearningPath for completeness if they ever get nested unexpectedly
        if hasattr(data, 'model_dump'):
            return data.model_dump() # Pydantic v2
        else:
            return data.dict() # Pydantic v1 (fallback)
    elif isinstance(data, datetime):
        return data.isoformat()
    # Add other specific types if necessary, e.g., UUIDs if not handled by default json encoder
    elif isinstance(data, uuid.UUID):
        return str(data)
    # Fallback for any other Pydantic models not explicitly listed (though less safe)
    elif hasattr(data, '__pydantic_model__') or hasattr(data, 'model_fields'): # Heuristic for Pydantic models
        if hasattr(data, 'model_dump'):
            return data.model_dump()
        elif hasattr(data, 'dict'):
            return data.dict()
    return data # Return data as is if not a list, dict, or known Pydantic model or datetime

# Initialize the API Key Manager singleton
key_manager = ApiKeyManager()

# Create FastAPI app
app = FastAPI(
    title="MapMyLearn API",
    description="API for MapMyLearn Course Generator",
    version="0.1.0"
)

# Setup static file serving (for audio files)
static_dir = os.path.join(os.path.dirname(__file__), "static")
audio_dir = os.path.join(static_dir, "audio")
os.makedirs(audio_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
logger.info(f"Static files mounted from: {static_dir}")

# Create the database tables if they don't exist
# We'll use alembic for proper migrations in production
@app.on_event("startup")
async def startup_db_and_limiter():
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

    # Initialize Rate Limiter
    logger.info("Initializing Rate Limiter...")
    try:
        # Configure Redis connection for rate limiting
        # Use environment variable or default to "redis://localhost"
        redis_url = os.getenv("REDIS_URL", None)
        
        if redis_url:
            # Si hay REDIS_URL configurada, usamos Redis
            redis_connection = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await FastAPILimiter.init(redis_connection)
            logger.info(f"FastAPI Limiter initialized with Redis backend: {redis_url}")
        else:
            # Si no hay Redis, logueamos un aviso pero no inicializamos FastAPILimiter
            # Esto deshabilita el rate limiting pero permite que la app funcione sin error
            logger.warning("REDIS_URL not set - rate limiting is DISABLED. Set REDIS_URL for production environments.")
    except Exception as e:
        logger.error(f"Failed to initialize FastAPI Limiter: {e}")
        logger.warning("Rate limiting will be DISABLED")
        # La aplicación seguirá funcionando, pero sin rate limiting

# --- Add X-Frame-Options Middleware ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    # You might consider adding other security headers here too, like:
    # response.headers["X-Content-Type-Options"] = "nosniff"
    # response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
# --- End X-Frame-Options Middleware ---

# Include the auth, course, and admin routers
app.include_router(auth_router, prefix="/api")
app.include_router(learning_paths_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(public_learning_paths_router, prefix="/api")

# Configuration Constants
CHAT_FREE_LIMIT_PER_DAY_STR = os.getenv("CHAT_FREE_LIMIT_PER_DAY", "100")
try:
    CHAT_FREE_LIMIT_PER_DAY = int(CHAT_FREE_LIMIT_PER_DAY_STR)
except ValueError:
    logger.error(f"Invalid CHAT_FREE_LIMIT_PER_DAY: '{CHAT_FREE_LIMIT_PER_DAY_STR}'. Using default 100.")
    CHAT_FREE_LIMIT_PER_DAY = 100

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

# Añadir middleware CORS con la configuración apropiada
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
    max_age=86400,  # Cachear resultados de pre-vuelo por 24 horas
)
# --------------------------------------------------------------------------------
# Fin de configuración automática de CORS
# --------------------------------------------------------------------------------

# Custom error class for course generation errors
class LearningPathGenerationError(Exception):
    """Custom exception for course generation errors."""
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
    brave_key_token: Optional[str] = Field(None, description="Token for Brave Search API key")
    language: Optional[str] = Field("en", description="ISO language code for content generation (e.g., 'en', 'es')")
    explanation_style: Optional[str] = Field("standard", description="Desired style for content explanation (e.g., standard, simple, technical, example, conceptual, grumpy_genius)")

class ApiKeyAuthRequest(BaseModel):
    google_api_key: Optional[str] = Field(None, description="Google API key for LLM operations")
    brave_api_key: Optional[str] = Field(None, description="Brave Search API key for search operations")
    
class ApiKeyAuthResponse(BaseModel):
    google_key_token: Optional[str] = None
    brave_key_token: Optional[str] = None
    google_key_valid: bool = False
    brave_key_valid: bool = False
    google_key_error: Optional[str] = None
    brave_key_error: Optional[str] = None

class ApiKeyValidationRequest(BaseModel):
    google_api_key: Optional[str] = None
    brave_api_key: Optional[str] = None

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
    preview_data: Optional[Dict[str, Any]] = None  # Early preview data
    action: Optional[str] = None  # e.g., "started", "processing", "completed", "error"

class ImportPathRequest(BaseModel):
    json_data: str

# Store for active generation tasks with lock for thread safety
active_generations: Dict[str, Dict[str, Any]] = {} # Added type hint for clarity
active_generations_lock = asyncio.Lock()

# Custom class for handling datetime object serialization
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# --- Helper Function to Get Redis Client ---
async def get_redis_client():
    """Creates and returns an async Redis client instance."""
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.warning("REDIS_URL not set. Progress snapshotting will be disabled.")
        return None
    try:
        # Use decode_responses=True for easier handling of strings
        client = redis.from_url(redis_url, decode_responses=True) 
        await client.ping() # Verify connection
        logger.debug("Redis client created successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to create Redis client: {e}")
        return None
# --- End Helper Function ---

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
    
    # Validate and store Brave Search API key if provided
    if request.brave_api_key:
        is_valid, error_message = validate_brave_key(request.brave_api_key)
        response.brave_key_valid = is_valid
        if is_valid:
            try:
                # Only store the key if validation passed
                response.brave_key_token = key_manager.store_key(
                    "brave",
                    request.brave_api_key,
                    ip_address=client_ip
                )
                logger.info(f"Generated token for Brave Search API key from {client_ip}")
            except Exception as e:
                # In case of storage error
                response.brave_key_valid = False
                response.brave_key_error = "Error generating token: " + str(e)
                logger.error(f"Error storing Brave Search API key: {str(e)}")
        else:
            response.brave_key_error = error_message
            logger.info(f"Invalid Brave Search API key from {client_ip}: {error_message}")
    
    return response

@app.post("/api/generate-learning-path")
async def api_generate_learning_path(request: LearningPathRequest, background_tasks: BackgroundTasks, req: Request):
    """
    Generate a course for the specified topic.

    This endpoint starts a background task to generate the course.
    It now performs an initial check if the user *could* potentially afford the generation
    (balance >= 1) but the actual charge happens within the background task.

    The task ID can be used to retrieve the result or track progress.
    """
    client_ip = req.client.host if req.client else None

    # Get database session
    db = next(get_db())

    # Use get_optional_user to handle both authenticated and unauthenticated requests initially
    user = await get_optional_user(request=req, db=db)
    user_id = user.id if user else None

    if not user:
        logger.warning("Learning path generation requested without authentication. Blocking request.")
        db.close() # Close session before raising
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required to generate courses.")

    # --- Initial Check (Not the actual charge) ---
    # Perform a quick check here to see if the user *might* have enough credits.
    # This avoids creating a task if the user definitely has zero credits.
    # The actual charge with locking happens in the background task.
    if user.credits < 1:
        logger.warning(f"User {user.id} has insufficient credits ({user.credits}) for generation request.")
        db.close() # Close session before raising
        # Use the specific InsufficientCreditsError which returns 403
        raise InsufficientCreditsError(f"Insufficient credits. You need 1 credit to start generation, but have {user.credits}.")
    # --- End Initial Check ---

    # Create a unique task ID
    task_id = str(uuid.uuid4())

    # --- Create GenerationTask record --- 
    try:
        new_task = GenerationTask(
            task_id=task_id,
            user_id=user_id,
            status=GenerationTaskStatus.PENDING,
            request_topic=request.topic
        )
        db.add(new_task)
        db.commit()
        logger.info(f"Created GenerationTask record for task_id: {task_id}, user_id: {user_id}")
    except Exception as db_err:
        logger.exception(f"Database error creating GenerationTask for task {task_id}: {db_err}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize generation task state."
        )
    finally:
        db.close() # Close the session obtained from get_db()
    # --- End Create GenerationTask record ---

    # Initialize the task in active_generations dictionary
    async with active_generations_lock:
        active_generations[task_id] = {
            "status": "pending", 
            "result": None, 
            "user_id": user_id,
            "progress_stream": [], # Initialize progress_stream list
            "error": None # Initialize error field
        }

    # Create key providers with server API keys (prioritized)
    # but accept user tokens for backward compatibility
    google_provider = GoogleKeyProvider(
        token_or_key=request.google_key_token,
        user_id=user_id
    ).set_operation("generate_learning_path")

    brave_provider = BraveKeyProvider(
        token_or_key=request.brave_key_token,
        user_id=user_id
    ).set_operation("generate_learning_path")

    # Start a background task to generate the course
    background_tasks.add_task(
        generate_learning_path_task,
        task_id=task_id,
        topic=request.topic,
        parallelCount=request.parallel_count,
        searchParallelCount=request.search_parallel_count,
        submoduleParallelCount=request.submodule_parallel_count,
        desiredModuleCount=request.desired_module_count,
        desiredSubmoduleCount=request.desired_submodule_count,
        explanation_style=request.explanation_style,
        googleKeyProvider=google_provider,
        braveKeyProvider=brave_provider,
        language=request.language,
        user_id=user_id
    )

    # Include information that API keys are provided by the server now
    return {
        "task_id": task_id,
        "status": "pending", # Task is pending until background task starts
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
    googleKeyProvider = None,
    braveKeyProvider = None,
    desiredModuleCount: Optional[int] = None,
    desiredSubmoduleCount: Optional[int] = None,
    explanation_style: str = "standard",
    language: str = "en",
    user_id: Optional[int] = None
):
    """
    Execute the course generation task with comprehensive error handling.
    Handles credit charging and potential refunds atomically.
    Ensures all exceptions are caught, logged, and reported through progress updates.
    """
    db = SessionLocal() # Create a dedicated session for this background task
    credit_service = CreditService(db=db) # Instantiate credit service with the task's session
    charge_successful = False
    error_occurred_after_charge = False
    final_status = GenerationTaskStatus.FAILED # Default
    error_msg_to_save = None
    history_entry_id_to_link = None
    result = None
    current_overall_progress = 0.0 # Track current overall progress

    # Define a wrapper progress callback to ensure messages are logged and structured
    async def enhanced_progress_callback(message: str,
                                         phase: Optional[str] = None,
                                         phase_progress: Optional[float] = None,
                                         overall_progress: Optional[float] = None,
                                         preview_data: Optional[Dict[str, Any]] = None,
                                         action: Optional[str] = None):
        nonlocal current_overall_progress # Allow modification of the outer scope variable
        timestamp = datetime.now().isoformat()
        
        # Construct a log message. Preview_data can be verbose, so just indicate its presence.
        log_message_parts = [
            f"Task {task_id}: {message}",
            f"Phase: {phase}" if phase else None,
            f"PhaseProgress: {phase_progress:.2f}" if phase_progress is not None else None,
            f"OverallProgress: {overall_progress:.2f}" if overall_progress is not None else None,
            f"Action: {action}" if action else None,
            "PreviewData: Present" if preview_data else None
        ]
        full_log_message = " | ".join(filter(None, log_message_parts))
        logging.info(full_log_message)
        
        # For debugging, optionally log the preview_data structure if needed, but be mindful of log size
        # if preview_data:
        #    logging.debug(f"Task {task_id} Preview Data: {json.dumps(preview_data, default=str)[:500]}...")

        # Update current_overall_progress if a new value is provided
        if overall_progress is not None:
            current_overall_progress = overall_progress
        
        progress_update_obj = ProgressUpdate(
            message=message,
            timestamp=timestamp,
            phase=phase,
            phase_progress=phase_progress,
            overall_progress=current_overall_progress, # Use the tracked overall_progress
            preview_data=preview_data,
            action=action
        )

        async with active_generations_lock:
            if task_id in active_generations:
                # Ensure progress_stream exists, defensively
                if "progress_stream" not in active_generations[task_id]:
                    active_generations[task_id]["progress_stream"] = []
                active_generations[task_id]["progress_stream"].append(progress_update_obj.model_dump()) # Store as dict
                # Keep only the last N updates if necessary to save memory, e.g., last 50
                active_generations[task_id]["progress_stream"] = active_generations[task_id]["progress_stream"][-50:]
            else:
                logger.warning(f"Task {task_id} not found in active_generations when trying to append progress.")


    try:
        # --- Mark Task as RUNNING --- 
        async with active_generations_lock:
            if task_id in active_generations:
                active_generations[task_id]["status"] = "running"
                # Initialize progress_stream if it wasn't (should be done at creation)
                if "progress_stream" not in active_generations[task_id]:
                    active_generations[task_id]["progress_stream"] = [] 
            else:
                # Should not happen if endpoint logic is correct, but handle defensively
                active_generations[task_id] = {"status": "running", "result": None, "user_id": user_id, "progress_stream": [], "error": None}
        
        try:
            # Use db from this task's scope
            stmt = update(GenerationTask).where(GenerationTask.task_id == task_id).values(
                status=GenerationTaskStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            db.execute(stmt)
            db.commit()
            logger.info(f"Updated GenerationTask {task_id} status to RUNNING")
        except Exception as db_err_update:
            logger.exception(f"DB error updating GenerationTask {task_id} to RUNNING: {db_err_update}")
            db.rollback()
            # If we can't even mark as running, fail early
            raise LearningPathGenerationError("Failed to initialize generation task state in database.")

        logging.info(f"Starting course generation for: {topic} in language: {language}")
        await enhanced_progress_callback(
            f"Starting course generation for: {topic} in language: {language}",
            phase="initialization",
            phase_progress=0.0,
            overall_progress=0.0,
            preview_data={"type": "GENERATION_STARTED", "data": {"topic": topic, "language": language}},
            action="started"
        )

        # --- Charge Credit --- 
        if user_id is None:
             # Should be caught by endpoint, but double-check
             raise LearningPathGenerationError("User authentication is required.")
             
        charge_error = None
        try:
            # Use a transaction block for the charge
            with db.begin(): 
                notes = f"Generate course for topic: {topic}"
                await credit_service.charge_credits(
                    user_id=user_id,
                    amount=1,
                    transaction_type=TransactionType.GENERATION_USE,
                    notes=notes
                )
            charge_successful = True 
            logger.info(f"Credit charge successful for user {user_id}, task {task_id}.")
            await enhanced_progress_callback(
                "Credit charged successfully.",
                phase="initialization",
                phase_progress=0.5, 
                overall_progress=0.05,
                action="processing"
            )
        except InsufficientCreditsError as ice:
            logger.warning(f"Credit charge failed for task {task_id}: Insufficient credits for user {user_id}. Detail: {ice.detail}")
            charge_error = ice 
            raise 
        except Exception as charge_exc:
            logger.exception(f"Credit charge failed unexpectedly for task {task_id}, user {user_id}: {charge_exc}")
            charge_error = charge_exc 
            raise 
        # --- End Credit Charge --- 

        # --- Execute Core Generation Logic --- 
        if not googleKeyProvider: googleKeyProvider = GoogleKeyProvider()
        if not braveKeyProvider: braveKeyProvider = BraveKeyProvider()

        await enhanced_progress_callback(
            f"Preparing to generate course for '{topic}'",
            phase="search_queries",
            phase_progress=0.0,
            overall_progress=0.15,
            action="started"
        )

        # The main generation call happens *after* successful credit charge
        result = await generate_learning_path(
            topic,
            parallel_count=parallelCount,
            search_parallel_count=searchParallelCount,
            submodule_parallel_count=submoduleParallelCount,
            progress_callback=enhanced_progress_callback, # Pass the simplified logger callback
            google_key_provider=googleKeyProvider,
            brave_key_provider=braveKeyProvider,
            desired_module_count=desiredModuleCount,
            desired_submodule_count=desiredSubmoduleCount,
            explanation_style=explanation_style,
            language=language
        )
        # --- End Core Generation Logic --- 

        final_status = GenerationTaskStatus.COMPLETED
        await enhanced_progress_callback(
            "Learning path generation completed successfully!",
            phase="completion",
            phase_progress=1.0,
            overall_progress=1.0,
            action="completed"
        )

        # --- Save Successful Result to History --- 
        try:
            serializable_result = make_path_data_serializable(result)
            new_lp = LearningPath(
                user_id=user_id,
                path_id=serializable_result.get("path_id", str(uuid.uuid4())),
                topic=serializable_result.get("topic", topic),
                language=language,
                path_data=serializable_result,
                source="generated"
            )
            db.add(new_lp)
            db.commit() 
            db.refresh(new_lp)
            history_entry_id_to_link = new_lp.id 
            logger.info(f"Successfully saved generated course {history_entry_id_to_link} for task {task_id}.")
            # No SSE notification about persistentPathId anymore
        except Exception as save_err:
            logger.error(f"Failed to save successful course for task {task_id}: {save_err}")
            db.rollback() 
            final_status = GenerationTaskStatus.FAILED
            error_msg_to_save = json.dumps({"message": "Generation succeeded but failed to save result to history.", "type": "history_save_error"})
            error_occurred_after_charge = True 
            async with active_generations_lock:
                if task_id in active_generations:
                     active_generations[task_id]["status"] = "failed"
                     active_generations[task_id]["error"] = json.loads(error_msg_to_save)
                     active_generations[task_id]["progress_stream"].append(ProgressUpdate(
                        message=f"Error: {error_msg_to_save}",
                        timestamp=datetime.now().isoformat(),
                        phase="error",
                        overall_progress=current_overall_progress,
                        action="error",
                        preview_data={"type": "TASK_FAILED_EVENT", "data": json.loads(error_msg_to_save)}
                     ).model_dump())
            raise LearningPathGenerationError("Failed to save course result.") from save_err 

    except Exception as task_exception:
        final_status = GenerationTaskStatus.FAILED
        error_occurred_after_charge = charge_successful 
        
        if isinstance(task_exception, InsufficientCreditsError):
            user_error_msg = task_exception.detail
            error_type = "insufficient_credits"
            error_msg_to_save = json.dumps({"message": user_error_msg, "type": error_type})
            logger.warning(f"Task {task_id} failed due to insufficient credits: {user_error_msg}")
        elif isinstance(task_exception, LearningPathGenerationError):
            user_error_msg = task_exception.message
            error_type = "learning_path_generation_error"
            error_details = getattr(task_exception, 'details', None)
            error_content = {"message": user_error_msg, "type": error_type}
            if error_details: error_content["details"] = error_details
            error_msg_to_save = json.dumps(error_content) 
            logger.error(f"Task {task_id} failed with LearningPathGenerationError: {user_error_msg}")
            try:
                error_path_id = str(uuid.uuid4())
                err_lp = LearningPath(
                    user_id=user_id,
                    path_id=error_path_id,
                    topic=topic,
                    language=language,
                    path_data={"status": "failed", "error": user_error_msg, "error_type": error_type},
                    source="generated-failed",
                    tags=["[Failed Generation]"]
                )
                db.add(err_lp)
                db.commit() 
                db.refresh(err_lp)
                history_entry_id_to_link = err_lp.id 
                logger.info(f"Saved failed course stub {history_entry_id_to_link} to history for task {task_id}.")
                # No SSE notification
            except Exception as save_err2:
                logger.error(f"Failed to save failed LearningPath stub for task {task_id}: {save_err2}")
                db.rollback() 
        else:
            user_error_msg = "An unexpected error occurred during course generation. Please try again later or contact support."
            error_type = "internal_server_error"
            error_msg_to_save = json.dumps({"message": user_error_msg, "type": error_type})
            logger.exception(f"Task {task_id} failed with unexpected error: {task_exception}")
            try:
                error_path_id = str(uuid.uuid4())
                err_lp = LearningPath(
                    user_id=user_id,
                    path_id=error_path_id,
                    topic=topic,
                    language=language,
                    path_data={"status": "failed", "error": user_error_msg, "error_type": error_type},
                    source="generated-failed",
                    tags=["[Failed Generation]"]
                )
                db.add(err_lp)
                db.commit()
                db.refresh(err_lp)
                history_entry_id_to_link = err_lp.id
                logger.info(f"Saved failed course stub {history_entry_id_to_link} (unexpected error) for task {task_id}.")
                # No SSE notification
            except Exception as save_err3:
                logger.error(f"Failed to save failed LearningPath stub (unexpected error) for task {task_id}: {save_err3}")
                db.rollback()
        
        await enhanced_progress_callback(
            f"Error: {user_error_msg}",
            phase="error",
            action="error"
        )

        async with active_generations_lock:
            if task_id in active_generations:
                active_generations[task_id]["status"] = "failed"
                error_data_for_state = {}
                try:
                    error_data_for_state = json.loads(error_msg_to_save)
                except (json.JSONDecodeError, TypeError):
                    error_data_for_state = {"message": error_msg_to_save, "type": "unknown_error_format"}
                
                active_generations[task_id]["error"] = error_data_for_state
                
                # Ensure progress_stream exists
                if "progress_stream" not in active_generations[task_id]:
                    active_generations[task_id]["progress_stream"] = []
                
                active_generations[task_id]["progress_stream"].append(ProgressUpdate(
                    message=user_error_msg, # Use the user-facing error message
                    timestamp=datetime.now().isoformat(),
                    phase="error",
                    overall_progress=current_overall_progress, # Use last known progress
                    action="error",
                    preview_data={"type": "TASK_FAILED_EVENT", "data": error_data_for_state}
                ).model_dump())
            else: # This else is aligned with the 'if task_id in active_generations'
                logger.warning(f"Task {task_id} not found in active_generations when handling exception.")
        
        # This block is for closing the DB session obtained at the start of generate_learning_path_task
        # specifically within the exception handling path, before reaching the main finally.
        if db: 
            try:
                db.close()
                logger.debug(f"Database session closed for task {task_id} after exception.")
            except Exception as db_close_err:
                logger.error(f"Error closing database session for task {task_id} after exception: {db_close_err}")

    finally:
        if error_occurred_after_charge and user_id is not None:
            logger.warning(f"Task {task_id} failed after successful charge. Attempting refund for user {user_id}.")
            try:
                with db.begin():
                    refund_notes = f"Refund for failed generation task {task_id} (topic: {topic}). Error: {error_msg_to_save[:150] if error_msg_to_save else 'N/A'}"
                    await credit_service.grant_credits(
                        user_id=user_id,
                        amount=1,
                        transaction_type=TransactionType.REFUND,
                        notes=refund_notes
                    )
                logger.info(f"Successfully refunded 1 credit to user {user_id} for failed task {task_id}.")
            except Exception as refund_exc:
                logger.error(f"CRITICAL FAILURE: Failed to refund credit to user {user_id} for failed task {task_id}: {refund_exc}")
        
        try:
            stmt = update(GenerationTask).where(GenerationTask.task_id == task_id).values(
                status=final_status,
                ended_at=datetime.utcnow(),
                error_message=error_msg_to_save,
                history_entry_id=history_entry_id_to_link
            ).execution_options(synchronize_session=False) 
            db.execute(stmt)
            db.commit()
            logger.info(f"Updated GenerationTask {task_id} final status to {final_status} in DB.")
        except Exception as db_final_err:
            logger.exception(f"DB error updating final status for GenerationTask {task_id}: {db_final_err}")
            db.rollback()
        
        async with active_generations_lock:
            if task_id in active_generations:
                active_generations[task_id]["status"] = final_status.lower() 
                if final_status == GenerationTaskStatus.COMPLETED:
                     # Ensure the result stored in memory is already serializable
                     active_generations[task_id]["result"] = make_path_data_serializable(result) 
                     active_generations[task_id]["progress_stream"].append(ProgressUpdate(
                        message="Course generated successfully!",
                        timestamp=datetime.now().isoformat(),
                        phase="completion",
                        overall_progress=1.0,
                        action="completed",
                        # Optionally include final preview data if available from result
                        preview_data={"type": "COURSE_COMPLETED", "data": {"module_count": len(result.get("modules",[])) if result else 0}}
                     ).model_dump())
                elif error_msg_to_save:
                     try:
                         error_data = json.loads(error_msg_to_save)
                         active_generations[task_id]["error"] = error_data
                         active_generations[task_id]["progress_stream"].append(ProgressUpdate(
                            message=error_data.get("message", "Task failed."),
                            timestamp=datetime.now().isoformat(),
                            phase="error",
                            overall_progress=current_overall_progress, # Use last known progress
                            action="error",
                            preview_data={"type": "TASK_FAILED_EVENT", "data": error_data}
                         ).model_dump())
                     except (json.JSONDecodeError, TypeError):
                          active_generations[task_id]["error"] = {"message": error_msg_to_save}
                          active_generations[task_id]["progress_stream"].append(ProgressUpdate(
                            message=error_msg_to_save,
                            timestamp=datetime.now().isoformat(),
                            phase="error",
                            overall_progress=current_overall_progress,
                            action="error",
                            preview_data={"type": "TASK_FAILED_EVENT", "data": {"message": error_msg_to_save}}
                         ).model_dump())
            else:
                 logger.warning(f"Task {task_id} not found in active_generations during finalization.")
        
        if db:
            try:
                db.close()
                logger.debug(f"Database session closed for task {task_id}.")
            except Exception as db_close_err:
                 logger.error(f"Error closing database session for task {task_id}: {db_close_err}")

@app.post("/api/validate-api-keys")
async def validate_api_keys(request: ApiKeyValidationRequest):
    """
    Validate API keys without storing them.
    This endpoint is used to check if keys are valid before submitting a full request.
    """
    response = {
        "google_key_valid": False, 
        "brave_key_valid": False,
        "google_key_error": None,
        "brave_key_error": None
    }
    
    # Validate Google API key if provided
    if request.google_api_key:
        is_valid, error_message = validate_google_key(request.google_api_key)
        response["google_key_valid"] = is_valid
        if not is_valid:
            response["google_key_error"] = error_message
            logger.info(f"Google API key validation failed: {error_message}")
    
    # Validate Brave Search API key if provided
    if request.brave_api_key:
        is_valid, error_message = validate_brave_key(request.brave_api_key)
        response["brave_key_valid"] = is_valid
        if not is_valid:
            response["brave_key_error"] = error_message
            logger.info(f"Brave Search API key validation failed: {error_message}")
    
    return response

@app.get("/api/learning-path/{task_id}")
async def get_learning_path_status(task_id: str):
    """
    Get the status and result of a course generation task.
    Relies on in-memory cache and database, no SSE progress snapshots.
    """
    final_status_info = None
    db = SessionLocal()

    try:
        # 1. Check in-memory active_generations
        async with active_generations_lock:
            task_data_memory = active_generations.get(task_id)
            if task_data_memory:
                # Make a deep copy to avoid issues if the caller modifies the result
                # Ensure that the data from memory is passed through make_path_data_serializable 
                # before json.dumps, although it should ideally be serializable already if stored correctly.
                result_from_memory = task_data_memory.get("result")
                final_status_info = {
                    "status": task_data_memory["status"],
                    "result": make_path_data_serializable(result_from_memory) if result_from_memory else None, 
                    "error": task_data_memory.get("error"),
                    # progress_stream is not directly returned by this status endpoint
                    # it's used by the dedicated SSE progress stream endpoint
                }
        
        # 2. If task is marked completed in memory but result is missing, try to fetch from DB
        if final_status_info and final_status_info["status"] == "completed" and not final_status_info.get("result"):
            logger.info(f"Task {task_id} completed in memory, attempting to fetch result from DB.")
            task_record_for_result = db.query(GenerationTask).filter(
                GenerationTask.task_id == task_id, 
                GenerationTask.status == GenerationTaskStatus.COMPLETED
            ).first()

            if task_record_for_result and task_record_for_result.history_entry_id:
                learning_path_record = db.query(LearningPath).filter(LearningPath.id == task_record_for_result.history_entry_id).first()
                if learning_path_record and learning_path_record.path_data:
                    # path_data from DB should already be serializable if saved correctly by make_path_data_serializable
                    fetched_result = make_path_data_serializable(learning_path_record.path_data) 
                    final_status_info["result"] = fetched_result
                    # Update in-memory cache with the fetched result
                    async with active_generations_lock:
                        if task_id in active_generations:
                            active_generations[task_id]["result"] = fetched_result # Store the serializable version
                    logger.info(f"Fetched result for completed task {task_id} from DB.")
                else:
                    logger.warning(f"Task {task_id} completed, but LearningPath or path_data not found for history_entry_id {task_record_for_result.history_entry_id}. Treating as error.")
                    final_status_info["status"] = "failed"
                    final_status_info["error"] = {"message": "Course data retrieval failed after completion.", "type": "data_retrieval_error"}
                    async with active_generations_lock: # Update memory status
                        if task_id in active_generations:
                            active_generations[task_id]["status"] = "failed"
                            active_generations[task_id]["error"] = final_status_info["error"]
            else:
                logger.warning(f"Task {task_id} marked completed in memory, but no corresponding DB record or history_entry_id found. Treating as error.")
                final_status_info["status"] = "failed"
                final_status_info["error"] = {"message": "Inconsistent completion state for course.", "type": "state_inconsistency_error"}
                async with active_generations_lock: # Update memory status
                    if task_id in active_generations:
                        active_generations[task_id]["status"] = "failed"
                        active_generations[task_id]["error"] = final_status_info["error"]


        # 3. If task not found in memory, query the database
        elif not final_status_info:
            logger.info(f"Task {task_id} not in memory, querying DB.")
            task_record_db = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
            if task_record_db:
                status_from_db = task_record_db.status.lower()
                error_info_from_db = None
                result_from_db = None

                if task_record_db.error_message:
                    try:
                        error_info_from_db = json.loads(task_record_db.error_message)
                    except (json.JSONDecodeError, TypeError):
                        error_info_from_db = {"message": task_record_db.error_message, "type": "db_error_string"}
                
                if status_from_db == "completed":
                    if task_record_db.history_entry_id:
                        learning_path_record_db = db.query(LearningPath).filter(LearningPath.id == task_record_db.history_entry_id).first()
                        if learning_path_record_db and learning_path_record_db.path_data:
                            # path_data from DB should be serializable
                            result_from_db = make_path_data_serializable(learning_path_record_db.path_data)
                            logger.info(f"Fetched result for completed task {task_id} (from DB query).")
                        else:
                            logger.warning(f"Task {task_id} (from DB) completed, but LearningPath/path_data not found for history_entry_id {task_record_db.history_entry_id}. Treating as error.")
                            status_from_db = "failed"
                            error_info_from_db = {"message": "Course data retrieval failed after completion (DB).", "type": "data_retrieval_error_db"}
                    else:
                        logger.warning(f"Task {task_id} (from DB) completed, but no history_entry_id. Treating as error.")
                        status_from_db = "failed"
                        error_info_from_db = {"message": "Completed task has no associated course data (DB).", "type": "missing_history_link_db"}


                final_status_info = {
                    "status": status_from_db,
                    "result": result_from_db,
                    "error": error_info_from_db
                }
                
                # Update in-memory cache with DB findings
                async with active_generations_lock:
                    active_generations[task_id] = {
                        "status": final_status_info["status"],
                        "result": final_status_info.get("result"),
                        "error": final_status_info.get("error"),
                        "user_id": task_record_db.user_id 
                    }
                logger.info(f"Populated in-memory cache for task {task_id} from DB: Status {status_from_db}")
            else:
                # Task not in memory and not in DB
                logger.warning(f"Task {task_id} not found in memory or DB.")
                raise HTTPException(status_code=404, detail="Learning path task not found.")

        # 4. Final return
        if final_status_info:
            return {
                "task_id": task_id,
                "status": final_status_info["status"],
                # No need for json.loads(json.dumps(...)) here anymore if final_status_info["result"] is already a serializable dict
                "result": final_status_info.get("result"), 
                "error": final_status_info.get("error")
            }
        else:
            # This case should ideally be covered by the DB check leading to 404 if not found
            logger.error(f"Logic error: final_status_info not populated for task {task_id} despite checks.")
            raise HTTPException(status_code=500, detail="Could not determine task status.")
            
    finally:
        db.close()

@app.delete("/api/learning-path/{task_id}")
async def delete_learning_path(task_id: str):
    """
    Delete a course generation task and its progress queue.
    """
    try:
        # Check if the task exists
        task_existed = False
        async with active_generations_lock:
            if task_id in active_generations:
                del active_generations[task_id]
                task_existed = True
        
        if not task_existed:
            raise HTTPException(
                status_code=404,
                detail="Learning path task not found. The task ID may be invalid or the task has already been deleted."
            )
        
        logger.info(f"Deleted course task: {task_id}")
        return {"status": "success", "message": "Learning path task deleted successfully."}
    except HTTPException:
        # Re-raise HTTP exceptions to be handled by our custom handler
        raise
    except Exception as e:
        logger.exception(f"Error deleting course task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete course task. Please try again later."
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

@app.get("/api/learning-path/{task_id}/progress-stream")
async def learning_path_progress_stream(task_id: str, request: Request):
    """
    Server-Sent Events endpoint to stream progress updates for a learning path generation task.
    """
    async def event_generator():
        last_sent_index = 0
        try:
            while True:
                # Check for client disconnect
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from SSE stream for task {task_id}.")
                    break

                async with active_generations_lock:
                    task_info = active_generations.get(task_id)
                    if not task_info:
                        # Task not found or already cleaned up
                        logger.warning(f"SSE stream request for unknown or completed task {task_id}.")
                        yield f"data: {json.dumps({'error': 'Task not found or completed.', 'status': 'unknown'})}" + "\n\n"
                        break
                    
                    progress_items = task_info.get("progress_stream", [])
                    current_status = task_info.get("status", "pending")
                
                # Send new messages
                if len(progress_items) > last_sent_index:
                    for i in range(last_sent_index, len(progress_items)):
                        message_to_send = progress_items[i]
                        # Ensure message_to_send is a dict (it should be from model_dump())
                        if isinstance(message_to_send, dict):
                            yield f"data: {json.dumps(message_to_send, cls=DateTimeEncoder)}" + "\n\n"
                        else:
                            logger.warning(f"Skipping non-dict progress item for task {task_id}: {type(message_to_send)}")
                    last_sent_index = len(progress_items)

                # Check if task is completed or failed to close stream
                if current_status in ["completed", "failed"]:
                    logger.info(f"Task {task_id} reached terminal state ({current_status}). Closing SSE stream.")
                    final_message = {
                        "message": f"Task {current_status}. Closing stream.",
                        "timestamp": datetime.now().isoformat(),
                        "phase": "finalization",
                        "action": "stream_close",
                        "status": current_status
                    }
                    yield f"data: {json.dumps(final_message)}" + "\n\n"
                    break
                
                await asyncio.sleep(0.5)  # Poll for new messages periodically
        except asyncio.CancelledError:
            logger.info(f"SSE stream for task {task_id} was cancelled (client likely disconnected).")
        except Exception as e:
            logger.exception(f"Error in SSE stream for task {task_id}: {e}")
            try:
                error_payload = {"error": "Stream error", "detail": str(e), "status": "error"}
                yield f"data: {json.dumps(error_payload)}" + "\n\n"
            except Exception: # Guard against errors during error reporting itself
                pass # Avoid further exceptions in the error handling path
        finally:
            logger.info(f"SSE event_generator for task {task_id} finished.")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
