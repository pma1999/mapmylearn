import os
from typing import List, Dict, TypedDict, Annotated, Optional, Any, Callable, Union
from operator import add
import logging
from dotenv import load_dotenv

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
    """Execute web searches using the generated queries."""
    logger.info("Executing web searches")
    
    if not state["search_queries"]:
        logger.warning("No search queries available to execute")
        return {
            "search_results": [],
            "steps": ["No search queries available to execute"]
        }
    
    search_results = []
    
    try:
        search_tool = get_search_tool()
        
        for query in state["search_queries"]:
            try:
                logger.info(f"Searching for: {query.keywords}")
                result = await search_tool.ainvoke({"query": query.keywords})
                search_results.append({
                    "query": query.keywords,
                    "rationale": query.rationale,
                    "results": result
                })
            except Exception as e:
                logger.error(f"Error searching for '{query.keywords}': {str(e)}")
                search_results.append({
                    "query": query.keywords,
                    "rationale": query.rationale,
                    "results": f"Error performing search: {str(e)}"
                })
        
        logger.info(f"Completed {len(search_results)} web searches")
        
        return {
            "search_results": search_results,
            "steps": [f"Executed web searches for all queries"]
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

# New node functions for module development
async def initialize_module_development(state: LearningPathState):
    """Initialize the module development process."""
    logger.info("Initializing module development process")
    
    if not state.get("modules"):
        logger.warning("No modules to develop")
        return {
            "developed_modules": [],
            "steps": ["No modules to develop"]
        }
    
    return {
        "current_module_index": 0,
        "developed_modules": [],
        "steps": ["Started module development process"]
    }

async def generate_module_queries(state: LearningPathState):
    """Generate targeted search queries for the current module."""
    logger.info("Generating module-specific search queries")
    
    if state.get("current_module_index", 0) >= len(state.get("modules", [])):
        logger.info("All modules have been processed")
        return {
            "steps": ["All modules have been processed"]
        }
    
    current_module = state["modules"][state["current_module_index"]]
    
    # Create a context of the entire learning path
    learning_path_context = "Complete Learning Path:\n"
    for i, module in enumerate(state["modules"]):
        learning_path_context += f"Module {i+1}: {module.title}\n"
        learning_path_context += f"Description: {module.description}\n\n"
    
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
            "module_title": current_module.title,
            "module_description": current_module.description,
            "learning_path_context": learning_path_context,
            "format_instructions": module_queries_parser.get_format_instructions()
        })
        
        # Extract the queries from the container object
        module_search_queries = search_query_list.queries
        logger.info(f"Generated {len(module_search_queries)} search queries for module: {current_module.title}")
        
        return {
            "module_search_queries": module_search_queries,
            "steps": [f"Generated search queries for module {state['current_module_index'] + 1}: {current_module.title}"]
        }
    except Exception as e:
        logger.error(f"Error generating module search queries: {str(e)}")
        return {
            "module_search_queries": [],
            "steps": [f"Error generating module search queries: {str(e)}"]
        }

async def execute_module_searches(state: LearningPathState):
    """Execute web searches for the current module's queries."""
    logger.info("Executing module-specific web searches")
    
    if not state.get("module_search_queries"):
        logger.warning("No module search queries available to execute")
        return {
            "module_search_results": [],
            "steps": ["No module search queries available to execute"]
        }
    
    current_module = state["modules"][state["current_module_index"]]
    search_results = []
    
    try:
        search_tool = get_search_tool()
        
        for query in state["module_search_queries"]:
            try:
                logger.info(f"Searching for module query: {query.keywords}")
                result = await search_tool.ainvoke({"query": query.keywords})
                search_results.append({
                    "query": query.keywords,
                    "rationale": query.rationale,
                    "results": result
                })
            except Exception as e:
                logger.error(f"Error searching for module query '{query.keywords}': {str(e)}")
                search_results.append({
                    "query": query.keywords,
                    "rationale": query.rationale,
                    "results": f"Error performing search: {str(e)}"
                })
        
        logger.info(f"Completed {len(search_results)} module web searches")
        
        return {
            "module_search_results": search_results,
            "steps": [f"Executed web searches for module {state['current_module_index'] + 1}: {current_module.title}"]
        }
    except Exception as e:
        logger.error(f"Error executing module web searches: {str(e)}")
        return {
            "module_search_results": [],
            "steps": [f"Error executing module web searches: {str(e)}"]
        }

