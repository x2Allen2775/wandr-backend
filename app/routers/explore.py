from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from typing import List

from app.database import get_db
from app.utils.jwt import get_current_user
from app.models.user import User
from app.models.post import Post
from app.schemas.post import PostResponse

router = APIRouter(prefix="/explore", tags=["Explore"])

@router.get("/", response_model=List[PostResponse], summary="Get the Global Explore Feed")
def get_explore_feed(
    limit: int = Query(20, ge=1, le=100), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch a randomized grid of posts from Public accounts 
    that the user does NOT currently follow.
    """
    following_ids = [u.id for u in current_user.following]
    
    # Base query: Join Post -> User
    query = db.query(Post).join(User, Post.user_id == User.id)
    
    # Filters: Public accounts, not the current user, not already following
    query = query.filter(
        User.is_public == True,
        User.id != current_user.id,
    )
    
    if following_ids:
        query = query.filter(~User.id.in_(following_ids))
        
    # Randomize and limit
    explore_posts = query.order_by(func.random()).limit(limit).all()
    
    return explore_posts
