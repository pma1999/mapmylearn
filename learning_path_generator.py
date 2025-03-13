import os
from typing import List, Dict, TypedDict, Annotated, Optional, Any, Callable, Union
from operator import add
import logging
from dotenv import load_dotenv
import asyncio
from functools import partial

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the state schema
class SearchQuery(BaseModel):
    keywords: str = Field(description="The search query keywords")
    rationale: str = Field(description="Explanation of why this search is important")

class Module(BaseModel):
    title: str = Field(description="Title of the learning module")
    description: str = Field(description="Detailed description of the module content")

# Create container models for lists
class SearchQueryList(BaseModel):
    queries: List[SearchQuery] = Field(description="List of search queries")

class ModuleList(BaseModel):
    modules: List[Module] = Field(description="List of learning modules")

# Define models for module development
class ModuleContent(BaseModel):
    module_id: int = Field(description="Index of the module in the learning path")
    title: str = Field(description="Title of the learning module")
    description: str = Field(description="Description of the module content")
    search_queries: List[SearchQuery] = Field(description="Search queries used for module research")
    search_results: List[Dict[str, Any]] = Field(description="Search results used to develop the module")
    content: str = Field(description="Fully developed module content")

class LearningPathState(TypedDict):
    user_topic: str
    search_queries: Optional[List[SearchQuery]]
    search_results: Optional[List[Dict[str, str]]]
    modules: Optional[List[Module]]
    steps: Annotated[List[str], add]  # For tracking execution steps
    
    # New fields for module development
    current_module_index: Optional[int]
    module_search_queries: Optional[List[SearchQuery]]
    module_search_results: Optional[List[Dict[str, Any]]]
    developed_modules: Optional[List[ModuleContent]]
    final_learning_path: Optional[Dict[str, Any]]
    
    # New fields for parallel processing
    parallel_count: Optional[int]  # Number of modules to process in parallel
    module_batches: Optional[List[List[int]]]  # Batches of module indices
    current_batch_index: Optional[int]  # Current batch being processed
    modules_in_process: Optional[Dict[int, Dict[str, Any]]]  # Status of modules being processed
    progress_callback: Optional[Callable]  # Callback function for progress updates
    
    # New field for parallel search execution
    search_parallel_count: Optional[int]  # Number of search queries to execute in parallel

# Define output parsers using the container models
search_queries_parser = PydanticOutputParser(pydantic_object=SearchQueryList)
modules_parser = PydanticOutputParser(pydantic_object=ModuleList)
module_queries_parser = PydanticOutputParser(pydantic_object=SearchQueryList)

# Initialize the LLM and tools with error handling
def get_llm():
    """Initialize and return the LLM with proper error handling."""
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
    
    try:
        return ChatOpenAI(temperature=0.2, model="gpt-4o-mini", api_key=openai_api_key)
    except Exception as e:
        logger.error(f"Error initializing ChatOpenAI: {str(e)}")
        raise

def get_search_tool():
    """Initialize and return the web search tool with proper error handling."""
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_api_key:
        logger.warning("TAVILY_API_KEY not found in environment variables")
    
    try:
        return TavilySearchResults(max_results=5, api_key=tavily_api_key)
    except Exception as e:
        logger.error(f"Error initializing TavilySearchResults: {str(e)}")
        raise

# Helper function for executing a single search
async def execute_single_search(query: SearchQuery) -> Dict[str, Any]:
    """Execute a single web search for a query."""
    try:
        search_tool = get_search_tool()
        logger.info(f"Searching for: {query.keywords}")
        result = await search_tool.ainvoke({"query": query.keywords})
        return {
            "query": query.keywords,
            "rationale": query.rationale,
            "results": result
        }
    except Exception as e:
        logger.error(f"Error searching for '{query.keywords}': {str(e)}")
        # Return an error result instead of raising to prevent batch failures
        return {
            "query": query.keywords,
            "rationale": query.rationale,
            "results": f"Error performing search: {str(e)}"
        }

