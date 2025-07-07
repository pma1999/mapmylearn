import os
import logging
import re
import asyncio
import aiohttp
import io # Added for BytesIO
import fitz # Added for PyMuPDF
import json # Added for parsing Brave response
import threading # Added for thread-safe rate limiting
import time # Added for thread-safe rate limiting
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import BraveSearch # Replaced TavilySearch
from langchain_core.messages import AIMessage
from typing import Optional, Union, Tuple, Any, Dict, List
from bs4 import BeautifulSoup
import trafilatura # Added for HTML extraction

# Import official Google GenAI SDK for Grounding with Google Search
try:
    from google import genai
    from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    genai = None
    Tool = None
    GenerateContentConfig = None
    GoogleSearch = None
    logging.warning("google-genai SDK not available, Google Search grounding will be disabled")

# Import LangChain core components for Runnable interface
from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage

# Import LangSmith for tracing
try:
    from langsmith import traceable, Client as LangSmithClient
    from langsmith.run_trees import RunTree
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    traceable = None
    LangSmithClient = None
    RunTree = None
    logging.warning("LangSmith not available, tracing will be disabled for grounded LLM")

# Import models directly for runtime use
from backend.models.models import SearchServiceResult, ScrapedResult, GoogleSearchMetadata, LearningPathState

# Import key provider for type hints but with proper import protection
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.services.key_provider import KeyProvider, GoogleKeyProvider, BraveKeyProvider # Renamed TavilyKeyProvider
    # Keep models here for type checking if needed, but they are already imported above
    # from backend.models.models import SearchServiceResult, ScrapedResult
    from google.genai import Client as GenAIClient
    from google.genai.types import Tool as GenAITool

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
# TODO: Consider moving constants to a config file/object
SEARCH_SERVICE = "brave" # Updated from "tavily"
# Maximum characters to extract from scraped content (HTML or PDF)
MAX_SCRAPE_LENGTH = 100000
# Minimum content length threshold for Trafilatura fallback
TRAFILATURA_MIN_LENGTH_FALLBACK = 100
# Percentage of page height to consider as header/footer margin in PDF
PDF_HEADER_MARGIN_PERCENT = 0.10 # 10%
PDF_FOOTER_MARGIN_PERCENT = 0.10 # 10%

# --- New Constants for Scraping Enhancement ---
TARGET_SUCCESSFUL_SCRAPES = 3 # Desired minimum number of successful scrapes
FETCH_BUFFER = 3 # How many extra results to fetch beyond max_results
# --- End New Constants ---

# Shared rate limiter for Brave Search API (1 call per second)
# brave_search_rate_limiter = aiolimiter.AsyncLimiter(1, 1) # Removed

# Thread-safe rate limiter components for Brave Search
_brave_search_lock = threading.Lock()
_last_brave_call_time = 0.0

# --- Start of Modified PDF Helper Function ---
def _extract_pdf_text_sync(pdf_bytes: bytes, source_url: str) -> str:
    """Synchronous helper to extract text from PDF bytes using PyMuPDF block analysis.

    Attempts to extract text by analyzing blocks, filtering headers/footers,
    and sorting blocks by reading order. Falls back to simple page text extraction if
    block analysis fails or yields no content.

    Designed to be run in a thread executor.

    Args:
        pdf_bytes: The byte content of the PDF file.
        source_url: The original URL for logging context.

    Returns:
        The extracted and cleaned text content.

    Raises:
        ValueError: If the PDF is encrypted.
        fitz.fitz.FileDataError: If the PDF data is corrupted or invalid.
        RuntimeError: For other PyMuPDF or general exceptions during processing.
    """
    logger.debug(f"Starting PDF block analysis text extraction for {source_url}")
    all_text_content = ""
    extraction_method_used = "block_analysis" # Track method

    try:
        with fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf") as doc:
            if doc.is_encrypted:
                logger.warning(f"Skipping encrypted PDF: {source_url}")
                raise ValueError("PDF is encrypted")

            page_texts = []
            for page_num in range(len(doc)):
                page_text_blocks = []
                try:
                    page = doc.load_page(page_num)
                    page_rect = page.rect
                    page_height = page_rect.height
                    header_limit = page_rect.y0 + page_height * PDF_HEADER_MARGIN_PERCENT
                    footer_limit = page_rect.y1 - page_height * PDF_FOOTER_MARGIN_PERCENT

                    blocks = page.get_text("blocks", sort=False) # Get blocks with coordinates, no initial sort

                    # Filter headers/footers and empty blocks
                    filtered_blocks = [
                        b for b in blocks
                        if b[1] >= header_limit and b[3] <= footer_limit and b[4].strip() # y0>=header, y1<=footer, text exists
                    ]

                    # Sort by reading order (top-to-bottom, left-to-right)
                    filtered_blocks.sort(key=lambda b: (b[1], b[0])) # Sort by y0, then x0

                    page_text_blocks = [b[4].strip() for b in filtered_blocks] # Extract text

                    if page_text_blocks:
                        page_texts.append("\n".join(page_text_blocks)) # Join blocks with single newline

                except Exception as page_err:
                    logger.error(f"Error processing blocks on page {page_num+1} of PDF {source_url}: {page_err}", exc_info=False)
                    # For now, continue processing other pages.

            if page_texts:
                 all_text_content = "\n\n".join(page_texts) # Join pages with double newline

            # --- Fallback to simple page text extraction if block analysis yielded nothing ---
            if not all_text_content.strip():
                logger.warning(f"PDF block analysis yielded no text for {source_url}. Falling back to simple page extraction.")
                extraction_method_used = "page_text_fallback"
                all_text_fallback = []
                for page_num in range(len(doc)):
                     try:
                         page = doc.load_page(page_num)
                         page_text = page.get_text("text", sort=True).strip() # Simple text extraction
                         if page_text:
                             all_text_fallback.append(page_text)
                     except Exception as page_err:
                         logger.error(f"Error during fallback text extraction on page {page_num+1} of PDF {source_url}: {page_err}", exc_info=False)
                all_text_content = "\n\n".join(all_text_fallback)

            # --- Final Cleaning (Applied regardless of method) ---
            if all_text_content:
                # Corrected regex substitutions
                clean_text = re.sub(r'[ \t]*\n[ \t]*', '\n', all_text_content)
                clean_text = re.sub(r'\n{3,}', '\n\n', clean_text).strip()
                logger.debug(f"Successfully extracted text from PDF ({extraction_method_used}): {source_url}")
                return clean_text
            else:
                 logger.warning(f"No text could be extracted from PDF {source_url} using any method.")
                 return "" # Return empty string if no content found

    except (fitz.fitz.FileDataError, ValueError) as e:
        logger.error(f"Failed to process PDF {source_url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during PDF processing for {source_url}: {type(e).__name__} - {e}", exc_info=True)
        raise RuntimeError(f"Unexpected error during PDF processing: {type(e).__name__}") from e

# --- End of Modified PDF Helper Function ---


async def get_llm(key_provider=None, user=None):
    """
    Initialize the Google Gemini LLM with user-specific model selection.
    
    Args:
        key_provider: KeyProvider object for Google API key (or direct API key as string)
        user: User object for model selection (optional for backward compatibility)
        
    Returns:
        Initialized ChatGoogleGenerativeAI instance
    """
    google_api_key = None
    
    # Handle different input types
    if hasattr(key_provider, 'get_key') and callable(key_provider.get_key):
        # It's a KeyProvider
        try:
            google_api_key = await key_provider.get_key()
            logger.debug("Retrieved Google API key from provider")
        except Exception as e:
            logger.error(f"Error retrieving Google API key from provider: {str(e)}")
            raise
    elif isinstance(key_provider, str):
        # Direct API key
        google_api_key = key_provider
        logger.debug("Using provided Google API key directly")
    else:
        # Fallback to environment
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        if not google_api_key:
            logger.warning("GOOGLE_API_KEY not set in environment")
        else:
            logger.debug("Using Google API key from environment")
    
    if not google_api_key:
        raise ValueError("No Google API key available from any source")
    
    # Determine model based on user
    model = _get_model_for_user(user)
    
    try:
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=0.2,
            google_api_key=google_api_key,
            max_output_tokens=8192,
        )
    except Exception as e:
        logger.error(f"Error initializing ChatGoogleGenerativeAI: {str(e)}")
        raise

