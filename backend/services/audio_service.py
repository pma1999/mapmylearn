import asyncio
import logging
import os
import uuid
import shutil
import tempfile
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAI, AsyncOpenAI, APIError
from pydub import AudioSegment

from backend.models.auth_models import LearningPath, Base
from backend.services.services import _scrape_single_url, get_llm
# Import the dictionary of prompts instead of the single prompt string
from backend.prompts.audio_prompts import AUDIO_SCRIPT_PROMPTS_BY_LANG

logger = logging.getLogger(__name__)

# --- TTS Configuration Constants ---
# Feel free to tune these constants to adjust the audio output
TTS_PERSONA = "enthusiastic, encouraging, and clear tutor"
Tts_tone = "positive, engaging, and helpful"
Tts_pacing = "moderate, understandable pace with natural variation"
Tts_intonation = "vary intonation naturally to emphasize key points and keep the listener engaged"
TTS_CHUNK_CHAR_LIMIT = int(os.getenv("TTS_CHUNK_CHAR_LIMIT", 3000))
TTS_CHUNK_PAUSE_MS = int(os.getenv("TTS_CHUNK_PAUSE_MS", 200))

# Language-specific accent preferences (add more as needed)
Tts_accent_map = {
    "en": "standard North American English accent", # Default/Fallback English
    "es": "Castilian Spanish accent (español de España)",
    "fr": "standard Metropolitan French accent",
    "de": "standard German accent (Hochdeutsch)",
    "it": "standard Italian accent",
    "pt": "standard European Portuguese accent",
    # Add other languages and desired accents here, e.g.:
    # "zh": "Mandarin Chinese accent",
    # "ja": "standard Japanese accent",
}
# --- End TTS Configuration Constants ---


# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "shimmer") # Default voice

STATIC_AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "audio")

# Ensure static audio directory exists
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

# --- Helper Functions ---

def _split_script(script: str, limit: int) -> List[str]:
    """
    Splits a script into chunks suitable for TTS, trying to respect paragraph boundaries first.
    """
    chunks = []
    paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]

    for paragraph in paragraphs:
        if len(paragraph) <= limit:
            if paragraph: # Avoid empty chunks
                 chunks.append(paragraph)
        else:
            # Paragraph is too long, split it further
            current_pos = 0
            while current_pos < len(paragraph):
                end_pos = current_pos + limit
                if end_pos >= len(paragraph):
                    chunk = paragraph[current_pos:]
                    if chunk.strip(): chunks.append(chunk.strip())
                    break
                else:
                    # Find best split point (sentence end preferred, then whitespace)
                    split_point = -1
                    for char in reversed(['.', '!', '?', '\\n']): # Prefer sentence-ending punctuation/newlines
                        found = paragraph.rfind(char, current_pos, end_pos)
                        if found != -1:
                            split_point = found + 1
                            break
                    if split_point == -1: # Fallback to last whitespace
                        found = paragraph.rfind(' ', current_pos, end_pos)
                        if found != -1:
                             split_point = found + 1
                        else: # Force split at limit if no good point found
                            split_point = end_pos

                    chunk = paragraph[current_pos:split_point]
                    if chunk.strip(): chunks.append(chunk.strip())
                    current_pos = split_point
                    # Skip leading whitespace for the next chunk
                    while current_pos < len(paragraph) and paragraph[current_pos].isspace():
                        current_pos += 1
    return chunks

async def _generate_tts_chunk(
    async_client: AsyncOpenAI,
    chunk_text: str,
    instruction_text: str,
    output_path: str
):
    """Generates audio for a single text chunk and saves it."""
    try:
        response = await async_client.audio.speech.create(
            model=OPENAI_TTS_MODEL,
            voice=OPENAI_TTS_VOICE,
            input=chunk_text,
            instructions=instruction_text,
            response_format="mp3"
        )
        # response.stream_to_file is sync, run in thread pool
        await asyncio.to_thread(response.stream_to_file, output_path)
        logger.debug(f"Successfully generated TTS chunk: {output_path}")
    except APIError as e:
        logger.error(f"OpenAI API error generating chunk for {output_path}: {e}")
        raise # Re-raise to be caught by the main function
    except Exception as e:
        logger.error(f"Unexpected error generating chunk {output_path}: {e}")
        raise # Re-raise


