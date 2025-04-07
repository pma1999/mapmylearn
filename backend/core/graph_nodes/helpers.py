import asyncio
from typing import List, Any, Dict, Optional, Union, Callable, TypeVar
import logging
import re
import time
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import BaseOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger("learning_path.helpers")

T = TypeVar('T')  # Type variable for parser return type

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

def create_retry_prompt(original_prompt, format_instructions: str, failed_response: str, error_message: str) -> ChatPromptTemplate:
    """
    Creates a specialized prompt for retrying after a parsing error.
    
    Args:
        original_prompt: The original ChatPromptTemplate instance.
        format_instructions: The format instructions for the parser.
        failed_response: The failed response from the LLM.
        error_message: The error message that occurred during parsing.
        
    Returns:
        A ChatPromptTemplate instance with enhanced instructions for fixing formatting errors.
    """
    # Extract the original template more safely
    try:
        if hasattr(original_prompt, 'messages'):
            # For ChatPromptTemplate objects, try to safely extract content from each message
            message_contents = []
            for msg in original_prompt.messages:
                try:
                    # Try different methods of getting content based on message type
                    if hasattr(msg, 'prompt') and hasattr(msg.prompt, 'template'):
                        message_contents.append(f"[{msg.__class__.__name__}]: {msg.prompt.template}")
                    elif hasattr(msg, 'template'):
                        message_contents.append(f"[{msg.__class__.__name__}]: {msg.template}")
                    else:
                        message_contents.append(str(msg))
                except Exception:
                    # If anything fails, use string representation
                    message_contents.append(str(msg))
            
            original_template = "\n".join(message_contents)
        else:
            original_template = str(original_prompt)
    except Exception as e:
        logger.warning(f"Could not extract original prompt content: {str(e)}")
        original_template = "Original prompt not available"
    
    # Extract validation error information if available
    validation_details = ""
    if "validation error" in error_message.lower():
        validation_match = re.search(r'validation error.+', error_message, re.DOTALL)
        if validation_match:
            validation_details = validation_match.group(0)
    
    # Create enhanced template with explicit retry instructions
    retry_template = f"""
I need you to fix a formatting error in your previous response. 

Original prompt:
--------
{original_template}
--------

Format required:
--------
{format_instructions}
--------

Your previous response:
--------
{failed_response}
--------

Error details:
--------
{error_message}
{validation_details}
--------

IMPORTANT: Return ONLY valid JSON that strictly follows the required format. 
Do not include any explanations, notes, or extra text. 
The response MUST be valid JSON that can be parsed with the given schema.
Make sure all required fields are present and correctly formatted.
"""
    
    # Create a new prompt template with the retry instructions
    return ChatPromptTemplate.from_messages([("system", retry_template)])

