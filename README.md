# Learny - AI-Powered Learning Path Generator

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Web-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-yellow)
![React](https://img.shields.io/badge/React-18.x-61DAFB)
![Deployment](https://img.shields.io/badge/deployment-Vercel%20%7C%20Railway-success)

<div align="center">
  <a href="https://learny-peach.vercel.app">
    <img src="https://img.shields.io/badge/View_Demo-Live_Site-blue?style=for-the-badge" alt="View Demo" />
  </a>
</div>

## 🚀 Overview

Learny is an innovative AI-powered application that generates personalized learning paths for any topic. Simply enter what you want to learn, and Learny will create a structured, comprehensive curriculum with modules and submodules specifically designed for that subject. The system leverages large language models (LLMs) to research, organize, and develop educational content, saving you hours of curriculum planning.

## ✨ Features

- **AI-Generated Learning Paths**: Enter any topic to receive a structured learning path with modules and submodules
- **Smart Web Research**: Automatically gathers relevant information from the web to enrich your learning path
- **Parallel Processing**: Efficiently processes multiple modules and submodules simultaneously
- **Comprehensive Content**: Generates detailed educational content for each submodule
- **History Management**: Save, organize, tag, and search your generated learning paths
- **Import/Export**: Share learning paths via JSON export/import functionality
- **Multi-language Support**: Generate content in various languages
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
- **AI Integration**: Google AI (Gemini) API via LangChain
- **Search Integration**: Perplexity API for web research
- **Processing**: Graph-based workflow for parallelized content generation
- **Storage**: Browser-based localStorage for history management


## 🔍 Prerequisites

- Python 3.8+
- Node.js 14+
- API Keys:
  - Google AI (Gemini) API key
  - Perplexity API key
- Git

## 🚀 Installation

### Clone the Repository

```bash
git clone https://github.com/pma1999/learny.git
cd learny
```

### Backend Setup

1. Create and activate a virtual environment:

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
cp backend/.env.example .env
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
```

## ⚙️ Configuration

Edit your `.env` file with the following required API keys:

```
# Required API Keys
GOOGLE_API_KEY=your_google_api_key_here
PPLX_API_KEY=your_perplexity_api_key_here

# IMPORTANT: SERVER_SECRET_KEY is MANDATORY in production environments
# Generate a secure key with: openssl rand -hex 32
SERVER_SECRET_KEY=your_secure_random_key_here
```

Additional configuration options:

- Set logging levels and formats in `backend/config/log_config.py`
- Configure parallel processing parameters in the API or UI

## 🎮 Usage

### Starting the Application

1. Start the backend server:

```bash
# From the root directory
python run_server.py
```

2. In a separate terminal, start the frontend development server:

```bash
# From the frontend directory
npm start
```

3. Open your browser and navigate to `http://localhost:3000`

### Creating a Learning Path

1. Navigate to the Generator page
2. Enter your desired learning topic
3. Configure your API keys (required on first use)
4. Adjust advanced settings if needed (optional)
5. Select your preferred language
6. Click "Generate Learning Path"
7. Wait while the system researches and creates your personalized path
8. Review your comprehensive learning path with modules and submodules

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
python run_server.py
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
   - Push your code to GitHub
   - Create a new project in Vercel linking to your repository
   - Set the root directory to "frontend"
   - Deploy the application

For a complete step-by-step guide, please refer to the [Deployment Guide](DEPLOYMENT.md).

## 📡 API Documentation

The backend exposes a RESTful API with the following main endpoints:

### API Key Management

- `POST /api/auth/api-keys`: Validate and store API keys securely
- `POST /api/validate-api-keys`: Validate API keys without storing them

### Learning Path Generation

- `POST /api/generate-learning-path`: Start generating a new learning path
- `GET /api/learning-path/{task_id}`: Get generation status and results
- `GET /api/progress/{task_id}`: Stream progress updates (SSE)
- `DELETE /api/learning-path/{task_id}`: Clean up completed tasks

### Health Monitoring

- `GET /api/health`: Health check endpoint

## 💻 Development

### Project Structure

```
learny/
├── backend/             # Backend application package
│   ├── api.py           # FastAPI endpoints
│   ├── core/            # Core logic and graph workflow
│   ├── models/          # Data models
│   ├── prompts/         # LLM prompt templates
│   ├── services/        # External services (LLM, search)
│   └── utils/           # Utility functions
├── frontend/            # React application
│   ├── public/          # Static assets
│   └── src/             # React source code
│       ├── components/  # UI components
│       ├── pages/       # Page components
│       └── services/    # API services
├── tests/               # Test suite
└── requirements.txt     # Python dependencies
```

### Key Components

- **Graph Builder**: The system uses a directed graph workflow for generating learning paths (`backend/core/graph_builder.py`)
- **Prompt Templates**: Carefully crafted prompts for the LLM are stored in `backend/prompts/learning_path_prompts.py`
- **API Key Management**: Secure handling of API keys with token-based encryption (`backend/services/key_management.py`)
- **State Management**: The application state flows through the graph nodes (`backend/models/models.py`)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain) for the LLM framework
- [FastAPI](https://fastapi.tiangolo.com/) for the backend API
- [React](https://reactjs.org/) and [Material UI](https://mui.com/) for the frontend
- [Google AI (Gemini)](https://ai.google/discover/generativeai/) and [Perplexity](https://www.perplexity.ai/) for AI services

---

Created by [pma1999](https://github.com/pma1999) | [View Demo](https://learny-peach.vercel.app) | [Report an Issue](https://github.com/pma1999/learny/issues)