# --- Main Service Function ---

async def generate_submodule_audio(
    db: Optional[Session],
    learning_path: LearningPath,
    module_index: int,
    submodule_index: int,
    language: str # Expecting ISO code 'en', 'es', etc.
) -> str:
    """
    Generates audio for a specific submodule using OpenAI TTS, saves it, and returns the URL.
    Handles scraping, LLM script generation, potential script chunking, concurrent TTS,
    concatenation, and database updates if applicable.
    """
    # --- Validate Language ---
    if language not in AUDIO_SCRIPT_PROMPTS_BY_LANG:
         logger.error(f"Unsupported language requested for audio generation: {language}")
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail=f"Audio generation is not currently supported for language: {language}. Supported languages are: {list(AUDIO_SCRIPT_PROMPTS_BY_LANG.keys())}"
         )

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

    logger.info(f"Generating audio script with LLM using prompt for language '{language}'...")
    try:
        selected_prompt_template = AUDIO_SCRIPT_PROMPTS_BY_LANG[language]
        llm = await get_llm()
        prompt = ChatPromptTemplate.from_template(selected_prompt_template)
        chain = prompt | llm | StrOutputParser()
        audio_script = await chain.ainvoke({"context": llm_context[:30000]}) # Limit context for LLM
        logger.info(f"LLM script generation successful (lang: {language}).")
    except Exception as e:
        logger.exception(f"Error generating audio script with LLM (lang: {language})")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate audio script.")

    if not audio_script or not isinstance(audio_script, str) or len(audio_script.strip()) < 10:
        logger.error(f"LLM generated invalid or empty script (lang: {language}): '{audio_script[:100]}...'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Generated audio script was invalid or empty.")

    # --- Text-to-Speech (OpenAI SDK) ---
    logger.info(f"Initiating audio generation with OpenAI TTS model '{OPENAI_TTS_MODEL}' and voice '{OPENAI_TTS_VOICE}'...")

    # Instantiate Async Client
    async_openai_client = AsyncOpenAI()

    # --- Construct the Rich TTS Instruction ---
    submodule_title = submodule.get('title', 'this topic')
    target_accent = Tts_accent_map.get(language, Tts_accent_map.get("en"))
    if not target_accent:
         target_accent = "standard accent for the language"
         logger.warning(f"No specific accent mapping found for language '{language}' or fallback 'en'. Using generic instruction.")

    instruction_text = (
        f"Act as an {TTS_PERSONA} explaining '{submodule_title}' to a learner. "
        f"Maintain a {Tts_tone} tone throughout. "
        f"Speak clearly at a {Tts_pacing}. "
        f"Use natural speech patterns and {Tts_intonation}. "
        f"Ensure accurate pronunciation using a {target_accent} in the {language} language."
    )
    logger.info(f"Using Rich TTS instruction: {instruction_text}")

    permanent_audio_path = None
    temp_files = []
    audio_url = None

    try:
        if len(audio_script) <= TTS_CHUNK_CHAR_LIMIT:
            # Script is short, process directly
            logger.info("Script is short, generating single audio file.")
            unique_filename = f"{uuid.uuid4()}.mp3"
            permanent_audio_path = os.path.join(STATIC_AUDIO_DIR, unique_filename)

            response = await async_openai_client.audio.speech.create(
                model=OPENAI_TTS_MODEL,
                voice=OPENAI_TTS_VOICE,
                input=audio_script,
                instructions=instruction_text,
                response_format="mp3"
            )
            # response.stream_to_file is sync, run in thread pool
            await asyncio.to_thread(response.stream_to_file, permanent_audio_path)
            audio_url = f"/static/audio/{unique_filename}"
            logger.info(f"Single TTS audio generated and saved successfully: {permanent_audio_path}")

        else:
            # Script is long, split into chunks and process concurrently
            logger.info(f"Script length ({len(audio_script)} chars) > {TTS_CHUNK_CHAR_LIMIT}. Splitting into chunks.")
            script_chunks = _split_script(audio_script, TTS_CHUNK_CHAR_LIMIT)
            logger.info(f"Split script into {len(script_chunks)} chunks.")

            # Generate TTS for each chunk concurrently
            tasks = []
            for i, chunk in enumerate(script_chunks):
                temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir=STATIC_AUDIO_DIR) # Use static dir for temp to avoid cross-device issues if temp is on different volume
                temp_files.append(temp_file.name)
                tasks.append(
                    _generate_tts_chunk(
                        async_openai_client,
                        chunk,
                        instruction_text, # Pass the same instruction to maintain consistency
                        temp_file.name
                    )
                )
            
            logger.info(f"Generating TTS for {len(tasks)} chunks concurrently...")
            await asyncio.gather(*tasks)
            logger.info("Finished generating all TTS chunks.")

            # Concatenate chunks
            logger.info("Concatenating audio chunks...")
            if not temp_files:
                raise ValueError("No temporary audio files were generated.")

            combined_audio = AudioSegment.empty()
            # Start with simple concatenation. If clicks/pops are audible, consider crossfade.
            # e.g., combined_audio = AudioSegment.from_mp3(temp_files[0])
            # for path in temp_files[1:]:
            #     combined_audio = combined_audio.append(AudioSegment.from_mp3(path), crossfade=10) # 10ms crossfade

            # Create the pause segment once
            pause_segment = AudioSegment.silent(duration=TTS_CHUNK_PAUSE_MS)

            first_segment = True
            for path in temp_files:
                try:
                     segment = await asyncio.to_thread(AudioSegment.from_mp3, path)
                     if first_segment:
                         combined_audio = segment
                         first_segment = False
                     else:
                         combined_audio += pause_segment + segment
                except Exception as e:
                     logger.error(f"Error loading/concatenating chunk {path}: {e}")
                     raise # Re-raise to trigger cleanup and error response

            # Export concatenated audio
            unique_filename = f"{uuid.uuid4()}.mp3"
            permanent_audio_path = os.path.join(STATIC_AUDIO_DIR, unique_filename)
            
            logger.info(f"Exporting concatenated audio to {permanent_audio_path}...")
            await asyncio.to_thread(combined_audio.export, permanent_audio_path, format="mp3")
            
            audio_url = f"/static/audio/{unique_filename}"
            logger.info(f"Concatenated TTS audio generated and saved successfully: {permanent_audio_path}")

    except APIError as e:
        logger.exception(f"OpenAI API error during TTS processing: {e}")
        detail = f"Text-to-Speech service error (API): {getattr(e, 'message', str(e))}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    except Exception as e:
        logger.exception(f"Error during TTS generation/concatenation: {e}")
        # Ensure permanent_audio_path is not left if it was created before failure
        if permanent_audio_path and os.path.exists(permanent_audio_path):
            try: os.remove(permanent_audio_path)
            except OSError as cleanup_error:
                logger.error(f"Failed to cleanup partially created permanent audio file {permanent_audio_path} after error: {cleanup_error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Text-to-Speech generation failed: {str(e)}")
    finally:
        # --- Cleanup Temporary Files ---
        if temp_files:
            logger.info(f"Cleaning up {len(temp_files)} temporary audio chunk files...")
            for temp_path in temp_files:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        logger.debug(f"Removed temp file: {temp_path}")
                except OSError as e:
                    logger.error(f"Error removing temporary file {temp_path}: {e}")

    if not audio_url:
         # Should not happen if logic is correct, but as a safeguard
         logger.error("Audio generation process completed but no audio_url was generated.")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Audio generation failed unexpectedly.")

    # --- Update Database (Only if persisted) ---
    if is_persisted:
        logger.info(f"Updating database for persisted path {learning_path.path_id}...")
        try:
            if not isinstance(learning_path.path_data, dict):
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
            # Attempt to delete the orphaned audio file (the final concatenated one)
            try:
                if permanent_audio_path and os.path.exists(permanent_audio_path):
                    os.remove(permanent_audio_path)
                    logger.info(f"Cleaned up orphaned final audio file due to DB error: {permanent_audio_path}")
            except Exception as cleanup_err:
                logger.error(f"Failed to cleanup orphaned final audio file {permanent_audio_path}: {cleanup_err}")

            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save audio generation result.")
    else:
         logger.info(f"Skipping database update for temporary path {learning_path.path_id}.")

    return audio_url 