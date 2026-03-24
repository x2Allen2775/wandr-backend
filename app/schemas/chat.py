from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.post import PostAuthorResponse

class MessageCreate(BaseModel):
    content: Optional[str] = None
    iv: Optional[str] = None
    media_url: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    receiver_id: str
    content: Optional[str] = None
    iv: Optional[str] = None
    media_url: Optional[str] = None
    is_read: bool
    timestamp: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    other_user: PostAuthorResponse  # The details of the person you are talking to
    last_message: Optional[MessageResponse] = None

    class Config:
        from_attributes = True

class InboxResponse(BaseModel):
    inbox: List[ConversationResponse]
    requests: List[ConversationResponse]
