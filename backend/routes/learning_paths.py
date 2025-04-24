from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
import uuid
import os
from datetime import datetime
from fastapi.responses import FileResponse
import logging

from backend.config.database import get_db
from backend.models.auth_models import User, LearningPath, TransactionType
from backend.schemas.auth_schemas import (
    LearningPathCreate, LearningPathUpdate, LearningPathResponse, 
    LearningPathList, MigrationRequest, MigrationResponse,
    GenerateAudioRequest, GenerateAudioResponse # Import new schemas
)
from backend.utils.auth_middleware import get_current_user
from backend.utils.pdf_generator import generate_pdf, create_filename
# Import the new audio generation service
from backend.services.audio_service import generate_submodule_audio 
from backend.services.credit_service import CreditService # Import CreditService

router = APIRouter(prefix="/v1/learning-paths", tags=["learning-paths"])
logger = logging.getLogger(__name__) # Add logger instance

# Define supported languages
SUPPORTED_AUDIO_LANGUAGES = ["en", "es", "fr", "de", "it", "pt"]
DEFAULT_AUDIO_LANGUAGE = "en" # Although we expect frontend to always send it

@router.get("", response_model=LearningPathList)
async def get_learning_paths(
    sort_by: str = Query("creation_date", description="Field to sort by"),
    source: Optional[str] = Query(None, description="Filter by source type"),
    search: Optional[str] = Query(None, description="Search term for topic or tags"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    favorite_only: bool = Query(False, description="Only return favorite learning paths"),
    include_full_data: bool = Query(False, description="Include full path_data in response"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all learning paths for the current user with filtering and pagination.
    """
    # Start timing the request for performance monitoring
    start_time = datetime.utcnow()
    
    # Select only needed columns for better performance
    # Only include path_data if explicitly requested
    if include_full_data:
        query = db.query(LearningPath)
    else:
        query = db.query(
            LearningPath.id,
            LearningPath.path_id,
            LearningPath.user_id,
            LearningPath.topic,
            LearningPath.language,
            LearningPath.creation_date,
            LearningPath.last_modified_date,
            LearningPath.favorite,
            LearningPath.tags,
            LearningPath.source
        )
    
    # Apply user filter - this should be the first filter for index usage
    query = query.filter(LearningPath.user_id == user.id)
    
    # Apply favorite filter
    if favorite_only:
        query = query.filter(LearningPath.favorite == True)
    
    # Apply source filter
    if source:
        query = query.filter(LearningPath.source == source)
    
    # Apply search filter on topic and tags
    if search:
        # Convert search to lowercase for case-insensitive search
        search_term = f"%{search.lower()}%"
        query = query.filter(
            # Search in topic
            LearningPath.topic.ilike(search_term)
        )
    
    # Apply sorting - ensure these match database indexes
    if sort_by == "creation_date":
        query = query.order_by(LearningPath.creation_date.desc())
    elif sort_by == "last_modified_date":
        query = query.order_by(LearningPath.last_modified_date.desc().nullslast())
    elif sort_by == "topic":
        query = query.order_by(LearningPath.topic)
    elif sort_by == "favorite":
        # Sort by favorite status (True first), then by creation date
        query = query.order_by(LearningPath.favorite.desc(), LearningPath.creation_date.desc())
    else:
        # Default to creation date if invalid sort field
        query = query.order_by(LearningPath.creation_date.desc())
    
    # Instead of separate count query, we'll use window functions
    # for more efficient counting with the same query
    from sqlalchemy import func
    from sqlalchemy.sql import label
    
    # First prepare the base query with all the filters
    filtered_query = query
    
    # Get total count using SQL COUNT OVER() window function to avoid a separate query
    if db.bind.dialect.name == 'postgresql':
        # PostgreSQL supports window functions - most efficient approach
        count_query = filtered_query.add_columns(
            func.count().over().label('total_count')
        )
        
        # Apply pagination for data fetching
        offset = (page - 1) * per_page
        paginated_query = count_query.offset(offset).limit(per_page)
        
        # Execute query and get results
        results = paginated_query.all()
        
        # Extract total count from first row
        total_count = results[0].total_count if results else 0
        
        # Convert to dictionaries for serialization, excluding the count column
        if include_full_data:
            learning_paths = [row for row in results]
        else:
            learning_paths = [
                LearningPath(
                    id=row.id,
                    path_id=row.path_id,
                    user_id=row.user_id,
                    topic=row.topic,
                    language=row.language,
                    creation_date=row.creation_date,
                    last_modified_date=row.last_modified_date,
                    favorite=row.favorite,
                    tags=row.tags,
                    source=row.source,
                    path_data={} if not include_full_data else row.path_data
                )
                for row in results
            ]
    else:
        # For other databases (SQLite, etc.), fall back to a separate count query
        total_count = filtered_query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        paginated_query = filtered_query.offset(offset).limit(per_page)
        
        # Execute query and get results
        results = paginated_query.all()
        
        if not include_full_data and results:
            # For SQLite or other DBs, we need to manually create lightweight objects
            if hasattr(results[0], '_asdict'):  # For query with individual columns
                learning_paths = [
                    LearningPath(
                        id=row.id,
                        path_id=row.path_id,
                        user_id=row.user_id,
                        topic=row.topic,
                        language=row.language,
                        creation_date=row.creation_date,
                        last_modified_date=row.last_modified_date,
                        favorite=row.favorite,
                        tags=row.tags,
                        source=row.source,
                        path_data={}
                    )
                    for row in results
                ]
            else:
                # This branch likely handles full LearningPath objects already,
                # but we'll ensure language is present if accessed later.
                # If 'results' contains full objects, language is already there.
                learning_paths = results
                # Ensure path_data is empty if not requested (already handled by schema)
                # No specific action needed for language here if full objects are fetched
        else:
            learning_paths = results
    
    # Calculate request duration for monitoring
    end_time = datetime.utcnow()
    duration_ms = (end_time - start_time).total_seconds() * 1000
    
    return {
        "entries": learning_paths,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "request_time_ms": int(duration_ms)
    }


@router.get("/export", response_model=List[LearningPathResponse])
async def export_all_learning_paths(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all learning paths (including full path_data) for the current user.
    """
    try:
        learning_paths = db.query(LearningPath).filter(
            LearningPath.user_id == user.id
        ).order_by(LearningPath.creation_date.desc()).all()
        
        logger.info(f"Exporting {len(learning_paths)} learning paths for user {user.id}")
        # The LearningPathResponse schema will handle serialization
        return learning_paths
    except Exception as e:
        logger.exception(f"Error exporting learning paths for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not export learning paths due to a server error."
        )


@router.get("/{path_id}", response_model=LearningPathResponse)
async def get_learning_path(
    path_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific learning path by ID. 
    The LearningPathResponse schema automatically includes the full path_data.
    """
    learning_path = db.query(LearningPath).filter(
        LearningPath.path_id == path_id,
        LearningPath.user_id == user.id
    ).first()
    
    if not learning_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found"
        )
    
    return learning_path


@router.post("", response_model=LearningPathResponse, status_code=status.HTTP_201_CREATED)
async def create_learning_path(
    learning_path: LearningPathCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new learning path.
    """
    # Generate a unique ID for the learning path
    path_id = str(uuid.uuid4())
    
    # --- Debugging: Log structure of incoming path_data --- 
    logger.info(f"Received learning_path object type: {type(learning_path)}")
    logger.info(f"Received learning_path.path_data type: {type(learning_path.path_data)}")
    if isinstance(learning_path.path_data, dict):
        logger.info(f"Received learning_path.path_data keys: {list(learning_path.path_data.keys())}")
    else:
        logger.warning(f"Received learning_path.path_data is not a dict: {str(learning_path.path_data)[:200]}...")
    # --- End Debugging ---

    # Extract the actual learning path content dictionary
    # The incoming learning_path.path_data might incorrectly contain the entire payload structure
    actual_content_to_save = None
    if isinstance(learning_path.path_data, dict):
        # Look for the nested 'path_data' key which holds the real content
        if 'path_data' in learning_path.path_data and isinstance(learning_path.path_data['path_data'], dict):
             actual_content_to_save = learning_path.path_data['path_data']
             logger.info("Extracted nested 'path_data' from request for saving.")
        # Fallback: Maybe the structure is already correct? (Shouldn't happen based on logs, but check)
        elif 'modules' in learning_path.path_data: 
             actual_content_to_save = learning_path.path_data
             logger.warning("Incoming learning_path.path_data had direct 'modules' key, using directly.")
        else:
             logger.error("Could not find 'modules' or nested 'path_data' in received learning_path.path_data.")
    
    # If extraction failed, log error but proceed with potentially incorrect data to avoid breaking entirely?
    # Or raise an error? Raising is safer but might break saving if the root cause isn't fixed.
    # For now, we'll default to the (likely incorrect) full dict if extraction fails, but log heavily.
    if actual_content_to_save is None:
        logger.error("Failed to extract actual learning content! Saving raw learning_path.path_data. THIS WILL LIKELY CAUSE NESTING ISSUES.")
        actual_content_to_save = learning_path.path_data # Fallback to potentially incorrect data

    # Create database entry using the extracted content
    db_learning_path = LearningPath(
        user_id=user.id,
        path_id=path_id,
        topic=learning_path.topic,
        language=learning_path.language,
        path_data=actual_content_to_save,  # Use the correctly extracted content
        favorite=learning_path.favorite,
        tags=learning_path.tags,
        source=learning_path.source,
        creation_date=datetime.utcnow(),
    )
    
    try:
        # --- Debugging: Log structure ACTUALLY being saved --- 
        logger.info(f"Attempting to save path_data type: {type(actual_content_to_save)}")
        if isinstance(actual_content_to_save, dict):
             logger.info(f"Attempting to save path_data keys: {list(actual_content_to_save.keys())}")
        else:
             logger.warning(f"Attempting to save non-dict path_data: {str(actual_content_to_save)[:200]}...")
        # --- End Debugging ---
        db.add(db_learning_path)
        db.commit()
        db.refresh(db_learning_path)
    except IntegrityError as e:
        db.rollback()
        # Log a concise error message for IntegrityError
        logger.error(f"Database integrity error for user {user.id} creating learning path '{learning_path.topic}': {e}")
        # Raise the user-facing exception
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create learning path. Database integrity constraint violated." # Keep informative detail
        )
    except Exception as e: # Catch other potential errors during commit
         db.rollback()
         # Log unexpected errors with full traceback using exc_info=True
         logger.error(f"Unexpected error for user {user.id} creating learning path '{learning_path.topic}'.", exc_info=True)
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail="An unexpected error occurred while saving the learning path."
         )

    return db_learning_path


@router.put("/{path_id}", response_model=LearningPathResponse)
async def update_learning_path(
    path_id: str,
    update_data: LearningPathUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a learning path (favorite status or tags).
    """
    learning_path = db.query(LearningPath).filter(
        LearningPath.path_id == path_id,
        LearningPath.user_id == user.id
    ).first()
    
    if not learning_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found"
        )
    
    # Update favorite status if provided
    if update_data.favorite is not None:
        learning_path.favorite = update_data.favorite
    
    # Update tags if provided
    if update_data.tags is not None:
        learning_path.tags = update_data.tags
    
    # Update modification date
    learning_path.last_modified_date = datetime.utcnow()
    
    db.commit()
    db.refresh(learning_path)
    
    return learning_path


@router.delete("/clear-all", status_code=status.HTTP_204_NO_CONTENT)
async def clear_all_learning_paths(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete ALL learning paths for the current user. Use with caution!
    """
    try:
        # Perform bulk delete
        deleted_count = db.query(LearningPath).filter(
            LearningPath.user_id == user.id
        ).delete(synchronize_session=False) # Use synchronize_session=False for potentially better performance
        
        db.commit()
        logger.info(f"Cleared {deleted_count} learning paths for user {user.id}")
        # Return No Content response
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Error clearing all learning paths for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not clear learning paths due to a server error."
        )


@router.delete("/{path_id}")
async def delete_learning_path(
    path_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a learning path.
    """
    learning_path = db.query(LearningPath).filter(
        LearningPath.path_id == path_id,
        LearningPath.user_id == user.id
    ).first()
    
    if not learning_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found"
        )
    
    db.delete(learning_path)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/migrate", response_model=MigrationResponse)
async def migrate_learning_paths(
    migration_data: MigrationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Migrate learning paths from local storage to the database.
    """
    if not migration_data.learning_paths:
        return MigrationResponse(success=True, migrated_count=0)
    
    migrated_count = 0
    errors = []
    
    # Log the incoming data for debugging
    print(f"Received {len(migration_data.learning_paths)} learning paths to migrate")
    
    for path_data in migration_data.learning_paths:
        try:
            # Extract required fields or use defaults
            topic = path_data.get("topic", "Untitled Path")
            favorite = path_data.get("favorite", False)
            tags = path_data.get("tags", [])
            source = path_data.get("source", "imported")
            
            # Extract path data correctly based on the source structure
            actual_path_data = path_data.get("path_data", path_data)
            
            # Use the original ID if available, otherwise generate a new UUID
            # This helps maintain compatibility with history URLs
            original_id = str(path_data.get("id", ""))
            if not original_id:
                original_id = str(path_data.get("path_id", ""))
            
            # If still no ID, generate one
            path_id = original_id if original_id else str(uuid.uuid4())
            
            print(f"Migrating learning path: '{topic}' with ID: {path_id}")
            
            # Check if a learning path with this ID already exists for this user
            existing_path = db.query(LearningPath).filter(
                LearningPath.user_id == user.id,
                LearningPath.path_id == path_id
            ).first()
            
            if existing_path:
                # Skip this one as it's already migrated
                print(f"Path '{topic}' with ID {path_id} already exists, skipping")
                continue
            
            # Get creation date from the data or use current time
            creation_date_str = path_data.get("creation_date")
            creation_date = None
            if creation_date_str:
                try:
                    creation_date = datetime.fromisoformat(creation_date_str)
                except (ValueError, TypeError):
                    creation_date = None
            
            if not creation_date:
                creation_date = datetime.utcnow()
            
            # Get last modified date if exists
            last_modified_date_str = path_data.get("last_modified_date")
            last_modified_date = None
            if last_modified_date_str:
                try:
                    last_modified_date = datetime.fromisoformat(last_modified_date_str)
                except (ValueError, TypeError):
                    last_modified_date = None
            
            # Create database entry
            db_learning_path = LearningPath(
                user_id=user.id,
                path_id=path_id,
                topic=topic,
                path_data=actual_path_data,
                favorite=favorite,
                tags=tags,
                source=source,
                creation_date=creation_date,
                last_modified_date=last_modified_date,
            )
            
            db.add(db_learning_path)
            migrated_count += 1
            print(f"Successfully added learning path '{topic}' with ID {path_id}")
            
        except Exception as e:
            error_msg = f"Error migrating path '{path_data.get('topic', 'unknown')}': {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    if migrated_count > 0:
        try:
            db.commit()
            print(f"Successfully committed {migrated_count} learning paths to database")
        except Exception as e:
            db.rollback()
            error_msg = f"Database error during commit: {str(e)}"
            print(error_msg)
            return MigrationResponse(
                success=False,
                migrated_count=0,
                errors=[error_msg]
            )
    
    return MigrationResponse(
        success=len(errors) == 0,
        migrated_count=migrated_count,
        errors=errors if errors else None
    )


@router.get("/{path_id}/pdf")
async def download_learning_path_pdf(
    path_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate and download a PDF version of a specific learning path.
    """
    # Find the learning path
    learning_path = db.query(LearningPath).filter(
        LearningPath.path_id == path_id,
        LearningPath.user_id == user.id
    ).first()
    
    if not learning_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found"
        )
    
    try:
        # Generate PDF
        pdf_path = generate_pdf(learning_path.__dict__, user.full_name)
        
        # Create a meaningful filename
        filename = create_filename(learning_path.topic)
        
        # Return the file as a download
        response = FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf"
        )
        
        # Set headers to ensure file downloads properly
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        
        # Cleanup is handled in background task
        # Return the file response
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )


# --- Updated Audio Generation Endpoint ---
@router.post(
    "/{path_id}/modules/{module_index}/submodules/{submodule_index}/audio",
    response_model=GenerateAudioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate or retrieve audio for a submodule"
)
async def generate_or_get_submodule_audio(
    request_data: GenerateAudioRequest, # Moved first
    path_id: str = Path(..., description="ID of the learning path (can be temporary task ID or persistent UUID)"),
    module_index: int = Path(..., ge=0, description="Zero-based index of the module"),
    submodule_index: int = Path(..., ge=0, description="Zero-based index of the submodule"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    credit_service: CreditService = Depends() # Inject CreditService
):
    """
    Generates audio narration for a specific submodule in the requested language.

    - If the learning path is persisted and audio already exists (assumed to be in the default language initially), returns the existing URL.
      (Note: This doesn't re-generate in a different language if already exists. Future enhancement could be to store language with URL).
    - If the learning path is persisted and audio doesn't exist, generates it in the requested language, saves the URL, and returns it.
    - If the learning path ID is temporary (not in DB), uses `request_data.path_data` to generate the audio in the requested language and returns the URL (without persisting).
    """
    logger.info(f"Received audio generation request for path {path_id}, module {module_index}, sub {submodule_index}, lang {request_data.language}")

    # --- Validate Language ---
    requested_language = request_data.language
    if requested_language not in SUPPORTED_AUDIO_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language '{requested_language}'. Supported languages are: {SUPPORTED_AUDIO_LANGUAGES}"
        )

    # 1. Try fetching from Database (for persisted paths)
    learning_path = db.query(LearningPath).filter(
        LearningPath.path_id == path_id,
        LearningPath.user_id == user.id
    ).first()

    is_persisted = learning_path is not None
    temp_path_data = request_data.path_data if not is_persisted else None

    if is_persisted:
        logger.info(f"Path {path_id} found in DB (persisted). Checking for existing audio URL.")
        # --- Check Cache (existing URL in path_data) ---
        # Note: Current cache check doesn't consider language. If found, returns existing URL.
        try:
            path_data_json = learning_path.path_data
            if isinstance(path_data_json, dict):
                modules = path_data_json.get('modules', [])
                if 0 <= module_index < len(modules):
                    submodules = modules[module_index].get('submodules', [])
                    if 0 <= submodule_index < len(submodules):
                        # TODO: Future: Store language alongside URL? e.g., audio_urls: {"en": "/path/en.mp3"}
                        existing_url = submodules[submodule_index].get('audio_url')
                        if existing_url:
                            logger.info(f"Found cached audio URL for {path_id}/{module_index}/{submodule_index}: {existing_url}. Returning cached version.")
                            return GenerateAudioResponse(audio_url=existing_url)
            else:
                logger.warning(f"path_data for persisted path {path_id} is not a dict. Type: {type(path_data_json)}")
        except Exception as e:
            # Log error but proceed to generate if cache check fails
            logger.exception(f"Error checking audio cache for {path_id}/{module_index}/{submodule_index}: {e}")

        # If no cached URL, proceed to generate and persist
        logger.info(f"No cached audio found for persisted path {path_id}. Charging credit and generating in '{requested_language}'...")
        notes = f"Audio generation ({requested_language}) for persisted path {path_id}, Mod {module_index}, Sub {submodule_index}"
        try:
            # Use credit service context manager
            async with credit_service.charge(user=user, amount=1, transaction_type=TransactionType.AUDIO_GENERATION_USE, notes=notes):
                generated_url = await generate_submodule_audio(
                    db=db,
                    learning_path=learning_path,
                    module_index=module_index,
                    submodule_index=submodule_index,
                    language=requested_language # Pass language
                )
            # If context manager exits without error, credit is deducted and committed.
            return GenerateAudioResponse(audio_url=generated_url)
        except HTTPException as http_exc:
            # If charge() raised 403, or generate_submodule_audio raised HTTPException
            # The context manager's __aexit__ handles refund if needed. Re-raise.
            raise http_exc
        except Exception as e:
            # Context manager's __aexit__ handles refund. Log and raise standard 500.
            logger.exception(f"Unexpected error during credit charge or audio generation for persisted path {path_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Audio generation failed unexpectedly.")

    else: # Temporary path
        logger.info(f"Path {path_id} not found in DB (temporary). Charging credit and generating audio in '{requested_language}' using request body data.")
        if not temp_path_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="path_data is required in the request body for temporary learning paths."
            )

        # Create a temporary LearningPath-like object for the service function
        class TempLearningPath:
            def __init__(self, data, temp_id):
                self.path_data = data
                self.id = None # Indicate it's not from DB
                self.path_id = temp_id # Keep temporary ID if needed

        temp_lp_obj = TempLearningPath(temp_path_data, path_id) # Use the path_id from the endpoint

        notes = f"Audio generation ({requested_language}) for temporary path {path_id}, Mod {module_index}, Sub {submodule_index}"
        try:
            # Use credit service context manager
            async with credit_service.charge(user=user, amount=1, transaction_type=TransactionType.AUDIO_GENERATION_USE, notes=notes):
                # Call the main service, it should skip DB ops based on temp_lp_obj.id == None
                generated_url = await generate_submodule_audio(
                    db=None, # Pass None for DB session for temp path
                    learning_path=temp_lp_obj,
                    module_index=module_index,
                    submodule_index=submodule_index,
                    language=requested_language # Pass language
                )
            # If context manager exits without error, credit is deducted and committed.
            return GenerateAudioResponse(audio_url=generated_url)

        except HTTPException as http_exc:
            # Context manager handles refund if needed. Re-raise.
            raise http_exc
        except Exception as e:
            # Context manager handles refund. Log and raise standard 500.
            logger.exception(f"Unexpected error during credit charge or audio generation for temporary path {path_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Audio generation failed unexpectedly for temporary path.") 