async def get_llm_for_evaluation(key_provider=None, user=None):
    """
    Initialize the Google Gemini LLM specifically for evaluations (research and content).
    Always uses gemini-2.0-flash regardless of user to ensure consistent evaluation quality.
    
    Args:
        key_provider: KeyProvider object for Google API key (or direct API key as string)
        user: User object (optional, not used for model selection in evaluations)
        
    Returns:
        Initialized ChatGoogleGenerativeAI instance with gemini-2.0-flash
    """
    google_api_key = None
    
    # Handle different input types
    if hasattr(key_provider, 'get_key') and callable(key_provider.get_key):
        # It's a KeyProvider
        try:
            google_api_key = await key_provider.get_key()
            logger.debug("Retrieved Google API key from provider for evaluation")
        except Exception as e:
            logger.error(f"Error retrieving Google API key from provider: {str(e)}")
            raise
    elif isinstance(key_provider, str):
        # Direct API key
        google_api_key = key_provider
        logger.debug("Using provided Google API key directly for evaluation")
    else:
        # Fallback to environment
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        if not google_api_key:
            logger.warning("GOOGLE_API_KEY not set in environment")
        else:
            logger.debug("Using Google API key from environment for evaluation")
    
    if not google_api_key:
        raise ValueError("No Google API key available from any source")
    
    # Always use gemini-2.0-flash for evaluations for consistency
    model = "gemini-2.0-flash"
    logger.info(f"Using gemini-2.0-flash for evaluation (user: {getattr(user, 'email', 'unknown')})")
    
    try:
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=0.2,
            google_api_key=google_api_key,
            max_output_tokens=8192,
        )
    except Exception as e:
        logger.error(f"Error initializing ChatGoogleGenerativeAI for evaluation: {str(e)}")
        raise

def _get_model_for_user(user):
    """
    Determine the appropriate Gemini model based on user.
    
    Args:
        user: User object containing id and email fields
        
    Returns:
        str: Model name to use
    """
    # Check if user is one of the special users who should get the preview model
    if user and (
        (hasattr(user, 'email') and user.email in ["pablomiguelargudo@gmail.com", "oscarvlc98@gmail.com"]) or
        (hasattr(user, 'id') and user.id in [1, 13])
    ):
        logger.info(f"Using special model gemini-2.5-flash-preview-05-20 for user {getattr(user, 'email', 'unknown')} (ID: {getattr(user, 'id', 'unknown')})")
        return "gemini-2.5-flash-preview-05-20"
    
    # Default model for all other users
    logger.debug(f"Using default model gemini-2.0-flash for user {getattr(user, 'email', 'unknown')} (ID: {getattr(user, 'id', 'unknown')})")
    return "gemini-2.0-flash"

def _is_premium_search_user(user):
    """
    Check if user is eligible for online search functionality.
    
    Args:
        user: User object containing id and email fields
        
    Returns:
        bool: True if user is eligible for online search, False otherwise
    """
    if user and (
        (hasattr(user, 'email') and user.email in ["pablomiguelargudo@gmail.com", "oscarvlc98@gmail.com"]) or
        (hasattr(user, 'id') and user.id in [1, 13])
    ):
        return True
    return False

async def _get_google_api_key(key_provider):
    """
    Extract Google API key from various sources.
    
    Args:
        key_provider: KeyProvider object, direct API key string, or None
        
    Returns:
        str: Google API key
        
    Raises:
        ValueError: If no valid API key is found
    """
    google_api_key = None
    
    # Handle different input types
    if hasattr(key_provider, 'get_key') and callable(key_provider.get_key):
        # It's a KeyProvider
        try:
            google_api_key = await key_provider.get_key()
            logger.debug("Retrieved Google API key from provider")
        except Exception as e:
            logger.error(f"Error retrieving Google API key from provider: {str(e)}")
            raise
    elif isinstance(key_provider, str):
        # Direct API key
        google_api_key = key_provider
        logger.debug("Using provided Google API key directly")
    else:
        # Fallback to environment
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        if not google_api_key:
            logger.warning("GOOGLE_API_KEY not set in environment")
        else:
            logger.debug("Using Google API key from environment")
    
    if not google_api_key:
        raise ValueError("No Google API key available from any source")
    
    return google_api_key

async def get_llm_with_search(key_provider=None, user=None) -> Union['GroundedGeminiWrapper', ChatGoogleGenerativeAI]:
    """
    Initialize Google Gemini with official Grounding with Google Search for premium users.
    Returns a wrapper that provides LangChain-compatible interface while using official Google GenAI SDK.
    Automatically falls back to regular LLM if search unavailable or user not premium.
    
    Args:
        key_provider: KeyProvider object for Google API key (or direct API key as string)
        user: User object for premium user validation and model selection
        
    Returns:
        Either a GroundedGeminiWrapper (for premium users) or regular ChatGoogleGenerativeAI instance
    """
    # Check if user is eligible for search functionality
    if not _is_premium_search_user(user):
        logger.debug(f"User {getattr(user, 'email', 'unknown')} not eligible for search, using regular LLM")
        return await get_llm(key_provider=key_provider, user=user)
    
    # Check if Google GenAI SDK is available
    if not GOOGLE_GENAI_AVAILABLE or genai is None:
        logger.warning("Google GenAI SDK not available, falling back to regular LLM")
        return await get_llm(key_provider=key_provider, user=user)
    
    try:
        # Get API key using helper function
        google_api_key = await _get_google_api_key(key_provider)
        
        # Determine model based on user
        model = _get_model_for_user(user)
        
        # Create Google GenAI client with grounding
        client = genai.Client(api_key=google_api_key)
        google_search_tool = Tool(google_search=GoogleSearch())
        
        logger.info(f"Initializing grounded LLM for premium user {getattr(user, 'email', 'unknown')} with model {model}")
        
        # Return wrapper that provides LangChain-compatible interface
        return GroundedGeminiWrapper(
            client=client,
            model=model,
            search_tool=google_search_tool,
            user=user
        )
        
    except Exception as e:
        logger.warning(f"Failed to initialize grounded LLM for user {getattr(user, 'email', 'unknown')}: {str(e)}. Falling back to regular LLM")
        # Fallback to regular LLM on any error
        return await get_llm(key_provider=key_provider, user=user)


