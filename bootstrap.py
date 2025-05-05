import os
import sys
import logging
from typing import Optional, List

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

def get_forwarded_allow_ips() -> List[str] | str:
    """
    Gets and validates the trusted proxy IPs from the TRUSTED_PROXY_IPS environment variable.

    In production, requires TRUSTED_PROXY_IPS to be set. Exits if not set.
    In development, defaults to "*" if not set.

    Returns:
        Union[List[str], str]: A list of trusted IP/CIDR strings, or "*"
    """
    trusted_ips_env = os.environ.get("TRUSTED_PROXY_IPS")
    is_production = os.getenv("ENVIRONMENT", "development") == "production"

    if is_production:
        if not trusted_ips_env:
            logger.critical("FATAL: TRUSTED_PROXY_IPS environment variable is not set in production environment. Exiting for security.")
            sys.exit(1)
        # In production, use the explicitly set value (even if it's "*")
        # Allow "*" or parse comma-separated list/CIDR
        if trusted_ips_env == "*":
            logger.warning("TRUSTED_PROXY_IPS is set to '*' in production. Trusting all proxy IPs.")
            return "*"
        else:
            try:
                ip_list = [ip.strip() for ip in trusted_ips_env.split(',') if ip.strip()]
                if not ip_list: # Handle case where env var is set but empty/only commas
                    logger.critical("FATAL: TRUSTED_PROXY_IPS is set but resulted in an empty list after parsing in production. Exiting.")
                    sys.exit(1)
                logger.info(f"Production: Trusting proxy IPs: {ip_list}")
                return ip_list
            except Exception as e:
                 logger.critical(f"FATAL: Error parsing TRUSTED_PROXY_IPS in production: {e}. Value was '{trusted_ips_env}'. Exiting.")
                 sys.exit(1)
    else: # Development environment
        if not trusted_ips_env:
            logger.warning("Development: TRUSTED_PROXY_IPS not set. Defaulting forwarded_allow_ips to '*'")
            return "*"
        else:
             # Allow "*" or parse comma-separated list/CIDR
            if trusted_ips_env == "*":
                logger.info("Development: TRUSTED_PROXY_IPS explicitly set to '*'. Trusting all proxy IPs.")
                return "*"
            else:
                try:
                    ip_list = [ip.strip() for ip in trusted_ips_env.split(',') if ip.strip()]
                    if not ip_list:
                         logger.warning("Development: TRUSTED_PROXY_IPS is set but resulted in an empty list after parsing. Defaulting to '*'")
                         return "*"
                    logger.info(f"Development: Trusting proxy IPs: {ip_list}")
                    return ip_list
                except Exception as e:
                     logger.warning(f"Development: Error parsing TRUSTED_PROXY_IPS: {e}. Value was '{trusted_ips_env}'. Defaulting to '*'.")
                     return "*"

def log_environment():
    """Log important environment variables for debugging purposes"""
    env_vars = [
        "ENVIRONMENT", "PYTHONPATH", "RAILWAY_ENVIRONMENT", 
        "RAILWAY_SERVICE_NAME", "PORT", "TRUSTED_HOSTS", "ALLOWED_ORIGINS",
        "TRUSTED_PROXY_IPS" # Add the new variable here
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
        
        # Get validated forwarded IPs
        forwarded_ips = get_forwarded_allow_ips()
        
        # Import here to ensure environment is fully set up first
        import uvicorn
        
        logger.info(f"Starting uvicorn server on host '0.0.0.0', port {port}")
        uvicorn.run(
            "backend.api:app", 
            host="0.0.0.0", # Changed back from "::"
            port=port,
            log_level=os.environ.get("LOG_LEVEL", "info").lower(),
            proxy_headers=True, # Keep True
            forwarded_allow_ips=forwarded_ips # Use validated value
        )
    except SystemExit as e:
        # Log SystemExit specifically if it happens (e.g., from get_forwarded_allow_ips)
        logger.critical(f"Application exiting with status {e.code}")
        sys.exit(e.code)
    except Exception as e:
        logger.exception(f"Fatal error during bootstrap: {e}")
        sys.exit(1) 