# Define node functions
async def generate_search_queries(state: LearningPathState):
    """Generate optimal search queries for the user topic."""
    logger.info(f"Generating search queries for topic: {state['user_topic']}")
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert research assistant. Your task is to generate 5 search queries that 
    will gather comprehensive information for creating a learning path about {user_topic}.

    For each search query:
    1. Make it specific and targeted
    2. Ensure it covers a different aspect of the topic
    3. Design it to return high-quality educational content
    4. Explain why this search is important for understanding the topic

    Your response should be exactly 5 search queries, each with its rationale.
    
    {format_instructions}
    """)
    
    try:
        llm = get_llm()
        chain = prompt | llm | search_queries_parser
        
        search_query_list = await chain.ainvoke({
            "user_topic": state["user_topic"],
            "format_instructions": search_queries_parser.get_format_instructions()
        })
        
        # Extract the queries from the container object
        search_queries = search_query_list.queries
        logger.info(f"Generated {len(search_queries)} search queries")
        
        return {
            "search_queries": search_queries,
            "steps": [f"Generated {len(search_queries)} search queries for topic: {state['user_topic']}"]
        }
    except Exception as e:
        logger.error(f"Error generating search queries: {str(e)}")
        return {
            "search_queries": [],
            "steps": [f"Error generating search queries: {str(e)}"]
        }

async def execute_web_searches(state: LearningPathState):
    """Execute web searches using the generated queries in parallel."""
    logger.info("Executing web searches in parallel")
    
    if not state["search_queries"]:
        logger.warning("No search queries available to execute")
        return {
            "search_results": [],
            "steps": ["No search queries available to execute"]
        }
    
    # Get the search parallel count (default to 3 if not specified)
    search_parallel_count = state.get("search_parallel_count", 3)
    queries = state["search_queries"]
    
    # Create batches of search queries based on the parallel count
    query_batches = []
    for i in range(0, len(queries), search_parallel_count):
        batch = queries[i:min(i + search_parallel_count, len(queries))]
        query_batches.append(batch)
    
    logger.info(f"Executing {len(queries)} searches in {len(query_batches)} batches with parallelism of {search_parallel_count}")
    
    search_results = []
    
    try:
        # Process each batch of queries in parallel
        for batch_index, batch in enumerate(query_batches):
            logger.info(f"Processing search batch {batch_index + 1}/{len(query_batches)} with {len(batch)} queries")
            
            # Create a task for each query in the batch
            tasks = []
            for query in batch:
                tasks.append(execute_single_search(query))
            
            # Execute the batch of searches in parallel
            batch_results = await asyncio.gather(*tasks)
            search_results.extend(batch_results)
            
            # Add a small delay between batches to prevent rate limiting
            if batch_index < len(query_batches) - 1:
                await asyncio.sleep(0.5)
        
        logger.info(f"Completed {len(search_results)} web searches in parallel")
        
        # Update progress callback if available
        if state.get("progress_callback"):
            await state["progress_callback"](f"Executed {len(search_results)} web searches in {len(query_batches)} parallel batches")
        
        return {
            "search_results": search_results,
            "steps": [f"Executed {len(search_results)} web searches in parallel batches"]
        }
    except Exception as e:
        logger.error(f"Error executing web searches: {str(e)}")
        return {
            "search_results": [],
            "steps": [f"Error executing web searches: {str(e)}"]
        }

async def create_learning_path(state: LearningPathState):
    """Create a structured learning path based on search results."""
    logger.info("Creating learning path")
    
    if not state["search_results"]:
        logger.warning("No search results available to create learning path")
        return {
            "modules": [],
            "steps": ["No search results available to create learning path"]
        }
    
    # Format search results for the prompt
    formatted_results = ""
    for result in state["search_results"]:
        formatted_results += f"Search Query: {result['query']}\n"
        formatted_results += f"Rationale: {result['rationale']}\n"
        formatted_results += "Results:\n"
        
        if isinstance(result['results'], str):  # Error case
            formatted_results += f"  {result['results']}\n\n"
        else:
            for item in result['results']:
                formatted_results += f"  - {item.get('title', 'No title')}: {item.get('content', 'No content')}\n"
                formatted_results += f"    URL: {item.get('url', 'No URL')}\n"
            formatted_results += "\n"
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert education specialist. Your task is to create a comprehensive learning path 
    for {user_topic}.

    Use the following research information:
    {search_results}

    Design a logical sequence of learning modules. For each module, provide:
    1. A clear, informative title
    2. A detailed description of what will be covered in the module

    Structure your response as a series of modules that build upon each other.
    
    {format_instructions}
    """)
    
    try:
        llm = get_llm()
        chain = prompt | llm | modules_parser
        
        module_list = await chain.ainvoke({
            "user_topic": state["user_topic"],
            "search_results": formatted_results,
            "format_instructions": modules_parser.get_format_instructions()
        })
        
        # Extract the modules from the container object
        modules = module_list.modules
        logger.info(f"Created learning path with {len(modules)} modules")
        
        return {
            "modules": modules,
            "steps": [f"Created learning path with {len(modules)} modules"]
        }
    except Exception as e:
        logger.error(f"Error creating learning path: {str(e)}")
        return {
            "modules": [],
            "steps": [f"Error creating learning path: {str(e)}"]
        }

