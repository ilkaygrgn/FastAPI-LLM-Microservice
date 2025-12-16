from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str = Field(..., description="The users message to the assistant")
    session_id: Optional[str] = Field(None, description="The id for the chat session")
    use_rag: Optional[bool] = Field(True, description="Whether to use RAG for this request")