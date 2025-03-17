import asyncio
import logging
from typing import Dict, Any

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
        result = await run_chain(prompt, lambda: get_llm(api_key=state.get("openai_api_key")), search_queries_parser, {
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
    Executes all search queries in parallel batches.
    
    Args:
        state: The current LearningPathState containing 'search_queries'.
        
    Returns:
        A dictionary with aggregated search results and execution steps.
    """
    logging.info("Executing web searches in parallel")
    if not state.get("search_queries"):
        logging.warning("No search queries to execute")
        return {"search_results": [], "steps": ["No search queries available"]}
    
    search_parallel_count = state.get("search_parallel_count", 3)
    queries = state["search_queries"]
    query_batches = batch_items(queries, search_parallel_count)
    logging.info(f"Executing {len(queries)} searches in {len(query_batches)} batches")
    search_results = []
    try:
        for batch_index, batch in enumerate(query_batches):
            tasks = [execute_single_search(query, tavily_api_key=state.get("tavily_api_key")) for query in batch]
            batch_results = await asyncio.gather(*tasks)
            search_results.extend(batch_results)
            if batch_index < len(query_batches) - 1:
                await asyncio.sleep(0.5)
        logging.info(f"Completed {len(search_results)} web searches")
        if state.get("progress_callback"):
            await state["progress_callback"](f"Executed {len(search_results)} web searches")
        return {"search_results": search_results, "steps": [f"Executed {len(search_results)} searches"]}
    except Exception as e:
        logging.error(f"Error executing web searches: {str(e)}")
        return {"search_results": [], "steps": [f"Error: {str(e)}"]}

async def create_learning_path(state: LearningPathState) -> Dict[str, Any]:
    """
    Creates a comprehensive learning path based on search results using an LLM chain.
    
    Args:
        state: The current LearningPathState containing 'search_results'.
        
    Returns:
        A dictionary with generated learning modules and execution steps.
    """
    logging.info("Creating learning path")
    if not state.get("search_results"):
        logging.warning("No search results available")
        return {"modules": [], "steps": ["No search results available"]}
    
    formatted_results = format_search_results(state["search_results"])
    
    prompt_text = """
# EXPERT TEACHING ASSISTANT INSTRUCTIONS

Your task is to create a comprehensive learning path for the topic "{user_topic}" based on thorough research.

## RESEARCH INFORMATION
{search_results}

## MODULE PLANNING PRINCIPLES

### A) Progressive Expertise Development
- First module must be truly introductory, assuming zero knowledge
- Each subsequent module builds expertise systematically
- Advanced concepts are introduced only after solid foundations
- Technical depth increases progressively but steadily
- Final modules should reach expert-level understanding

### B) Topic Focus and Granularity
- Each module must focus on ONE specific concept or aspect
- Break down large topics into focused, manageable modules
- No mixing of different fundamental concepts in a single module
- Prefer smaller, focused modules for clarity
- Ensure each module is exhaustive within its focus

### C) Knowledge Building
- Start with fundamentals accessible to beginners
- Build complexity gradually but thoroughly
- Each module represents a clear step toward expertise
- Connect new knowledge with established concepts
- Ensure deep understanding before advancing

### D) Module Independence and Interconnection
- Each module must be self-contained
- Clear prerequisites must be identified
- Strong connections with previous modules
- Preview future module connections
- Create a cohesive learning journey

### E) Depth and Accessibility Balance
- Maintain detail while ensuring clarity
- Break complex topics into digestible segments
- Provide thorough coverage without overwhelming
- Each module should feel complete and focused

## LEARNING PATH REQUIREMENTS

Design a logical sequence of 4-7 learning modules that follows these principles. For each module, provide:
1. A clear title indicating its focus.
2. The core concept addressed.
3. A detailed description of content.
4. Clear learning objectives.
5. Prerequisites (if any).
6. Key components to cover.
7. Expected outcomes.

Ensure the modules build upon each other progressively.

{format_instructions}
"""
    prompt = ChatPromptTemplate.from_template(prompt_text)
    try:
        result = await run_chain(prompt, lambda: get_llm(api_key=state.get("openai_api_key")), enhanced_modules_parser, {
            "user_topic": state["user_topic"],
            "search_results": formatted_results,
            "format_instructions": enhanced_modules_parser.get_format_instructions()
        })
        modules = result.modules
        logging.info(f"Created learning path with {len(modules)} modules")
        return {"modules": modules, "steps": [f"Created learning path with {len(modules)} modules"]}
    except Exception as e:
        logging.error(f"Error creating learning path: {str(e)}")
        return {"modules": [], "steps": [f"Error: {str(e)}"]}
