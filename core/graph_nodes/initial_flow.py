import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from models.models import SearchQuery, LearningPathState
from parsers.parsers import search_queries_parser, enhanced_modules_parser
from services.services import get_llm, get_search_tool
from langchain_core.prompts import ChatPromptTemplate

from core.graph_nodes.helpers import run_chain, batch_items, format_search_results

async def execute_single_search(query: SearchQuery, tavily_api_key: str = None) -> Dict[str, Any]:
    """
    Executes a single web search using the search tool.
    
    Args:
        query: A SearchQuery instance with keywords and rationale.
        tavily_api_key: Optional Tavily API key for search.
        
    Returns:
        A dictionary with the query, rationale, and search results.
    """
    try:
        search_tool = get_search_tool(api_key=tavily_api_key)
        logging.info(f"Searching for: {query.keywords}")
        result = await search_tool.ainvoke({"query": query.keywords})
        return {
            "query": query.keywords,
            "rationale": query.rationale,
            "results": result
        }
    except Exception as e:
        logging.error(f"Error searching for '{query.keywords}': {str(e)}")
        return {
            "query": query.keywords,
            "rationale": query.rationale,
            "results": f"Error performing search: {str(e)}"
        }

async def generate_search_queries(state: LearningPathState) -> Dict[str, Any]:
    """
    Generates optimal search queries for the user topic using an LLM chain.
    
    Args:
        state: The current LearningPathState with 'user_topic'.
        
    Returns:
        A dictionary containing the generated search queries and a list of execution steps.
    """
    logging.info(f"Generating search queries for topic: {state['user_topic']}")
    prompt_text = """
# EXPERT TEACHING ASSISTANT INSTRUCTIONS

Your task is to analyze a learning topic and generate optimal search queries to gather comprehensive information.

## TOPIC ANALYSIS

Please analyze the topic "{user_topic}" thoroughly:

### CORE CONCEPT IDENTIFICATION
- Primary concepts that form the foundation
- Supporting concepts necessary for understanding
- Advanced concepts that build on the basics
- Practical applications and implications
- Tools, methodologies, or frameworks involved

### KNOWLEDGE STRUCTURE MAPPING
- Fundamental principles and theories
- Key relationships and dependencies
- Historical or contextual elements
- Current state and developments
- Future implications or trends

### COMPLEXITY LAYERS
- Basic principles and definitions
- Intermediate concepts and applications
- Advanced theories and implementations
- Expert-level considerations
- Cross-domain connections

## SEARCH STRATEGY

Based on this analysis, generate 5 search queries that will:
1. Cover different critical aspects of the topic
2. Address various complexity levels
3. Explore diverse perspectives and applications
4. Ensure comprehensive understanding
5. Target high-quality educational content

For each search query:
- Make it specific and targeted
- Explain why this search is essential for understanding the topic
- Ensure it addresses a different aspect of the topic
- Design it to return high-quality educational content

Your response should be exactly 5 search queries, each with its detailed rationale.

{format_instructions}
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    try:
        # Access the OpenAI API key from state with logging
        openai_api_key = state.get("openai_api_key")
        if not openai_api_key:
            logging.warning("OpenAI API key not found in state, this may cause errors")
        else:
            logging.debug("Found OpenAI API key in state, using for search query generation")
            
        result = await run_chain(prompt, lambda: get_llm(api_key=openai_api_key), search_queries_parser, {
            "user_topic": state["user_topic"],
            "format_instructions": search_queries_parser.get_format_instructions()
        })
        search_queries = result.queries
        logging.info(f"Generated {len(search_queries)} search queries")
        return {
            "search_queries": search_queries,
            "steps": [f"Generated {len(search_queries)} search queries for topic: {state['user_topic']}"]
        }
    except Exception as e:
        logging.error(f"Error generating search queries: {str(e)}")
        return {"search_queries": [], "steps": [f"Error: {str(e)}"]}

async def execute_web_searches(state: LearningPathState) -> Dict[str, Any]:
    """
    Execute web searches for each search query in parallel.
    """
    if not state.get("search_queries"):
        logging.info("No search queries to execute")
        return {
            "search_results": [],
            "steps": state.get("steps", []) + ["No search queries to execute"]
        }
    
    search_queries = state["search_queries"]
    
    # Get the tavily API key from state with logging
    tavily_api_key = state.get("tavily_api_key")
    if not tavily_api_key:
        logging.warning("Tavily API key not found in state, this may cause errors")
    else:
        logging.debug("Found Tavily API key in state, using for web searches")
    
    # Set up parallel processing
    batch_size = min(len(search_queries), state.get("search_parallel_count", 3))
    logging.info(f"Executing web searches in parallel with batch size {batch_size}")
    
    all_results = []
    
    try:
        for i in range(0, len(search_queries), batch_size):
            batch = search_queries[i:i+batch_size]
            logging.info(f"Processing batch of {len(batch)} searches")
            
            # Create tasks for parallel execution
            tasks = [execute_single_search(query, tavily_api_key=tavily_api_key) for query in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logging.error(f"Error executing search: {str(result)}")
                    # Add a placeholder for failed searches
                    all_results.append({
                        "query": batch[j].query,
                        "results": [],
                        "error": str(result)
                    })
                else:
                    all_results.append(result)
        
        logging.info(f"Completed {len(all_results)} web searches")
        
        return {
            "search_results": all_results,
            "steps": state.get("steps", []) + [f"Executed {len(all_results)} web searches"]
        }
    except Exception as e:
        logging.exception(f"Error executing web searches: {str(e)}")
        return {
            "search_results": all_results,
            "steps": state.get("steps", []) + [f"Error executing web searches: {str(e)}"]
        }

async def create_learning_path(state: LearningPathState) -> Dict[str, Any]:
    """
    Create a structured learning path from search results.
    """
    if not state.get("search_results") or len(state["search_results"]) == 0:
        logging.info("No search results available")
        return {
            "modules": [],
            "final_learning_path": {
                "topic": state["user_topic"],
                "modules": []
            },
            "steps": state.get("steps", []) + ["No search results available"]
        }
    
    # Get the OpenAI API key from state with logging
    openai_api_key = state.get("openai_api_key")
    if not openai_api_key:
        logging.warning("OpenAI API key not found in state, this may cause errors")
    else:
        logging.debug("Found OpenAI API key in state, using for learning path creation")
    
    # Build the learning path
    try:
        # Process search results into a format suitable for generating modules
        processed_results = []
        for result in state["search_results"]:
            query = result.get("query", "Unknown query")
            search_results = result.get("results", [])
            
            # Skip empty results
            if not search_results:
                continue
                
            processed_results.append({
                "query": query,
                "relevant_information": "\n\n".join([
                    f"Source: {item.get('source', 'Unknown')}\n{item.get('content', 'No content')}" 
                    for item in search_results[:3]  # Limit to top 3 results per query
                ])
            })
        
        # Convert search results to a text representation for the prompt
        results_text = ""
        for i, result in enumerate(processed_results, 1):
            results_text += f"""
