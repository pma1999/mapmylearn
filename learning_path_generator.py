import os
from typing import List, Dict, TypedDict, Annotated, Optional
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

class LearningPathState(TypedDict):
    user_topic: str
    search_queries: Optional[List[SearchQuery]]
    search_results: Optional[List[Dict[str, str]]]
    modules: Optional[List[Module]]
    steps: Annotated[List[str], add]  # For tracking execution steps

# Define output parsers using the container models
search_queries_parser = PydanticOutputParser(pydantic_object=SearchQueryList)
modules_parser = PydanticOutputParser(pydantic_object=ModuleList)

# Initialize the LLM and tools with error handling
def get_llm():
    """Initialize and return the LLM with proper error handling."""
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
    
    try:
        return ChatOpenAI(temperature=0.2, model="gpt-3.5-turbo", api_key=openai_api_key)
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

# Build the graph
def build_graph():
    """Construct and return the LangGraph."""
    logger.info("Building graph")
    
    graph = StateGraph(LearningPathState)
    
    # Add nodes
    graph.add_node("generate_search_queries", generate_search_queries)
    graph.add_node("execute_web_searches", execute_web_searches)
    graph.add_node("create_learning_path", create_learning_path)
    
    # Add edges
    graph.add_edge(START, "generate_search_queries")
    graph.add_edge("generate_search_queries", "execute_web_searches")
    graph.add_edge("execute_web_searches", "create_learning_path")
    graph.add_edge("create_learning_path", END)
    
    # Compile the graph
    return graph.compile()

# Main entry point to use the graph
async def generate_learning_path(topic: str):
    """Generate a learning path for the given topic."""
    logger.info(f"Generating learning path for topic: {topic}")
    
    # Create the graph
    learning_graph = build_graph()
    
    # Initialize the state
    initial_state = {
        "user_topic": topic,
        "search_queries": None,
        "search_results": None,
        "modules": None,
        "steps": []
    }
    
    # Execute the graph
    try:
        result = await learning_graph.ainvoke(initial_state)
        
        # Format the result for display
        formatted_output = {
            "topic": topic,
            "modules": result["modules"],
            "execution_steps": result["steps"]
        }
        
        logger.info(f"Successfully generated learning path for {topic}")
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
    for step in result["execution_steps"]:
        print(f"- {step}")
    
    print("\nModules:")
    for i, module in enumerate(result["modules"], 1):
        print(f"\nModule {i}: {module.title}")
        print(f"Description: {module.description}") 