# Learning Path Generator

A powerful application that generates personalized learning paths for any topic using LangGraph and LangChain.

## Overview

The Learning Path Generator creates comprehensive, structured learning paths for any topic of interest. It leverages:

- **LangGraph** for orchestrating the workflow
- **LangChain** for LLM interactions and tools
- **Streamlit** for a user-friendly web interface

## Features

- **Topic-based Learning Path Generation**: Input any topic and get a customized learning path
- **Web Research**: Performs targeted web searches to gather up-to-date information
- **Structured Modules**: Creates logical learning modules that build upon each other
- **Downloadable Results**: Export your learning path as JSON for later use

## Architecture

The system follows a three-step process:

1. **Search Query Generation**: Determines the 5 most effective search queries for gathering information on the topic
2. **Web Search Execution**: Performs web searches to gather relevant content
3. **Learning Path Creation**: Structures the information into logical learning modules

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
   pip install langchain langchain-core langchain-openai langgraph pydantic streamlit langchain-community
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

2. Open your browser and go to the URL displayed in the terminal (usually http://localhost:8501)

3. Enter a topic in the text field and click "Generate Learning Path"

4. Review your personalized learning path modules

5. Optionally download the learning path as a JSON file

## File Structure

- `learning_path_generator.py`: Core implementation of the LangGraph workflow
- `app.py`: Streamlit web interface
- `requirements.txt`: Project dependencies

## How It Works

1. **User Input**: The user enters a topic they want to learn about
2. **Query Generation**: The system uses LLMs to generate 5 optimal search queries related to the topic
3. **Web Search**: It performs web searches using these queries to gather information
4. **Learning Path Creation**: The gathered information is structured into a logical sequence of learning modules
5. **Result Presentation**: The user is presented with the complete learning path

## Example

For a topic like "Machine Learning for Beginners," the system might generate these modules:

1. **Introduction to Machine Learning**: Core concepts and terminology
2. **Mathematical Foundations**: Essential statistics and linear algebra
3. **Supervised Learning Algorithms**: Classification and regression techniques
4. **Python for Machine Learning**: Libraries and implementation
5. **Building Your First ML Model**: Step-by-step project

## License

[MIT License](LICENSE) 