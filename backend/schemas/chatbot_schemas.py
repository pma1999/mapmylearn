from pydantic import BaseModel
from typing import Optional, Dict, Any

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

class ClearChatRequest(BaseModel):
    thread_id: str 