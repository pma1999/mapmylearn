import asyncio
import logging
import os
import uuid
import shutil
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Import OpenAI client
import openai

from backend.models.auth_models import LearningPath, Base
from backend.services.services import _scrape_single_url, get_llm
from backend.prompts.audio_prompts import SUBMODULE_AUDIO_SCRIPT_PROMPT

logger = logging.getLogger(__name__)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "onyx") # Default voice

STATIC_AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "audio")

async def generate_submodule_audio(
    db: Optional[Session],
    learning_path: LearningPath,
    module_index: int,
    submodule_index: int,
    language: str
) -> str:
    """
    Generates audio for a specific submodule using OpenAI TTS, saves it, and returns the URL.
    Handles scraping, LLM script generation (in the specified language), and TTS using OpenAI SDK.
    If db session and learning_path.id are provided, updates DB.
    """
    is_persisted = db is not None and hasattr(learning_path, 'id') and learning_path.id is not None

    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Audio generation service is not configured (Missing OpenAI API Key).")

    path_data = learning_path.path_data
    if not isinstance(path_data, dict):
        logger.error(f"Invalid path_data format for path_id {learning_path.path_id}. Expected dict, got {type(path_data)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid learning path data structure.")

    modules = path_data.get('modules', [])
    if not (0 <= module_index < len(modules)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Module index {module_index} out of bounds.")

    module = modules[module_index]
    submodules = module.get('submodules', [])
    if not (0 <= submodule_index < len(submodules)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Submodule index {submodule_index} out of bounds.")

    submodule = submodules[submodule_index]

    # --- Scraping --- 
    scraped_content_parts = []
    resource_urls = [res.get('url') for res in submodule.get('resources', []) if res.get('url')]
    scrape_timeout = int(os.environ.get("SCRAPE_TIMEOUT", 10))
    if resource_urls:
        logger.info(f"Scraping {len(resource_urls)} resources for submodule audio script...")
        import aiohttp
        async with aiohttp.ClientSession() as session: 
            scrape_tasks = [_scrape_single_url(session, url, scrape_timeout) for url in resource_urls] 
            scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)

        for i, result in enumerate(scrape_results):
            url = resource_urls[i]
            if isinstance(result, Exception):
                logger.warning(f"Scraping failed for {url}: {result}")
            elif isinstance(result, tuple) and result[0]: # Successful scrape with content
                scraped_content_parts.append(f"--- Content from {url} ---\n{result[0][:5000]}...\n---") # Limit length per resource
            elif isinstance(result, tuple) and result[1]: # Scrape error reported
                 logger.warning(f"Scraping failed for {url}: {result[1]}")
                 
        logger.info(f"Finished scraping resources. Got content from {len(scraped_content_parts)} URLs.")
    
    scraped_context = "\n".join(scraped_content_parts)

    # --- LLM Script Generation --- 
    submodule_main_content = submodule.get('content', '')
    if not submodule_main_content and not scraped_context:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No content available (submodule or resources) to generate audio script.")
         
    llm_context = f"Submodule Title: {submodule.get('title', 'N/A')}\nSubmodule Description: {submodule.get('description', 'N/A')}\n\nSubmodule Content:\n{submodule_main_content}\n\nAdditional Content from Resources:\n{scraped_context}"
    
    logger.info(f"Generating audio script with LLM in language '{language}'...")
    try:
        # Assuming get_llm doesn't require key provider here if keys are in env
        llm = await get_llm()
        # Ensure the prompt template now includes language
        prompt = ChatPromptTemplate.from_template(SUBMODULE_AUDIO_SCRIPT_PROMPT)
        chain = prompt | llm | StrOutputParser()
        # Pass language to the chain invocation
        audio_script = await chain.ainvoke({"context": llm_context[:30000], "language": language})
        logger.info(f"LLM script generation successful (lang: {language}).")
    except Exception as e:
        logger.exception(f"Error generating audio script with LLM (lang: {language})")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate audio script.")

    if not audio_script or not isinstance(audio_script, str) or len(audio_script.strip()) < 10:
        logger.error(f"LLM generated invalid or empty script (lang: {language}): '{audio_script[:100]}...'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Generated audio script was invalid or empty.")

    # --- Text-to-Speech (OpenAI SDK) ---
    logger.info(f"Generating audio with OpenAI TTS model '{OPENAI_TTS_MODEL}' and voice '{OPENAI_TTS_VOICE}'...")
    
    # Warn if the script is potentially too long for the model
    if len(audio_script) > 3500:
        logger.warning(f"Audio script length ({len(audio_script)} chars) is long. Model '{OPENAI_TTS_MODEL}' might have stability issues (pauses, repetition). Consider splitting longer content.")
        
    permanent_audio_path = None # Define path variable outside try
    try:
        openai_client = openai.OpenAI() # API key is automatically picked up from OPENAI_API_KEY env var
        response = openai_client.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice=OPENAI_TTS_VOICE,
            input=audio_script,
            response_format="mp3" # Ensure MP3 format
        )
        
        # --- File Storage & Serving --- 
        unique_filename = f"{uuid.uuid4()}.mp3"
        permanent_audio_path = os.path.join(STATIC_AUDIO_DIR, unique_filename)
        
        # Stream the response content directly to a file
        response.stream_to_file(permanent_audio_path)

        audio_url = f"/static/audio/{unique_filename}"
        logger.info(f"OpenAI TTS audio generated and saved successfully: {permanent_audio_path}")

    except Exception as e:
        logger.exception("Error during OpenAI TTS generation or saving file")
        if permanent_audio_path and os.path.exists(permanent_audio_path):
             try: os.remove(permanent_audio_path)
             except OSError: pass
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Text-to-Speech generation failed: {e}")
    except openai.APIError as e:
        # Handle API errors from OpenAI (e.g., invalid key, rate limits, server issues)
        logger.exception(f"OpenAI API error during TTS generation: {e}")
        if permanent_audio_path and os.path.exists(permanent_audio_path):
            try: os.remove(permanent_audio_path)
            except OSError as cleanup_error:
                 logger.error(f"Failed to cleanup partially created audio file {permanent_audio_path} after API error: {cleanup_error}")
        # Try to provide a more specific error message if available
        detail = f"Text-to-Speech service error (API): {str(e)}"
        if hasattr(e, 'message') and e.message: 
             detail = f"Text-to-Speech service error (API): {e.message}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    except Exception as e:
        # Handle other potential errors (e.g., file system issues, unexpected errors)
        logger.exception("Unexpected error during OpenAI TTS generation or saving file")
        if permanent_audio_path and os.path.exists(permanent_audio_path):
            try: os.remove(permanent_audio_path)
            except OSError as cleanup_error:
                logger.error(f"Failed to cleanup partially created audio file {permanent_audio_path} after unexpected error: {cleanup_error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Text-to-Speech generation failed: {str(e)}")

    # --- Update Database (Only if persisted) --- 
    if is_persisted:
        logger.info(f"Updating database for persisted path {learning_path.path_id}...")
        try:
            # Directly modify the existing path_data dictionary
            # Note: Make sure path_data is loaded/treated as a dict
            if not isinstance(learning_path.path_data, dict):
                 # This shouldn't happen if validation passed earlier, but handle defensively
                 logger.error("path_data is not a dict during update attempt!")
                 raise TypeError("Cannot update non-dictionary path_data")
                 
            # Modify the nested structure directly
            learning_path.path_data['modules'][module_index]['submodules'][submodule_index]['audio_url'] = audio_url
            
            # Explicitly flag the path_data field as modified
            flag_modified(learning_path, "path_data")
            
            learning_path.last_modified_date = datetime.utcnow()
            
            db.add(learning_path) # Add is safe even if object is already tracked
            db.commit()
            db.refresh(learning_path)
            logger.info(f"Database updated successfully for path_id {learning_path.path_id}")
        except Exception as e:
            db.rollback()
            logger.exception("Error updating database with audio URL")
            # Attempt to delete the orphaned audio file
            try:
                if os.path.exists(permanent_audio_path):
                    os.remove(permanent_audio_path)
                    logger.info(f"Cleaned up orphaned audio file: {permanent_audio_path}")
            except Exception as cleanup_err:
                logger.error(f"Failed to cleanup orphaned audio file {permanent_audio_path}: {cleanup_err}")
            
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save audio generation result.")
    else:
         logger.info(f"Skipping database update for temporary path {learning_path.path_id}.")

    return audio_url 