import unittest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
from fastapi.testclient import TestClient
from fastapi import HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse

# Add parent directory to path to allow importing the application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import app, generate_learning_path_task, LearningPathGenerationError, active_generations, active_generations_lock

class TestErrorHandling(unittest.TestCase):
    """Test error handling improvements in the learning path generation API."""
    
    def setUp(self):
        self.client = TestClient(app)
        # Reset active_generations for each test
        active_generations.clear()
    
    def test_http_exception_handler(self):
        """Test that HTTP exceptions return the standardized error format."""
        # Test a 404 error
        response = self.client.get("/api/learning-path/non-existent-task")
        self.assertEqual(response.status_code, 404)
        
        # Verify the response follows our error format
        data = response.json()
        self.assertEqual(data["status"], "failed")
        self.assertIn("error", data)
        self.assertIn("message", data["error"])
        self.assertEqual(data["error"]["type"], "http_error")
    
    def test_validation_error_handler(self):
        """Test that validation errors return the standardized error format."""
        # Send an invalid request (missing required field 'topic')
        response = self.client.post("/api/generate-learning-path", json={
            "parallel_count": 2,
            "google_key_token": "fake-token"
        })
        self.assertEqual(response.status_code, 422)
        
        # Verify the response follows our error format
        data = response.json()
        self.assertEqual(data["status"], "failed")
        self.assertIn("error", data)
        self.assertIn("message", data["error"])
        self.assertEqual(data["error"]["type"], "validation_error")
        self.assertIn("details", data["error"])
        
    @patch('api.key_manager.get_key')
    @patch('api.key_manager.get_env_key')
    @patch('api.generate_learning_path')
    def test_learning_path_generation_error_handling(self, mock_generate, mock_get_env_key, mock_get_key):
        """Test that LearningPathGenerationError is properly handled and reported."""
        # Setup mocks
        mock_get_key.side_effect = Exception("Invalid token")
        mock_get_env_key.return_value = None  # No fallback key
        
        # Run synchronous test with asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_test():
            # Setup test data
            task_id = "test-task-id"
            progress_messages = []
            
            # Mock progress callback
            async def progress_callback(message):
                progress_messages.append(message)
            
            # Initialize the task in active_generations
            async with active_generations_lock:
                active_generations[task_id] = {"status": "running", "result": None}
            
            # Call the function with mocked dependencies
            await generate_learning_path_task(
                task_id=task_id,
                topic="Test Topic",
                progress_callback=progress_callback,
                google_key_token="invalid-token",
                pplx_key_token=None
            )
            
            # Check that the error was properly reported
            self.assertIn("Error:", progress_messages[-1])
            
            # Check that the task status was updated correctly
            async with active_generations_lock:
                self.assertEqual(active_generations[task_id]["status"], "failed")
                self.assertIn("error", active_generations[task_id])
                self.assertIn("message", active_generations[task_id]["error"])
                self.assertIn("type", active_generations[task_id]["error"])
        
        # Run the async test
        loop.run_until_complete(run_test())
        loop.close()
    
    @patch('api.key_manager.get_key')
    @patch('api.key_manager.get_env_key')
    @patch('api.generate_learning_path')
    def test_unexpected_error_handling(self, mock_generate, mock_get_env_key, mock_get_key):
        """Test that unexpected exceptions are properly handled and sanitized."""
        # Setup mocks
        mock_get_key.return_value = "fake-api-key"
        mock_get_env_key.return_value = "fake-api-key"
        mock_generate.side_effect = Exception("Internal server error with sensitive details")
        
        # Run synchronous test with asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_test():
            # Setup test data
            task_id = "test-task-id-2"
            progress_messages = []
            
            # Mock progress callback
            async def progress_callback(message):
                progress_messages.append(message)
            
            # Initialize the task in active_generations
            async with active_generations_lock:
                active_generations[task_id] = {"status": "running", "result": None}
            
            # Call the function with mocked dependencies
            await generate_learning_path_task(
                task_id=task_id,
                topic="Test Topic",
                progress_callback=progress_callback,
                google_key_token="valid-token",
                pplx_key_token="valid-token"
            )
            
            # Check that a sanitized error was reported to the user
            self.assertIn("Error:", progress_messages[-1])
            # The error message should not contain the sensitive details
            self.assertNotIn("sensitive details", progress_messages[-1])
            
            # Check that the task status was updated correctly
            async with active_generations_lock:
                self.assertEqual(active_generations[task_id]["status"], "failed")
                self.assertIn("error", active_generations[task_id])
                self.assertEqual(active_generations[task_id]["error"]["type"], "unexpected_error")
                # The error message stored internally should also be sanitized
                self.assertNotIn("sensitive details", active_generations[task_id]["error"]["message"])
        
        # Run the async test
        loop.run_until_complete(run_test())
        loop.close()

    def test_global_exception_middleware(self):
        """Test that HTTP exceptions are properly formatted through the exception handler."""
        # Test a direct call to our http_exception_handler instead of using the middleware
        # which is harder to test with the test client
        
        # Create a mock request
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/test-path"
        
        # Create a test exception
        test_exception = HTTPException(status_code=500, detail="Test server error")
        
        # Run the handler directly
        async def run_test():
            # Import the handler here to avoid circular imports
            from api import http_exception_handler
            
            # Call the handler with our mock objects
            response = await http_exception_handler(mock_request, test_exception)
            
            # Verify it's a JSONResponse with our expected format
            self.assertIsInstance(response, JSONResponse)
            self.assertEqual(response.status_code, 500)
            
            # Check the content
            content = response.body
            data = json.loads(content)
            
            self.assertEqual(data["status"], "failed")
            self.assertIn("error", data)
            self.assertEqual(data["error"]["message"], "Test server error")
            self.assertEqual(data["error"]["type"], "http_error")
        
        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_test())
        loop.close()

if __name__ == '__main__':
    unittest.main() 