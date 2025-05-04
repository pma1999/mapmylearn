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
import redis.asyncio as redis

# Database imports
from backend.config.database import engine, Base, get_db
from backend.routes.auth import router as auth_router
from backend.routes.learning_paths import router as learning_paths_router, public_router as public_learning_paths_router
from backend.routes.admin import router as admin_router
from backend.routes.chatbot import router as chatbot_router
from backend.routes.payments import router as payments_router
from backend.models.auth_models import User, CreditTransaction, TransactionType, GenerationTask, GenerationTaskStatus, LearningPath
from backend.models.models import Resource
from backend.utils.auth import decode_access_token

# Import rate limiter and backend
from backend.utils.auth_middleware import get_optional_user, get_current_user
from backend.utils.rate_limiter import rate_limiting_middleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Import CreditService
from backend.services.credit_service import CreditService

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
    """Recursively converts Pydantic Resource models within data to dictionaries."""
    if isinstance(data, dict):
        return {k: make_path_data_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_path_data_serializable(item) for item in data]
    elif isinstance(data, Resource):
        # Use model_dump() for Pydantic v2, fallback to dict() for v1
        if hasattr(data, 'model_dump'):
            return data.model_dump()
        else:
            return data.dict()
    else:
        return data

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

# Include the auth, course, and admin routers
app.include_router(auth_router, prefix="/api")
app.include_router(learning_paths_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(public_learning_paths_router, prefix="/api")

# Initialize Redis client for middleware (ensure REDIS_URL is set)
redis_client_middleware = None
try:
    redis_url_mw = os.getenv("REDIS_URL")
    if redis_url_mw:
        redis_client_middleware = redis.from_url(redis_url_mw, encoding="utf-8", decode_responses=True)
        logger.info("Rate Limiter Redis client initialized.")
    else:
        logger.warning("REDIS_URL not set. Rate limiting features requiring Redis will be disabled.")
except Exception as e:
    logger.error(f"Failed to initialize Redis client for rate limiter middleware: {e}")

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

# Add rate limiting middleware before CORS middleware
@app.middleware("http")
async def apply_rate_limiting(request: Request, call_next):
    """Apply rate limiting: Custom for chat, standard (IP-based) otherwise."""
    # Skip OPTIONS requests
    if request.method == "OPTIONS":
        return await call_next(request)

    # Check if Redis is available for any rate limiting
    if not redis_client_middleware or not FastAPILimiter.redis:
        # If Redis isn't configured globally via FastAPILimiter.init, bypass all rate limits
        if not FastAPILimiter.redis:
             logger.debug("FastAPILimiter redis not initialized, skipping rate limiting.")
        else:
             logger.debug("Middleware redis client not available, skipping rate limiting.")
        return await call_next(request)

    # --- Custom Logic for /api/chatbot/chat --- 
    if request.url.path == "/api/chatbot/chat":
        user_id: Optional[int] = None
        token = None
        
        # Attempt to extract token and user_id without full dependency injection
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]
            token_data = decode_access_token(token) # Assuming this doesn't hit DB
            if token_data:
                user_id = token_data.user_id

        if user_id:
            try:
                today_utc_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                allowance_key = f"chat_allowance:{user_id}:{today_utc_str}"
                
                # Check if allowance exists and is greater than 0
                current_allowance = await redis_client_middleware.get(allowance_key)
                
                if current_allowance and int(current_allowance) > 0:
                    # Decrement allowance and proceed
                    await redis_client_middleware.decr(allowance_key)
                    logger.debug(f"User {user_id} used chat allowance. Remaining: {int(current_allowance) - 1}")
                    return await call_next(request)
                else:
                    # No allowance or allowance depleted, proceed to free limit check
                    logger.debug(f"User {user_id} has no remaining chat allowance for today. Checking free limit.")

            except redis.RedisError as e:
                logger.error(f"Redis error checking chat allowance for user {user_id}: {e}. Allowing request.")
                # Fail open on Redis error during check
                return await call_next(request)
            except Exception as e:
                 logger.error(f"Error checking allowance for user {user_id}: {e}. Allowing request.")
                 # Fail open on other errors during check
                 return await call_next(request)

            # --- Apply Free Daily Limit (User-Based) if no allowance was used --- 
            try:
                limit_key = f"chat_limit:{user_id}:{today_utc_str}"
                # Key identifier for fastapi-limiter
                # identifier = f"user:{user_id}" # <-- This identifier isn't actually used

                # --- CORRECTED LOGIC using redis-py async client --- 

                # 1. Get current count
                # Use the specific redis client for the middleware
                current_count_str = await redis_client_middleware.get(limit_key)
                current_count = int(current_count_str) if current_count_str else 0

                # 2. Check if limit exceeded BEFORE incrementing
                if current_count >= CHAT_FREE_LIMIT_PER_DAY:
                    logger.warning(f"User {user_id} exceeded free chat limit ({current_count}/{CHAT_FREE_LIMIT_PER_DAY}) for {today_utc_str}.")
                    ttl = await redis_client_middleware.ttl(limit_key)
                    # --- MODIFIED PART: Return JSONResponse instead of raising --- 
                    error_response_content = {
                        "status": "failed",
                        "error": {
                            "message": f"Daily chat limit reached. Purchase allowance or try again tomorrow.",
                            "type": "rate_limit_exceeded"
                        }
                    }
                    response_headers = {"Retry-After": str(ttl)} if ttl >= 0 else {}
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content=error_response_content,
                        headers=response_headers
                    )
                    # --- END MODIFIED PART --- 
                
                # 3. Increment the count (Hit)
                new_count = await redis_client_middleware.incr(limit_key, amount=1)

                # 4. Set expiry only if the key was just created (i.e., count is 1 after incr)
                if new_count == 1:
                    now_utc = datetime.now(timezone.utc)
                    end_of_day_utc = datetime.combine(now_utc.date() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
                    ttl_seconds = int((end_of_day_utc - now_utc).total_seconds())
                    if ttl_seconds > 0:
                        await redis_client_middleware.expire(limit_key, ttl_seconds)
                
                logger.debug(f"User {user_id} used free chat message. Count: {new_count}/{CHAT_FREE_LIMIT_PER_DAY}")
                # Limit check passed and hit recorded
                return await call_next(request)

            except redis.RedisError as e:
                logger.error(f"Redis error during free chat limit check for user {user_id}: {e}. Allowing request.")
                # Fail open on Redis error
                return await call_next(request)
            except HTTPException as http_exc: # Re-raise 429
                raise http_exc
            except Exception as e:
                logger.error(f"Error during free limit check/hit for user {user_id}: {e}. Allowing request.")
                # Fail open on other errors
                return await call_next(request)
        else:
            # Unauthenticated user trying to chat - block?
            # Or apply IP-based limit? For now, let's block unauthenticated chat.
            logger.warning(f"Unauthenticated request to /api/chatbot/chat from {request.client.host}. Blocking.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for chat."
            )

    # --- Standard Rate Limiting for other paths (IP-based example) ---
    else:
        # Apply a default IP-based limit to other routes if desired
        # Example: 60 requests per minute per IP
        # identifier = request.client.host
        # limit_key = f"ip_limit:{identifier}"
        # try:
        #     can_request = await FastAPILimiter.redis.check(limit_key)
        #     if not can_request:
        #         ttl = await FastAPILimiter.redis.ttl(limit_key)
        #         raise HTTPException(
        #             status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        #             detail="Rate limit exceeded for this endpoint.",
        #             headers={"Retry-After": str(ttl)} if ttl > 0 else None
        #         )
        #     await FastAPILimiter.redis.incr(limit_key, expire=60, amount=1) # 60 seconds expiry
        # except redis.RedisError as e:
        #     logger.error(f"Redis error during IP rate limit check for {identifier}: {e}. Allowing request.")
        #     # Fail open
        # except Exception as e:
        #     logger.error(f"Error during IP rate limit check/hit for {identifier}: {e}. Allowing request.")
        #     # Fail open
        
        # Pass through if no standard limit is defined or Redis fails
        return await call_next(request)

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
    API keys are now provided by the server - no need for user-provided keys.
    User API key tokens are still accepted for backward compatibility.
    
    The task ID can be used to retrieve the result or track progress.
    """
    client_ip = req.client.host if req.client else None
    
    # Get database session
    db = next(get_db())
    
    # Use get_optional_user to handle both authenticated and unauthenticated requests initially
    user = await get_optional_user(request=req, db=db)
    user_id = user.id if user else None
    
    if not user:
        # Handle case where authentication is strictly required (e.g., if credits are mandatory)
        # If anonymous generation isn't allowed, raise an error here.
        # For now, we proceed, but credit check will fail if user is None.
        logger.warning("Learning path generation requested without authentication.")
        # Optionally raise: HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required to generate courses.")
    else:
        # --- Refactored Credit Handling --- 
        try:
            notes = f"Generate course for topic: {request.topic}"
            # Note: CreditService expects db in __init__, not Depends directly here
            credit_service = CreditService(db=db)
            async with credit_service.charge(user=user, amount=1, transaction_type=TransactionType.GENERATION_USE, notes=notes):
                # If this block is entered, credit check passed and deduction was committed.
                logger.info(f"Credit check passed and 1 credit deducted for user {user.id} for topic: {request.topic}")
                pass # No action needed inside, just proceed if successful
        except HTTPException as e:
            # Handles 403 Forbidden from charge() or other HTTP errors
            logger.warning(f"Credit charge failed for user {user.id}: {e.detail}")
            raise e # Re-raise the original exception
        except Exception as e:
            # Catch unexpected errors during credit charge
            logger.exception(f"Unexpected error during credit charge for user {user.id}: {e}")
            # Raise a new HTTPException for internal errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error occurred while processing credits."
            )
        # --- End Refactored Credit Handling ---

    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # --- Create GenerationTask record --- 
    try:
        new_task = GenerationTask(
            task_id=task_id,
            user_id=user_id, # This will be None if user is not authenticated
            status=GenerationTaskStatus.PENDING,
            request_topic=request.topic
        )
        db.add(new_task)
        db.commit()
        logger.info(f"Created GenerationTask record for task_id: {task_id}, user_id: {user_id}")
    except Exception as db_err:
        logger.exception(f"Database error creating GenerationTask for task {task_id}: {db_err}")
        db.rollback() # Rollback credit deduction if task creation fails
        # Also rollback the credit deduction if necessary
        # Re-raise a 500 error as something went wrong saving the task state
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize generation task state."
        )
    finally:
        db.close() # Close the session obtained from get_db()
    # --- End Create GenerationTask record --- 
    
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
    braveKeyProvider = None,
    desiredModuleCount: Optional[int] = None,
    desiredSubmoduleCount: Optional[int] = None,
    explanation_style: str = "standard",
    language: str = "en",
    user_id: Optional[int] = None
):
    """
    Execute the course generation task with comprehensive error handling.
    Ensures all exceptions are caught, logged, and reported through progress updates.
    Stores the latest progress update in Redis.
    """
    redis_client = await get_redis_client() # Get Redis client for this task

    # Define a wrapper progress callback to ensure messages are logged and structured
    async def enhanced_progress_callback(message: str, 
                                         phase: Optional[str] = None, 
                                         phase_progress: Optional[float] = None, 
                                         overall_progress: Optional[float] = None,
                                         preview_data: Optional[Dict[str, Any]] = None,
                                         action: Optional[str] = None):
        """
        Enhanced progress callback that supports structured progress updates and Redis storage.
        """
        nonlocal redis_client # Allow modification of the outer scope variable
        timestamp = datetime.now().isoformat()
        
        preview_data_model = None
        if preview_data:
            try:
                # Ensure preview_data is serializable before creating the model
                serializable_preview = make_path_data_serializable(preview_data)
                preview_data_model = PreviewData(**serializable_preview)
            except Exception as preview_err:
                 logger.error(f"Error creating PreviewData model for task {task_id}: {preview_err}")
                 preview_data_model = None # Set to None if validation fails

        update = ProgressUpdate(
            message=message, 
            timestamp=timestamp,
            phase=phase,
            phase_progress=phase_progress,
            overall_progress=overall_progress,
            preview_data=preview_data_model,
            action=action
        )
        
        logging.info(f"Progress update for task {task_id}: {message} (Phase: {phase}, Progress: {overall_progress})")
        
        # Store latest update in Redis
        if redis_client:
            try:
                # Convert model to dict, then to JSON string
                update_dict = update.dict(exclude_none=True) # Exclude None values for cleaner JSON
                update_json = json.dumps(update_dict, cls=DateTimeEncoder) 
                await redis_client.set(f"progress:{task_id}", update_json, ex=86400) # 24-hour expiry
                logger.debug(f"Stored progress snapshot for task {task_id} in Redis.")
            except redis.RedisError as redis_err:
                logger.error(f"Redis error storing progress snapshot for task {task_id}: {redis_err}. Disabling Redis for this task.")
                await redis_client.aclose() # Close potentially broken connection
                redis_client = None # Disable further Redis attempts for this task run
            except Exception as e:
                logger.error(f"Error serializing/storing progress snapshot for task {task_id}: {e}")
                # Optionally disable Redis here too if serialization errors are frequent
        
        # Send update via asyncio queue
        if progressCallback:
            await progressCallback(update)
    
    try:
        # Get database session using SessionLocal within the task
        from backend.config.database import SessionLocal
        db = SessionLocal()
        
        # --- Update GenerationTask status to RUNNING --- 
        try:
            task_record = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
            if task_record:
                task_record.status = GenerationTaskStatus.RUNNING
                task_record.started_at = datetime.utcnow()
                db.commit()
                logger.info(f"Updated GenerationTask {task_id} status to RUNNING")
            else:
                logger.error(f"Could not find GenerationTask record for task_id: {task_id} to set status to RUNNING.")
                raise Exception(f"Task record {task_id} not found.") 
        except Exception as db_err:
            logger.exception(f"DB error updating GenerationTask {task_id} to RUNNING: {db_err}")
            db.rollback()
            # Let outer finally handle status update

        logging.info(f"Starting course generation for: {topic} in language: {language}")
        
        await enhanced_progress_callback(
            f"Starting course generation for: {topic} in language: {language}",
            phase="initialization",
            phase_progress=0.0,
            overall_progress=0.0,
            action="started"
        )
        
        if not googleKeyProvider: googleKeyProvider = GoogleKeyProvider()
        if not braveKeyProvider: braveKeyProvider = BraveKeyProvider()
        
        await enhanced_progress_callback(
            "API keys ready.",
            phase="initialization",
            phase_progress=0.6,
            overall_progress=0.1,
            action="processing"
        )
        
        await enhanced_progress_callback(
            f"Preparing to generate course for '{topic}'",
            phase="search_queries",
            phase_progress=0.0,
            overall_progress=0.15,
            action="started"
        )
        
        try:
            result = await generate_learning_path(
                topic,
                parallel_count=parallelCount,
                search_parallel_count=searchParallelCount, 
                submodule_parallel_count=submoduleParallelCount,
                progress_callback=enhanced_progress_callback,
                google_key_provider=googleKeyProvider,
                brave_key_provider=braveKeyProvider,
                desired_module_count=desiredModuleCount,
                desired_submodule_count=desiredSubmoduleCount,
                explanation_style=explanation_style,
                language=language
            )
        except Exception as e:
            # This is an unexpected error in the course generation process
            # Log the detailed error but provide a sanitized message to the user
            error_message = f"Unexpected error during course generation: {str(e)}"
            logging.exception(error_message)
            
            # Create a sanitized user-facing error message
            user_error_msg = "An error occurred during course generation. Please try again later."
            
            # Send error message to frontend
            await enhanced_progress_callback(
                f"Error: {user_error_msg}",
                phase="error",
                action="error"
            )
            
            # Automatically save failed course to history
            try:
                error_path_id = str(uuid.uuid4())
                err_lp = LearningPath(
                    user_id=user_id,
                    path_id=error_path_id,
                    topic=topic,
                    language=language,
                    path_data={"status": "failed", "error": user_error_msg},
                    source="generated-failed",
                    tags=["[Failed Generation]"]
                )
                db.add(err_lp)
                db.commit()
                db.refresh(err_lp)
                # Link generation task to history entry
                tr = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
                if tr:
                    tr.history_entry_id = err_lp.id
                    db.commit()
                if progressCallback:
                    await progressCallback({
                        "message": "Failed course saved to history.",
                        "persistentPathId": error_path_id,
                        "action": "history_saved",
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as save_err2:
                logger.error(f"Failed to save failed LearningPath for task {task_id}: {save_err2}")
                db.rollback()
            
            # Restore credit to user if the generation failed and record the transaction
            if user_id is not None:
                try:
                    # Find the user and restore credit
                    user = db.query(User).filter(User.id == user_id).first()
                    if user is not None:
                        user.credits += 1
                        
                        # Create credit transaction record for the refund
                        transaction = CreditTransaction(
                            user_id=user.id,
                            amount=1,  # Positive amount for refund
                            transaction_type="refund",
                            notes=f"Refunded 1 credit due to failed generation for topic: {topic}"
                        )
                        db.add(transaction)
                        db.commit()
                        logger.info(f"Restored 1 credit to user {user_id} due to generation error")
                    else:
                        logger.warning(f"User {user_id} not found for credit refund.")
                except Exception as credit_error:
                    logger.error(f"Failed to restore credit to user {user_id} after unexpected error: {str(credit_error)}")
            
            # Update task status with sanitized error info - this is an unexpected error
            async with active_generations_lock:
                if task_id in active_generations:
                    active_generations[task_id]["status"] = "failed"
                    active_generations[task_id]["error"] = {
                        "message": user_error_msg,
                        "type": "unexpected_error"
                    }
            return 

        await enhanced_progress_callback(
            "Learning path generation completed successfully!",
            phase="completion",
            phase_progress=1.0,
            overall_progress=1.0,
            action="completed"
        )
        # Automatically save generated course to history
        try:
            serializable_result = make_path_data_serializable(result)
            new_lp = LearningPath(
                user_id=user_id,
                path_id=serializable_result.get("path_id"),
                topic=serializable_result.get("topic", topic),
                language=language,
                path_data=serializable_result,
                source="generated"
            )
            db.add(new_lp)
            db.commit()
            db.refresh(new_lp)
            # Link generation task to history entry
            task_record = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
            if task_record:
                task_record.history_entry_id = new_lp.id
                db.commit()
            # Notify frontend of the persistent history path ID via SSE
            if progressCallback:
                await progressCallback({
                    "message": "Course saved to history.",
                    "persistentPathId": new_lp.path_id,
                    "action": "history_saved",
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as save_err:
            logger.error(f"Failed to save Course for task {task_id}: {save_err}")
            db.rollback() # Rollback on save failure
        
        # Store result in active_generations
        async with active_generations_lock:
            if task_id in active_generations:
                active_generations[task_id]["result"] = result
                # Status will be updated in DB in finally block
                active_generations[task_id]["status"] = "completed"
            
        logging.info(f"Course generation completed for: {topic}")
        
    except LearningPathGenerationError as e:
        # Handle specific, anticipated generation errors and auto-save to history
        # Send failure signal to frontend
        await enhanced_progress_callback(
            f"Error: {e.message}",
            phase="error",
            action="error"
        )
        async with active_generations_lock:
            if task_id in active_generations:
                active_generations[task_id]["status"] = "failed"
                active_generations[task_id]["error"] = {
                    "message": e.message,
                    "type": "learning_path_generation_error",
                    "details": e.details
                }
            
        # Automatically save known error course to history
        try:
            error_path_id = str(uuid.uuid4())
            err_lp = LearningPath(
                user_id=user_id,
                path_id=error_path_id,
                topic=topic,
                language=language,
                path_data={"status": "failed", "error": e.message},
                source="generated-failed",
                tags=["[Failed Generation]"]
            )
            db.add(err_lp)
            db.commit()
            db.refresh(err_lp)
            tr = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
            if tr:
                tr.history_entry_id = err_lp.id
                db.commit()
            if progressCallback:
                await progressCallback({
                    "message": "Failed course saved to history.",
                    "persistentPathId": error_path_id,
                    "action": "history_saved",
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as save_err3:
            logger.error(f"Failed to save known error Course for task {task_id}: {save_err3}")
            db.rollback()
        
        # Restore credit for anticipated errors too
        if user_id is not None:
             try:
                 # Find the user and restore credit
                 user = db.query(User).filter(User.id == user_id).first()
                 if user is not None:
                     user.credits += 1
                     transaction = CreditTransaction(
                         user_id=user.id,
                         amount=1,
                         transaction_type="refund",
                         notes=f"Refunded 1 credit due to known error: {e.message[:100]}"
                     )
                     db.add(transaction)
                     db.commit()
                     logger.info(f"Restored 1 credit to user {user_id} due to known error: {e.message[:100]}")
                 else:
                     logger.warning(f"User {user_id} not found for credit refund.")
             except Exception as credit_error:
                 logger.error(f"Failed to restore credit to user {user_id} after known error: {str(credit_error)}")
                 
    except Exception as outer_e:
        # Catch any other unexpected errors during setup or finalization
        error_message = f"Outer error in generate_learning_path_task: {str(outer_e)}"
        logging.exception(error_message)
        user_error_msg = "An unexpected error occurred before generation could complete."
        await enhanced_progress_callback(
            f"Error: {user_error_msg}",
            phase="error",
            action="error"
        )
        async with active_generations_lock:
            if task_id in active_generations:
                active_generations[task_id]["status"] = "failed"
                active_generations[task_id]["error"] = {
                    "message": user_error_msg,
                    "type": "outer_task_error"
                }
                
        # Attempt to restore credit here as well
        if user_id is not None:
            try:
                 # Find the user and restore credit
                 user = db.query(User).filter(User.id == user_id).first()
                 if user is not None:
                     user.credits += 1
                     transaction = CreditTransaction(
                         user_id=user.id,
                         amount=1,
                         transaction_type="refund",
                         notes=f"Refunded 1 credit due to outer task error."
                     )
                     db.add(transaction)
                     db.commit()
                     logger.info(f"Restored 1 credit to user {user_id} due to outer task error.")
                 else:
                     logger.warning(f"User {user_id} not found for credit refund.")
            except Exception as credit_error:
                 logger.error(f"Failed to restore credit to user {user_id} after outer task error: {str(credit_error)}")

    finally:
        # --- Update GenerationTask final status --- 
        final_status = GenerationTaskStatus.FAILED # Default to FAILED
        error_msg_to_save = None
        history_entry_id_to_link = None # Variable to hold the history ID
        try:
            # Check the status from the (potentially outdated) in-memory dict first
            # We rely on the DB as the source of truth, but this might give context
            task_info = None
            async with active_generations_lock:
                 task_info = active_generations.get(task_id)
                 
            if task_info and task_info["status"] == "completed":
                final_status = GenerationTaskStatus.COMPLETED
            elif task_info and task_info["status"] == "failed":
                error_msg_to_save = json.dumps(task_info.get("error")) # Store error dict as JSON string
                
            # If outer_e occurred, mark as failed regardless of in-memory state
            if 'outer_e' in locals() and outer_e:
                final_status = GenerationTaskStatus.FAILED
                if not error_msg_to_save:
                     user_error_msg = "An unexpected error occurred before generation could complete."
                     error_msg_to_save = json.dumps({"message": user_error_msg, "type": "outer_task_error"})
                     
            # If an inner exception occurred (not caught by outer_e)
            elif 'e' in locals() and e:
                final_status = GenerationTaskStatus.FAILED
                if not error_msg_to_save:
                     # Try to capture specific error message if possible
                    if isinstance(e, LearningPathGenerationError):
                        user_error_msg = e.message
                        error_type = "course_generation_error"
                    else:
                        user_error_msg = "An error occurred during course generation. Please try again later."
                        error_type = "unexpected_error"
                    error_msg_to_save = json.dumps({"message": user_error_msg, "type": error_type})

            # Find the recently saved history entry ID (if save was successful)
            if 'new_lp' in locals() and new_lp:
                history_entry_id_to_link = new_lp.id
            elif 'err_lp' in locals() and err_lp:
                history_entry_id_to_link = err_lp.id

            task_record = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
            if task_record:
                task_record.status = final_status
                task_record.ended_at = datetime.utcnow()
                task_record.error_message = error_msg_to_save
                task_record.history_entry_id = history_entry_id_to_link # Link task to history
                db.commit()
                logger.info(f"Updated GenerationTask {task_id} final status to {final_status}")
            else:
                 logger.error(f"Could not find GenerationTask record for task_id: {task_id} to set final status.")
        except Exception as db_err:
             logger.exception(f"DB error updating GenerationTask {task_id} final status: {db_err}")
             db.rollback()
        finally:
             db.close() # Close the session created for the background task
        # --- End Update Status --- 
        
        # --- Add finally block to signal SSE completion --- 
        logging.debug(f"Task {task_id} entering finally block.")
        async with progress_queues_lock:
            if task_id in progress_queues:
                try:
                    # logging.info(f"Task {task_id}: Attempting to signal completion queue.") # Remove this log
                    await progress_queues[task_id].put(None)  # Signal completion (or failure)
                    logging.info(f"Signaled completion queue for task {task_id}") # Restore original log message if needed, or remove this one too if the original wasn't there
                    # logging.info(f"Task {task_id}: Successfully signaled completion queue.") # Remove this log
                except Exception as q_err:
                    logging.error(f"Error signaling completion queue for task {task_id}: {q_err}")
            else:
                logging.warning(f"Progress queue for task {task_id} not found in finally block.")

        # --- Close Redis client ---
        if redis_client:
            try:
                await redis_client.aclose()
                logger.debug(f"Redis client closed for task {task_id}.")
            except Exception as redis_close_err:
                logger.error(f"Error closing Redis client for task {task_id}: {redis_close_err}")

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
async def get_learning_path(task_id: str):
    """
    Get the status and result of a course generation task.
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
        logger.exception(f"Error retrieving course for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve course data. Please try again later."
        )

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """
    Get progress updates for a course generation task using Server-Sent Events.
    Sends the latest snapshot from Redis on connection, then streams live updates.
    """
    redis_client = await get_redis_client() # Get Redis client for this request

    try:
        async with progress_queues_lock:
            if task_id not in progress_queues:
                # If queue doesn't exist, maybe task is done? Check active_generations? Or just 404?
                # Let's check active_generations briefly before 404ing
                async with active_generations_lock:
                    if task_id not in active_generations:
                         raise HTTPException(
                             status_code=404, 
                             detail="Progress updates not available. Task not found or already cleaned up."
                         )
                    # If task exists in active_generations but not progress_queues, it might be finished
                    # or had an error during setup. We can still try sending snapshot.
                    pass # Proceed to try sending snapshot even if queue is missing initially
            
            # Get the queue reference IF it exists, otherwise it's None
            queue = progress_queues.get(task_id) 
        
        async def event_generator():
            nonlocal redis_client # Allow modification if needed
            connected = True
            try:
                # 1. Send latest snapshot from Redis first (if available)
                if redis_client:
                    try:
                        snapshot_json = await redis_client.get(f"progress:{task_id}")
                        if snapshot_json:
                            try:
                                snapshot_data = json.loads(snapshot_json)
                                # Validate if it looks like a ProgressUpdate (optional)
                                if isinstance(snapshot_data, dict) and 'message' in snapshot_data and 'timestamp' in snapshot_data:
                                     yield f"data: {json.dumps(snapshot_data)}\n\n"
                                     logger.info(f"Sent progress snapshot from Redis for task {task_id}")
                                else:
                                     logger.warning(f"Invalid snapshot data structure in Redis for task {task_id}")
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse progress snapshot JSON from Redis for task {task_id}")
                            except Exception as parse_err:
                                logger.error(f"Error processing snapshot data for task {task_id}: {parse_err}")
                        else:
                            logger.info(f"No progress snapshot found in Redis for task {task_id}. Sending initial message.")
                            # Send initial message only if no snapshot exists
                            initial_update = ProgressUpdate(
                                message="Connection established. Waiting for progress...", 
                                timestamp=datetime.now().isoformat(),
                                phase="connection", action="connected"
                            )
                            yield f"data: {json.dumps(initial_update.dict())}\n\n"
                    except redis.RedisError as redis_err:
                        logger.error(f"Redis error fetching snapshot for task {task_id}: {redis_err}. Will rely on queue.")
                        # Send initial message if Redis fails
                        initial_update = ProgressUpdate(
                            message="Connection established (Redis snapshot unavailable). Waiting for progress...", 
                            timestamp=datetime.now().isoformat(),
                            phase="connection", action="connected"
                        )
                        yield f"data: {json.dumps(initial_update.dict())}\n\n"
                else:
                     # Send initial message if Redis is disabled
                    initial_update = ProgressUpdate(
                        message="Connection established (Redis disabled). Waiting for progress...", 
                        timestamp=datetime.now().isoformat(),
                        phase="connection", action="connected"
                    )
                    yield f"data: {json.dumps(initial_update.dict())}\n\n"

                # 2. Listen for live updates from the queue (if queue exists)
                if queue:
                    while connected: # Check connection status
                        try:
                            # Use asyncio.wait_for to handle client disconnects potentially faster
                            update = await asyncio.wait_for(queue.get(), timeout=60.0) # Example timeout
                        except asyncio.TimeoutError:
                            # No message received in timeout period, send a keep-alive comment or check connection?
                            # yield ": keep-alive\n\n" # Standard SSE keep-alive comment
                            # Or just continue waiting? For now, let's just continue.
                            continue 
                        except Exception as q_get_err:
                             logger.error(f"Error getting from queue for task {task_id}: {q_get_err}")
                             break # Exit loop on queue error

                        if update is None:
                            yield "data: {\"complete\": true}\n\n"
                            break # Exit loop on completion signal

                        if hasattr(update, 'dict'):
                            update_dict = update.dict(exclude_none=True)
                        else:
                            update_dict = update # Assume it's already a dict or basic type

                        yield f"data: {json.dumps(update_dict, cls=DateTimeEncoder)}\n\n"
                else:
                    # If queue was missing initially, check active_generations status.
                    # If task is completed/failed, send the final signal now.
                    async with active_generations_lock:
                        task_info = active_generations.get(task_id)
                        if task_info and task_info["status"] in ["completed", "failed"]:
                            logger.info(f"Task {task_id} finished, sending complete signal as queue was missing.")
                            yield "data: {\"complete\": true}\n\n"
                        else:
                            logger.warning(f"Progress queue for task {task_id} not found, and task not marked as finished. Stream ending.")
                            # Optionally send an error message here?
                    # End the stream if no queue exists and task isn't finished
                    pass 

            except asyncio.CancelledError:
                logger.info(f"SSE connection for task {task_id} cancelled by client.")
                connected = False # Mark as disconnected
            except Exception as e:
                logger.error(f"Error in SSE stream for task {task_id}: {str(e)}\n{traceback.format_exc()}")
                try:
                    # Attempt to send an error message to the client
                    error_data = {"error": "An internal error occurred in the progress stream.", "type": "stream_error"}
                    yield f"data: {json.dumps(error_data)}\n\n"
                except Exception:
                    logger.error(f"Failed to send error message to SSE client for task {task_id}")
            finally:
                logger.info(f"SSE event_generator loop finished for task {task_id}. Connected: {connected}")
                # Close Redis client used by this generator
                if redis_client:
                    try:
                        await redis_client.aclose()
                        logger.debug(f"Redis client closed for SSE stream {task_id}.")
                    except Exception as redis_close_err:
                        logger.error(f"Error closing Redis client for SSE stream {task_id}: {redis_close_err}")
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no" # Useful for Nginx buffering issues
            }
        )
    except HTTPException:
        # Close Redis client if HTTP exception occurs *before* generator starts
        if redis_client: await redis_client.aclose()
        raise
    except Exception as e:
        logger.exception(f"Error setting up progress stream for task {task_id}: {str(e)}")
        # Close Redis client on setup error
        if redis_client: await redis_client.aclose()
        raise HTTPException(
            status_code=500,
            detail="Failed to set up progress updates stream. Please try again later."
        )

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