class GroundedGeminiWrapper(Runnable[Any, AIMessage]):
    """
    Wrapper class that provides LangChain-compatible interface for Google GenAI SDK with grounding.
    Includes full LangSmith tracing for observability.
    This allows seamless integration with existing LangChain-based code while using official grounding.
    Inherits from Runnable to support LangChain chain composition with | operator.
    """
    
    def __init__(self, client: Optional['GenAIClient'], model: str, search_tool: Optional['GenAITool'], user=None):
        super().__init__()
        self.client = client
        self.model = model
        self.search_tool = search_tool
        self.user = user
        self.logger = logging.getLogger("GroundedGeminiWrapper")
        
        # Initialize LangSmith client for tracing
        self.langsmith_client = None
        if LANGSMITH_AVAILABLE and LangSmithClient:
            try:
                self.langsmith_client = LangSmithClient()
                self.logger.debug("LangSmith client initialized for grounded LLM tracing")
            except Exception as e:
                self.logger.warning(f"Failed to initialize LangSmith client: {e}")
                self.langsmith_client = None
    
    def invoke(self, input: Any, config=None, **kwargs) -> AIMessage:
        """
        Synchronous invoke method for LangChain compatibility.
        Delegates to ainvoke using asyncio.
        """
        import asyncio
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async method
        return loop.run_until_complete(self.ainvoke(input, config, **kwargs))
    
    async def ainvoke(self, input: Any, config=None, **kwargs) -> AIMessage:
        """
        LangChain-compatible async invoke method with full LangSmith tracing.
        Converts LangChain format to Google GenAI format and back.
        """
        # Extract langsmith_extra from kwargs if present
        langsmith_extra = kwargs.pop('langsmith_extra', {})
        
        # Create run tree for tracing if LangSmith is available
        run_tree = None
        if self.langsmith_client and LANGSMITH_AVAILABLE and RunTree:
            try:
                # Convert LangChain messages to input format for tracing
                if hasattr(input, 'messages'):
                    trace_inputs = {"messages": [msg.dict() if hasattr(msg, 'dict') else str(msg) for msg in input.messages]}
                elif isinstance(input, list):
                    trace_inputs = {"messages": [msg.dict() if hasattr(msg, 'dict') else str(msg) for msg in input]}
                else:
                    trace_inputs = {"messages": str(input)}
                
                # Add user context to metadata
                metadata = langsmith_extra.get('metadata', {})
                metadata.update({
                    'user_email': getattr(self.user, 'email', 'unknown'),
                    'user_id': getattr(self.user, 'id', 'unknown'),
                    'model': self.model,
                    'grounding_enabled': True,
                    'search_tool': 'google_search'
                })
                
                run_tree = RunTree(
                    name=langsmith_extra.get('name', 'GroundedGeminiLLM'),
                    run_type='llm',
                    inputs=trace_inputs,
                    metadata=metadata,
                    tags=langsmith_extra.get('tags', ['grounded', 'premium_user', 'google_search']),
                    project_name=langsmith_extra.get('project_name', os.environ.get('LANGSMITH_PROJECT', 'default'))
                )
                
                # Post the run to start tracing
                await asyncio.get_event_loop().run_in_executor(None, run_tree.post)
                self.logger.debug(f"Started LangSmith trace for grounded generation: {run_tree.id}")
                
            except Exception as e:
                self.logger.warning(f"Failed to create LangSmith trace: {e}")
                run_tree = None
        
        try:
            # Convert LangChain messages to Google GenAI format
            content = self._convert_langchain_to_genai_content(input)
            
            self.logger.debug(f"Converted content for grounded generation: {content[:200]}...")
            
            # Generate content with grounding and tracing
            response = await self._generate_with_grounding(content, run_tree)
            
            # Convert response back to LangChain format
            langchain_response = self._convert_genai_to_langchain_response(response)
            
            # Complete the trace if available
            if run_tree:
                try:
                    # Extract grounding metadata for trace
                    grounding_metadata = {}
                    search_queries_used = []
                    grounding_sources_count = 0
                    
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                            metadata = candidate.grounding_metadata
                            if hasattr(metadata, 'web_search_queries') and metadata.web_search_queries:
                                search_queries_used = metadata.web_search_queries
                                grounding_metadata['search_queries'] = search_queries_used
                                grounding_metadata['search_queries_count'] = len(search_queries_used)
                            if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                                grounding_sources_count = len(metadata.grounding_chunks)
                                grounding_metadata['grounding_sources'] = grounding_sources_count
                                grounding_metadata['grounding_chunks'] = [
                                    {
                                        'uri': chunk.web.uri if hasattr(chunk, 'web') and hasattr(chunk.web, 'uri') else 'unknown',
                                        'title': chunk.web.title if hasattr(chunk, 'web') and hasattr(chunk.web, 'title') else 'unknown'
                                    }
                                    for chunk in metadata.grounding_chunks[:5]  # Limit to first 5 for trace size
                                ]
                            if hasattr(metadata, 'search_entry_point') and metadata.search_entry_point:
                                if hasattr(metadata.search_entry_point, 'rendered_content'):
                                    grounding_metadata['search_suggestions'] = metadata.search_entry_point.rendered_content[:500]  # Limit length
                    
                    # Prepare outputs for trace
                    trace_outputs = {
                        'content': langchain_response.content,
                        'grounding_metadata': grounding_metadata,
                        'model_used': self.model
                    }
                    
                    # Add additional metadata from AIMessage if available
                    if hasattr(langchain_response, 'additional_kwargs') and langchain_response.additional_kwargs:
                        if 'grounding_metadata' in langchain_response.additional_kwargs:
                            trace_outputs['grounding_metadata'].update(langchain_response.additional_kwargs['grounding_metadata'])
                    
                    # Add usage data if available
                    if hasattr(response, 'usage_metadata') and response.usage_metadata:
                        usage = response.usage_metadata
                        trace_outputs['usage'] = {
                            'prompt_tokens': getattr(usage, 'prompt_token_count', 0),
                            'completion_tokens': getattr(usage, 'candidates_token_count', 0),
                            'total_tokens': getattr(usage, 'total_token_count', 0)
                        }
                    
                    run_tree.end(outputs=trace_outputs)
                    await asyncio.get_event_loop().run_in_executor(None, run_tree.patch)
                    self.logger.info(f"Completed LangSmith trace for grounded generation: {run_tree.id}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to complete LangSmith trace: {e}")
                    if run_tree:
                        try:
                            run_tree.end(outputs={'error': str(e)})
                            await asyncio.get_event_loop().run_in_executor(None, run_tree.patch)
                        except:
                            pass
            
            return langchain_response
            
        except Exception as e:
            self.logger.error(f"Error in grounded generation: {str(e)}")
            
            # Mark trace as failed if available
            if run_tree:
                try:
                    run_tree.end(outputs={'error': str(e)})
                    await asyncio.get_event_loop().run_in_executor(None, run_tree.patch)
                except:
                    pass
            
            # Log the grounding attempt but don't fail the entire request
            self.logger.warning("Grounding failed, this may affect response quality")
            raise
    
    def _convert_langchain_to_genai_content(self, input: Any) -> str:
        """Convert LangChain input to Google GenAI content format."""
        if not input:
            return ""
        
        # Handle different input types that LangChain might pass
        content_parts = []
        
        # Case 1: Input has a 'messages' attribute (like PromptValue)
        if hasattr(input, 'messages'):
            messages = input.messages
            for message in messages:
                if hasattr(message, 'content'):
                    content_parts.append(str(message.content))
                else:
                    content_parts.append(str(message))
        
        # Case 2: Input is a list of messages
        elif isinstance(input, list):
            for message in input:
                if hasattr(message, 'content'):
                    content_parts.append(str(message.content))
                else:
                    content_parts.append(str(message))
        
        # Case 3: Input is a dictionary (common in LangChain chains)
        elif isinstance(input, dict):
            # Look for common keys that contain messages
            if 'messages' in input:
                messages = input['messages']
                if isinstance(messages, list):
                    for message in messages:
                        if hasattr(message, 'content'):
                            content_parts.append(str(message.content))
                        else:
                            content_parts.append(str(message))
                else:
                    content_parts.append(str(messages))
            
            # Look for other common keys like 'input', 'text', 'query', etc.
            elif 'input' in input:
                content_parts.append(str(input['input']))
            elif 'text' in input:
                content_parts.append(str(input['text']))
            elif 'query' in input:
                content_parts.append(str(input['query']))
            else:
                # If it's a dict but no recognized keys, convert the whole thing
                content_parts.append(str(input))
        
        # Case 4: Input is a string or can be converted to string
        else:
            content_parts.append(str(input))
        
        return "\n".join(content_parts)
    
    async def _generate_with_grounding(self, content: str, run_tree=None):
        """Generate content using official Google GenAI SDK with grounding."""
        try:
            # Create child run for the actual LLM call if tracing
            llm_run = None
            if run_tree and LANGSMITH_AVAILABLE:
                try:
                    llm_run = run_tree.create_child(
                        name="GoogleGenAI_Grounded_Call",
                        run_type="llm",
                        inputs={"content": content, "model": self.model}
                    )
                    await asyncio.get_event_loop().run_in_executor(None, llm_run.post)
                except Exception as e:
                    self.logger.warning(f"Failed to create child run for LLM call: {e}")
                    llm_run = None
            
            # Use asyncio to run the synchronous client method
            loop = asyncio.get_event_loop()
            
            def _sync_generate():
                return self.client.models.generate_content(
                    model=self.model,
                    contents=content,
                    config=GenerateContentConfig(
                        tools=[self.search_tool],
                        response_modalities=["TEXT"],
                    )
                )
            
            # Run in thread executor to avoid blocking
            response = await loop.run_in_executor(None, _sync_generate)
            
            # Complete child run if available
            if llm_run:
                try:
                    # Extract actual response content for the child run
                    actual_content = ""
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                text_parts = []
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text'):
                                        text_parts.append(part.text)
                                actual_content = "".join(text_parts)
                    
                    llm_outputs = {
                        "response": actual_content if actual_content else "No content generated",
                        "grounded": True
                    }
                    
                    if hasattr(response, 'usage_metadata') and response.usage_metadata:
                        usage = response.usage_metadata
                        llm_outputs['usage'] = {
                            'prompt_tokens': getattr(usage, 'prompt_token_count', 0),
                            'completion_tokens': getattr(usage, 'candidates_token_count', 0),
                            'total_tokens': getattr(usage, 'total_token_count', 0)
                        }
                    
                    llm_run.end(outputs=llm_outputs)
                    await asyncio.get_event_loop().run_in_executor(None, llm_run.patch)
                except Exception as e:
                    self.logger.warning(f"Failed to complete child run: {e}")
            
            self.logger.info(f"Grounded generation completed for user {getattr(self.user, 'email', 'unknown')}")
            
            # Log grounding metadata if available
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    metadata = candidate.grounding_metadata
                    search_queries_count = 0
                    sources_count = 0
                    
                    if hasattr(metadata, 'web_search_queries') and metadata.web_search_queries:
                        search_queries_count = len(metadata.web_search_queries)
                        self.logger.info(f"Grounding used {search_queries_count} search queries: {metadata.web_search_queries}")
                    if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                        sources_count = len(metadata.grounding_chunks)
                        self.logger.info(f"Grounding found {sources_count} sources")
                    
                    if search_queries_count > 0 or sources_count > 0:
                        self.logger.info(f"Grounding summary: {search_queries_count} queries, {sources_count} sources")
                else:
                    self.logger.info("Grounding was enabled but no search metadata found")
            
            return response
            
        except Exception as e:
            # Complete child run with error if available
            if llm_run:
                try:
                    llm_run.end(outputs={'error': str(e)})
                    await asyncio.get_event_loop().run_in_executor(None, llm_run.patch)
                except:
                    pass
            
            self.logger.error(f"Error in grounded generation: {str(e)}")
            raise
    
    def _convert_genai_to_langchain_response(self, response):
        """Convert Google GenAI response to LangChain AIMessage format."""
        try:
            # Extract text content from response
            combined_text = ""
            grounding_metadata = {}
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        # Combine all text parts
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                text_parts.append(part.text)
                        
                        combined_text = "".join(text_parts)
                
                # Extract grounding metadata with detailed source information
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    metadata = candidate.grounding_metadata
                    
                    # Extract search queries
                    if hasattr(metadata, 'web_search_queries') and metadata.web_search_queries:
                        grounding_metadata['search_queries'] = metadata.web_search_queries
                        self.logger.debug(f"Extracted search queries: {metadata.web_search_queries}")
                    
                    # Extract grounding chunks with detailed source information
                    if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                        grounding_chunks = []
                        for chunk in metadata.grounding_chunks:
                            chunk_data = {}
                            
                            # Extract web source information
                            if hasattr(chunk, 'web') and chunk.web:
                                web_source = chunk.web
                                if hasattr(web_source, 'uri'):
                                    chunk_data['uri'] = web_source.uri
                                if hasattr(web_source, 'title'):
                                    chunk_data['title'] = web_source.title
                                
                                # Log each extracted source
                                self.logger.debug(f"Extracted source: {chunk_data.get('title', 'No title')} -> {chunk_data.get('uri', 'No URI')}")
                            
                            # Add chunk if we have at least a URI
                            if chunk_data.get('uri'):
                                grounding_chunks.append(chunk_data)
                        
                        grounding_metadata['grounding_chunks'] = grounding_chunks
                        grounding_metadata['grounding_sources'] = len(grounding_chunks)
                        
                        self.logger.info(f"Extracted {len(grounding_chunks)} sources from grounding metadata")
                    else:
                        grounding_metadata['grounding_sources'] = 0
                        self.logger.debug("No grounding chunks found in metadata")
            
            # Fallback if no content extracted
            if not combined_text:
                combined_text = str(response)
            
            # Return proper LangChain AIMessage with additional metadata
            additional_kwargs = {}
            if grounding_metadata:
                additional_kwargs['grounding_metadata'] = grounding_metadata
                self.logger.debug(f"Added grounding metadata to response: {grounding_metadata.keys()}")
            
            return AIMessage(
                content=combined_text,
                additional_kwargs=additional_kwargs
            )
            
        except Exception as e:
            self.logger.error(f"Error converting grounded response: {str(e)}", exc_info=True)
            # Return a basic AIMessage to avoid complete failure
            return AIMessage(
                content="Error processing grounded response",
                additional_kwargs={'error': str(e)}
            )

