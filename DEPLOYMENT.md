# Deployment Guide for Learny

This guide explains how to deploy the Learny application using Vercel for the frontend and Railway for the backend, as well as how to run it locally for development and testing.

## Local Development

### Setting Up Local Backend

1. **Create a virtual environment:**

   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows PowerShell
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   
   Create a `.env` file in the root directory with:

   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PPLX_API_KEY=your_perplexity_api_key_here
   # In development, SERVER_SECRET_KEY is optional
   # SERVER_SECRET_KEY=your_secure_random_key_here
   ```

4. **Run the backend:**

   ```bash
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

### Setting Up Local Frontend

1. **Install dependencies:**

   ```bash
   cd frontend
   npm install
   ```

2. **Run the frontend:**

   ```bash
   npm start
   ```

3. **Access the application:**
   Open your browser and go to `http://localhost:3000`

## Prerequisites

- [Vercel Account](https://vercel.com)
- [Railway Account](https://railway.app)
- [GitHub Account](https://github.com)
- OpenAI API Key
- Perplexity API Key

## Deploying the Backend to Railway

### Option 1: Deploy via Railway Dashboard

1. **Push your code to GitHub**
   
   Make sure your project is in a GitHub repository.

2. **Create a new project in Railway**

   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project" and select "Deploy from GitHub repo"
   - Select your repository
   - Railway will automatically detect the configuration from `railway.json` and `Procfile`

3. **Configure environment variables**

   In the Railway dashboard, add the following environment variables:
   
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `PPLX_API_KEY`: Your Perplexity API key
   - `SERVER_SECRET_KEY`: A secure secret key for encrypting API keys (REQUIRED in production)
   - `FRONTEND_URL`: Your Vercel frontend URL (once deployed)
   - Any other environment variables needed by your application
   
   **IMPORTANT: About SERVER_SECRET_KEY**
   
   The `SERVER_SECRET_KEY` is used to encrypt sensitive data, including API keys provided by users. 
   This variable is **mandatory** in production environments - the application will refuse to start 
   without it. You can generate a secure random key with this command:
   
   ```bash
   openssl rand -hex 32
   ```
   
   Once set, do not change this key as it will invalidate all existing encrypted tokens.
   Ensure this key is kept secure and not exposed in public repositories.

4. **Deploy the backend**

   Railway will automatically deploy your application based on the configuration in `railway.json`.

5. **Get your backend URL**

   Once deployed, Railway will provide you with a URL for your backend service. Note this URL as you'll need it for the frontend configuration.

### Option 2: Deploy via Railway CLI

1. **Install Railway CLI**

   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**

   ```bash
   railway login
   ```

3. **Initialize your project**

   ```bash
   railway init
   ```

4. **Link to an existing project (if you already created one in the dashboard)**

   ```bash
   railway link
   ```

5. **Set environment variables**

   ```bash
   railway variables set OPENAI_API_KEY=your_openai_api_key
   railway variables set PPLX_API_KEY=your_perplexity_api_key
   railway variables set SERVER_SECRET_KEY=your_secure_random_key
   railway variables set FRONTEND_URL=your_vercel_frontend_url
   ```

6. **Deploy the application**

   ```bash
   railway up
   ```

7. **Get your deployment URL**

   ```bash
   railway status
   ```

## Deploying the Frontend to Vercel

1. **Update the API URL in vercel.json**

   In the `frontend/vercel.json` file, replace `https://your-railway-app-name.railway.app` with your actual Railway backend URL.

2. **Push changes to GitHub**

   Make sure all changes are committed and pushed to your GitHub repository.

3. **Create a new project in Vercel**

   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "Add New" > "Project"
   - Import your GitHub repository
   - Configure the project:
     - Root Directory: `frontend`
     - Build Command: `npm run build`
     - Output Directory: `build`

4. **Configure environment variables**

   In the Vercel dashboard, add the following environment variables:
   
   - `REACT_APP_API_URL`: Your Railway backend URL

5. **Deploy the frontend**

   Click "Deploy" and Vercel will build and deploy your frontend application.

## Switching Between Local and Deployed Environments

### Frontend

1. **For local development:**
   - No environment variable changes needed
   - The frontend will automatically use `http://localhost:8000` as the API URL

2. **For testing with deployed backend:**
   - Create a `frontend/.env.local` file with:
     ```
     REACT_APP_API_URL=https://your-railway-app-name.railway.app
     ```

### Backend

1. **For local development:**
   - The CORS settings already include `http://localhost:3000`
   - No changes needed

2. **For production:**
   - Ensure the `FRONTEND_URL` environment variable is set in Railway
   - Make sure your frontend Vercel domain is in the allowed_origins list in `api.py`

## Connecting Frontend and Backend

1. **Update Railway environment variables**

   Once your frontend is deployed, go back to Railway and add your Vercel frontend URL to the `FRONTEND_URL` environment variable.

2. **Verify the connection**

   Visit your Vercel frontend URL and ensure it can communicate with the backend by testing the generation of a learning path.

## Troubleshooting

- **CORS Issues**: Ensure the `allowed_origins` in `api.py` includes your Vercel domain
- **API Connection Failures**: Check that environment variables are set correctly on both platforms
- **Application Fails to Start**: 
  - Verify that `SERVER_SECRET_KEY` is set in production environments
  - If you see an error about missing SERVER_SECRET_KEY, generate one as described in the "Configure environment variables" section
- **Deployment Failures**: 
  - On Railway: Check logs in the Railway dashboard
  - On Vercel: Check build logs in the Vercel dashboard

## Custom Domains (Optional)

Both Vercel and Railway support custom domains:

- **Vercel**: Go to your project settings > Domains to add a custom domain
- **Railway**: Go to your project settings > Domains to add a custom domain

If you add custom domains, remember to update the corresponding environment variables and CORS settings.

# Error Handling

## Overview

The application implements a comprehensive error handling strategy to ensure that all errors are:

1. **Captured and Logged**: All exceptions are caught, logged with appropriate context, and include stack traces for easier debugging.
2. **Properly Reported**: User-facing error messages are sanitized to avoid exposing sensitive information.
3. **Consistently Formatted**: All error responses follow a standard JSON format that the frontend can easily process.
4. **Progress-Tracked**: For background tasks, errors are reported via progress updates in real-time.

## Error Response Format

All API error responses follow this consistent format:

```json
{
  "status": "failed",
  "error": {
    "message": "User-friendly error message",
    "type": "error_type",
    "details": {},  // Optional additional details
    "error_id": "unique-reference-id"  // For server errors
  }
}
```

## Error Types

The system handles several types of errors:

1. **HTTP Errors**: Regular HTTP exceptions like 404 (Not Found), 400 (Bad Request), etc.
2. **Validation Errors**: Input validation failures from Pydantic models.
3. **Learning Path Generation Errors**: Specific errors that occur during learning path generation.
4. **Unexpected Errors**: Any unhandled exceptions caught by the middleware.

## Background Task Error Handling

Background tasks (like learning path generation) implement these error handling practices:

1. Each critical operation is wrapped in try/except blocks.
2. When an error occurs, it's logged with full details.
3. A user-friendly error message is sent via the progress callback.
4. The task status is updated to "failed" with error details.

## Frontend Error Handling

The frontend uses axios interceptors to process error responses and display user-friendly messages. It:

1. Extracts structured error information from the response.
2. Presents appropriate error messages to users.
3. Includes error reference IDs for easier support troubleshooting.

## Testing Error Handling

Unit tests verify the error handling behavior, including:

1. Testing that HTTP exceptions return the standardized format.
2. Verifying validation errors are properly formatted.
3. Confirming that task-specific errors are reported via progress updates.
4. Testing that the global middleware catches unhandled exceptions.

## Logging

All errors are logged using structured JSON logging with these details:

1. Timestamp
2. Log level
3. Module, function, and line number
4. Full exception details and stack trace (in development mode)
5. Sanitized exception details (in production mode)

This comprehensive approach ensures that no errors go unnoticed or unreported, improving overall application reliability and user experience. 