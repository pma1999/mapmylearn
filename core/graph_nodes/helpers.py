import asyncio
from typing import List, Any, Dict
import logging

def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Splits a list of items into batches of a specified size.
    
    Args:
        items: List of items to batch.
        batch_size: Maximum size of each batch.
        
    Returns:
        A list of batches (each batch is a list of items).
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

async def run_chain(prompt, llm_getter, parser, params: Dict[str, Any]) -> Any:
    """
    Sets up and runs an LLM chain with a given prompt and output parser.
    
    Args:
        prompt: A ChatPromptTemplate instance.
        llm_getter: A function that returns an initialized LLM (may be async).
        parser: An output parser instance (e.g., a PydanticOutputParser).
        params: Parameters for the chain invocation.
        
    Returns:
        The parsed result from the LLM chain.
    """
    # Handle both async and sync llm_getter functions
    llm_or_coroutine = llm_getter()
    if asyncio.iscoroutine(llm_or_coroutine):
        llm = await llm_or_coroutine
    else:
        llm = llm_or_coroutine
        
    chain = prompt | llm | parser
    return await chain.ainvoke(params)

def format_search_results(search_results: List[Dict[str, Any]]) -> str:
    """
    Formats a list of search results into a single string suitable for inclusion in prompts.
    
    Args:
        search_results: List of dictionaries with keys 'query', 'rationale', and 'results'.
        
    Returns:
        A formatted string aggregating all search results.
    """
    formatted = ""
    for result in search_results:
        formatted += f"Search Query: {result.get('query', '')}\n"
        formatted += f"Rationale: {result.get('rationale', '')}\nResults:\n"
        results = result.get("results", "")
        if isinstance(results, str):
            formatted += f"  {results}\n\n"
        else:
            for item in results:
                title = item.get("title", "No title")
                content = item.get("content", "No content")
                url = item.get("url", "No URL")
                formatted += f"  - {title}: {content}\n    URL: {url}\n"
            formatted += "\n"
    return formatted
