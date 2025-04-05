#!/usr/bin/env python
"""
Pre-deployment validation script for Railway environment.
This script simulates the Railway environment and validates the application startup.
"""

import os
import sys
import subprocess
import logging
import argparse
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("deployment-validator")

def parse_args():
    parser = argparse.ArgumentParser(description="Validate Railway deployment")
    parser.add_argument("--port", type=str, default="$PORT", 
                        help="PORT value to test (use $PORT to test literal dollar sign)")
    parser.add_argument("--log-level", type=str, default="info",
                        help="Log level for the test")
    parser.add_argument("--env-file", type=str, default=".env.production",
                        help="Environment file to load")
    return parser.parse_args()

def load_env_file(env_file):
    """Load environment variables from file"""
    if not Path(env_file).exists():
        logger.warning(f"Environment file {env_file} not found. Using defaults.")
        return {}
    
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key] = value
    
    return env_vars

def simulate_railway_environment(port_value, env_file, log_level):
    """Set up environment variables to simulate Railway"""
    env = os.environ.copy()
    
    # Load from env file
    file_vars = load_env_file(env_file)
    env.update(file_vars)
    
    # Add Railway-specific variables
    env["PORT"] = port_value
    env["RAILWAY_ENVIRONMENT"] = "production"
    env["RAILWAY_SERVICE_NAME"] = "backend"
    env["LOG_LEVEL"] = log_level
    
    return env

def test_bootstrap_script(env):
    """Test bootstrap.py with the simulated environment"""
    logger.info("Testing bootstrap.py with simulated Railway environment")
    logger.info(f"PORT = {env.get('PORT', '[not set]')}")
    
    try:
        result = subprocess.run(
            [sys.executable, "bootstrap.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=5  # Kill after 5 seconds since we just want to validate startup
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        logger.info("Bootstrap script started successfully (timeout as expected)")
        return "", "", 0

def test_startup_script(env):
    """Test startup.sh with the simulated environment"""
    if not Path("/app/startup.sh").exists() and not Path("startup.sh").exists():
        logger.warning("startup.sh not found. Creating temporary version for testing.")
        with open("startup.sh", "w") as f:
            f.write('#!/bin/bash\n')
            f.write('echo "Starting application with environment:"\n')
            f.write('echo "PORT=$PORT"\n')
            f.write('echo "PYTHONPATH=$PYTHONPATH"\n')
            f.write('python bootstrap.py\n')
        os.chmod("startup.sh", 0o755)
    
    script_path = "/app/startup.sh" if Path("/app/startup.sh").exists() else "./startup.sh"
    
    logger.info(f"Testing {script_path} with simulated Railway environment")
    try:
        result = subprocess.run(
            ["/bin/bash", script_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=5  # Kill after 5 seconds since we just want to validate startup
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        logger.info("Startup script started successfully (timeout as expected)")
        return "", "", 0
    except FileNotFoundError:
        logger.error(f"Startup script {script_path} not found or not executable")
        return "", "Startup script not found or not executable", 1

def main():
    args = parse_args()
    logger.info("Starting deployment validation")
    
    # Test with configured PORT value
    env = simulate_railway_environment(args.port, args.env_file, args.log_level)
    
    # Test bootstrap.py directly
    logger.info("=== Testing bootstrap.py ===")
    stdout, stderr, returncode = test_bootstrap_script(env)
    if returncode != 0:
        logger.error(f"Bootstrap script failed with code {returncode}")
        logger.error(f"STDERR: {stderr}")
    else:
        logger.info("Bootstrap script validation passed")
    
    # Test startup.sh
    logger.info("\n=== Testing startup script ===")
    stdout, stderr, returncode = test_startup_script(env)
    if returncode != 0:
        logger.error(f"Startup script failed with code {returncode}")
        logger.error(f"STDERR: {stderr}")
    else:
        logger.info("Startup script validation passed")
    
    # Clean up
    if Path("./startup.sh").exists():
        logger.info("Cleaning up temporary startup.sh")
        os.unlink("./startup.sh")
    
    logger.info("Deployment validation completed")

if __name__ == "__main__":
    main() 