# =========================================================================
# Search Services Architecture for Hybrid Pipeline
# =========================================================================

class GoogleNativeSearchService:
    """
    Native Google Search service using official Google GenAI SDK with grounding.
    Provides search functionality without external scraping for premium users.
    Now enhanced with scraping capabilities to provide full content.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("GoogleNativeSearchService")
        
        if not GOOGLE_GENAI_AVAILABLE or genai is None:
            raise ValueError("Google GenAI SDK not available for native search service")
        
        # Initialize LangSmith client for search tracing
        self.langsmith_client = None
        if LANGSMITH_AVAILABLE and LangSmithClient:
            try:
                self.langsmith_client = LangSmithClient()
                self.logger.debug("LangSmith client initialized for Google Search native tracing")
            except Exception as e:
                self.logger.warning(f"Failed to initialize LangSmith client for search: {e}")
                self.langsmith_client = None
    
    async def perform_search(
        self, 
        query: str, 
        google_key_provider=None, 
        user=None,
        max_results: int = 5,
        scrape_timeout: int = 10,
        langsmith_extra: Dict[str, Any] = None,
        **kwargs
    ) -> 'SearchServiceResult':
        """
        Perform native Google Search using the official Google GenAI SDK.
        
        Args:
            query: The search query string
            google_key_provider: Provider for Google API key
            user: User object for model selection
            max_results: Maximum number of results (used for context in prompt)
            scrape_timeout: Timeout for scraping operations
            langsmith_extra: Additional metadata for LangSmith tracing
            **kwargs: Additional configuration parameters
            
        Returns:
            SearchServiceResult with native Google Search metadata
        """
        self.logger.info(f"Executing native Google Search for query: '{query}'")
        
        # Initialize LangSmith tracing for this search operation
        run_tree = None
        if self.langsmith_client and LANGSMITH_AVAILABLE and RunTree:
            try:
                # Prepare metadata for search tracing
                langsmith_extra = langsmith_extra or {}
                metadata = langsmith_extra.get('metadata', {})
                metadata.update({
                    'user_email': getattr(user, 'email', 'unknown'),
                    'user_id': getattr(user, 'id', 'unknown'),
                    'search_query': query,
                    'search_type': 'google_native_search',
                    'max_results': max_results,
                    'service': 'GoogleNativeSearchService'
                })
                
                run_tree = RunTree(
                    name=langsmith_extra.get('name', 'GoogleNativeSearch'),
                    run_type='tool',
                    inputs={'query': query, 'max_results': max_results},
                    metadata=metadata,
                    tags=langsmith_extra.get('tags', ['google_search', 'native_search', 'premium_feature']),
                    project_name=langsmith_extra.get('project_name', os.environ.get('LANGSMITH_PROJECT', 'default'))
                )
                
                # Post the run to start tracing
                await asyncio.get_event_loop().run_in_executor(None, run_tree.post)
                self.logger.debug(f"Started LangSmith trace for Google Search: {run_tree.id}")
                
            except Exception as e:
                self.logger.warning(f"Failed to create LangSmith trace for search: {e}")
                run_tree = None
        
        try:
            # Get Google API key
            google_api_key = await _get_google_api_key(google_key_provider)
            
            # Determine model based on user
            model = _get_model_for_user(user)
            
            # Create Google GenAI client
            client = genai.Client(api_key=google_api_key)
            
            # Create optimized search prompt
            search_prompt = f"""Conduct a comprehensive research search about: {query}

Instructions:
- Search for the most current, authoritative information available
- Focus on finding detailed, factual content that would be useful for educational purposes
- Gather information from diverse, credible sources
- Synthesize findings into a well-structured research summary
- Include specific details, examples, and key insights
- Prioritize recent information and established sources

