from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.jwt import get_current_user
from app.schemas.match import MatchSuggestionResponse
from app.services import match_service
from typing import List

router = APIRouter(prefix="/match", tags=["Matching"])

@router.get("/suggestions", response_model=List[MatchSuggestionResponse])
def get_match_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the top algorithmic travel buddies for the active user.
    """
    return match_service.generate_match_suggestions(db=db, current_user=current_user)
