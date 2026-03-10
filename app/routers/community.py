from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.user import UserProfile
from app.utils.jwt import get_current_user
from app.models.user import User
from app.services.community_service import get_users_by_interest
from app.services.user_service import _deserialize_user

router = APIRouter(prefix="/community", tags=["Community - Matching"])


@router.get("/users", response_model=List[UserProfile], summary="Find users by travel interest")
def find_users_by_interest(
    interest: str = Query(..., description="The name of the interest to filter by (e.g., 'solo', 'beaches')"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch a list of users who share a specific travel interest.
    
    This powers the matching algorithm for the community feed.
    """
    users = get_users_by_interest(interest, db)
    return [_deserialize_user(u) for u in users]