Search Query: {query}"""
            
            # Create child run for the actual Google API call if tracing
            search_run = None
            if run_tree and LANGSMITH_AVAILABLE:
                try:
                    search_run = run_tree.create_child(
                        name="GoogleGenAI_Search_Call",
                        run_type="llm",
                        inputs={"query": query, "model": model, "prompt": search_prompt}
                    )
                    await asyncio.get_event_loop().run_in_executor(None, search_run.post)
                except Exception as e:
                    self.logger.warning(f"Failed to create child run for Google Search: {e}")
                    search_run = None
            
            # Execute search with grounding
            loop = asyncio.get_event_loop()
            
            def _sync_search():
                return client.models.generate_content(
                    model=model,
                    contents=search_prompt,
                    config=GenerateContentConfig(
                        tools=[Tool(google_search=GoogleSearch())],
                        response_modalities=["TEXT"],
                        temperature=0.1,  # Low temperature for factual research
                    )
                )
            
            # Run in thread executor to avoid blocking
            response = await loop.run_in_executor(None, _sync_search)
            
            # Complete child run if available
            if search_run:
                try:
                    # Extract response details for child run
                    search_outputs = {
                        "response_received": True,
                        "model_used": model
                    }
                    
                    # Add usage data if available
                    if hasattr(response, 'usage_metadata') and response.usage_metadata:
                        usage = response.usage_metadata
                        search_outputs['usage'] = {
                            'prompt_tokens': getattr(usage, 'prompt_token_count', 0),
                            'completion_tokens': getattr(usage, 'candidates_token_count', 0),
                            'total_tokens': getattr(usage, 'total_token_count', 0)
                        }
                    
                    search_run.end(outputs=search_outputs)
                    await asyncio.get_event_loop().run_in_executor(None, search_run.patch)
                except Exception as e:
                    self.logger.warning(f"Failed to complete child run for Google Search: {e}")
            
            # Process the response, now including scraping
            result = await self._process_google_response(response, query, scrape_timeout, run_tree)
            
            # Complete main trace if available
            if run_tree:
                try:
                    # Extract comprehensive trace outputs
                    trace_outputs = {
                        'search_query': query,
                        'sources_found': result.grounding_metadata.grounding_sources if result.grounding_metadata else 0,
                        'search_successful': not bool(result.search_provider_error),
                        'result_type': 'google_native_search'
                    }
                    
                    if result.grounding_metadata:
                        trace_outputs.update({
                            'search_queries_executed': result.grounding_metadata.web_search_queries,
                            'grounding_chunks': len(result.grounding_metadata.grounding_chunks),
                            'has_grounding_metadata': True
                        })
                    
                    if result.search_provider_error:
                        trace_outputs['error'] = result.search_provider_error
                    
                    run_tree.end(outputs=trace_outputs)
                    await asyncio.get_event_loop().run_in_executor(None, run_tree.patch)
                    self.logger.info(f"Completed LangSmith trace for Google Search: {run_tree.id}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to complete LangSmith trace for search: {e}")
                    if run_tree:
                        try:
                            run_tree.end(outputs={'error': str(e)})
                            await asyncio.get_event_loop().run_in_executor(None, run_tree.patch)
                        except:
                            pass
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in native Google Search for query '{query}': {str(e)}")
            
            # Mark trace as failed if available
            if run_tree:
                try:
                    run_tree.end(outputs={'error': str(e), 'search_successful': False})
                    await asyncio.get_event_loop().run_in_executor(None, run_tree.patch)
                except:
                    pass
            
            return SearchServiceResult(
                query=query,
                search_provider_error=f"Google Search native error: {str(e)}",
                is_native_google_search=True
            )
    
    def _extract_grounding_urls(self, response) -> List[Dict[str, str]]:
        """Extracts URLs and titles from Google Search grounding metadata.
        
        Note: URLs may be Google redirect URLs that will be resolved during scraping.
        """
        urls_info = []
        if not (hasattr(response, 'candidates') and response.candidates):
            return urls_info

        candidate = response.candidates[0]
        if not (hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata):
            return urls_info

        metadata = candidate.grounding_metadata
        if not (hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks):
            return urls_info

        redirect_count = 0
        for chunk in metadata.grounding_chunks:
            if hasattr(chunk, 'web') and chunk.web:
                web_source = chunk.web
                uri = getattr(web_source, 'uri', None)
                title = getattr(web_source, 'title', 'No Title')
                if uri:
                    urls_info.append({'url': uri, 'title': title})
                    # Log if this is a Google redirect URL
                    if _is_google_redirect_url(uri):
                        redirect_count += 1
                        self.logger.debug(f"Found Google redirect URL: {uri}")

        self.logger.info(f"Extracted {len(urls_info)} URLs from grounding metadata ({redirect_count} redirect URLs detected).")
        return urls_info

    async def _scrape_grounding_urls(self, urls_info: List[Dict[str, str]], scrape_timeout: int, run_tree=None) -> List[ScrapedResult]:
        """Scrapes a list of URLs extracted from Google Search grounding metadata."""
        if not urls_info:
            return []

        scraping_run = None
        if run_tree and LANGSMITH_AVAILABLE:
            try:
                scraping_run = run_tree.create_child(
                    name="GoogleSearch_Scraping",
                    run_type="tool",
                    inputs={"url_count": len(urls_info)}
                )
                await asyncio.get_event_loop().run_in_executor(None, scraping_run.post)
            except Exception as e:
                self.logger.warning(f"Failed to create scraping child run: {e}")
        
        processed_results = []
        async with aiohttp.ClientSession() as session:
            sem = asyncio.Semaphore(3)

            async def bounded_scrape(url_info: Dict):
                async with sem:
                    url = url_info['url']
                    title = url_info.get('title', 'No Title')
                    content, error = await _scrape_single_url(session, url, timeout=scrape_timeout)
                    return ScrapedResult(
                        title=title,
                        url=url,
                        search_snippet="Source found via Google Search grounding.",
                        scraped_content=content,
                        scrape_error=error
                    )

            tasks = [bounded_scrape(info) for info in urls_info]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, res in enumerate(results):
                if isinstance(res, Exception):
                    url_info = urls_info[i]
                    processed_results.append(ScrapedResult(
                        title=url_info.get('title', 'No Title'),
                        url=url_info['url'],
                        scrape_error=f"Scraping task failed: {str(res)}"
                    ))
                else:
                    processed_results.append(res)
        
        if scraping_run:
            successful_scrapes = sum(1 for r in processed_results if not r.scrape_error)
            scraping_run.end(outputs={"successful_scrapes": successful_scrapes, "failed_scrapes": len(processed_results) - successful_scrapes})
            await asyncio.get_event_loop().run_in_executor(None, scraping_run.patch)

        self.logger.info(f"Scraping completed for {len(processed_results)} grounding URLs. Successful: {successful_scrapes}/{len(processed_results)}.")
        return processed_results

    async def _process_google_response(self, response, query: str, scrape_timeout: int, run_tree=None) -> 'SearchServiceResult':
        """
        Processes Google GenAI response: extracts URLs, scrapes them, and formats the result.
        
        Args:
            response: Google GenAI response object
            query: Original search query
            scrape_timeout: Timeout for scraping individual URLs.
            run_tree: LangSmith run tree for tracing
            
        Returns:
            SearchServiceResult with extracted metadata and scraped content
        """
        # Create child run for response processing if tracing
        processing_run = None
        if run_tree and LANGSMITH_AVAILABLE:
            try:
                processing_run = run_tree.create_child(
                    name="GoogleSearch_Response_Processing",
                    run_type="parser",
                    inputs={"query": query, "has_response": bool(response)}
                )
                await asyncio.get_event_loop().run_in_executor(None, processing_run.post)
            except Exception as e:
                self.logger.warning(f"Failed to create processing child run: {e}")
                processing_run = None
        
        try:
            # 1. Extract URLs from grounding metadata
            urls_to_scrape = self._extract_grounding_urls(response)

            # 2. Scrape the extracted URLs
            scraped_results = await self._scrape_grounding_urls(urls_to_scrape, scrape_timeout, run_tree)

            # 3. Extract original text and metadata from Google's response
            content = ""
            grounding_metadata_obj = None
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                    content = "".join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
                
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    gm = candidate.grounding_metadata
                    grounding_metadata_obj = GoogleSearchMetadata(
                        grounding_chunks=[{'uri': c.web.uri, 'title': c.web.title} for c in gm.grounding_chunks if hasattr(c, 'web')],
                        web_search_queries=list(gm.web_search_queries) if hasattr(gm, 'web_search_queries') else [],
                        search_entry_point={'rendered_content': getattr(gm.search_entry_point, 'rendered_content', None)} if hasattr(gm, 'search_entry_point') else None,
                        grounding_sources=len(gm.grounding_chunks) if hasattr(gm, 'grounding_chunks') else 0
                    )
            
            # Prioritize successfully scraped content
            final_results = [res for res in scraped_results if res.scraped_content and not res.scrape_error]
            failed_results = [res for res in scraped_results if not res.scraped_content or res.scrape_error]
            
            # Fill with failed scrapes if we have space, to at least provide the source URL
            if len(final_results) < len(scraped_results):
                final_results.extend(failed_results[:len(scraped_results) - len(final_results)])

            if processing_run:
                processing_run.end(outputs={
                    'content_length': len(content), 
                    'sources_extracted': len(urls_to_scrape),
                    'successful_scrapes': len(final_results),
                    'processing_successful': True
                })
                await asyncio.get_event_loop().run_in_executor(None, processing_run.patch)

            return SearchServiceResult(
                query=query,
                results=final_results,
                search_provider_error=None,
                grounding_metadata=grounding_metadata_obj,
                is_native_google_search=True,
                native_response_content=content
            )

        except Exception as e:
            self.logger.error(f"Error processing Google Search response: {str(e)}")
            if processing_run:
                processing_run.end(outputs={'error': str(e), 'processing_successful': False})
                await asyncio.get_event_loop().run_in_executor(None, processing_run.patch)
            
            return SearchServiceResult(
                query=query,
                search_provider_error=f"Error processing Google Search response: {str(e)}",
                is_native_google_search=True
            )


class BraveSearchService:
    """
    Brave Search service wrapper around the existing perform_search_and_scrape functionality.
    Maintains compatibility with the current implementation for non-premium users.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("BraveSearchService")
    
    async def perform_search(
        self, 
        query: str, 
        brave_key_provider=None,
        max_results: int = 5,
        scrape_timeout: int = 10,
        **kwargs
    ) -> 'SearchServiceResult':
        """
        Perform Brave Search with scraping using existing implementation.
        
        Args:
            query: The search query string
            brave_key_provider: Provider for Brave Search API key
            max_results: Maximum number of search results
            scrape_timeout: Timeout for scraping operations
            **kwargs: Additional configuration parameters
            
        Returns:
            SearchServiceResult from Brave Search + scraping
        """
        self.logger.debug(f"Executing Brave Search + scraping for query: '{query}'")
        
        if not brave_key_provider:
            return SearchServiceResult(
                query=query,
                search_provider_error="Brave key provider not available",
                is_native_google_search=False
            )
        
        try:
            # Use existing perform_search_and_scrape function
            result = await perform_search_and_scrape(
                query=query,
                brave_key_provider=brave_key_provider,
                max_results=max_results,
                scrape_timeout=scrape_timeout
            )
            
            # Ensure is_native_google_search is set to False for Brave results
            result.is_native_google_search = False
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in Brave Search for query '{query}': {str(e)}")
            return SearchServiceResult(
                query=query,
                search_provider_error=f"Brave Search error: {str(e)}",
                is_native_google_search=False
            )


