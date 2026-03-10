from pydantic import BaseModel, HttpUrl, Field, field_validator
import json
from typing import Optional, List
from datetime import datetime
from app.schemas.user import UserProfile

class PostCreate(BaseModel):
    caption: Optional[str] = None
    media_urls: Optional[List[str]] = None
    location: Optional[str] = None
    visibility: str = "public"

class PostAuthorResponse(BaseModel):
    id: str
    username: str
    full_name: Optional[str]
    profile_picture: Optional[str]

    class Config:
        from_attributes = True

class PostResponse(BaseModel):
    id: str
    user_id: str
    caption: Optional[str]
    media_urls: Optional[List[str]]
    location: Optional[str]
    visibility: str
    created_at: datetime
    comments_count: int = 0
    
    # We embed a miniature author object to make frontend rendering easy
    author: PostAuthorResponse

    class Config:
        from_attributes = True

    @field_validator('media_urls', mode='before')
    @classmethod
    def parse_media_urls(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v


class CommentCreate(BaseModel):
    text: str
    parent_id: Optional[str] = None

class CommentResponse(BaseModel):
    id: str
    post_id: str
    text: str
    parent_id: Optional[str] = None
    created_at: datetime
    author: PostAuthorResponse
    replies: List['CommentResponse'] = []

    class Config:
        from_attributes = True

CommentResponse.model_rebuild()
