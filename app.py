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
with st.expander("Advanced Options", expanded=True):
    # Enable parallel processing options
    st.subheader("Parallel Processing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        parallel_count = st.slider(
            "Modules to process in parallel", 
            min_value=1, 
            max_value=5, 
            value=2,
            help="Process multiple modules simultaneously to reduce generation time"
        )
    
    with col2:
        search_parallel_count = st.slider(
            "Searches to execute in parallel", 
            min_value=1, 
            max_value=5, 
            value=3,
            help="Execute multiple search queries simultaneously to speed up research"
        )
    
    st.markdown("""
    **Note about parallel processing:**
    - Processing in parallel significantly reduces total generation time
    - Higher values use more API tokens simultaneously (may affect costs)
    - Recommended values:
      - Module parallelism: 2-3 for most topics
      - Search parallelism: 3-5 for faster research
    """)
    
    # Other advanced options
    st.subheader("Other Options")
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
                        async def update_progress(step_info):
                            progress_logs.append(f"✓ {step_info}")
                            detail_text.write("\n".join(progress_logs))
                        
                        # Set up storage for tracking steps
                        steps_seen = set()
                        module_count = 0
                        current_module = 0
                        processed_modules = 0
                        batch_count = 0
                        
                        # Create a task to generate the learning path
                        generate_task = asyncio.create_task(
                            generate_learning_path(
                                topic, 
                                parallel_count=parallel_count,
                                search_parallel_count=search_parallel_count,
                                progress_callback=update_progress
                            )
                        )
                        
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
                                        await update_progress("Generated initial search queries")
                                        overall_progress.progress(0.1)
                                    
                                    # Track parallel search execution
                                    elif "Executing" in entry and "searches in" in entry and "batches with parallelism" in entry and "Executing searches" not in steps_seen:
                                        steps_seen.add("Executing searches")
                                        # Extract search info if possible
                                        try:
                                            import re
                                            match = re.search(r"Executing (\d+) searches in (\d+) batches with parallelism of (\d+)", entry)
                                            if match:
                                                search_count = int(match.group(1))
                                                batch_count = int(match.group(2))
                                                parallel_value = int(match.group(3))
                                                await update_progress(f"Executing {search_count} searches in {batch_count} batches (parallelism: {parallel_value})")
                                        except:
                                            await update_progress("Executing searches in parallel batches")
                                    
                                    elif "Executed" in entry and "web searches in parallel batch" in entry and "Web searches completed" not in steps_seen:
                                        steps_seen.add("Web searches completed")
                                        # Extract search info if possible
                                        try:
                                            import re
                                            match = re.search(r"Executed (\d+) web searches in (\d+) parallel batches", entry)
                                            if match:
                                                search_count = int(match.group(1))
                                                batch_count = int(match.group(2))
                                                await update_progress(f"Completed {search_count} web searches in {batch_count} parallel batches")
                                        except:
                                            await update_progress("Completed web searches in parallel")
                                        overall_progress.progress(0.2)
                                    
                                    elif "Created learning path with" in entry and "Created learning path with" not in steps_seen:
                                        steps_seen.add("Created learning path with")
                                        # Extract the module count if possible
                                        try:
                                            import re
                                            match = re.search(r"Created learning path with (\d+) modules", entry)
                                            if match:
                                                module_count = int(match.group(1))
                                                await update_progress(f"Created initial learning path outline with {module_count} modules")
                                        except:
                                            await update_progress("Created initial learning path outline")
                                        
                                        # Update phase
                                        phase = 2
                                        status_text.write("Phase 2/3: Designing learning modules...")
                                        overall_progress.progress(0.3)
                                    
                                    # Track parallel processing
                                    elif "Initialized parallel processing with" in entry and "Initialized parallel processing" not in steps_seen:
                                        steps_seen.add("Initialized parallel processing")
                                        # Extract the parallel count if possible
                                        try:
                                            import re
                                            match = re.search(r"Initialized parallel processing with (\d+) modules at once", entry)
                                            if match:
                                                parallel_value = int(match.group(1))
                                                await update_progress(f"Set up parallel processing with {parallel_value} modules at once")
                                        except:
                                            await update_progress("Set up parallel processing")
                                    
                                    elif "Created" in entry and "batches of modules" in entry:
                                        try:
                                            import re
                                            match = re.search(r"Created (\d+) batches of modules", entry)
                                            if match:
                                                batch_count = int(match.group(1))
                                                await update_progress(f"Organized modules into {batch_count} processing batches")
                                        except:
                                            pass
                                    
                                    # Track batch processing
                                    elif "Started processing batch" in entry:
                                        batch_indicator = f"Started processing batch"
                                        if batch_indicator not in steps_seen:
                                            steps_seen.add(batch_indicator)
                                            await update_progress(f"Started parallel module processing")
                                    
                                    # Track module search parallelism
                                    elif "Executing" in entry and "module searches in" in entry and "parallelism of" in entry:
                                        # This is tracked via the progress callback
                                        pass
                                    
                                    elif "Processed batch" in entry:
                                        try:
                                            import re
                                            match = re.search(r"Processed batch (\d+)", entry)
                                            if match:
                                                batch_num = int(match.group(1))
                                                batch_indicator = f"Processed batch {batch_num}"
                                                if batch_indicator not in steps_seen:
                                                    steps_seen.add(batch_indicator)
                                                    await update_progress(f"Completed batch {batch_num} of {batch_count}")
                                                    
                                                    # Update progress based on batches completed
                                                    if batch_count > 0:
                                                        progress_value = 0.3 + (0.6 * (batch_num / batch_count))
                                                        overall_progress.progress(min(progress_value, 0.9))
                                        except:
                                            pass
                                            
                                    # Track module development via progress callback
                                    # The callback function will handle these directly
                                    
                                    elif "Finalized comprehensive learning path" in entry and "Finalized comprehensive learning path" not in steps_seen:
                                        steps_seen.add("Finalized comprehensive learning path")
                                        phase = 3
                                        status_text.write("Phase 3/3: Finalizing your learning path...")
                                        await update_progress("Assembling final learning path")
                                        overall_progress.progress(0.95)
                            except Exception as e:
                                # Ignore errors in progress tracking
                                pass
                        
                        # Get the result from the completed task
                        result = await generate_task
                        
                        # Mark as complete
                        overall_progress.progress(1.0)
                        status_text.write("✅ Learning path generation complete!")
                        await update_progress("Learning path generation completed successfully")
                        
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
                        
                        # Add info about parallel processing
                        st.info(f"Generated using {parallel_count} parallel module(s) and {search_parallel_count} parallel search(es)")
                    
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
    2. **Smart Web Search**: It generates optimal search queries and performs targeted web searches in parallel
    3. **Learning Path Creation**: The information is structured into logical modules that build upon each other
    4. **Parallel Module Development**: Each module is researched and developed with comprehensive content in parallel
    5. **Final Assembly**: The complete learning path is assembled with all module content
    
    ## Technologies
    
    - **LangGraph**: For orchestrating the complex workflow with parallel execution
    - **LangChain**: For LLM interactions and tools
    - **OpenAI's GPT**: For natural language understanding and generation
    - **Tavily**: For intelligent web search
    
    ## Privacy & Data
    
    - Your API keys are stored only for the current session
    - No user data is saved or shared
    
    Created with ❤️ using Python, Streamlit, LangGraph, and LangChain
    """) 