# New node functions for parallel module development
async def initialize_parallel_processing(state: LearningPathState):
    """Initialize the parallel module development process."""
    logger.info(f"Initializing parallel module development process with {state['parallel_count']} modules at once")
    
    if not state.get("modules"):
        logger.warning("No modules to develop")
        return {
            "developed_modules": [],
            "steps": ["No modules to develop"]
        }
    
    # Create module batches based on parallel_count
    parallel_count = state.get("parallel_count", 1)  # Default to 1 if not specified
    modules = state.get("modules", [])
    
    # Create batches of module indices
    module_batches = []
    for i in range(0, len(modules), parallel_count):
        batch = list(range(i, min(i + parallel_count, len(modules))))
        module_batches.append(batch)
    
    logger.info(f"Created {len(module_batches)} batches of modules for parallel processing")
    
    return {
        "module_batches": module_batches,
        "current_batch_index": 0,
        "modules_in_process": {},
        "developed_modules": [],
        "steps": [f"Initialized parallel processing with {parallel_count} modules at once"]
    }

async def process_module_batch(state: LearningPathState):
    """Process the current batch of modules in parallel."""
    logger.info("Processing a batch of modules in parallel")
    
    if state.get("current_batch_index", 0) >= len(state.get("module_batches", [])):
        logger.info("All module batches have been processed")
        return {
            "steps": ["All module batches have been processed"]
        }
    
    # Get the current batch of module indices
    current_batch = state["module_batches"][state["current_batch_index"]]
    modules = state["modules"]
    
    # Initialize modules_in_process for this batch if needed
    modules_in_process = state.get("modules_in_process", {})
    
    # Create a task for each module in the batch
    tasks = []
    for module_index in current_batch:
        if module_index not in modules_in_process:
            modules_in_process[module_index] = {
                "status": "starting",
                "search_queries": None,
                "search_results": None,
                "content": None
            }
            
            # Create a task to process this module
            module = modules[module_index]
            task = process_single_module(state, module_index, module)
            tasks.append(task)
    
    # Report progress
    progress_msg = f"Started processing batch {state['current_batch_index'] + 1} with {len(tasks)} modules"
    logger.info(progress_msg)
    
    # Process the tasks in parallel
    if tasks:
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update modules_in_process with results
            for i, module_index in enumerate(current_batch):
                if i < len(results):
                    result = results[i]
                    if isinstance(result, Exception):
                        logger.error(f"Error processing module {module_index}: {str(result)}")
                        modules_in_process[module_index]["status"] = "error"
                        modules_in_process[module_index]["error"] = str(result)
                    else:
                        modules_in_process[module_index] = result
            
            logger.info(f"Completed processing batch {state['current_batch_index'] + 1}")
        except Exception as e:
            logger.error(f"Error in parallel processing batch: {str(e)}")
    
    # Move to the next batch
    next_batch_index = state["current_batch_index"] + 1
    
    # Collect developed modules from this batch
    developed_modules = state.get("developed_modules", [])
    for module_index in current_batch:
        module_data = modules_in_process.get(module_index, {})
        if module_data.get("status") == "completed":
            developed_modules.append(ModuleContent(
                module_id=module_index,
                title=modules[module_index].title,
                description=modules[module_index].description,
                search_queries=module_data.get("search_queries", []),
                search_results=module_data.get("search_results", []),
                content=module_data.get("content", "")
            ))
    
    return {
        "modules_in_process": modules_in_process,
        "current_batch_index": next_batch_index,
        "developed_modules": developed_modules,
        "steps": [f"Processed batch {state['current_batch_index'] + 1} of modules in parallel"]
    }

