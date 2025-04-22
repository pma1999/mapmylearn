import logging
import functools # <-- Import functools
import datetime # Add datetime import
import uuid # Add uuid import
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import os # Import os

# Langchain & LangGraph imports
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.memory import MemorySaver # Using memory saver for now

# Local imports
from backend.config.database import get_db
from backend.models.auth_models import User, LearningPath
from backend.schemas.chatbot_schemas import ChatRequest, ChatResponse, ClearChatRequest
from backend.utils.auth_middleware import get_current_user
from backend.services.services import get_llm # Assuming user API key is available via user model or context
from backend.prompts.learning_path_prompts import CHATBOT_SYSTEM_PROMPT

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

logger = logging.getLogger(__name__)

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
    structure.append(f"Learning Path: {topic}")
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
    try:
        # 1. Fetch Learning Path
        learning_path = db.query(LearningPath).filter(
            LearningPath.path_id == request.path_id,
            LearningPath.user_id == user.id
        ).first()

        if not learning_path:
            logger.warning(f"Learning path {request.path_id} not found for user {user.id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found")

        path_data = learning_path.path_data
        if not isinstance(path_data, dict):
             logger.error(f"path_data is not a dict for path {request.path_id}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid learning path data structure")

        # 2. Extract Context
        modules = path_data.get('modules', [])
        if not (0 <= request.module_index < len(modules)):
            logger.warning(f"Invalid module index {request.module_index} for path {request.path_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module index")

        module = modules[request.module_index]
        submodules = module.get('submodules', [])
        if not (0 <= request.submodule_index < len(submodules)):
            logger.warning(f"Invalid submodule index {request.submodule_index} for module {request.module_index}, path {request.path_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid submodule index")

        submodule = submodules[request.submodule_index]

        # Safely get context elements
        submodule_title = submodule.get('title', 'N/A')
        submodule_description = submodule.get('description', 'N/A')
        submodule_content = submodule.get('content', 'No content available for this submodule.') # Crucial knowledge base
        module_title = module.get('title', 'N/A')
        user_topic = path_data.get('topic', 'N/A')
        
        # Get language from learning path and convert code to full name
        if not hasattr(learning_path, 'language') or not learning_path.language:
            logger.error(f"Learning path {learning_path.path_id} is missing the language attribute. Defaulting to English.")
            language_code = "en"
            language_name = "English"
        else:
            language_code = learning_path.language
            language_name = get_full_language_name(language_code)
            logger.info(f"Using language '{language_name}' (from code '{language_code}') for path {request.path_id}")

        # 3. Format Path Structure & Prompt
        learning_path_structure = format_path_structure(path_data)

        # Retrieve raw research context for this submodule (if present)
        submodule_research = submodule.get('research_context', '')

        system_prompt_string = CHATBOT_SYSTEM_PROMPT.format(
            submodule_title=submodule_title,
            user_topic=user_topic,
            module_title=module_title,
            module_order=request.module_index + 1,
            module_count=len(modules),
            submodule_order=request.submodule_index + 1,
            submodule_count=len(submodules),
            submodule_description=submodule_description,
            learning_path_structure=learning_path_structure,
            submodule_research=submodule_research,
            submodule_content=submodule_content,
            language=language_name  # Use the full language name instead of the code
        )

        # 4. Initialize LLM and Prompt Template for this request
        llm = await get_llm(key_provider=None)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt_string),
            MessagesPlaceholder(variable_name="messages"),
        ])

        # 5. Define and Compile LangGraph App for this request
        workflow = StateGraph(MessagesState)
        
        # Use functools.partial to bind llm and prompt to call_model
        call_model_with_context = functools.partial(call_model, llm=llm, prompt=prompt)
        
        # Pass the partial function to add_node
        workflow.add_node("model", call_model_with_context) 
        workflow.add_edge(START, "model")
        app = workflow.compile(checkpointer=memory)

        # 6. Prepare Input and Config
        input_data = {"messages": [HumanMessage(content=request.user_message)]}
        config = {"configurable": {"thread_id": request.thread_id}}

        # 7. Invoke Graph
        logger.debug(f"Invoking graph for thread_id: {request.thread_id} with input: {input_data}")
        output = await app.ainvoke(input_data, config)
        logger.debug(f"Graph invocation completed. Output: {output}")

        # 8. Extract Response
        if not output or "messages" not in output or not output["messages"]:
            logger.error(f"Invalid output from graph: {output}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Chatbot failed to generate a response.")

        # Get the last message, assuming it's the AI's response
        ai_response_message = output["messages"][-1]
        ai_response = ai_response_message.content

        # 9. Return Response
        return ChatResponse(ai_response=ai_response, thread_id=request.thread_id)

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions to be handled by FastAPI
        raise http_exc
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An internal error occurred: {e}")

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