from pydantic import BaseModel
from typing import List
from app.schemas.user import UserProfile

class MatchSuggestionResponse(BaseModel):
    user: UserProfile
    score: int
    match_reasons: List[str]

    class Config:
        from_attributes = True