async def develop_module_content(state: LearningPathState):
    """Develop comprehensive content for the current module."""
    logger.info("Developing module content")
    
    if not state.get("module_search_results"):
        logger.warning("No module search results available to develop content")
        return {
            "steps": ["No module search results available to develop content"]
        }
    
    current_module = state["modules"][state["current_module_index"]]
    
    # Format search results for the prompt
    formatted_results = ""
    for result in state["module_search_results"]:
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
    for i, module in enumerate(state["modules"]):
        if i == state["current_module_index"]:
            learning_path_context += f"Module {i+1}: {module.title} (CURRENT MODULE)\n"
        else:
            learning_path_context += f"Module {i+1}: {module.title}\n"
        learning_path_context += f"Description: {module.description}\n\n"
    
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
            "module_title": current_module.title,
            "module_description": current_module.description,
            "module_index": state["current_module_index"] + 1,
            "total_modules": len(state["modules"]),
            "learning_path_context": learning_path_context,
            "search_results": formatted_results
        })
        
        logger.info(f"Developed content for module: {current_module.title}")
        
        # Create a ModuleContent object
        developed_module = ModuleContent(
            module_id=state["current_module_index"],
            title=current_module.title,
            description=current_module.description,
            search_queries=state["module_search_queries"],
            search_results=state["module_search_results"],
            content=module_content
        )
        
        # Add to developed_modules
        developed_modules = state.get("developed_modules", []) + [developed_module]
        
        # Advance to next module
        next_module_index = state["current_module_index"] + 1
        
        return {
            "developed_modules": developed_modules,
            "current_module_index": next_module_index,
            "steps": [f"Developed content for module {state['current_module_index'] + 1}: {current_module.title}"]
        }
    except Exception as e:
        logger.error(f"Error developing module content: {str(e)}")
        return {
            "steps": [f"Error developing module content: {str(e)}"]
        }

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

# Function to check if all modules are processed
def check_module_processing(state: LearningPathState) -> str:
    """Conditional edge function to check if all modules are processed."""
    if state["current_module_index"] >= len(state["modules"]):
        return "all_modules_processed"
    else:
        return "continue_processing"

# Build the enhanced graph
def build_graph():
    """Construct and return the enhanced LangGraph."""
    logger.info("Building graph")
    
    graph = StateGraph(LearningPathState)
    
    # Add nodes for initial learning path generation
    graph.add_node("generate_search_queries", generate_search_queries)
    graph.add_node("execute_web_searches", execute_web_searches)
    graph.add_node("create_learning_path", create_learning_path)
    
    # Add nodes for module development
    graph.add_node("initialize_module_development", initialize_module_development)
    graph.add_node("generate_module_queries", generate_module_queries)
    graph.add_node("execute_module_searches", execute_module_searches)
    graph.add_node("develop_module_content", develop_module_content)
    graph.add_node("finalize_learning_path", finalize_learning_path)
    
    # Connect initial learning path flow
    graph.add_edge(START, "generate_search_queries")
    graph.add_edge("generate_search_queries", "execute_web_searches")
    graph.add_edge("execute_web_searches", "create_learning_path")
    
    # Connect module development flow
    graph.add_edge("create_learning_path", "initialize_module_development")
    graph.add_edge("initialize_module_development", "generate_module_queries")
    
    # Create a loop for processing each module
    graph.add_conditional_edges(
        "generate_module_queries",
        check_module_processing,
        {
            "all_modules_processed": "finalize_learning_path",
            "continue_processing": "execute_module_searches"
        }
    )
    
    graph.add_edge("execute_module_searches", "develop_module_content")
    graph.add_edge("develop_module_content", "generate_module_queries")  # Loop back
    graph.add_edge("finalize_learning_path", END)
    
    # Compile the graph
    return graph.compile()

# Main entry point to use the graph
async def generate_learning_path(topic: str):
    """Generate a comprehensive learning path for the given topic."""
    logger.info(f"Generating learning path for topic: {topic}")
    
    # Create the graph
    learning_graph = build_graph()
    
    # Initialize the state
    initial_state = {
        "user_topic": topic,
        "search_queries": None,
        "search_results": None,
        "modules": None,
        "steps": [],
        "current_module_index": None,
        "module_search_queries": None,
        "module_search_results": None,
        "developed_modules": None,
        "final_learning_path": None
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
    result = asyncio.run(generate_learning_path(topic))
    
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