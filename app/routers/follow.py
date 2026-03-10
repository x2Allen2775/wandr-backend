from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.utils.jwt import get_current_user
from app.models.user import User, FollowRequest
from app.schemas.user import UserProfile
from app.schemas.post import PostAuthorResponse  # Reusing the mini profile schema for compact follow lists
from app.services import follow_service
from app.services.user_service import _deserialize_user

router = APIRouter(tags=["Social Graph (Follows)"])

@router.post("/follow/{target_user_id}", status_code=status.HTTP_201_CREATED)
def follow_user(
    target_user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Follow another user by their ID."""
    status_msg = follow_service.follow_user(current_user, target_user_id, db)
    return {"message": f"Successfully processed follow action for user {target_user_id}", "status": status_msg}


@router.delete("/follow/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    target_user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unfollow a user."""
    follow_service.unfollow_user(current_user, target_user_id, db)
    return None


@router.get("/followers/{user_id}", response_model=List[PostAuthorResponse])
def get_followers(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all users who follow a given user_id."""
    followers = follow_service.get_followers(user_id, db, limit, offset)
    return followers


@router.get("/following/{user_id}", response_model=List[PostAuthorResponse])
def get_following(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all users that a given user_id is currently following."""
    following = follow_service.get_following(user_id, db, limit, offset)
    return following

@router.post("/requests/{request_id}/accept", status_code=status.HTTP_200_OK)
def accept_follow_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a pending follow request for a private account."""
    req = db.query(FollowRequest).filter(FollowRequest.id == request_id, FollowRequest.receiver_id == current_user.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Follow request not found")
    
    sender = db.query(User).filter(User.id == req.sender_id).first()
    if sender and current_user not in sender.following:
        sender.following.append(current_user)
        
    db.delete(req)
    db.commit()
    return {"message": "Request accepted"}

@router.post("/requests/{request_id}/reject", status_code=status.HTTP_200_OK)
def reject_follow_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject a pending follow request."""
    req = db.query(FollowRequest).filter(FollowRequest.id == request_id, FollowRequest.receiver_id == current_user.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Follow request not found")
    
    db.delete(req)
    db.commit()
    return {"message": "Request rejected"}
