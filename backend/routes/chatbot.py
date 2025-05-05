import logging
import functools # <-- Import functools
import datetime # Add datetime import
import uuid # Add uuid import
import time # Import time for manual rate limiting
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
import os # Import os
import redis.asyncio as redis
from datetime import datetime, timedelta, timezone # Import timezone

# Langchain & LangGraph imports
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.memory import MemorySaver # Using memory saver for now
from fastapi_limiter import FastAPILimiter # Import FastAPILimiter

# Local imports
from backend.config.database import get_db
from backend.models.auth_models import User, LearningPath, TransactionType # Import TransactionType
from backend.schemas.chatbot_schemas import ChatRequest, ChatResponse, ClearChatRequest
from backend.utils.auth_middleware import get_current_user
from backend.services.services import get_llm # Assuming user API key is available via user model or context
from backend.prompts.learning_path_prompts import CHATBOT_SYSTEM_PROMPT
from backend.services.credit_service import CreditService # Import CreditService

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

logger = logging.getLogger(__name__)

# --- Redis Client (Ensuring it's the same one FastAPI Limiter uses) ---
redis_client = None
try:
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        # Use the same redis instance as initialized in api.py for FastAPILimiter
        # Assuming FastAPILimiter.redis holds the initialized client after startup
        # We access it via the singleton instance if needed, or just use a new connection
        # from the same URL for manual checks.
        redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        logger.info("Chatbot Redis client (re)initialized for manual checks.")
    else:
        logger.warning("REDIS_URL not set. Chatbot allowance purchase AND rate limiting will not work.")
except Exception as e:
    logger.error(f"Failed to initialize Redis client for chatbot manual checks: {e}")
    # redis_client will remain None

# --- Configuration Constants (Read from environment) ---
try:
    CHAT_ALLOWANCE_COST = int(os.getenv("CHAT_ALLOWANCE_COST", "10"))
    CHAT_ALLOWANCE_MESSAGES = int(os.getenv("CHAT_ALLOWANCE_MESSAGES", "100"))
    CHAT_FREE_LIMIT_PER_DAY = int(os.getenv("CHAT_FREE_LIMIT_PER_DAY", "100")) # Read free limit here
except ValueError:
    logger.error("Invalid value for CHAT_ALLOWANCE_COST, CHAT_ALLOWANCE_MESSAGES, or CHAT_FREE_LIMIT_PER_DAY in environment. Using defaults.")
    CHAT_ALLOWANCE_COST = 10
    CHAT_ALLOWANCE_MESSAGES = 100
    CHAT_FREE_LIMIT_PER_DAY = 100

# --- Helper function to convert language code to full language name --- #
def get_full_language_name(language_code):
    """
    Convert an ISO 639-1 language code to its full language name.
    """
    language_map = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arabic",
        "hi": "Hindi",
        "bn": "Bengali",
        "pa": "Punjabi",
        "jv": "Javanese",
        "id": "Indonesian",
        "tr": "Turkish",
        "vi": "Vietnamese",
        "pl": "Polish",
        "uk": "Ukrainian",
        "nl": "Dutch",
        "el": "Greek",
        "cs": "Czech",
        "sv": "Swedish",
        "hu": "Hungarian",
        "fi": "Finnish",
        "no": "Norwegian",
        "da": "Danish",
        "th": "Thai",
        "he": "Hebrew",
        "ca": "Catalan"
    }
    
    # Handle more specific language codes with regions (e.g., "pt-BR")
    if "-" in language_code:
        base_code = language_code.split("-")[0]
        if base_code in language_map:
            return language_map[base_code]
    
    # Return the full name if found in the map, otherwise return the original code
    return language_map.get(language_code, language_code)

# --- Helper function to format path structure --- #
def format_path_structure(path_data):
    structure = []
    topic = path_data.get('topic', 'N/A')
    structure.append(f"Course: {topic}")
    modules = path_data.get('modules', [])
    for i, module in enumerate(modules):
        module_title = module.get('title', f'Module {i+1}')
        structure.append(f"  Module {i+1}: {module_title}")
        submodules = module.get('submodules', [])
        for j, submodule in enumerate(submodules):
            submodule_title = submodule.get('title', f'Submodule {i+1}.{j+1}')
            structure.append(f"    Submodule {i+1}.{j+1}: {submodule_title}")
    return "\n".join(structure)

