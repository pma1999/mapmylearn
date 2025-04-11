# MapMyLearn - Personalized Learning Path Generator

## Description

MapMyLearn is an AI-powered application designed to create personalized learning paths based on your interests and goals. The platform leverages advanced language models and web search capabilities to generate comprehensive, structured learning content tailored to any topic you wish to explore.

## Features

- **AI-Generated Learning Paths**: Create complete, structured learning paths for any topic using AI
- **Personalized Content**: Tailored modules and submodules specific to your learning objectives
- **Interactive UI**: Modern, responsive interface with real-time progress updates
- **Multi-language Support**: Generate content in different languages (English, Spanish, and more)
- **User Authentication**: Secure login system to save and manage your learning paths
- **Learning Path History**: Access and review your previously generated paths
- **API Key Management**: Bring your own Google and Perplexity API keys for enhanced functionality
- **Customizable Generation**: Control module count, submodule details, and other generation parameters
- **PDF Export**: Generate and download learning paths as PDF documents for offline use

## Installation

### Prerequisites

- Python 3.8+
- Node.js 14+ and npm
- PostgreSQL (optional, for production)

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/pma1999/mapmylearn.git
cd mapmylearn
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# For Windows
venv\Scripts\activate
# For macOS/Linux
source venv/bin/activate
```

3. Install backend dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
# Copy example env file and edit as needed
cp .env.example .env
```

5. Key environment variables to configure:
- `GOOGLE_API_KEY` - Your Google API key for LLM operations
- `PERPLEXITY_API_KEY` - Your Perplexity API key for search operations
- `SECRET_KEY` - Secret key for authentication
- `DATABASE_URL` - Database connection string (for PostgreSQL in production)

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install frontend dependencies:
```bash
npm install
```

3. Configure environment variables (optional):
```bash
# Copy example env file
cp .env.example .env
```

## Running the Application

### Development Mode

1. Start the backend server:
```bash
# From the main directory
python run_server.py
```

2. In a separate terminal, start the frontend server:
```bash
cd frontend
npm start
```

3. Access the application at http://localhost:3000

### Using the Development Script

For convenience, you can use the provided development script:

```bash
# On Windows
python bootstrap.py
# OR use the shell script on macOS/Linux
./run_dev.sh
```

## Usage

1. **Create an Account**: Register a new account or log in if you already have one

2. **Generate a Learning Path**:
   - Navigate to the Generator page
   - Enter your desired learning topic
   - Configure optional settings (module count, language, etc.)
   - Click "Generate Learning Path"
   - Watch real-time updates as your path is created

3. **View and Export Your Path**:
   - Review the generated learning path with its modules and submodules
   - Navigate through different sections and content
   - Export to PDF for offline reference

4. **Access Your History**:
   - Visit the History page to see previous learning paths
   - Reload past paths and continue your learning journey

## Architecture

MapMyLearn is built with a modern stack and architecture:

### Backend
- **Framework**: FastAPI for a high-performance API server
- **AI Processing**: LangChain and LangGraph for orchestration of LLM workflows
- **Database**: SQLAlchemy ORM with SQLite (dev) or PostgreSQL (prod)
- **Authentication**: JWT-based authentication system
- **PDF Generation**: WeasyPrint for high-quality PDF exports

### Frontend
- **Framework**: React with React Router for navigation
- **UI Components**: Material-UI (MUI) for design system
- **State Management**: React Context API for global state
- **API Communication**: Axios for HTTP requests
- **Content Rendering**: React Markdown with syntax highlighting

### Workflow
1. User submits a topic through the UI
2. Backend generates search queries for the topic
3. Web searches provide relevant, current information
4. AI models structure content into modules and submodules
5. Generated learning path is returned to the UI
6. User can interact with, save, and export the learning path

## Development

### Project Structure

```
mapmylearn/
├── backend/             # Backend FastAPI application
│   ├── api.py           # Main API endpoints
│   ├── main.py          # Core learning path generation logic
│   ├── core/            # Core functionality modules
│   ├── models/          # Database models
│   ├── routes/          # API route definitions
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic services
│   ├── utils/           # Utility functions
│   └── templates/       # Templates for PDF generation
├── frontend/            # React frontend application
│   ├── public/          # Static assets
│   └── src/             # React source code
│       ├── components/  # Reusable UI components
│       ├── pages/       # Page components
│       ├── services/    # API service connectors
│       └── utils/       # Utility functions
├── .env.example         # Example environment variables
├── requirements.txt     # Python dependencies
├── run_server.py        # Server startup script
└── run_dev.sh           # Development startup script
```

### Running Tests

To run the backend tests:

```bash
python run_tests.py
```

## Deployment

The application is configured for deployment on various platforms:

### Railway

The project includes Railway configuration files for easy deployment:
- `.railway.toml`
- `railway.json`

### Docker

A Dockerfile is provided for containerized deployment:

```bash
# Build the Docker image
docker build -t mapmylearn .

# Run the container
docker run -p 8000:8000 mapmylearn
```

## License

This project is licensed under the ISC License - see the LICENSE file for details.

## Credits

Built with:
- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Graph orchestrator for LLM applications
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [React](https://reactjs.org/) - Frontend library
- [Material-UI](https://mui.com/) - React UI framework