async def run_chain(prompt, llm_getter, parser: BaseOutputParser[T], params: Dict[str, Any], 
                   max_retries: int = 3, initial_retry_delay: float = 1.0,
                   retry_parsing_errors: bool = True, max_parsing_retries: int = 2) -> T:
    """
    Sets up and runs an LLM chain with a given prompt and output parser.
    Includes retry logic for handling empty responses, API errors, and parsing errors.
    
    Args:
        prompt: A ChatPromptTemplate instance.
        llm_getter: A function that returns an initialized LLM (may be async).
        parser: An output parser instance (e.g., a PydanticOutputParser).
        params: Parameters for the chain invocation.
        max_retries: Maximum number of retry attempts for empty/API errors (default: 3).
        initial_retry_delay: Base delay in seconds before first retry, doubles for each attempt (default: 1.0).
        retry_parsing_errors: Whether to retry when parsing errors occur (default: True).
        max_parsing_retries: Maximum number of retries specifically for parsing errors (default: 2).
        
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
    
    # Add retry logic for various error conditions
    api_retries = 0
    api_retry_start_time = None
    parsing_retries = 0
    parsing_retry_start_time = None
    is_gemini = isinstance(llm, ChatGoogleGenerativeAI)
    last_response = None  # Track the last raw response for parsing error retries
    
    while True:
        try:
            # If we're retrying after a parsing error, use a different approach
            if parsing_retry_start_time and retry_parsing_errors:
                # Get format instructions from the parser if available
                format_instructions = escaped_params.get("format_instructions", "")
                if not format_instructions and hasattr(parser, "get_format_instructions"):
                    format_instructions = parser.get_format_instructions()
                
                # Create specialized retry prompt
                error_message = f"Failed to parse the previous response: {str(last_response)[:200]}..."
                retry_prompt = create_retry_prompt(prompt, format_instructions, str(last_response), error_message)
                
                # Use a direct string output parser to get the raw JSON response
                from langchain.schema.output_parser import StrOutputParser
                raw_chain = retry_prompt | llm | StrOutputParser()
                
                logger.info(f"Retrying with formatting fix prompt (attempt {parsing_retries}/{max_parsing_retries})")
                raw_response = await raw_chain.ainvoke({})
                
                # Try to parse the raw response with the original parser
                try:
                    # Store response for potential retry
                    last_response = raw_response
                    
                    # Try to parse directly using the parser
                    if hasattr(parser, "parse"):
                        result = parser.parse(raw_response)
                        logger.info(f"Successfully parsed response after reformatting (attempt {parsing_retries})")
                        return result
                except Exception as parsing_error:
                    # If we still can't parse after max retries, give up
                    if parsing_retries >= max_parsing_retries:
                        logger.error(f"Failed to parse response after {parsing_retries} parsing retries: {str(parsing_error)}")
                        raise
                    
                    # Increment retries and try again
                    parsing_retries += 1
                    parsing_retry_delay = initial_retry_delay * (2 ** (parsing_retries - 1))
                    
                    logger.warning(
                        f"Still couldn't parse reformatted response. Retry {parsing_retries}/{max_parsing_retries} "
                        f"after {parsing_retry_delay:.2f}s delay. Error: {str(parsing_error)}"
                    )
                    
                    await asyncio.sleep(parsing_retry_delay)
                    continue
            
            # Normal execution path for initial attempt and API retries
            if api_retry_start_time:
                logger.info(f"Retrying API call (attempt {api_retries}/{max_retries})")
            
            # Store the raw response for potential parsing retries
            last_response = await (prompt | llm).ainvoke(escaped_params)
            
            # Try to parse with the provided parser
            result = await chain.ainvoke(escaped_params)
            
            # For string results, empty string is considered an empty response
            if isinstance(result, str):
                is_empty = not result.strip()
            # For structured outputs like Pydantic models or dictionaries, check if they're falsy
            elif hasattr(result, "__bool__"):
                is_empty = not bool(result)
            # If we can't determine emptiness, assume it's not empty
            else:
                is_empty = False
            
            # Only retry for Gemini LLMs returning empty responses
            if is_empty and is_gemini and api_retries < max_retries:
                if not api_retry_start_time:
                    api_retry_start_time = time.time()
                
                api_retries += 1
                retry_delay = initial_retry_delay * (2 ** (api_retries - 1))  # Exponential backoff
                
                logger.warning(
                    f"Empty response from Gemini detected. Retry attempt {api_retries}/{max_retries} "
                    f"after {retry_delay:.2f}s delay. Prompt: '{str(prompt)[:100]}...'"
                )
                
                await asyncio.sleep(retry_delay)
                continue
            
            # If we've retried and got a result, or we've exhausted retries, return result
            if api_retry_start_time:
                if is_empty:
                    logger.error(
                        f"Failed to get non-empty response from Gemini after {api_retries} "
                        f"retries ({time.time() - api_retry_start_time:.2f}s)"
                    )
                else:
                    logger.info(
                        f"Successfully got content from Gemini after {api_retries} "
                        f"retries ({time.time() - api_retry_start_time:.2f}s)"
                    )
            
            return result
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error in LLM chain execution: {error_str}")
            
            # Identify if this is a parsing error
            is_parsing_error = (
                "json" in error_str.lower() or 
                "validation error" in error_str.lower() or 
                "output_parsing_failure" in error_str.lower() or
                "jsondecodeerror" in error_str.lower() or
                "expected value" in error_str.lower() or
                "failed to parse" in error_str.lower()
            )
            
            # Handle parsing errors with retry if enabled
            if is_parsing_error and retry_parsing_errors and parsing_retries < max_parsing_retries:
                if not parsing_retry_start_time:
                    parsing_retry_start_time = time.time()
                
                parsing_retries += 1
                parsing_retry_delay = initial_retry_delay * (2 ** (parsing_retries - 1))
                
                logger.warning(
                    f"Parsing error detected: {error_str}. Retry attempt {parsing_retries}/{max_parsing_retries} "
                    f"after {parsing_retry_delay:.2f}s delay"
                )
                
                await asyncio.sleep(parsing_retry_delay)
                continue
            
            # Handle API call errors
            if is_gemini and api_retries < max_retries and "api" in error_str.lower():
                if not api_retry_start_time:
                    api_retry_start_time = time.time()
                
                api_retries += 1
                retry_delay = initial_retry_delay * (2 ** (api_retries - 1))
                
                logger.warning(
                    f"Gemini API error: {error_str}. Retry attempt {api_retries}/{max_retries} "
                    f"after {retry_delay:.2f}s delay"
                )
                
                await asyncio.sleep(retry_delay)
                continue
            
            # If not a retryable error or max retries reached, re-raise
            raise

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
