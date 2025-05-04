from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
from pydantic import field_validator, model_validator, field_serializer


# Helper function to format datetime to ISO 8601 UTC with 'Z'
def serialize_datetime_to_iso_z(dt: Optional[datetime]) -> Optional[str]:
    if dt:
        # Assume naive datetime is UTC, make it aware, then format
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # Format to ISO string and ensure 'Z' for UTC
        return dt.isoformat().replace('+00:00', 'Z')
    return None


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

    @field_serializer('created_at', 'last_login')
    def serialize_dates(self, dt: Optional[datetime]) -> Optional[str]:
        return serialize_datetime_to_iso_z(dt)

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiration
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str


class LearningPathBase(BaseModel):
    """Base schema for course."""
    topic: str
    language: str = Field(..., min_length=2, max_length=10, description="ISO 639-1 language code")
    path_data: Dict[str, Any]
    favorite: bool = False
    tags: List[str] = []
    source: str = "generated"


class LearningPathCreate(LearningPathBase):
    """Schema for creating a course."""
    pass
    task_id: Optional[str] = Field(None, description="Optional task ID from generation to link history entry")


class LearningPathUpdate(BaseModel):
    """Schema for updating a course."""
    favorite: Optional[bool] = None
    tags: Optional[List[str]] = None


class LearningPathPublicityUpdate(BaseModel):
    """Schema for updating the public status of a course."""
    is_public: bool


class LearningPathResponse(LearningPathBase):
    """Schema for course in responses."""
    id: int
    path_id: str
    user_id: int
    creation_date: datetime
    last_modified_date: Optional[datetime] = None
    progress_map: Optional[Dict[str, bool]] = Field(None, description="Map of submodule keys to completion status (e.g., {'0_0': true, '0_1': false})")
    last_visited_module_idx: Optional[int] = Field(None, description="Index of the last module visited by the user for this path")
    last_visited_submodule_idx: Optional[int] = Field(None, description="Index of the last submodule visited by the user for this path")
    is_public: bool = False
    share_id: Optional[str] = None

    @field_serializer('creation_date', 'last_modified_date')
    def serialize_dates(self, dt: Optional[datetime]) -> Optional[str]:
        return serialize_datetime_to_iso_z(dt)

    class Config:
        from_attributes = True


class LearningPathList(BaseModel):
    """Schema for list of courses."""
    entries: List[LearningPathResponse]
    total: int
    page: int
    per_page: int


class MigrationRequest(BaseModel):
    """Schema for migrating local storage courses to database."""
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
    notes: Optional[str] = None  # Will be stored as 'notes' in the database


class CreditTransactionResponse(BaseModel):
    """Schema for credit transaction in responses."""
    id: int
    user_id: int
    admin_id: Optional[int] = None
    amount: int
    action_type: str
    created_at: datetime
    notes: Optional[str] = None  # Actual field in database
    description: Optional[str] = None  # Alias for notes for backwards compatibility
    user_email: Optional[str] = None
    admin_email: Optional[str] = None

    @field_serializer('created_at')
    def serialize_created_at(self, dt: Optional[datetime]) -> Optional[str]:
        return serialize_datetime_to_iso_z(dt)

    class Config:
        from_attributes = True
    
    @model_validator(mode='before')
    @classmethod
    def map_db_fields(cls, data):
        """Map database model fields to schema fields"""
        if isinstance(data, dict):
            return data
            
        # Handle SQLAlchemy model conversion
        if hasattr(data, '__dict__'):
            # Copy data to avoid modifying the original
            model_dict = data.__dict__.copy()
            
            # Map transaction_type to action_type
            if hasattr(data, 'transaction_type') and data.transaction_type is not None:
                model_dict['action_type'] = data.transaction_type
                
            # Copy admin_user_id to admin_id if needed
            if (
                hasattr(data, 'admin_user_id') and data.admin_user_id is not None
                and ('admin_id' not in model_dict or model_dict['admin_id'] is None)
            ):
                model_dict['admin_id'] = data.admin_user_id
                
            return model_dict
            
        return data
        
    @field_validator('action_type', mode='before')
    @classmethod
    def map_transaction_type_to_action_type(cls, v, info):
        """Map transaction_type from the model to action_type in the schema"""
        if v is None and hasattr(info.data, 'transaction_type'):
            return info.data.transaction_type
        return v
        
    @field_validator('description', mode='before')
    @classmethod
    def set_description_from_notes(cls, v, info):
        # If description is None but notes exists, use notes
        if v is None and 'notes' in info.data:
            return info.data.get('notes')
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


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password reset."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for resetting password with a token."""
    token: str
    new_password: str = Field(..., min_length=8)


class GenerateAudioRequest(BaseModel):
    """Request body for generating audio."""
    path_data: Optional[Dict[str, Any]] = None # Needed for temporary paths
    language: str # ISO language code like 'en', 'es'
    force_regenerate: bool = False # Add this field
    audio_style: Optional[str] = Field("standard", description="Desired style for audio script and TTS delivery (e.g., standard, engaging, calm_narrator, conversational, grumpy_genius)")


class GenerateAudioResponse(BaseModel):
    """Response body for audio generation."""
    audio_url: str = Field(..., description="URL to the generated audio file") 