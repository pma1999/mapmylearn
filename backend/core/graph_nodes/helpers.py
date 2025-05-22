import asyncio
from typing import List, Any, Dict, Optional, Union, Callable, TypeVar
import logging
import re
import time
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import BaseOutputParser, StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger("learning_path.helpers")

# --- Constants ---
MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT = 100000
# --- End Constants ---

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

def extract_json_from_markdown(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from text that might be formatted as markdown code blocks.
    
    Args:
        text: The text that may contain markdown-formatted JSON
        
    Returns:
        Parsed JSON object or None if extraction failed
    """
    # First try to parse directly as JSON (in case it's already valid JSON)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(code_block_pattern, text)
    
    # If we found code blocks, try each one
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    # If no code blocks or none contained valid JSON, try a more lenient approach
    # Look for text that appears to be JSON (starting with { and ending with })
    json_object_pattern = r'(\{[\s\S]*\})'
    object_matches = re.findall(json_object_pattern, text)
    
    for match in object_matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    # If we couldn't extract JSON, return None
    return None

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
    Enhanced to handle Gemini API requirements and markdown JSON extraction.
    
    Args:
        original_prompt: The original ChatPromptTemplate instance.
        format_instructions: The format instructions for the parser.
        failed_response: The failed response from the LLM.
        error_message: The error message that occurred during parsing.
        
    Returns:
        A ChatPromptTemplate instance with enhanced instructions for fixing formatting errors.
    """
    # Safely truncate and escape inputs to prevent template errors
    safe_failed_response = str(failed_response)[:1000] + "..." if len(str(failed_response)) > 1000 else str(failed_response)
    safe_failed_response = escape_curly_braces(safe_failed_response)
    
    safe_error_message = str(error_message)[:500] + "..." if len(str(error_message)) > 500 else str(error_message)
    safe_error_message = escape_curly_braces(safe_error_message)
    
    safe_format_instructions = escape_curly_braces(str(format_instructions))
    
    # Create a simplified retry template that focuses on proper JSON formatting
    retry_template = f"""You failed to format your previous response correctly. The response must be valid JSON that can be parsed.

REQUIRED FORMAT:
{safe_format_instructions}

YOUR PREVIOUS RESPONSE (which caused an error):
{safe_failed_response}

ERROR DETAILS:
{safe_error_message}

CRITICAL FORMATTING REQUIREMENTS:
1. Return ONLY valid JSON - no markdown code blocks, no explanations
2. Use proper JSON syntax with correct quotes and commas
3. Ensure all string values are properly quoted
4. Do not wrap the JSON in ```json or ``` markers
5. Provide a complete, well-formed JSON object

Please provide the corrected response as pure JSON:"""
    
    # Create a simple prompt template
    return ChatPromptTemplate.from_messages([("user", retry_template)])

async def run_chain(prompt, llm_getter, parser: BaseOutputParser[T], params: Dict[str, Any], 
                   max_retries: int = 3, initial_retry_delay: float = 1.0,
                   retry_parsing_errors: bool = True, max_parsing_retries: int = 2) -> T:
    """
    Enhanced run_chain with improved JSON extraction and error handling.
    
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
    
    # Add retry logic for various error conditions
    api_retries = 0
    api_retry_start_time = None
    parsing_retries = 0
    parsing_retry_start_time = None
    is_gemini = isinstance(llm, ChatGoogleGenerativeAI)
    last_raw_response = None  # Track the last raw response for parsing error retries
    
    while True:
        try:
            # If we're retrying after a parsing error, try JSON extraction first
            if parsing_retry_start_time and retry_parsing_errors and last_raw_response:
                logger.info(f"Attempting JSON extraction from previous response (attempt {parsing_retries}/{max_parsing_retries})")
                
                # Try to extract JSON from the previous response
                extracted_json = extract_json_from_markdown(last_raw_response)
                
                if extracted_json:
                    try:
                        # Try to parse the extracted JSON with the original parser
                        if hasattr(parser, "parse"):
                            result = parser.parse(json.dumps(extracted_json))
                            logger.info(f"Successfully extracted and parsed JSON on retry attempt {parsing_retries}")
                            return result
                    except Exception as parse_error:
                        logger.warning(f"Extracted JSON but failed to parse: {str(parse_error)}")
                
                # If JSON extraction failed, try with a formatting retry prompt
                try:
                    format_instructions = escaped_params.get("format_instructions", "")
                    if not format_instructions and hasattr(parser, "get_format_instructions"):
                        format_instructions = parser.get_format_instructions()
                    
                    # Create specialized retry prompt
                    retry_prompt = create_retry_prompt(prompt, format_instructions, last_raw_response, f"JSON parsing failed on attempt {parsing_retries}")
                    
                    # Use string output parser for the retry to get raw response
                    raw_chain = retry_prompt | llm | StrOutputParser()
                    
                    logger.info(f"Retrying with formatting fix prompt (attempt {parsing_retries}/{max_parsing_retries})")
                    retry_response = await raw_chain.ainvoke({})  # Empty params for retry prompt
                    
                    # Try to extract and parse JSON from retry response
                    retry_extracted_json = extract_json_from_markdown(retry_response)
                    
                    if retry_extracted_json:
                        try:
                            if hasattr(parser, "parse"):
                                result = parser.parse(json.dumps(retry_extracted_json))
                                logger.info(f"Successfully parsed retry response with JSON extraction")
                                return result
                        except Exception as retry_parse_error:
                            logger.warning(f"Retry response JSON extraction failed: {str(retry_parse_error)}")
                    
                    # Store the retry response for potential next iteration
                    last_raw_response = retry_response
                    
                except Exception as retry_error:
                    logger.warning(f"Retry prompt execution failed: {str(retry_error)}")
                
                # If we still can't parse after max retries, give up
                if parsing_retries >= max_parsing_retries:
                    logger.error(f"Failed to parse response after {parsing_retries} parsing retries")
                    raise Exception(f"Failed to parse JSON after {parsing_retries} retry attempts")
                
                # Increment retries and try again
                parsing_retries += 1
                parsing_retry_delay = initial_retry_delay * (2 ** (parsing_retries - 1))
                
                logger.warning(f"Still couldn't parse response. Retry {parsing_retries}/{max_parsing_retries} after {parsing_retry_delay:.2f}s delay")
                await asyncio.sleep(parsing_retry_delay)
                continue
            
            # Normal execution path for initial attempt and API retries
            if api_retry_start_time:
                logger.info(f"Retrying API call (attempt {api_retries}/{max_retries})")
            
            # Execute the chain and store raw response
            chain = prompt | llm | StrOutputParser()
            raw_response = await chain.ainvoke(escaped_params)
            last_raw_response = raw_response
            
            # Try to extract JSON first
            extracted_json = extract_json_from_markdown(raw_response)
            
            if extracted_json:
                try:
                    # Parse the extracted JSON
                    if hasattr(parser, "parse"):
                        result = parser.parse(json.dumps(extracted_json))
                    else:
                        # Fallback for parsers without parse method
                        result = extracted_json
                    
                    # Check if result is empty for Gemini retry logic
                    if isinstance(result, str):
                        is_empty = not result.strip()
                    elif hasattr(result, "__bool__"):
                        is_empty = not bool(result)
                    else:
                        is_empty = False
                    
                    # Only retry for Gemini LLMs returning empty responses
                    if is_empty and is_gemini and api_retries < max_retries:
                        if not api_retry_start_time:
                            api_retry_start_time = time.time()
                        
                        api_retries += 1
                        retry_delay = initial_retry_delay * (2 ** (api_retries - 1))
                        
                        logger.warning(f"Empty response from Gemini detected. Retry attempt {api_retries}/{max_retries} after {retry_delay:.2f}s delay")
                        await asyncio.sleep(retry_delay)
                        continue
                    
                    # Success case
                    if api_retry_start_time and not is_empty:
                        logger.info(f"Successfully got content from Gemini after {api_retries} retries")
                    
                    return result
                    
                except Exception as parse_error:
                    # JSON extraction succeeded but parsing failed
                    if not parsing_retry_start_time:
                        parsing_retry_start_time = time.time()
                    
                    parsing_retries += 1
                    if parsing_retries <= max_parsing_retries:
                        logger.warning(f"JSON extracted but parsing failed. Will retry. Error: {str(parse_error)}")
                        continue
                    else:
                        logger.error(f"Failed to parse extracted JSON after {parsing_retries} attempts")
                        raise parse_error
            else:
                # No JSON could be extracted
                if not parsing_retry_start_time:
                    parsing_retry_start_time = time.time()
                
                parsing_retries += 1
                if parsing_retries <= max_parsing_retries:
                    logger.warning(f"Could not extract JSON from response. Will retry parsing.")
                    continue
                else:
                    logger.error(f"Could not extract valid JSON from response after {parsing_retries} attempts")
                    raise Exception(f"No valid JSON found in response: {raw_response[:200]}...")
            
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
                
                logger.warning(f"Parsing error detected: {error_str}. Retry attempt {parsing_retries}/{max_parsing_retries} after {parsing_retry_delay:.2f}s delay")
                await asyncio.sleep(parsing_retry_delay)
                continue
            
            # Handle API call errors
            if is_gemini and api_retries < max_retries and ("api" in error_str.lower() or "400" in error_str):
                if not api_retry_start_time:
                    api_retry_start_time = time.time()
                
                api_retries += 1
                retry_delay = initial_retry_delay * (2 ** (api_retries - 1))
                
                logger.warning(f"Gemini API error: {error_str}. Retry attempt {api_retries}/{max_retries} after {retry_delay:.2f}s delay")
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