async def process_single_module(state: LearningPathState, module_index: int, module: Module) -> Dict[str, Any]:
    """Process a single module from research to content development."""
    logger.info(f"Processing module {module_index + 1}: {module.title}")
    
    try:
        # Step 1: Generate search queries for this module
        module_search_queries = await generate_module_specific_queries(state, module_index, module)
        
        # Update progress
        if state.get("progress_callback"):
            await state["progress_callback"](f"Generated search queries for module {module_index + 1}: {module.title}")
        
        # Step 2: Execute web searches for the module
        module_search_results = await execute_module_specific_searches(state, module_index, module, module_search_queries)
        
        # Update progress
        if state.get("progress_callback"):
            await state["progress_callback"](f"Completed research for module {module_index + 1}: {module.title}")
        
        # Step 3: Develop the module content
        module_content = await develop_module_specific_content(state, module_index, module, module_search_queries, module_search_results)
        
        # Update progress
        if state.get("progress_callback"):
            await state["progress_callback"](f"Completed development of module {module_index + 1}: {module.title}")
        
        # Return the results for this module
        return {
            "status": "completed",
            "search_queries": module_search_queries,
            "search_results": module_search_results,
            "content": module_content
        }
    except Exception as e:
        logger.error(f"Error processing module {module_index}: {str(e)}")
        # Update progress with error
        if state.get("progress_callback"):
            await state["progress_callback"](f"Error processing module {module_index + 1}: {str(e)}")
        
        return {
            "status": "error",
            "error": str(e)
        }

async def generate_module_specific_queries(state: LearningPathState, module_index: int, module: Module) -> List[SearchQuery]:
    """Generate targeted search queries for a specific module."""
    logger.info(f"Generating search queries for module {module_index + 1}: {module.title}")
    
    # Create a context of the entire learning path
    learning_path_context = "Complete Learning Path:\n"
    for i, mod in enumerate(state["modules"]):
        learning_path_context += f"Module {i+1}: {mod.title}\n"
        learning_path_context += f"Description: {mod.description}\n\n"
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert research assistant. Your task is to generate 5 search queries that 
    will gather comprehensive information for developing the module titled "{module_title}" 
    which is part of a learning path about "{user_topic}".

    Here is the description of this module:
    {module_description}

    Here is the context of the entire learning path:
    {learning_path_context}

    For each search query:
    1. Make it specific and targeted to this particular module
    2. Ensure it covers different aspects needed to develop this module
    3. Design it to return high-quality educational content
    4. Explain why this search is important for developing this module

    Your response should be exactly 5 search queries, each with its rationale.
    
    {format_instructions}
    """)
    
    try:
        llm = get_llm()
        chain = prompt | llm | module_queries_parser
        
        search_query_list = await chain.ainvoke({
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "module_description": module.description,
            "learning_path_context": learning_path_context,
            "format_instructions": module_queries_parser.get_format_instructions()
        })
        
        # Extract the queries from the container object
        module_search_queries = search_query_list.queries
        logger.info(f"Generated {len(module_search_queries)} search queries for module: {module.title}")
        
        return module_search_queries
    except Exception as e:
        logger.error(f"Error generating module search queries: {str(e)}")
        return []

async def execute_module_specific_searches(
    state: LearningPathState, 
    module_index: int, 
    module: Module, 
    module_search_queries: List[SearchQuery]
) -> List[Dict[str, Any]]:
    """Execute web searches for a specific module's queries in parallel."""
    logger.info(f"Executing web searches for module {module_index + 1} in parallel: {module.title}")
    
    if not module_search_queries:
        logger.warning(f"No search queries available for module {module_index + 1}")
        return []
    
    # Get the search parallel count (default to 3 if not specified)
    search_parallel_count = state.get("search_parallel_count", 3)
    
    # Create batches of search queries based on the parallel count
    query_batches = []
    for i in range(0, len(module_search_queries), search_parallel_count):
        batch = module_search_queries[i:min(i + search_parallel_count, len(module_search_queries))]
        query_batches.append(batch)
    
    logger.info(f"Executing {len(module_search_queries)} module searches in {len(query_batches)} batches with parallelism of {search_parallel_count}")
    
    search_results = []
    
    try:
        # Process each batch of queries in parallel
        for batch_index, batch in enumerate(query_batches):
            logger.info(f"Processing module search batch {batch_index + 1}/{len(query_batches)} with {len(batch)} queries")
            
            # Create a task for each query in the batch
            tasks = []
            for query in batch:
                tasks.append(execute_single_search(query))
            
            # Execute the batch of searches in parallel
            batch_results = await asyncio.gather(*tasks)
            search_results.extend(batch_results)
            
            # Add a small delay between batches to prevent rate limiting
            if batch_index < len(query_batches) - 1:
                await asyncio.sleep(0.5)
        
        logger.info(f"Completed {len(search_results)} web searches for module {module_index + 1} in parallel")
        
        return search_results
    except Exception as e:
        logger.error(f"Error executing module web searches: {str(e)}")
        return []

