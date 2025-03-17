# Learny - AI-Powered Learning Path Generator

Learny is an intelligent application that generates personalized learning paths for any topic using AI and web research.

## Project Structure

- `api.py` - FastAPI backend for handling learning path generation
- `main.py` - Core learning path generation functionality
- `frontend/` - React frontend application

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 14+ and npm
- API keys:
  - OpenAI API key
  - Tavily API key

### Setup

1. Clone the repository
2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your OpenAI and Tavily API keys to the `.env` file

```
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

4. Install frontend dependencies:

```bash
cd frontend
npm install
```

### Running the Application

1. Start the FastAPI backend:

```bash
uvicorn api:app --reload
```

2. Start the React frontend:

```bash
cd frontend
npm start
```

3. Open your browser and navigate to [http://localhost:3000](http://localhost:3000)

## Features

- **Generate Learning Paths**: Create a comprehensive learning path for any topic
- **Real-time Progress**: See updates as your learning path is generated
- **Customizable Settings**: Configure the generation process with advanced settings
- **View and Export**: View your generated learning path and export it as JSON
- **Responsive Design**: Works on desktop and mobile devices

## How It Works

1. The frontend allows users to input a topic and configure settings
2. The backend uses Langchain and LangGraph to:
   - Generate search queries based on the topic
   - Conduct web research using the Tavily API
   - Create a structured learning path with modules and submodules
   - Develop detailed content for each submodule
3. Results are streamed back to the frontend in real-time

## Technology Stack

- **Frontend**: React, Material UI, React Router, Axios
- **Backend**: FastAPI, Langchain, LangGraph, Pydantic
- **External Services**: OpenAI API, Tavily API

## Acknowledgments

- This project uses the Langchain framework for LLM integration
- The search functionality is powered by Tavily
- LLM capabilities are provided by OpenAI's GPT models 