class SearchServiceRouter:
    """
    Router that automatically selects the appropriate search service based on user permissions.
    Implements the hybrid pipeline with automatic fallback mechanisms.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("SearchServiceRouter")
        self.google_service = None
        self.brave_service = BraveSearchService()
        
        # Initialize Google service only if available
        try:
            if GOOGLE_GENAI_AVAILABLE:
                self.google_service = GoogleNativeSearchService()
        except Exception as e:
            self.logger.warning(f"Google Native Search Service not available: {e}")
            self.google_service = None
    
    async def execute_search(
        self, 
        state: LearningPathState, 
        query: str, 
        search_config: Dict[str, Any] = None,
        langsmith_extra: Dict[str, Any] = None
    ) -> 'SearchServiceResult':
        """
        Execute search using the appropriate service based on user permissions.
        
        Args:
            state: LearningPathState containing user and key providers
            query: The search query string
            search_config: Configuration for search parameters
            langsmith_extra: Additional metadata for LangSmith tracing
            
        Returns:
            SearchServiceResult from the appropriate search service
        """
        if search_config is None:
            search_config = {}
        
        if langsmith_extra is None:
            langsmith_extra = {}
        
        user = state.get('user')
        
        # Check if user is eligible for Google Search native
        if _is_premium_search_user(user) and self.google_service:
            try:
                self.logger.info(f"Using Google Search native for premium user: {getattr(user, 'email', 'unknown')}")
                
                # Enhance LangSmith metadata for Google Search
                google_langsmith_extra = langsmith_extra.copy()
                google_metadata = google_langsmith_extra.get('metadata', {})
                google_metadata.update({
                    'search_service': 'google_native',
                    'user_type': 'premium',
                    'query_origin': google_langsmith_extra.get('query_origin', 'unknown'),
                    'operation_context': google_langsmith_extra.get('operation_context', 'search')
                })
                google_langsmith_extra['metadata'] = google_metadata
                
                # Update tags
                google_tags = google_langsmith_extra.get('tags', [])
                google_tags.extend(['google_search', 'native_search', 'premium_user'])
                google_langsmith_extra['tags'] = list(set(google_tags))  # Remove duplicates
                
                google_key_provider = state.get('google_key_provider')
                result = await self.google_service.perform_search(
                    query=query,
                    google_key_provider=google_key_provider,
                    user=user,
                    max_results=search_config.get('max_results', 5),
                    scrape_timeout=search_config.get('scrape_timeout', 10),
                    langsmith_extra=google_langsmith_extra
                )
                
                # Log success
                if not result.search_provider_error:
                    sources_count = len(result.results)
                    grounding_count = result.grounding_metadata.grounding_sources if result.grounding_metadata else 0
                    self.logger.info(f"Google Search completed: {sources_count} sources, {grounding_count} grounding chunks")
                
                return result
                
            except Exception as e:
                self.logger.warning(f"Google Search failed for user {getattr(user, 'email', 'unknown')}: {str(e)}. Falling back to Brave Search")
                # Continue to Brave Search fallback
        
        # Use Brave Search (default or fallback)
        self.logger.debug(f"Using Brave Search for user: {getattr(user, 'email', 'unknown')}")
        
        brave_key_provider = state.get('brave_key_provider')
        return await self.brave_service.perform_search(
            query=query,
            brave_key_provider=brave_key_provider,
            max_results=search_config.get('max_results', 5),
            scrape_timeout=search_config.get('scrape_timeout', 10)
        )
    
    @staticmethod
    def get_search_service_type(user) -> str:
        """
        Determine which search service type should be used for a user.
        
        Args:
            user: User object
            
        Returns:
            'google_native' for premium users, 'brave_scraping' for others
        """
        if _is_premium_search_user(user):
            return 'google_native'
        return 'brave_scraping'


# Global search router instance
_search_router = SearchServiceRouter()


async def execute_search_with_router(
    state: LearningPathState, 
    query: str, 
    search_config: Dict[str, Any] = None,
    langsmith_extra: Dict[str, Any] = None
) -> 'SearchServiceResult':
    """
    Convenience function to execute search using the global router.
    
    Args:
        state: LearningPathState containing user and key providers
        query: The search query string
        search_config: Configuration for search parameters
        langsmith_extra: Additional metadata for LangSmith tracing
        
    Returns:
        SearchServiceResult from the appropriate search service
    """
    return await _search_router.execute_search(state, query, search_config, langsmith_extra)

def _is_google_redirect_url(url: str) -> bool:
    """Check if URL is a Google redirect URL that needs to be resolved."""
    if not url:
        return False
    
    google_redirect_patterns = [
        'vertexaisearch.cloud.google.com/grounding-api-redirect/',
        'google.com/url?',
        'google.com/search?',
        'googleusercontent.com/url?'
    ]
    
    return any(pattern in url for pattern in google_redirect_patterns)

async def _resolve_google_redirect_url(session: aiohttp.ClientSession, redirect_url: str, timeout: int) -> Tuple[str, Optional[str]]:
    """Resolve a Google redirect URL to get the real destination URL.
    
    Args:
        session: The aiohttp client session.
        redirect_url: The Google redirect URL to resolve.
        timeout: Request timeout in seconds.
        
    Returns:
        A tuple containing (resolved_url, error_message).
        If resolution fails, returns (original_url, error_message).
    """
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; LearniBot/1.0; +https://learni.com/bot)'}
    
    try:
        logger.debug(f"Resolving Google redirect URL: {redirect_url}")
        
        # Use HEAD request to follow redirects without downloading content
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        async with session.head(redirect_url, timeout=timeout_obj, headers=headers, ssl=False, allow_redirects=True) as response:
            # The final URL after all redirects
            final_url = str(response.url)
            
            # Verify we got a different URL
            if final_url != redirect_url:
                logger.info(f"Resolved Google redirect: {redirect_url} -> {final_url}")
                return final_url, None
            else:
                logger.warning(f"Google redirect resolution didn't change URL: {redirect_url}")
                return redirect_url, "URL resolution didn't produce a different URL"
                
    except asyncio.TimeoutError:
        logger.warning(f"Timeout resolving Google redirect URL: {redirect_url}")
        return redirect_url, f"Timeout resolving redirect after {timeout}s"
    except aiohttp.ClientError as e:
        logger.warning(f"Client error resolving Google redirect URL {redirect_url}: {type(e).__name__}")
        return redirect_url, f"Client error resolving redirect: {type(e).__name__}"
    except Exception as e:
        logger.error(f"Unexpected error resolving Google redirect URL {redirect_url}: {type(e).__name__} - {e}")
        return redirect_url, f"Unexpected error resolving redirect: {type(e).__name__}"

# --- Start of Modified _scrape_single_url ---
async def _scrape_single_url(session: aiohttp.ClientSession, url: str, timeout: int) -> Tuple[Optional[str], Optional[str]]:
    """Scrapes cleaned textual content from a single URL (HTML or PDF).

    Prioritizes using Trafilatura for HTML and block analysis for PDF, with fallbacks.
    Cleans the content THEN truncates to MAX_SCRAPE_LENGTH.
    Now includes Google redirect URL resolution.

    Args:
        session: The aiohttp client session.
        url: The URL to scrape.
        timeout: Request timeout in seconds.

    Returns:
        A tuple containing (cleaned_scraped_content, error_message).
        cleaned_scraped_content is None if an error occurred or no content found after cleaning.
        error_message contains details if scraping or processing failed.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; LearniBot/1.0; +https://learni.com/bot)'} # Example Bot UA
    clean_text: Optional[str] = None
    error_message: Optional[str] = None
    
    # Resolve Google redirect URLs first
    actual_url = url
    if _is_google_redirect_url(url):
        logger.info(f"Detected Google redirect URL, resolving: {url}")
        resolved_url, resolve_error = await _resolve_google_redirect_url(session, url, timeout)
        if resolve_error:
            logger.warning(f"Failed to resolve Google redirect URL {url}: {resolve_error}")
            # Continue with original URL but log the issue
            actual_url = url
        else:
            actual_url = resolved_url
            logger.info(f"Successfully resolved Google redirect: {url} -> {actual_url}")

    try:
        logger.debug(f"Attempting to scrape URL: {actual_url}")
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        async with session.get(actual_url, timeout=timeout_obj, headers=headers, ssl=False) as response:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            
            # --- PDF Handling ---
            if "application/pdf" in content_type:
                logger.debug(f"Detected PDF content type for: {url}")
                extraction_method_used = "pdf_block_analysis" # Default assumption
                try:
                    pdf_bytes = await response.read()
                    if not pdf_bytes:
                        logger.warning(f"Received empty response body for PDF: {url}")
                        return None, "Received empty PDF content"

                    loop = asyncio.get_running_loop()
                    clean_text = await loop.run_in_executor(
                        None, _extract_pdf_text_sync, pdf_bytes, url
                    )
                    # _extract_pdf_text_sync now returns empty string if no content, not None
                    if not clean_text:
                         logger.warning(f"PDF extraction yielded no content for {url}")
                         error_message = "No text content extracted from PDF"
                         # clean_text remains "" (empty string) which evaluates as False later
                    else:
                         error_message = None # Success

                except ValueError as ve: # Specific encryption error
                    logger.warning(f"Skipping encrypted PDF {url}: {ve}")
                    clean_text = None
                    error_message = "Skipped: PDF is encrypted"
                    extraction_method_used = "pdf_error_encrypted"
                except (fitz.fitz.FileDataError, RuntimeError) as pdf_err: # Specific processing errors
                    logger.error(f"PDF processing failed for {url}: {pdf_err}")
                    clean_text = None
                    error_message = f"PDF processing error: {type(pdf_err).__name__}"
                    extraction_method_used = "pdf_error_processing"
                except asyncio.CancelledError:
                    logger.warning(f"PDF processing cancelled for {url}")
                    raise
                except Exception as e: # Catch-all for read/executor errors
                    logger.error(f"Error handling PDF content for {url}: {type(e).__name__} - {e}", exc_info=True)
                    clean_text = None
                    error_message = f"Error reading/processing PDF: {type(e).__name__}"
                    extraction_method_used = "pdf_error_unknown"

            # --- HTML Handling ---
            elif "text/html" in content_type:
                logger.debug(f"Detected HTML content type for: {url}")
                extraction_method_used = "trafilatura" # Default assumption
                try:
                    html_content = await response.text()

                    # Attempt extraction with Trafilatura first
                    extracted_text = trafilatura.extract(
                        html_content,
                        include_comments=False, # Don't include comments
                        include_tables=True,    # Include table content if relevant
                        # favor_recall=True,    # Consider if more content is desired at risk of noise
                    )

                    # Check if Trafilatura result is usable
                    if extracted_text and len(extracted_text) >= TRAFILATURA_MIN_LENGTH_FALLBACK:
                        clean_text = extracted_text
                        logger.debug(f"Using Trafilatura extracted content for {url}")
                    else:
                        # Fallback to BeautifulSoup method if Trafilatura failed or got too little
                        extraction_method_used = "beautifulsoup_fallback"
                        logger.warning(f"Trafilatura yielded insufficient content (<{TRAFILATURA_MIN_LENGTH_FALLBACK} chars) for {url}. Falling back to BeautifulSoup.")
                        soup = BeautifulSoup(html_content, 'lxml') # Use lxml parser
                        # Remove common noise tags more aggressively
                        for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'form', 'button', 'input', 'textarea', 'select', 'option', 'label', 'iframe', 'noscript', 'figure', 'figcaption']):
                            tag.decompose()

                        # Find main content areas (add more selectors if needed)
                        main_content = soup.find('main') or \
                                       soup.find('article') or \
                                       soup.find('div', role='main') or \
                                       soup.find('div', id='content') or \
                                       soup.find('div', class_=re.compile(r'\b(content|main|body|article)\b', re.I)) # More flexible class search

                        target_element = main_content if main_content else soup.find('body')

                        if target_element:
                            clean_text = target_element.get_text(separator='\n', strip=True)
                        else:
                            # Extremely unlikely fallback
                            logger.error(f"Could not find body or main content element for HTML fallback: {url}")
                            clean_text = None # Mark as failure
                            error_message = "HTML parsing failed: No body/main element found"

                    # Apply final cleaning steps to text from either method
                    if clean_text:
                        # Corrected regex substitutions
                        clean_text = re.sub(r'[ \t]*\n[ \t]*', '\n', clean_text)
                        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text).strip()
                        logger.info(f"Successfully extracted text from HTML ({extraction_method_used}): {url}")
                        error_message = None # Reset error on success
                    elif not error_message: # If clean_text became None/empty without an explicit error set
                         logger.warning(f"HTML processing ({extraction_method_used}) resulted in empty content for {url}")
                         error_message = "No text content extracted from HTML"

                except Exception as html_err:
                    logger.error(f"Error processing HTML content ({extraction_method_used}) for {url}: {type(html_err).__name__} - {html_err}", exc_info=True)
                    clean_text = None
                    error_message = f"Error processing HTML: {type(html_err).__name__}"
                    extraction_method_used = "html_error_unknown"

            # --- Other Content Types ---
            else:
                logger.warning(f"Skipping unsupported content type '{content_type}' for URL: {url}")
                clean_text = None
                error_message = f"Skipped: Unsupported content type ({content_type})"
                extraction_method_used = "skipped_content_type"

            # --- Truncation (Applied AFTER cleaning if text exists) ---
            if clean_text is not None and len(clean_text) > MAX_SCRAPE_LENGTH:
                logger.debug(f"Truncating content ({extraction_method_used}) for {url} from {len(clean_text)} chars to {MAX_SCRAPE_LENGTH}")
                clean_text = clean_text[:MAX_SCRAPE_LENGTH] + "... (truncated)"
            elif clean_text == "": # Handle case where cleaning resulted in empty string but no error
                clean_text = None # Treat as no content found
                if not error_message: # Avoid overwriting specific errors
                     error_message = "No text content found after cleaning"

            # Return the cleaned (and possibly truncated) text
            return clean_text, error_message

    except asyncio.TimeoutError:
        logger.warning(f"Scrape timed out for {url} after {timeout}s")
        return None, f"Scrape timed out after {timeout}s"
    except aiohttp.ClientResponseError as e:
        logger.warning(f"HTTP error scraping {url}: {e.status} {e.message}")
        return None, f"HTTP error: {e.status} ({e.message})"
    except aiohttp.ClientError as e: # Includes connection errors etc.
        logger.warning(f"Client error scraping {url}: {type(e).__name__}")
        return None, f"Scraping client error: {type(e).__name__}"
    except Exception as e:
        logger.error(f"Unexpected error during initial scrape request for {url}: {type(e).__name__} - {str(e)}", exc_info=True)
        return None, f"Unexpected scraping error: {type(e).__name__}"
