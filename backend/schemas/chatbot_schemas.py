from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class GroundingSource(BaseModel):
    """Individual grounding source information"""
    title: str
    uri: str

class GroundingMetadata(BaseModel):
    """Metadata about grounding with Google Search for premium users"""
    is_grounded: bool
    search_queries: Optional[List[str]] = None
    sources_count: Optional[int] = None
    sources: Optional[List[GroundingSource]] = None
    model_used: Optional[str] = None

class ChatRequest(BaseModel):
    path_id: str
    submodule_index: int # Assuming simple index is enough, adjust if needed
    module_index: int # Need module index too to find the submodule
    user_message: str
    thread_id: str
    path_data: Optional[Dict[str, Any]] = None  # Ephemeral full path data for new sessions

class ChatResponse(BaseModel):
    ai_response: str
    thread_id: str # Return thread_id in case it was generated/modified
    grounding_metadata: Optional[GroundingMetadata] = None  # Grounding info for premium users

class ClearChatRequest(BaseModel):
    thread_id: str 