# --- Global LangGraph Setup (Consider moving if state needs more complex management) --- #
# WARNING: MemorySaver is not persistent across server restarts.
# For production, use a persistent checkpointer like SQLSaver.
memory = MemorySaver()

# Define the function that calls the model - needs llm and prompt
async def call_model(state: MessagesState, llm, prompt):
    try:
        logger.debug(f"Calling model with state: {state}")
        prompt_value = await prompt.ainvoke(state)
        response = await llm.ainvoke(prompt_value)
        logger.debug(f"Model response received: {response}")
        # LangGraph expects a list of messages in the state update
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Error in call_model: {e}", exc_info=True)
        # How to propagate this error back? LangGraph might handle it,
        # but we need to ensure the endpoint returns an error.
        # For now, re-raise to potentially be caught by the endpoint handler.
        raise

# --- Chat Endpoint --- #
@router.post("/chat", response_model=ChatResponse)
async def handle_chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Received chat request for path {request.path_id}, module {request.module_index}, sub {request.submodule_index}, thread {request.thread_id}")

    if not redis_client:
        logger.error("Redis client not available. Cannot process chat request.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is temporarily unavailable due to backend configuration.",
        )

    allowance_used = False
    today_utc_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # --- 1. Check and Consume Purchased Allowance (Atomic Check/Decrement) ---
    try:
        allowance_key = f"chat_allowance:{user.id}:{today_utc_str}"
        
        # Use a LUA script for atomicity (check > 0 then decrement)
        # Ensure Redis server supports EVALSHA/EVAL
        # Script: Check if key exists and value > 0, if so, decrement and return 1, else return 0
        lua_script = """
        local current_val = redis.call('GET', KEYS[1])
        if current_val and tonumber(current_val) > 0 then
            redis.call('DECR', KEYS[1])
            return 1
        else
            return 0
        end
        """
        # result = await redis_client.eval(lua_script, 1, allowance_key) # Use eval for simplicity here
        # Note: Using pipeline with watch is another way, but LUA is generally preferred if available
        
        # Alternative using Pipeline + WATCH (if LUA is not available/desired)
        async with redis_client.pipeline(transaction=True) as pipe:
            await pipe.watch(allowance_key)
            current_value_str = await pipe.get(allowance_key)
            current_value = int(current_value_str) if current_value_str else 0
            
            if current_value > 0:
                pipe.multi()
                pipe.decr(allowance_key)
                try:
                    result_list = await pipe.execute()
                    # If execute succeeds without WatchError, the decrement happened
                    if result_list: # Check if transaction executed
                       allowance_used = True
                       logger.info(f"User {user.id} used purchased chat allowance. Remaining approx: {current_value - 1}")
                    # else: Transaction aborted due to watch error, handle if needed (e.g., retry)
                    # For this use case, if it fails, we just fall through to the free limit check
                       
                except redis.WatchError:
                    logger.warning(f"WatchError on allowance key for user {user.id}. Concurrent modification detected. Falling back to free limit check.")
                    # Transaction failed, allowance not used
                    pass # Fall through to free limit check
            else:
                # If no allowance (or key doesn't exist), unlock and proceed
                await pipe.reset()
                logger.debug(f"User {user.id} has no purchased chat allowance for {today_utc_str}.")

    except redis.RedisError as e:
        logger.error(f"Redis error checking/decrementing chat allowance for user {user.id}: {e}")
        # Fail Closed
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service temporarily unavailable due to backend issues.",
        )
    except Exception as e: # Catch potential int conversion errors etc.
        logger.error(f"Unexpected error during allowance check for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during allowance check.")

    # --- 2. Apply Free Daily Limit if Allowance NOT Used ---
    if not allowance_used:
        try:
            # Manually implement rate limit check/increment using Redis
            limit_key_base = f"chat_limit:{user.id}:{today_utc_str}"
            window_seconds = 86400 # 24 hours

            # Key format similar to fastapi-limiter for potential future consistency:
            # Note: fastapi-limiter usually includes the window interval in the key name.
            # We'll use a simpler key here for manual implementation.
            redis_key = limit_key_base # Keep it simple

            # Atomically increment and check using a pipeline
            pipe = redis_client.pipeline()
            # Increment the counter
            pipe.incr(redis_key)
            # Set expiry only when incrementing (avoids race condition on initial set)
            # Note: Setting expire on every hit is slightly less efficient but robust
            pipe.expire(redis_key, window_seconds) 
            # Execute the pipeline
            results = await pipe.execute()
            current_count = results[0] # Result of INCR

            if current_count is None: # Should not happen with INCR normally
                 raise redis.RedisError("INCR command did not return a value.")

            # Check if the limit is exceeded
            if current_count > CHAT_FREE_LIMIT_PER_DAY:
                 ttl = await redis_client.ttl(redis_key)
                 headers = {"Retry-After": str(ttl)} if ttl >= 0 else {}
                 logger.warning(f"User {user.id} exceeded free chat limit ({current_count}/{CHAT_FREE_LIMIT_PER_DAY}).")
                 raise HTTPException(
                     status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                     detail=f"Daily free chat limit reached ({CHAT_FREE_LIMIT_PER_DAY}). Purchase allowance or try again tomorrow.",
                     headers=headers
                 )
            
            logger.debug(f"User {user.id} used free chat message. Count: {current_count}/{CHAT_FREE_LIMIT_PER_DAY}")

        except redis.RedisError as e:
            logger.error(f"Redis error during free chat limit check/increment for user {user.id}: {e}")
            # Fail Closed
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chat service temporarily unavailable due to backend issues.",
            )
        except HTTPException as http_exc: # Re-raise 429 specifically
            raise http_exc
        except Exception as e:
            logger.error(f"Unexpected error during free limit check/increment for user {user.id}: {e}")
            # Fail Closed
            raise HTTPException(status_code=500, detail="Internal server error during rate limit processing.")

    # --- 3. Proceed with Chat Logic (if rate limits passed) ---
    try:
        # 3.1. Determine the source of path_data (DB vs Request) and normalize structure
        actual_learning_content = None
        db_entry = db.query(LearningPath).filter(
            LearningPath.path_id == request.path_id,
            LearningPath.user_id == user.id
        ).first()
        
        using_ephemeral_data = False
        if db_entry:
            raw_db_path_data = db_entry.path_data
            if isinstance(raw_db_path_data, dict):
                # Check for direct structure (older format)
                if 'modules' in raw_db_path_data and isinstance(raw_db_path_data.get('modules'), list):
                    actual_learning_content = raw_db_path_data
                    logger.info(f"Using direct path_data structure from DB for {request.path_id}")
                # Check for nested structure (newer format)
                elif 'path_data' in raw_db_path_data and isinstance(raw_db_path_data.get('path_data'), dict):
                    nested_content = raw_db_path_data['path_data']
                    if 'modules' in nested_content and isinstance(nested_content.get('modules'), list):
                        actual_learning_content = nested_content
                        logger.info(f"Using nested path_data structure from DB for {request.path_id}")
                    else:
                         logger.error(f"Invalid nested path_data structure in DB for {request.path_id}: 'modules' key missing or not a list inside nested 'path_data'.")
                else:
                    logger.error(f"Unrecognized dictionary structure in path_data from DB for {request.path_id}. Keys: {list(raw_db_path_data.keys())}")
            else:
                logger.error(f"path_data from DB for {request.path_id} is not a dictionary. Type: {type(raw_db_path_data)}")
        else:
            # Fallback: use ephemeral path_data from the request payload
            if request.path_data and isinstance(request.path_data, dict):
                # Check if ephemeral data itself has the 'modules' key
                if 'modules' in request.path_data and isinstance(request.path_data.get('modules'), list):
                    actual_learning_content = request.path_data
                    using_ephemeral_data = True
                    logger.info(f"Using ephemeral path_data for path {request.path_id} from request payload.")
                else:
                    logger.error(f"Ephemeral path_data structure invalid for {request.path_id}: 'modules' key missing or not a list.")
            else:
                # No DB entry and no valid ephemeral data
                logger.warning(f"Learning path {request.path_id} not found for user {user.id} and no valid ephemeral data provided.")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found and no valid ephemeral data provided.")

        # If after all checks, we don't have valid content, raise an error
        if actual_learning_content is None:
             logger.error(f"Could not determine valid course content for path {request.path_id}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid course data structure encountered.")

        # 3.2. Extract Context using the normalized 'actual_learning_content'
        modules = actual_learning_content.get('modules', []) # Use the normalized content
        if not (0 <= request.module_index < len(modules)):
            logger.warning(f"Invalid module index {request.module_index} for path {request.path_id} (module count: {len(modules)})")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module index")

        module = modules[request.module_index]
        submodules = module.get('submodules', [])
        if not (0 <= request.submodule_index < len(submodules)):
            logger.warning(f"Invalid submodule index {request.submodule_index} for module {request.module_index}, path {request.path_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid submodule index")

        submodule = submodules[request.submodule_index]

        # Safely get context elements from the normalized content
        submodule_title = submodule.get('title', 'N/A')
        submodule_description = submodule.get('description', 'N/A')
        submodule_content = submodule.get('content', 'No content available for this submodule.') # Crucial knowledge base
        module_title = module.get('title', 'N/A')
        user_topic = actual_learning_content.get('topic', 'N/A') # Use normalized content

        # Determine language: Use DB entry if available, else default
        if db_entry and getattr(db_entry, 'language', None):
            language_code = db_entry.language
            language_name = get_full_language_name(language_code)
            logger.info(f"Using persisted language '{language_name}' for path {request.path_id}")
        else:
            # Use language from ephemeral data if present, otherwise default
            language_code = actual_learning_content.get('language', 'en') # Check ephemeral data too
            language_name = get_full_language_name(language_code)
            if db_entry:
                logger.error(f"Stored course {db_entry.path_id} missing language; defaulting to '{language_name}'.")
            elif using_ephemeral_data:
                 logger.info(f"Using language '{language_name}' from ephemeral data for path {request.path_id}.")
            else: # Should not happen given checks above, but defensively log
                 logger.info(f"No stored entry or language in ephemeral data for path {request.path_id}; using default language '{language_name}'.")

        # 3.3. Format Path Structure & Prompt using the normalized 'actual_learning_content'
        learning_path_structure = format_path_structure(actual_learning_content) # Use normalized content

        # Retrieve raw research context for this submodule (if present) from normalized content
        submodule_research = submodule.get('research_context', '')

        # System prompt uses values derived from actual_learning_content
        system_prompt_string = CHATBOT_SYSTEM_PROMPT.format(
            submodule_title=submodule_title,
            user_topic=user_topic,
            module_title=module_title,
            module_order=request.module_index + 1,
            module_count=len(modules), # Derived from actual_learning_content
            submodule_order=request.submodule_index + 1,
            submodule_count=len(submodules), # Derived from actual_learning_content
            submodule_description=submodule_description,
            learning_path_structure=learning_path_structure, # Derived from actual_learning_content
            submodule_research=submodule_research,
            submodule_content=submodule_content,
            language=language_name
        )

        # 3.4. Initialize LLM and Prompt Template for this request
        llm = await get_llm(key_provider=None)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt_string),
            MessagesPlaceholder(variable_name="messages"),
        ])

        # 3.5. Define and Compile LangGraph App for this request
        workflow = StateGraph(MessagesState)
        
        # Use functools.partial to bind llm and prompt to call_model
        call_model_with_context = functools.partial(call_model, llm=llm, prompt=prompt)
        
        # Pass the partial function to add_node
        workflow.add_node("model", call_model_with_context) 
        workflow.add_edge(START, "model")
        app = workflow.compile(checkpointer=memory)

        # 3.6. Prepare Input and Config
        input_data = {"messages": [HumanMessage(content=request.user_message)]}
        config = {"configurable": {"thread_id": request.thread_id}}

        # 3.7. Invoke Graph
        logger.debug(f"Invoking graph for thread_id: {request.thread_id} with input: {input_data}")
        output = await app.ainvoke(input_data, config)
        logger.debug(f"Graph invocation completed. Output: {output}")

        # 3.8. Extract Response
        if not output or "messages" not in output or not output["messages"]:
            logger.error(f"Invalid output from graph: {output}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Chatbot failed to generate a response.")

        # Get the last message, assuming it's the AI's response
        ai_response_message = output["messages"][-1]
        ai_response = ai_response_message.content

        # 3.9. Return Response
        return ChatResponse(ai_response=ai_response, thread_id=request.thread_id)

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions to be handled by FastAPI's default handler
        # or any custom handlers defined earlier in the middleware stack
        raise http_exc
    except Exception as e:
        # Catch-all for unexpected errors during the main chat logic
        logger.error(f"Error processing chat request after rate limiting: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An internal error occurred during chat processing: {e}")

