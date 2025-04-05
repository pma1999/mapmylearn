import os
import sys
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("bootstrap")

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath("."))
logger.info(f"Python path: {sys.path}")

def get_validated_port(port_env: Optional[str] = None) -> int:
    """
    Validates and returns the port from environment variable.
    Falls back to 8000 if the port is invalid or not provided.
    """
    if port_env is None:
        port_env = os.environ.get("PORT")
    
    default_port = 8000
    
    if port_env is None:
        logger.warning(f"PORT environment variable not set. Using default: {default_port}")
        return default_port
        
    logger.info(f"PORT environment variable: '{port_env}'")
    
    try:
        port = int(port_env)
        if port < 1 or port > 65535:
            logger.warning(f"PORT {port} out of valid range (1-65535). Using default: {default_port}")
            return default_port
        logger.info(f"Using PORT: {port}")
        return port
    except ValueError as e:
        logger.error(f"Error converting PORT to integer: {e}")
        logger.warning(f"Using default port: {default_port}")
        return default_port

def log_environment():
    """Log important environment variables for debugging purposes"""
    env_vars = [
        "ENVIRONMENT", "PYTHONPATH", "RAILWAY_ENVIRONMENT", 
        "RAILWAY_SERVICE_NAME", "PORT", "TRUSTED_HOSTS", "ALLOWED_ORIGINS"
    ]
    
    logger.info("Environment variables:")
    for var in env_vars:
        value = os.environ.get(var, "[not set]")
        # Mask sensitive values if needed
        logger.info(f"  {var}: {value}")

if __name__ == "__main__":
    try:
        logger.info("Starting application bootstrap")
        log_environment()
        
        # Get validated port
        port = get_validated_port()
        
        # Import here to ensure environment is fully set up first
        import uvicorn
        
        logger.info(f"Starting uvicorn server on port {port}")
        uvicorn.run(
            "backend.api:app", 
            host="0.0.0.0", 
            port=port,
            log_level=os.environ.get("LOG_LEVEL", "info").lower(),
            proxy_headers=True,
            forwarded_allow_ips="*"
        )
    except Exception as e:
        logger.exception(f"Fatal error during bootstrap: {e}")
        sys.exit(1) 