async def develop_module_specific_content(
    state: LearningPathState, 
    module_index: int, 
    module: Module, 
    module_search_queries: List[SearchQuery],
    module_search_results: List[Dict[str, Any]]
) -> str:
    """Develop comprehensive content for a specific module."""
    logger.info(f"Developing content for module {module_index + 1}: {module.title}")
    
    if not module_search_results:
        logger.warning(f"No search results available for module {module_index + 1}")
        return "No content could be developed due to missing search results."
    
    # Format search results for the prompt
    formatted_results = ""
    for result in module_search_results:
        formatted_results += f"Search Query: {result['query']}\n"
        formatted_results += f"Rationale: {result['rationale']}\n"
        formatted_results += "Results:\n"
        
        if isinstance(result['results'], str):  # Error case
            formatted_results += f"  {result['results']}\n\n"
        else:
            for item in result['results']:
                formatted_results += f"  - {item.get('title', 'No title')}: {item.get('content', 'No content')}\n"
                formatted_results += f"    URL: {item.get('url', 'No URL')}\n"
            formatted_results += "\n"
    
    # Create a context of the entire learning path
    learning_path_context = "Complete Learning Path:\n"
    for i, mod in enumerate(state["modules"]):
        if i == module_index:
            learning_path_context += f"Module {i+1}: {mod.title} (CURRENT MODULE)\n"
        else:
            learning_path_context += f"Module {i+1}: {mod.title}\n"
        learning_path_context += f"Description: {mod.description}\n\n"
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert education content developer. Your task is to create comprehensive
    educational content for a module titled "{module_title}" which is part of a learning 
    path about "{user_topic}".

    Module description: {module_description}

    The position of this module in the learning path: Module {module_index} of {total_modules}

    Context of the entire learning path:
    {learning_path_context}

    Use the following research information to develop this module:
    {search_results}

    Your content should:
    1. Be comprehensive and educational
    2. Include clear explanations of concepts
    3. Provide examples where appropriate
    4. Reference authoritative sources
    5. Build upon prior modules in the learning path
    6. Prepare the learner for subsequent modules

    Structure your content with appropriate sections, subsections, and formatting.
    Use markdown formatting for headings, lists, code blocks, etc.
    """)
    
    try:
        llm = get_llm()
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser
        
        module_content = await chain.ainvoke({
            "user_topic": state["user_topic"],
            "module_title": module.title,
            "module_description": module.description,
            "module_index": module_index + 1,
            "total_modules": len(state["modules"]),
            "learning_path_context": learning_path_context,
            "search_results": formatted_results
        })
        
        logger.info(f"Developed content for module {module_index + 1}: {module.title}")
        
        return module_content
    except Exception as e:
        logger.error(f"Error developing module content: {str(e)}")
        return f"Error developing content: {str(e)}"

async def finalize_learning_path(state: LearningPathState):
    """Create the final learning path with all developed modules."""
    logger.info("Finalizing learning path")
    
    if not state.get("developed_modules"):
        logger.warning("No developed modules available")
        return {
            "final_learning_path": {
                "topic": state["user_topic"],
                "modules": []
            },
            "steps": ["No modules were developed"]
        }
    
    # Format the final learning path with all module content
    final_learning_path = {
        "topic": state["user_topic"],
        "modules": [
            {
                "id": module.module_id,
                "title": module.title,
                "description": module.description,
                "content": module.content
            }
            for module in state["developed_modules"]
        ],
        "execution_steps": state["steps"]
    }
    
    logger.info(f"Finalized comprehensive learning path with {len(final_learning_path['modules'])} modules")
    
    return {
        "final_learning_path": final_learning_path,
        "steps": ["Finalized comprehensive learning path"]
    }

# Function to check if all module batches are processed
def check_batch_processing(state: LearningPathState) -> str:
    """Conditional edge function to check if all module batches are processed."""
    if state["current_batch_index"] >= len(state["module_batches"]):
        return "all_batches_processed"
    else:
        return "continue_processing"

# Build the enhanced graph with parallel processing
def build_graph():
    """Construct and return the enhanced LangGraph with parallel processing."""
    logger.info("Building graph with parallel processing support")
    
    graph = StateGraph(LearningPathState)
    
    # Add nodes for initial learning path generation
    graph.add_node("generate_search_queries", generate_search_queries)
    graph.add_node("execute_web_searches", execute_web_searches)
    graph.add_node("create_learning_path", create_learning_path)
    
    # Add nodes for parallel module development
    graph.add_node("initialize_parallel_processing", initialize_parallel_processing)
    graph.add_node("process_module_batch", process_module_batch)
    graph.add_node("finalize_learning_path", finalize_learning_path)
    
    # Connect initial learning path flow
    graph.add_edge(START, "generate_search_queries")
    graph.add_edge("generate_search_queries", "execute_web_searches")
    graph.add_edge("execute_web_searches", "create_learning_path")
    
    # Connect module development flow
    graph.add_edge("create_learning_path", "initialize_parallel_processing")
    
    # Create a loop for processing batches of modules
    graph.add_edge("initialize_parallel_processing", "process_module_batch")
    graph.add_conditional_edges(
        "process_module_batch",
        check_batch_processing,
        {
            "all_batches_processed": "finalize_learning_path",
            "continue_processing": "process_module_batch"  # Loop back to process next batch
        }
    )
    
    graph.add_edge("finalize_learning_path", END)
    
    # Compile the graph
    return graph.compile()

# Main entry point to use the graph
async def generate_learning_path(
    topic: str, 
    parallel_count: int = 1, 
    search_parallel_count: int = 3,  # Added parameter for search parallelism
    progress_callback: Callable = None
):
    """Generate a comprehensive learning path for the given topic."""
    logger.info(f"Generating learning path for topic: {topic} with {parallel_count} parallel modules and {search_parallel_count} parallel searches")
    
    # Create the graph
    learning_graph = build_graph()
    
    # Initialize the state
    initial_state = {
        "user_topic": topic,
        "search_queries": None,
        "search_results": None,
        "modules": None,
        "steps": [],
        
        # Module development fields
        "current_module_index": None,
        "module_search_queries": None,
        "module_search_results": None,
        "developed_modules": None,
        "final_learning_path": None,
        
        # Parallel processing fields
        "parallel_count": parallel_count,
        "module_batches": None,
        "current_batch_index": None,
        "modules_in_process": None,
        "progress_callback": progress_callback,
        
        # Parallel search fields
        "search_parallel_count": search_parallel_count
    }
    
    # Execute the graph
    try:
        result = await learning_graph.ainvoke(initial_state)
        
        # Format the result for display
        formatted_output = result["final_learning_path"] if result.get("final_learning_path") else {
            "topic": topic,
            "modules": result.get("modules", []),
            "execution_steps": result["steps"]
        }
        
        logger.info(f"Successfully generated comprehensive learning path for {topic}")
        return formatted_output
    except Exception as e:
        logger.error(f"Error in graph execution: {str(e)}")
        # Return a minimal result in case of error
        return {
            "topic": topic,
            "modules": [],
            "execution_steps": [f"Error: {str(e)}"]
        }

# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Example topic
    topic = "Quantum computing for beginners"
    
    # Run the learning path generator
    result = asyncio.run(generate_learning_path(topic, parallel_count=2, search_parallel_count=3))
    
    # Print the result
    print(f"Learning Path for: {result['topic']}")
    print("\nExecution Steps:")
    for step in result.get("execution_steps", []):
        print(f"- {step}")
    
    print("\nModules:")
    for i, module in enumerate(result.get("modules", []), 1):
        print(f"\nModule {i}: {module.get('title')}")
        print(f"Description: {module.get('description')}")
        
        # Print module content if available
        if "content" in module:
            print("\nContent:")
            print(module["content"][:500] + "..." if len(module["content"]) > 500 else module["content"]) 