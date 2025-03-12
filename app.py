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
                # Create placeholder containers for progress tracking
                progress_container = st.container()
                
                with progress_container:
                    st.write("### 🔄 Generation Progress")
                    overall_progress = st.progress(0)
                    status_text = st.empty()
                    status_text.write("Phase 1/3: Researching your topic...")
                    
                    # Display a detailed progress area
                    detail_container = st.expander("View detailed progress", expanded=True)
                    detail_text = detail_container.empty()
                    
                    # Create a new event loop for the async function
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Define a wrapper function to update progress during execution
                    async def generate_with_progress(topic):
                        # Track phases and update progress bar
                        phase = 1
                        
                        # Initialize progress logs
                        progress_logs = []
                        
                        # Helper function to update progress
                        def update_progress(step_info):
                            progress_logs.append(f"✓ {step_info}")
                            detail_text.write("\n".join(progress_logs))
                        
                        # Set up storage for tracking steps
                        steps_seen = set()
                        module_count = 0
                        current_module = 0
                        
                        # Create a task to generate the learning path
                        generate_task = asyncio.create_task(generate_learning_path(topic))
                        
                        # Poll for progress updates while the task is running
                        while not generate_task.done():
                            await asyncio.sleep(1)  # Check every second
                            
                            # Use a try/except block to safely check the running task's state
                            try:
                                # This would be better with proper progress reporting from the LangGraph,
                                # but we'll use logs as a fallback
                                log_entries = []
                                with open("learning_path_generator.log", "r", encoding="utf-8") as f:
                                    log_entries = f.readlines()
                                
                                # Process log entries to extract progress information
                                for entry in log_entries:
                                    # Look for key progress indicators
                                    if "Generated search queries for topic" in entry and "Generated search queries for topic" not in steps_seen:
                                        steps_seen.add("Generated search queries for topic")
                                        update_progress("Generated initial search queries")
                                        overall_progress.progress(0.1)
                                    
                                    elif "Executed web searches for all queries" in entry and "Executed web searches for all queries" not in steps_seen:
                                        steps_seen.add("Executed web searches for all queries")
                                        update_progress("Completed web searches for topic")
                                        overall_progress.progress(0.2)
                                    
                                    elif "Created learning path with" in entry and "Created learning path with" not in steps_seen:
                                        steps_seen.add("Created learning path with")
                                        # Extract the module count if possible
                                        try:
                                            import re
                                            match = re.search(r"Created learning path with (\d+) modules", entry)
                                            if match:
                                                module_count = int(match.group(1))
                                                update_progress(f"Created initial learning path outline with {module_count} modules")
                                        except:
                                            update_progress("Created initial learning path outline")
                                        
                                        # Update phase
                                        phase = 2
                                        status_text.write("Phase 2/3: Designing learning modules...")
                                        overall_progress.progress(0.3)
                                    
                                    # Track module development
                                    elif "Generated search queries for module" in entry:
                                        module_indicator = f"Generated search queries for module {current_module+1}"
                                        if module_indicator not in steps_seen:
                                            steps_seen.add(module_indicator)
                                            update_progress(f"Researching for module {current_module+1}")
                                    
                                    elif "Executed web searches for module" in entry:
                                        module_indicator = f"Executed web searches for module {current_module+1}"
                                        if module_indicator not in steps_seen:
                                            steps_seen.add(module_indicator)
                                            update_progress(f"Completed research for module {current_module+1}")
                                    
                                    elif "Developed content for module" in entry:
                                        module_indicator = f"Developed content for module {current_module+1}"
                                        if module_indicator not in steps_seen:
                                            steps_seen.add(module_indicator)
                                            update_progress(f"Completed development of module {current_module+1}")
                                            current_module += 1
                                            
                                            # Update progress based on modules completed
                                            if module_count > 0:
                                                progress_value = 0.3 + (0.6 * (current_module / module_count))
                                                overall_progress.progress(min(progress_value, 0.9))
                                            
                                    elif "Finalized comprehensive learning path" in entry and "Finalized comprehensive learning path" not in steps_seen:
                                        steps_seen.add("Finalized comprehensive learning path")
                                        phase = 3
                                        status_text.write("Phase 3/3: Finalizing your learning path...")
                                        update_progress("Assembling final learning path")
                                        overall_progress.progress(0.95)
                            except Exception as e:
                                # Ignore errors in progress tracking
                                pass
                        
                        # Get the result from the completed task
                        result = await generate_task
                        
                        # Mark as complete
                        overall_progress.progress(1.0)
                        status_text.write("✅ Learning path generation complete!")
                        update_progress("Learning path generation completed successfully")
                        
                        return result
                    
                    # Run the learning path generator with progress tracking
                    result = loop.run_until_complete(generate_with_progress(user_topic))
                    loop.close()
                
                # Handle potential errors in result
                if not result.get("modules"):
                    st.error("Failed to generate learning path. Please check the logs for details.")
                    st.write("Error details:")
                    for step in result.get("execution_steps", []):
                        if "Error" in step:
                            st.code(step)
                else:
                    # Remove the progress display
                    progress_container.empty()
                    
                    # Display execution steps in the sidebar if needed
                    with st.sidebar:
                        st.header("Generation Process")
                        steps_expander = st.expander("View execution steps", expanded=False)
                        with steps_expander:
                            for i, step in enumerate(result.get("execution_steps", []), 1):
                                st.write(f"{i}. {step}")
                    
                    # Display the learning path modules
                    st.success(f"Learning path for **{result['topic']}** created successfully! 🎉")
                    
                    # Summary section
                    st.write(f"### Learning Path Summary")
                    st.write(f"Created {len(result['modules'])} modules to help you learn about {result['topic']}.")
                    
                    # Check if we have full module content
                    has_content = any("content" in module for module in result["modules"])
                    
                    if has_content:
                        # Display tabs for different views
                        tab1, tab2 = st.tabs(["Module View", "Print View"])
                        
                        with tab1:
                            # Display modules in expanded cards with full content
                            for i, module in enumerate(result["modules"], 1):
                                with st.expander(f"Module {i}: {module['title']}", expanded=i==1):
                                    st.markdown(f"**Description:**")
                                    st.markdown(module["description"])
                                    
                                    if "content" in module:
                                        st.markdown("---")
                                        st.markdown(module["content"])
                        
                        with tab2:
                            # Print view shows all content in a single scrollable view
                            st.markdown(f"# Complete Learning Path: {result['topic']}")
                            
                            for i, module in enumerate(result["modules"], 1):
                                st.markdown(f"## Module {i}: {module['title']}")
                                st.markdown(f"*{module['description']}*")
                                
                                if "content" in module:
                                    st.markdown(module["content"])
                                
                                # Add a separator between modules
                                if i < len(result["modules"]):
                                    st.markdown("---")
                    else:
                        # Fallback for basic module view (no detailed content)
                        for i, module in enumerate(result["modules"], 1):
                            with st.expander(f"Module {i}: {module['title']}", expanded=i==1):
                                st.markdown(f"**Description:**")
                                st.markdown(module["description"])
                    
                    # Download options
                    st.write("### Download Options")
                    col1, col2 = st.columns(2)
                    
                    # Convert modules to dictionary format if needed
                    if isinstance(result["modules"], list) and not isinstance(result["modules"][0], dict):
                        modules_dict = [module.dict() for module in result["modules"]]
                    else:
                        modules_dict = result["modules"]
                    
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
                        markdown_content += f"## Module {i}: {module['title']}\n\n"
                        markdown_content += f"{module['description']}\n\n"
                        
                        if "content" in module:
                            markdown_content += f"### Content\n\n"
                            markdown_content += f"{module['content']}\n\n"
                    
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
    4. **Module Development**: Each module is researched and developed with comprehensive content
    5. **Final Assembly**: The complete learning path is assembled with all module content
    
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