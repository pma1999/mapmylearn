import streamlit as st
import asyncio
import os
import json
from io import StringIO
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import after environment variables are loaded
from learning_path_generator import generate_learning_path

st.set_page_config(
    page_title="Learning Path Generator",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Learning Path Generator")
st.subheader("Generate a personalized learning path for any topic")

# Check if API keys are already set in environment
openai_key_set = "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"]
tavily_key_set = "TAVILY_API_KEY" in os.environ and os.environ["TAVILY_API_KEY"]

# Add API key input fields
with st.sidebar:
    st.header("API Settings")
    
    # Show status of API keys
    if openai_key_set:
        st.success("OpenAI API Key is set ✅")
        openai_api_key = st.text_input("Change OpenAI API Key?", type="password", 
                                      help="Leave blank to use the existing key", value="")
    else:
        st.warning("OpenAI API Key is required ⚠️")
        openai_api_key = st.text_input("OpenAI API Key", type="password", 
                                      help="Required for LLM functionality")
    
    if tavily_key_set:
        st.success("Tavily API Key is set ✅")
        tavily_api_key = st.text_input("Change Tavily API Key?", type="password", 
                                      help="Leave blank to use the existing key", value="")
    else:
        st.warning("Tavily API Key is required ⚠️")
        tavily_api_key = st.text_input("Tavily API Key", type="password", 
                                      help="Required for web search functionality")
    
    # Update environment variables if new keys are provided
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
        openai_key_set = True
    
    if tavily_api_key:
        os.environ["TAVILY_API_KEY"] = tavily_api_key
        tavily_key_set = True
    
    st.info("API keys are securely stored only for the current session and are not saved.", icon="ℹ️")
    
    # Add a link to get API keys
    st.markdown("""
    **Need API keys?**
    - [Get OpenAI API Key](https://platform.openai.com/api-keys)
    - [Get Tavily API Key](https://tavily.com/)
    """)

# Main input form
st.write("### Enter a Topic to Learn")
user_topic = st.text_input("What do you want to learn about?", 
                         placeholder="e.g., Machine Learning, Guitar, Spanish, Quantum Computing...")

# Advanced options in an expander
with st.expander("Advanced Options"):
    st.write("These options will be available in future versions.")
    st.slider("Number of modules", min_value=3, max_value=10, value=5, disabled=True)
    st.selectbox("Difficulty level", ["Beginner", "Intermediate", "Advanced"], disabled=True)
    st.checkbox("Include resources (links, books, videos)", value=True, disabled=True)

# Generate button with API key validation
generate_button = st.button("Generate Learning Path", type="primary", 
                          disabled=not (openai_key_set and tavily_key_set))

if not openai_key_set or not tavily_key_set:
    missing_keys = []
    if not openai_key_set:
        missing_keys.append("OpenAI API Key")
    if not tavily_key_set:
        missing_keys.append("Tavily API Key")
    
    st.warning(f"Please provide the missing API keys: {', '.join(missing_keys)}")

# Process the generation request
if generate_button:
    if not user_topic:
        st.error("Please enter a topic first!")
    else:
        with st.spinner(f"Generating your personalized learning path for '{user_topic}'..."):
            try:
                # Display a progress indicator while the graph runs
                progress_placeholder = st.empty()
                progress_bar = progress_placeholder.progress(0)
                
                # Create a new event loop for the async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Run the learning path generator
                result = loop.run_until_complete(generate_learning_path(user_topic))
                loop.close()
                
                progress_bar.progress(100)
                progress_placeholder.empty()
                
                # Handle potential errors in result
                if not result.get("modules"):
                    st.error("Failed to generate learning path. Please check the logs for details.")
                    st.write("Error details:")
                    for step in result.get("execution_steps", []):
                        if "Error" in step:
                            st.code(step)
                else:
                    # Display execution steps in the sidebar
                    with st.sidebar:
                        st.header("Execution Steps")
                        for i, step in enumerate(result["execution_steps"], 1):
                            st.write(f"{i}. {step}")
                    
                    # Display the learning path modules
                    st.success(f"Learning path for **{result['topic']}** created successfully! 🎉")
                    
                    # Summary section
                    st.write(f"### Learning Path Summary")
                    st.write(f"Created {len(result['modules'])} modules to help you learn about {result['topic']}.")
                    
                    # Display modules in cards
                    for i, module in enumerate(result["modules"], 1):
                        with st.expander(f"Module {i}: {module.title}", expanded=i==1):
                            st.markdown(f"**Description:**")
                            st.markdown(module.description)
                    
                    # Download options
                    st.write("### Download Options")
                    col1, col2 = st.columns(2)
                    
                    # Convert modules to dictionary for JSON serialization
                    modules_dict = [{"title": m.title, "description": m.description} for m in result["modules"]]
                    
                    download_data = {
                        "topic": result["topic"],
                        "modules": modules_dict
                    }
                    
                    # JSON download
                    json_str = json.dumps(download_data, indent=2)
                    with col1:
                        st.download_button(
                            label="Download as JSON",
                            data=json_str,
                            file_name=f"{user_topic.replace(' ', '_')}_learning_path.json",
                            mime="application/json"
                        )
                    
                    # Markdown download
                    markdown_content = f"# Learning Path: {result['topic']}\n\n"
                    for i, module in enumerate(result["modules"], 1):
                        markdown_content += f"## Module {i}: {module.title}\n\n"
                        markdown_content += f"{module.description}\n\n"
                    
                    with col2:
                        st.download_button(
                            label="Download as Markdown",
                            data=markdown_content,
                            file_name=f"{user_topic.replace(' ', '_')}_learning_path.md",
                            mime="text/markdown"
                        )
                
            except Exception as e:
                logger.error(f"Error generating learning path: {str(e)}")
                st.error(f"An error occurred: {str(e)}")
                st.info("Please check your API keys and try again.")

# Information about the app
with st.expander("About this app"):
    st.markdown("""
    # About Learning Path Generator
    
    The **Learning Path Generator** is powered by LangGraph and LangChain to create personalized learning paths for any topic.
    
    ## How it works
    
    1. **Topic Analysis**: The system analyzes your topic to understand what information is needed
    2. **Smart Web Search**: It generates optimal search queries and performs targeted web searches
    3. **Learning Path Creation**: The information is structured into logical modules that build upon each other
    4. **Module Generation**: Each module is crafted with a clear title and detailed description
    
    ## Technologies
    
    - **LangGraph**: For orchestrating the complex workflow
    - **LangChain**: For LLM interactions and tools
    - **OpenAI's GPT**: For natural language understanding and generation
    - **Tavily**: For intelligent web search
    
    ## Privacy & Data
    
    - Your API keys are stored only for the current session
    - No user data is saved or shared
    
    Created with ❤️ using Python, Streamlit, LangGraph, and LangChain
    """) 