# --- End of Modified _scrape_single_url ---


async def perform_search_and_scrape(
    query: str,
    brave_key_provider: 'BraveKeyProvider', # Renamed provider
    max_results: int = 5,
    scrape_timeout: int = 10
) -> 'SearchServiceResult':
    """Performs Brave search and scrapes results concurrently. # Updated docstring

    Args:
        query: The search query.
        brave_key_provider: The key provider instance for Brave Search. # Updated docstring
        max_results: Maximum number of search results to retrieve from Brave. # Updated docstring
        scrape_timeout: Timeout in seconds for each scrape request.

    Returns:
        A SearchServiceResult object containing the query, scraped results,
        and any potential errors.
    """
    logger.info(f"Performing search and scrape for query: '{query}' using Brave Search")
    service_result = SearchServiceResult(query=query)
    api_key = None

    try:
        api_key = await brave_key_provider.get_key()
        # Calculate the number of results to fetch including the buffer
        fetch_count = max_results + FETCH_BUFFER
        logger.debug(f"Requesting {fetch_count} search results (max_results={max_results}, buffer={FETCH_BUFFER}) for query: '{query}'")

        # Use BraveSearch.from_api_key and pass fetch_count via search_kwargs
        brave_search = BraveSearch.from_api_key(
            api_key=api_key,
            search_kwargs={"count": fetch_count} # Use fetch_count here
        )

        # --- Thread-safe Rate Limiting --- 
        global _last_brave_call_time # Needed to modify the global variable
        required_delay = 0.0 # Initialize delay
        wait_until_time = 0.0 # Initialize scheduled start time

        logger.debug(f"Acquiring thread lock for Brave search rate limit check: '{query}'")
        with _brave_search_lock: # Acquire thread-safe lock only for time check/update
            current_time = time.monotonic()
            # Calculate the earliest time this call can start (1.05s after the last scheduled start)
            wait_until_time = max(current_time, _last_brave_call_time + 1.05) # Added 50ms buffer
            # Calculate the delay needed from the current time
            required_delay = wait_until_time - current_time
            # Update the global last call time to reserve the slot for *this* call
            _last_brave_call_time = wait_until_time
            logger.debug(f"Rate limit: Current time: {current_time:.2f}, Last scheduled: {_last_brave_call_time:.2f}, Wait until: {wait_until_time:.2f}, Delay: {required_delay:.2f}s. Lock released.")
        # --- Lock is released --- 

        # Perform wait *outside* the lock using asyncio.sleep
        if required_delay > 0:
            logger.info(f"Rate limiting Brave search. Waiting {required_delay:.2f} seconds...")
            await asyncio.sleep(required_delay) # Use asyncio.sleep for cooperative multitasking

        # --- Make the actual call (no lock held here) ---
        logger.debug(f"Rate limit wait complete. Invoking Brave search: '{query}'")
        try:
            brave_response_str = await brave_search.ainvoke({"query": query})
        except Exception as invoke_err:
             logger.error(f"Error during brave_search.ainvoke for '{query}': {invoke_err}", exc_info=True)
             # Add error to result and return, or raise depending on desired behavior
             service_result.search_provider_error = f"Invoke Error: {str(invoke_err)}"
             return service_result # Example: return error result
             # raise # Alternatively, re-raise the exception
        # --- End Rate Limiting Logic & Call ---

        logger.debug(f"Received Brave response for: '{query}'")

        # Parse the JSON string response from Brave
        try:
            brave_results_list = json.loads(brave_response_str)
            if not isinstance(brave_results_list, list):
                 raise ValueError("Brave search response is not a list")
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            error_msg = f"Brave search returned invalid JSON or unexpected format: {e}. Response: {brave_response_str[:500]}..."
            logger.error(error_msg)
            service_result.search_provider_error = error_msg
            return service_result

        scrape_tasks = []
        # Process the parsed list from Brave
        # Rename tavily_result_map -> search_result_map
        search_result_map = {} 
        urls_to_scrape = []

        for result in brave_results_list:
            # Brave uses 'link' for URL and 'snippet' for content snippet
            if isinstance(result, dict) and "link" in result and result["link"] and "title" in result and "snippet" in result:
                url = result["link"]
                if url not in urls_to_scrape:
                    urls_to_scrape.append(url)
                    # Store the necessary mapped info
                    search_result_map[url] = {
                        "url": url, 
                        "title": result.get("title"), 
                        "search_snippet": result.get("snippet") # Map brave 'snippet' to internal 'search_snippet'
                    }
            else:
                logger.warning(f"Skipping invalid or incomplete Brave Search result item: {result}")

        if not urls_to_scrape:
            logger.warning(f"No valid URLs found in Brave Search results for query '{query}'")
            return service_result

        logger.debug(f"Prepared {len(urls_to_scrape)} unique URLs for scraping.")
        scraped_data_map = {}

        async with aiohttp.ClientSession() as session:
            for url in urls_to_scrape:
                task = asyncio.create_task(
                    _scrape_single_url(session, url, scrape_timeout),
                    name=f"scrape_{url}"
                )
                scrape_tasks.append((url, task))

            logger.debug(f"Gathering results for {len(scrape_tasks)} scraping tasks.")
            scrape_results_tuples = await asyncio.gather(*(task for _, task in scrape_tasks), return_exceptions=True)
            logger.debug(f"Completed gathering scrape results.")

            for i, (url, _) in enumerate(scrape_tasks):
                scrape_outcome = scrape_results_tuples[i]
                if isinstance(scrape_outcome, Exception):
                    if isinstance(scrape_outcome, asyncio.CancelledError):
                        logger.warning(f"Scraping task for {url} was cancelled.")
                        scraped_data_map[url] = (None, "Scraping task cancelled")
                    else:
                        logger.error(f"Gather caught exception for scrape task {url}: {scrape_outcome}", exc_info=isinstance(scrape_outcome, Exception))
                        scraped_data_map[url] = (None, f"Gather error: {type(scrape_outcome).__name__}")
                elif isinstance(scrape_outcome, tuple) and len(scrape_outcome) == 2:
                    scraped_data_map[url] = scrape_outcome
                else:
                    logger.error(f"Unexpected scrape outcome type for {url}: {type(scrape_outcome)} - {scrape_outcome}")
                    scraped_data_map[url] = (None, f"Unexpected scrape result type: {type(scrape_outcome).__name__}")

        # --- Start Prioritization Logic ---
        successful_scrapes = []
        failed_scrapes = []

        # Populate successful_scrapes and failed_scrapes lists
        for url in urls_to_scrape: # Iterate through all fetched URLs
            search_info = search_result_map.get(url)
            if search_info:
                content, error = scraped_data_map.get(url, (None, "Scraping task result missing"))
                # Treat empty string "" as failure too
                if content: # Check if content is not None and not empty string
                    successful_scrapes.append((url, search_info, content))
                else:
                    # Ensure error string is present, provide default if None
                    error_msg = error if error is not None else "No content found or scrape failed"
                    failed_scrapes.append((url, search_info, error_msg))

        logger.debug(f"Scraping yielded {len(successful_scrapes)} successful scrapes and {len(failed_scrapes)} failed scrapes out of {len(urls_to_scrape)} attempted.")

        final_scraped_results_data = []

        # 1. Add successful scrapes up to TARGET_SUCCESSFUL_SCRAPES, capped by max_results
        num_successful_added = 0
        for url, search_info, content in successful_scrapes:
            # Check if we've reached the overall max_results limit for the final list
            if len(final_scraped_results_data) < max_results:
                # Prioritize adding successful scrapes until the target is met OR max_results is hit
                if num_successful_added < TARGET_SUCCESSFUL_SCRAPES:
                    final_scraped_results_data.append(
                        ScrapedResult(
                            title=search_info.get("title"),
                            url=url,
                            search_snippet=search_info.get("search_snippet"),
                            scraped_content=content,
                            scrape_error=None
                        )
                    )
                    num_successful_added += 1
                else:
                    # If target met, only add more successful ones if space allows
                    # (This case might be less common if max_results is close to target)
                    pass # Optionally add more successful ones here if needed up to max_results
            else:
                break # Stop if we hit max_results cap

        # If target was not met, add remaining successful scrapes up to max_results
        successful_added_beyond_target = 0
        if num_successful_added < TARGET_SUCCESSFUL_SCRAPES:
            for url, search_info, content in successful_scrapes[num_successful_added:]: # Start from where we left off
                if len(final_scraped_results_data) < max_results:
                    final_scraped_results_data.append(
                        ScrapedResult(
                            title=search_info.get("title"),
                            url=url,
                            search_snippet=search_info.get("search_snippet"),
                            scraped_content=content,
                            scrape_error=None
                        )
                    )
                    successful_added_beyond_target += 1
                else:
                    break # Stop if max_results is reached

        total_successful_added = num_successful_added + successful_added_beyond_target
        logger.debug(f"Added {total_successful_added} successful scrapes to the final list (Target: {TARGET_SUCCESSFUL_SCRAPES}).")


        # 2. Fill remaining slots up to max_results with failed scrapes (for snippets/errors)
        remaining_slots = max_results - len(final_scraped_results_data)
        num_failed_added = 0
        if remaining_slots > 0:
            for url, search_info, error in failed_scrapes:
                 if num_failed_added < remaining_slots:
                     final_scraped_results_data.append(
                         ScrapedResult(
                             title=search_info.get("title"),
                             url=url,
                             search_snippet=search_info.get("search_snippet"),
                             scraped_content=None,
                             scrape_error=error
                         )
                     )
                     num_failed_added += 1
                 else:
                     break # Stop if we fill the remaining slots

        logger.debug(f"Added {num_failed_added} failed scrapes to fill remaining {remaining_slots} slots (cap: {max_results}).")

        # Assign the prioritized list to the service result
        service_result.results = final_scraped_results_data
        # --- End Prioritization Logic ---

        logger.info(f"Successfully processed search and scrape for query: '{query}', returning {len(service_result.results)} prioritized results.")

    except aiohttp.ClientError as http_err:
        logger.exception(f"Network error during Brave Search/scrape for query '{query}': {http_err}")
        service_result.search_provider_error = f"Network Error: {type(http_err).__name__}"
    except Exception as e:
        logger.exception(f"General error during search/scrape for query '{query}': {e}")
        if api_key is None and isinstance(e, (ValueError, AttributeError)): 
             service_result.search_provider_error = f"Key Provider Error: {type(e).__name__}: {str(e)}"
             logger.error(f"Failed to retrieve Brave Search API key: {e}") # Updated message
        elif api_key and ("401" in str(e) or "Unauthorized" in str(e)): # Check for common auth failure
             service_result.search_provider_error = "Brave Search API key seems invalid (401 Unauthorized)" # Updated message
             logger.error(service_result.search_provider_error)
        else: 
             service_result.search_provider_error = f"{type(e).__name__}: {str(e)}"

    return service_result

