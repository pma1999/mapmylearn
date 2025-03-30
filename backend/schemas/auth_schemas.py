from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str
    remember_me: bool = False


class UserResponse(UserBase):
    """Schema for user data in responses."""
    id: int
    full_name: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiration
    user: UserResponse


class LearningPathBase(BaseModel):
    """Base schema for learning path."""
    topic: str
    path_data: Dict[str, Any]
    favorite: bool = False
    tags: List[str] = []
    source: str = "generated"


class LearningPathCreate(LearningPathBase):
    """Schema for creating a learning path."""
    pass


class LearningPathUpdate(BaseModel):
    """Schema for updating a learning path."""
    favorite: Optional[bool] = None
    tags: Optional[List[str]] = None


class LearningPathResponse(LearningPathBase):
    """Schema for learning path in responses."""
    id: int
    path_id: str
    user_id: int
    creation_date: datetime
    last_modified_date: Optional[datetime] = None

    class Config:
        orm_mode = True


class LearningPathList(BaseModel):
    """Schema for list of learning paths."""
    entries: List[LearningPathResponse]
    total: int
    page: int
    per_page: int


class MigrationRequest(BaseModel):
    """Schema for migrating local storage learning paths to database."""
    learning_paths: List[Dict[str, Any]]


class MigrationResponse(BaseModel):
    """Schema for migration response."""
    success: bool
    migrated_count: int
    errors: Optional[List[str]] = None 