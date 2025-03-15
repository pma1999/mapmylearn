# Learning Path Generator

A powerful application that generates personalized learning paths for any topic using LangGraph and LangChain.

## What's New in Version 2.0

**Comprehensive Module Development**: The Learning Path Generator now fully develops each module with in-depth educational content:

- Each module is individually researched with targeted web searches
- Detailed content is generated for each module with proper structure and formatting
- The application shows real-time progress of the development process
- Enhanced UI with module view and print view options
- Complete markdown export with all module content

## Overview

The Learning Path Generator creates comprehensive, structured learning paths for any topic of interest. It leverages:

- **LangGraph** for orchestrating the workflow
- **LangChain** for LLM interactions and tools
- **Streamlit** for a user-friendly web interface

## Features

- **Topic-based Learning Path Generation**: Input any topic and get a customized learning path
- **Web Research**: Performs targeted web searches to gather up-to-date information
- **Structured Modules**: Creates logical learning modules that build upon each other
- **Comprehensive Content**: Develops detailed educational content for each module
- **Real-time Progress Tracking**: Shows the progress of each phase of development
- **Multiple View Options**: Module view for exploration and print view for reading
- **Downloadable Results**: Export your learning path as JSON or Markdown

## Architecture

The system follows a multi-phase process:

1. **Initial Research Phase**:
   - Generates optimal search queries for the topic
   - Performs web searches to gather relevant information
   - Creates an initial learning path outline with modules

2. **Module Development Phase**:
   - For each module in the learning path:
     - Generates targeted search queries specific to the module
     - Executes web searches to gather module-specific information
     - Develops comprehensive content for the module
   - Assembles the complete learning path with all developed modules

## Requirements

- Python 3.7+
- OpenAI API Key
- Tavily API Key (for web searches)

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd learning-path-generator
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   
   Or install individually:
   ```
   pip install langchain langchain-core langchain-openai langgraph pydantic streamlit langchain-community python-dotenv
   ```

3. Set up your API keys:
   - Create a `.env` file in the root directory
   - Add your API keys:
     ```
     OPENAI_API_KEY=your_openai_api_key
     TAVILY_API_KEY=your_tavily_api_key
     ```
   - Or enter them in the web interface

## Usage

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

   Or use the provided launcher script:
   ```
   python run.py
   ```

2. Open your browser and go to the URL displayed in the terminal (usually http://localhost:8501)

3. Set up your API keys (OpenAI and Tavily) in the Settings page

4. Enter a topic in the text field and click "Generate Learning Path"

5. Track the progress as the system develops your learning path

6. Explore the fully developed modules and submodules, and download the complete learning path in JSON or Markdown format

## Streamlit App Features

The Streamlit app provides a user-friendly interface for generating and exploring learning paths:

- **Home Page**: Input your topic and generation settings
- **Settings Page**: Configure API keys and generation parameters
- **Learning Path View**: Navigate through modules and submodules
- **Real-time Progress Tracking**: Monitor the generation process
- **Download Options**: Export your learning path as JSON or Markdown

## Advanced Settings

The app allows you to configure parallel processing settings:

- **Module Parallelism**: Number of modules to process in parallel (1-4)
- **Search Parallelism**: Number of searches to execute in parallel (1-5)
- **Submodule Parallelism**: Number of submodules to process in parallel (1-5)

Adjusting these settings can significantly impact generation speed and API costs.

## File Structure

- `learning_path_generator.py`: Core implementation of the LangGraph workflow
- `app.py`: Streamlit web interface
- `run.py`: Launcher script
- `requirements.txt`: Project dependencies
- `test_app.py`: Test script to verify functionality

## How It Works

1. **User Input**: The user enters a topic they want to learn about
2. **Initial Research**: The system analyzes the topic and performs web searches
3. **Learning Path Outline**: An initial learning path with logical modules is created
4. **Module Development**: Each module is individually researched and developed
   - Module-specific search queries are generated
   - Targeted web searches are performed for each module
   - Comprehensive content is created for each module
5. **Final Assembly**: All developed modules are assembled into a complete learning path
6. **Result Presentation**: The user can explore the fully developed learning path

## Example

For a topic like "Machine Learning for Beginners," the system will:

1. Generate an initial learning path outline with modules
2. Develop each module in depth with comprehensive content
3. Present the complete learning path with all modules

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE) 