def validate_google_key(api_key):
    """
    Validate if the Google API key is functional.
    
    Args:
        api_key: Google API key to validate
        
    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    # Initial format validation
    if not api_key or not isinstance(api_key, str):
        return False, "API key must be a non-empty string"
    
    # Google API key format validation
    pattern = r'^AIza[0-9A-Za-z_-]{35}$'
    if not re.match(pattern, api_key):
        return False, "Invalid Google API key format - must start with 'AIza' followed by 35 characters"
    
    try:
        # Minimal test to validate key functionality
        llm = ChatGoogleGenerativeAI(
            temperature=0,
            model="gemini-2.0-flash",
            google_api_key=api_key,
            max_output_tokens=5
        )
        llm.invoke("test")
        return True, None
    except Exception as e:
        error_str = str(e)
        logger.warning(f"Google API key validation failed: {error_str}") # Log warning
        
        # Check for specific error cases
        if "invalid api key" in error_str.lower():
            return False, "Invalid Google API key format or key not activated"
        
        if "permission" in error_str.lower() or "access" in error_str.lower():
            return False, "API key error: Insufficient permissions or access denied"
        
        if "quota" in error_str.lower() or "limit" in error_str.lower():
            return False, "API key error: Quota exceeded or rate limits reached"
        
        # Default error message
        return False, f"API key validation failed: Check key and permissions."

async def validate_brave_key(api_key: str) -> Tuple[bool, Optional[str]]: # Renamed function
    """Validate if the Brave Search API key is correctly formatted and functional.""" # Updated docstring
    if not api_key or not isinstance(api_key, str):
        return False, "API key must be a non-empty string"

    # No standard prefix check for Brave keys based on docs

    try:
        # Minimal test call to Brave Search API
        search = BraveSearch.from_api_key(api_key=api_key) # Use BraveSearch
        # Use a simple, common query
        await search.ainvoke({"query": "test"}) 
        return True, None
    except Exception as e:
        error_str = str(e)
        logger.warning(f"Brave Search API key validation failed: {error_str}") # Updated message

        # Provide clearer error messages based on common issues for Brave (adapt as needed)
        # Langchain might wrap HTTP errors, check the error message content
        if "401" in error_str or "Unauthorized" in error_str or "invalid api key" in error_str.lower():
            return False, "API key error: Unauthorized. The Brave Search API key is likely invalid or revoked." # Updated message
        # Add checks for other potential Brave errors if known (e.g., 400, rate limits)
        # if "400" in error_str ... :
        #     return False, "API key validation returned Bad Request (400). Check Brave API status or query format."
        if "rate limit" in error_str.lower():
            return False, "API key error: Rate limit exceeded."
        if "connection error" in error_str.lower() or "cannot connect" in error_str.lower():
            return False, "Network error during API key validation. Check connectivity."

        # Default error message for other exceptions
        return False, f"API key validation failed: {type(e).__name__}. Check key and Brave Search service status." # Updated message
