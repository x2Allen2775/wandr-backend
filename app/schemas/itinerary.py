from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ItineraryMessageBase(BaseModel):
    role: str
    content: str
    
class ItineraryMessageResponse(ItineraryMessageBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ItineraryCreate(BaseModel):
    # Only used if a User wants to explicitly create a named trip to start parsing
    destination: Optional[str] = None
    days: Optional[str] = None

class ItineraryResponse(BaseModel):
    id: str
    user_id: str
    destination: Optional[str] = None
    days: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ItineraryMessageResponse] = []

    class Config:
        from_attributes = True

class AIChatRequest(BaseModel):
    content: str
