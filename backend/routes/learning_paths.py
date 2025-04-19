from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import uuid
import os
from datetime import datetime
from fastapi.responses import FileResponse
import logging

from backend.config.database import get_db
from backend.models.auth_models import User, LearningPath
from backend.schemas.auth_schemas import LearningPathCreate, LearningPathUpdate, LearningPathResponse, LearningPathList, MigrationRequest, MigrationResponse
from backend.utils.auth_middleware import get_current_user
from backend.utils.pdf_generator import generate_pdf, create_filename

router = APIRouter(prefix="/learning-paths", tags=["learning-paths"])
logger = logging.getLogger(__name__) # Add logger instance


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
    
    # Create database entry
    db_learning_path = LearningPath(
        user_id=user.id,
        path_id=path_id,
        topic=learning_path.topic,
        language=learning_path.language,
        path_data=learning_path.path_data,
        favorite=learning_path.favorite,
        tags=learning_path.tags,
        source=learning_path.source,
        creation_date=datetime.utcnow(),
    )
    
    try:
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