# --- Clear Chat Endpoint --- #
@router.post("/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    request: ClearChatRequest,
    user: User = Depends(get_current_user) # Keep user dependency for potential future use/logging
):
    logger.info(f"Received clear chat request for thread_id: {request.thread_id} by user {user.id}")
    
    thread_id = request.thread_id
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    
    # Generate a UUID string to use as the ID for the cleared state checkpoint
    cleared_checkpoint_id = str(uuid.uuid4())
    
    # Define an empty state checkpoint with the new UUID ID and expected keys
    empty_checkpoint = {
        "id": cleared_checkpoint_id,
        "messages": [], 
        "pending_sends": [],
        "channel_values": {}, # Add expected channel_values key
        "channel_versions": {}, # Add expected channel_versions key
        "versions_seen": {} # Add expected versions_seen key
    }
    
    try:
        # Use memory.put to overwrite the checkpoint for the thread_id with an empty state
        # MemorySaver.put is synchronous and requires metadata (including 'step') and new_versions
        memory.put(config, empty_checkpoint, {"step": 0}, {})
        logger.info(f"Successfully cleared chat history for thread_id: {thread_id} (new checkpoint_id: {cleared_checkpoint_id})")
        
    except Exception as e:
        logger.error(f"Failed to clear chat history for thread_id {thread_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear chat history for thread {thread_id}"
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- Purchase Chat Allowance Endpoint --- #
@router.post("/purchase-allowance", status_code=status.HTTP_200_OK)
async def purchase_chat_allowance(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    credit_service: CreditService = Depends(CreditService) # Inject CreditService
):
    """Allows users to purchase additional chat message allowance using credits."""
    logger.info(f"User {user.id} attempting to purchase chat allowance.")

    if not redis_client:
        logger.error("Redis client not available. Cannot purchase chat allowance.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat allowance purchase service is temporarily unavailable.",
        )

    try:
        # 1. Deduct credits using the direct method
        await credit_service.direct_deduct(
            user=user,
            amount=CHAT_ALLOWANCE_COST,
            transaction_type=TransactionType.CHAT_ALLOWANCE_PURCHASE,
            notes=f"Purchased {CHAT_ALLOWANCE_MESSAGES} additional chat messages."
        )
        logger.info(f"Successfully deducted {CHAT_ALLOWANCE_COST} credits from user {user.id} for chat allowance.")

    except HTTPException as http_exc:
        # Re-raise 403 (Insufficient Credits) or 500 (DB Error) from direct_deduct
        logger.warning(f"Credit deduction failed for user {user.id} during allowance purchase: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        # Catch any other unexpected errors during deduction
        logger.error(f"Unexpected error during credit deduction for user {user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing credits.",
        )

    try:
        # 2. Grant allowance in Redis
        today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        allowance_key = f"chat_allowance:{user.id}:{today_utc}"
        
        # Use INCRBY to add to existing allowance or create if not present
        current_allowance = await redis_client.incrby(allowance_key, CHAT_ALLOWANCE_MESSAGES)
        
        # Set expiry to end of current UTC day
        now_utc = datetime.now(timezone.utc)
        end_of_day_utc = datetime.combine(now_utc.date() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        ttl_seconds = int((end_of_day_utc - now_utc).total_seconds())
        
        # Ensure TTL is positive, set expiry only if key was just created or needs refresh
        if ttl_seconds > 0:
             await redis_client.expire(allowance_key, ttl_seconds)

        logger.info(f"Granted {CHAT_ALLOWANCE_MESSAGES} message allowance to user {user.id} for {today_utc}. New allowance: {current_allowance}. TTL set to {ttl_seconds}s.")

        return {"message": f"Successfully purchased {CHAT_ALLOWANCE_MESSAGES} chat messages.", "new_allowance_today": current_allowance}

    except redis.RedisError as e:
        logger.error(f"Redis error granting chat allowance for user {user.id}: {e}", exc_info=True)
        # Note: Credits were already deducted. This is a state inconsistency.
        # For now, we inform the user but don't automatically refund. Manual intervention might be needed.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Allowance grant failed after credit deduction. Please contact support.",
        )
    except Exception as e:
        logger.error(f"Unexpected error granting chat allowance for user {user.id} after deduction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred after credit deduction. Please contact support.",
        ) 