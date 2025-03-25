# Learny - AI-Powered Learning Path Generator

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Web-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-yellow)
![React](https://img.shields.io/badge/React-18.x-61DAFB)
![Deployment](https://img.shields.io/badge/deployment-Local%20%7C%20Vercel%20%7C%20Railway-success)

Learny is an innovative web application that creates personalized learning paths for any topic using artificial intelligence (AI). The system leverages large language models (LLMs) to research, organize, and generate comprehensive educational content, saving you hours of curriculum planning.

## ✨ Features

- **AI-Generated Learning Paths**: Enter any topic to receive a structured learning path with modules and submodules
- **Smart Web Research**: Automatically gathers relevant information from the web to enrich your learning path
- **Parallel Processing**: Efficiently processes multiple modules and submodules simultaneously
- **Comprehensive Content**: Generates detailed educational content for each submodule
- **History Management**: Save, organize, tag, and search your generated learning paths
- **Import/Export**: Share learning paths via JSON export/import functionality
- **Modern UI**: Responsive and intuitive React-based interface

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [License](#-license)

## 🏗 Architecture

Learny follows a modern web application architecture:

- **Backend**: Python-based FastAPI application with LangChain for AI integration
- **Frontend**: React application with Material UI components
- **AI Integration**: OpenAI models via LangChain
- **Search Integration**: Perplexity API for web research
- **Processing**: Graph-based workflow for parallelized content generation


## 🔍 Prerequisites

- Python 3.8+
- Node.js 14+
- OpenAI API key
- Perplexity API key
- Git

## 🚀 Installation

### Clone the Repository

```bash
git clone https://github.com/pma1999/learny.git
cd learny
```

### Backend Setup

1. Create and activate a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install backend dependencies:

```bash
pip install -r requirements.txt
```

3. Configure your environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys
```

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install frontend dependencies:

```bash
npm install
# or if you use yarn
yarn install
```

## ⚙️ Configuration

Edit your `.env` file with the following required API keys:

```
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
PPLX_API_KEY=your_perplexity_api_key_here

# Optional Settings
# LANGCHAIN_TRACING=true
# LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
# LANGCHAIN_API_KEY=your_langchain_api_key_here
```

Additional configuration options:

- Set logging levels and formats in `config/log_config.py`
- Configure parallel processing parameters in the API or UI

## 🎮 Usage

### Starting the Application

1. Start the backend server:

```bash
# From the root directory
uvicorn api:app --reload
```

2. In a separate terminal, start the frontend development server:

```bash
# From the frontend directory
npm start
# or with yarn
yarn start
```

3. Open your browser and navigate to `http://localhost:3000`

### Creating a Learning Path

1. Navigate to the Generator page
2. Enter your desired learning topic
3. Adjust advanced settings if needed (optional)
4. Click "Generate Learning Path"
5. Wait while the system researches and creates your personalized path
6. Review your comprehensive learning path with modules and submodules

### Managing Your Learning Paths

- **Save**: Automatically save generated paths to your history
- **Tag**: Add custom tags to organize your learning paths
- **Favorite**: Mark paths as favorites for quick access
- **Export/Import**: Share your learning paths with others via JSON files
- **Search**: Find specific learning paths in your history

## 🌐 Deployment

Learny supports both local development and cloud deployment:

### Local Development

Run the application locally for development and testing:

1. **Start the backend server:**

```bash
# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\activate

# Run the backend
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

2. **Start the frontend development server:**

```bash
cd frontend
npm start
```

3. **Access the application at:** `http://localhost:3000`

### Cloud Deployment

Deploy to Vercel (frontend) and Railway (backend) for production:

1. **Backend (Railway)**
   - Push your code to GitHub
   - Create a new project in Railway linking to your repository
   - Set required environment variables (API keys)
   
2. **Frontend (Vercel)**
   - Update the API URL in frontend/vercel.json with your Railway URL
   - Create a new project in Vercel linking to your repository
   - Set the root directory to "frontend"
   - Deploy the application

For a complete step-by-step guide, please refer to the [Deployment Guide](DEPLOYMENT.md).

## 📡 API Documentation

The backend exposes a RESTful API with the following main endpoints:

### API Key Management

- `POST /api/auth/api-keys`: Validate and store API keys securely
  - Body: `{ "google_api_key": "string", "pplx_api_key": "string" }`
  - Returns: `{ "google_key_token": "string", "pplx_key_token": "string", "google_key_valid": bool, "pplx_key_valid": bool, "google_key_error": "string", "pplx_key_error": "string" }`
  - Notes: Performs strict validation on key format and functionality. Google keys must start with "AIza" followed by 35 characters. Perplexity keys must start with "pplx-" followed by at least 32 characters. Keys are encrypted and referenced by secure tokens.

- `POST /api/validate-api-keys`: Validate API keys without storing them
  - Body: `{ "google_api_key": "string", "pplx_api_key": "string" }`
  - Returns: `{ "google_key_valid": bool, "pplx_key_valid": bool, "google_key_error": "string", "pplx_key_error": "string" }`

### Learning Path Generation

- `POST /api/generate-learning-path`: Start generating a new learning path
  - Body: `{ "topic": "string", "parallel_count": int, "search_parallel_count": int, "submodule_parallel_count": int, "google_key_token": "string", "pplx_key_token": "string" }`
  - Returns: `{ "task_id": "string", "status": "string" }`

- `GET /api/learning-path/{task_id}`: Get generation status and results
- `GET /api/progress/{task_id}`: Stream progress updates (SSE)
- `DELETE /api/learning-path/{task_id}`: Clean up completed tasks

### History Management

- `GET /api/history`: Get list of saved learning paths
- `GET /api/history/{entry_id}`: Get a specific learning path
- `POST /api/history`: Save a learning path to history
- `PUT /api/history/{entry_id}`: Update tags and favorite status
- `DELETE /api/history/{entry_id}`: Delete a learning path
- `POST /api/history/import`: Import a learning path from JSON
- `GET /api/history/export`: Export all history entries
- `DELETE /api/history/clear`: Clear all history

## 💻 Development

### Debugging

Learny includes helpful debugging tools:

```bash
# Run with debug options
python debug_learning_path.py "Your Topic" --log-level DEBUG --save-result

# Analyze logs
python diagnostic.py learning_path.log --summary
```

### Project Structure

```
learny/
├── api.py              # FastAPI endpoints
├── main.py             # Main application entry point
├── config/             # Configuration utilities
├── core/               # Core logic and graph workflow
├── frontend/           # React application
├── history/            # History management
├── models/             # Data models
├── parsers/            # Output parsers
├── prompts/            # LLM prompt templates
├── services/           # External services (LLM, search)
├── tests/              # Test suite
└── utils/              # Utility functions
```

### Key Components

- **Graph Builder**: The system uses a directed graph workflow for generating learning paths (`core/graph_builder.py`)
- **Prompt Templates**: Carefully crafted prompts for the LLM are stored in `prompts/learning_path_prompts.py`
- **State Management**: The application state flows through the graph nodes (`models/models.py`)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Created by [pma1999](https://github.com/pma1999) | [Report an Issue](https://github.com/pma1999/learny/issues)

## Recent Code Refactoring

The codebase has been refactored to organize files into a proper Python package structure. The main changes are:

1. All backend code has been moved into a `backend` directory package
2. All imports have been updated to use the new package structure (e.g., `from backend.models.models import ...`)
3. A `setup.py` file has been added to make the package installable

### Running the Application after Refactoring

To run the application after the refactoring:

1. Install the package in development mode:
```
pip install -e .
```

2. Run the server using the new script:
```
python run_server.py
```

Alternatively, you can run it with direct module imports:
```
python -m backend.api
```

## Deployment on Railway

The application is configured for deployment on Railway. With the recent code refactoring that moved all backend code into a `/backend` directory, deployment configuration has been updated accordingly:

- `Procfile` has been updated to run from the backend directory
- `railway.json` has been configured to install dependencies from the backend directory
- `requirements.txt` in the root points to the backend requirements file
- `PYTHONPATH` is set to include the root directory so imports work correctly

These changes ensure that the application will deploy correctly on Railway despite the new directory structure.

When deploying:
1. Ensure all environment variables are set in Railway's dashboard
2. The deployment will automatically use the root-level configuration files
3. No additional steps are needed - Railway will handle the new directory structure
