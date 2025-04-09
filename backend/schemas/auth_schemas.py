from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import field_validator


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
    credits: int = 0
    is_admin: bool = False
    is_active: bool = True

    class Config:
        from_attributes = True


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
        from_attributes = True


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


# Admin schemas for user and credit management

class AdminUserUpdate(BaseModel):
    """Schema for admin to update user details."""
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class UserListFilters(BaseModel):
    """Schema for filtering user list."""
    search: Optional[str] = None  # Search in email or full_name
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    has_credits: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int


class AddCreditsRequest(BaseModel):
    """Schema for adding credits to a user."""
    user_id: int
    amount: int = Field(..., gt=0)
    notes: Optional[str] = None  # Will be stored as 'description' in the database


class CreditTransactionResponse(BaseModel):
    """Schema for credit transaction in responses."""
    id: int
    user_id: int
    admin_id: Optional[int] = None
    amount: int
    action_type: str
    created_at: datetime
    description: Optional[str] = None  # Actual field in database
    notes: Optional[str] = None  # Alias for description used by frontend
    user_email: Optional[str] = None
    admin_email: Optional[str] = None

    class Config:
        from_attributes = True
        
    @field_validator('notes', mode='before')
    @classmethod
    def set_notes_from_description(cls, v, info):
        # If notes is None but description exists, use description
        if v is None and 'description' in info.data:
            return info.data.get('description')
        return v


class CreditTransactionListFilters(BaseModel):
    """Schema for filtering credit transaction list."""
    user_id: Optional[int] = None
    admin_id: Optional[int] = None
    action_type: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None


class CreditTransactionListResponse(BaseModel):
    """Schema for paginated credit transaction list response."""
    transactions: List[CreditTransactionResponse]
    total: int
    page: int
    per_page: int 