import asyncio
from typing import List, Any, Dict
import logging
import re

def escape_curly_braces(text: str) -> str:
    """
    Escapa las llaves en un texto para evitar que sean interpretadas como variables de formato
    en los prompts de LangChain.
    
    Args:
        text: Texto que puede contener llaves {} que necesitan ser escapadas.
        
    Returns:
        Texto con las llaves escapadas (cada llave se duplica).
    """
    if not isinstance(text, str):
        return str(text)
    
    # Duplicar todas las llaves para escaparlas
    return text.replace('{', '{{').replace('}', '}}')

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
    
    # Escapar cualquier texto en los parámetros que podría contener llaves
    escaped_params = {}
    for key, value in params.items():
        if isinstance(value, str) and key != "format_instructions":
            escaped_params[key] = escape_curly_braces(value)
        else:
            escaped_params[key] = value
    
    chain = prompt | llm | parser
    return await chain.ainvoke(escaped_params)

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
        # Escapar las llaves en query y rationale
        query = escape_curly_braces(result.get('query', ''))
        rationale = escape_curly_braces(result.get('rationale', ''))
        
        formatted += f"Search Query: {query}\n"
        formatted += f"Rationale: {rationale}\nResults:\n"
        
        results = result.get("results", "")
        if isinstance(results, str):
            # Escapar las llaves en el contenido del resultado
            escaped_content = escape_curly_braces(results)
            formatted += f"  {escaped_content}\n\n"
        else:
            for item in results:
                # Escapar las llaves en cada campo del resultado
                title = escape_curly_braces(item.get("title", "No title"))
                content = escape_curly_braces(item.get("content", "No content"))
                url = escape_curly_braces(item.get("url", "No URL"))
                
                formatted += f"  - {title}: {content}\n    URL: {url}\n"
            formatted += "\n"
    
    return formatted
