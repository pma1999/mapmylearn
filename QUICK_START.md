# Learning Path Generator - Quick Start Guide

This guide will help you get started with the Learning Path Generator in just a few minutes.

## What's New in Version 2.0

The Learning Path Generator now features **comprehensive module development**:

- Each module in your learning path is fully researched and developed with in-depth content
- The system performs targeted research for each specific module
- Content is structured with sections, examples, and references
- Complete markdown export of the entire learning path

## Prerequisites

Before you begin, make sure you have:

1. **Python 3.7 or higher** installed on your system
2. **API Keys** from:
   - [OpenAI](https://platform.openai.com/api-keys) (for the LLM)
   - [Tavily](https://tavily.com/) (for web searches)

## Setup

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd learning-path-generator
```

Or download and extract the ZIP file from the repository.

### 2. Install Dependencies

Run this command to install all required packages:

```bash
pip install -r requirements.txt
```

### 3. Set Up Your API Keys (Optional)

You can enter your API keys directly in the web interface, but for convenience, you can create a `.env` file:

1. Copy the `.env.example` file to `.env`
2. Edit the `.env` file with your API keys:

```
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here
```

## Running the Application

### Option 1: Using the Run Script (Recommended)

Simply run:

```bash
python run.py
```

This will:
- Check for dependencies
- Verify API keys
- Start the application
- Open it in your web browser

### Option 2: Using Streamlit Directly

```bash
streamlit run app.py
```

The application will open in your default web browser.

## Using the Application

1. **Enter Your Topic**: Type any topic you want to learn about
2. **Generate Learning Path**: Click the "Generate Learning Path" button
3. **Track Progress**: Monitor the progress as the system:
   - Researches your topic
   - Creates a learning path outline
   - Develops each module with comprehensive content
   - Finalizes the complete learning path
4. **Explore Content**: Browse through the modules using either:
   - Module View: Displays each module in expandable sections
   - Print View: Shows all content in a single scrollable view
5. **Download**: Save your learning path as JSON or Markdown

## Important Notes

- **Generation Time**: Creating a comprehensive learning path with fully developed modules takes longer than just generating an outline. Expect processing to take several minutes.
- **API Usage**: This version uses more API calls due to the in-depth research and content generation for each module.

## Example Topics

Try these topics to see how the application works:

- Machine Learning for Beginners
- History of Ancient Egypt
- Introduction to Guitar Playing
- Spanish for Travelers
- Quantum Computing Fundamentals

## Troubleshooting

- **API Key Issues**: Make sure your API keys are valid and correctly entered
- **Dependency Problems**: Run `pip install -r requirements.txt` to ensure all packages are installed
- **Connection Issues**: Check your internet connection for web search functionality
- **Log Files**: If you encounter errors, check the `learning_path_generator.log` file for details

## Next Steps

After generating your learning path, consider:

1. Following the modules in sequence
2. Searching for additional resources mentioned in the modules
3. Creating a study schedule based on the learning path
4. Sharing your learning path with others

Enjoy your learning journey! 