from pydantic import BaseModel

class ChatRequest(BaseModel):
    path_id: str
    submodule_index: int # Assuming simple index is enough, adjust if needed
    module_index: int # Need module index too to find the submodule
    user_message: str
    thread_id: str

class ChatResponse(BaseModel):
    ai_response: str
    thread_id: str # Return thread_id in case it was generated/modified

class ClearChatRequest(BaseModel):
    thread_id: str 