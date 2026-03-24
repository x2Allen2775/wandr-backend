from pydantic import BaseModel, EmailStr, field_validator, Field, model_validator
from typing import Optional, List, Any
from datetime import datetime
import re


# ── Signup ─────────────────────────────────────────────────────────
class UserSignup(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError(
                "Username must be 3-30 chars, only letters, numbers, underscores."
            )
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


# ── Login ──────────────────────────────────────────────────────────
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ── Onboarding — Travel Interests (shown after first login) ────────
class TravelInterests(BaseModel):
    travel_interests: List[str]   # ["solo", "beaches", "mountains", ...]
    travel_style: Optional[str] = None  # solo | group | adventure | chill
    budget_preference: Optional[str] = None # budget | mid | luxury
    languages: Optional[List[str]] = None
    location: Optional[str] = None


# ── Profile Update ─────────────────────────────────────────────────
class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    travel_interests: Optional[List[str]] = None
    countries_visited: Optional[List[str]] = None
    travel_style: Optional[str] = None
    budget_preference: Optional[str] = None
    languages: Optional[List[str]] = None
    is_public: Optional[bool] = None
    public_key: Optional[str] = None


# ── Profile Response (what API returns) ────────────────────────────
class UserProfile(BaseModel):
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str]
    bio: Optional[str]
    profile_picture: Optional[str]
    location: Optional[str]
    website: Optional[str]
    travel_interests: Optional[List[str]] = Field(default=None, alias="interests")
    countries_visited: Optional[List[str]]
    travel_style: Optional[str]
    budget_preference: Optional[str]
    languages: Optional[List[str]]
    kyc_status: str
    is_verified: bool
    is_public: bool
    public_key: Optional[str] = None
    following_count: int = 0
    followers_count: int = 0
    created_at: datetime

    @field_validator("travel_interests", mode="before")
    @classmethod
    def extract_interest_names(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        # If the input is a list of SQLAlchemy Interest objects, extract names.
        if isinstance(v, list) and len(v) > 0 and hasattr(v[0], "name"):
            return [interest.name for interest in v]
        return v

    class Config:
        from_attributes = True
        populate_by_name = True


# ── Token Response ─────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

# ── Remote Profile (Viewing other users) ─────────────────────────
class RemoteProfileResponse(UserProfile):
    follower_count: int = 0
    mutual_connections_count: int = 0
    follow_status: str = "none" # none, requested, following


# ── Generic Message ────────────────────────────────────────────────
class MessageResponse(BaseModel):
    message: str
