from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import uuid
from datetime import datetime

from backend.config.database import get_db
from backend.models.auth_models import User, LearningPath
from backend.schemas.auth_schemas import LearningPathCreate, LearningPathUpdate, LearningPathResponse, LearningPathList, MigrationRequest, MigrationResponse
from backend.utils.auth_middleware import get_current_user

router = APIRouter(prefix="/learning-paths", tags=["learning-paths"])


@router.get("", response_model=LearningPathList)
async def get_learning_paths(
    sort_by: str = Query("creation_date", description="Field to sort by"),
    source: Optional[str] = Query(None, description="Filter by source type"),
    search: Optional[str] = Query(None, description="Search term for topic or tags"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    favorite_only: bool = Query(False, description="Only return favorite learning paths"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all learning paths for the current user with filtering and pagination.
    """
    # Build query
    query = db.query(LearningPath).filter(LearningPath.user_id == user.id)
    
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
            # Note: Proper JSON/JSONB search would depend on the specific database
            # For PostgreSQL, we would use something like:
            # or LearningPath.tags.cast(sa.String).ilike(search_term)
        )
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply sorting
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
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    # Execute query
    learning_paths = query.all()
    
    return {
        "entries": learning_paths,
        "total": total_count,
        "page": page,
        "per_page": per_page
    }


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
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create learning path"
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
    
    return {"detail": "Learning path deleted successfully"}


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