Search {i}: "{result['query']}"
{result['relevant_information']}
---
"""

        # Prepare the prompt for creating modules
        prompt_text = f"""
You are an expert curriculum designer. Create a comprehensive learning path for the topic: {state['user_topic']}.

Based on the following search results, organize the learning into logical modules:

{results_text}

Create a structured learning path with 3-7 modules. For each module:
1. Give it a clear, descriptive title
2. Write a comprehensive overview (100-200 words)
3. Identify 3-5 key learning objectives
4. Explain why this module is important in the overall learning journey

Format your response as a structured curriculum. Each module should build on previous knowledge.

{enhanced_modules_parser.get_format_instructions()}
"""
        prompt = ChatPromptTemplate.from_template(prompt_text)
        
        result = await run_chain(prompt, lambda: get_llm(api_key=openai_api_key), enhanced_modules_parser, {})
        
        modules = result.modules
        
        # Create the final learning path structure
        final_learning_path = {
            "topic": state["user_topic"],
            "modules": modules,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "num_modules": len(modules)
            }
        }
        
        logging.info(f"Created learning path with {len(modules)} modules")
        
        return {
            "modules": modules,
            "final_learning_path": final_learning_path,
            "steps": state.get("steps", []) + [f"Created learning path with {len(modules)} modules"]
        }
    except Exception as e:
        logging.exception(f"Error creating learning path: {str(e)}")
        return {
            "modules": [],
            "final_learning_path": {
                "topic": state["user_topic"],
                "modules": []
            },
            "steps": state.get("steps", []) + [f"Error creating learning path: {str(e)}"]
        }
