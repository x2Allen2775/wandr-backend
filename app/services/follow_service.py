from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, FollowRequest

def follow_user(follower: User, target_user_id: str, db: Session) -> str:
    """Create a follow relationship or FollowRequest if private."""
    if follower.id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself."
        )

    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User to follow not found.")

    if target_user in follower.following:
        raise HTTPException(status_code=400, detail="You already follow this user.")

    # Check if target is private
    if not target_user.is_public:
        # Check if request already exists
        existing_req = db.query(FollowRequest).filter(
            FollowRequest.sender_id == follower.id,
            FollowRequest.receiver_id == target_user_id
        ).first()
        if existing_req:
            raise HTTPException(status_code=400, detail="Follow request already sent.")
        
        new_req = FollowRequest(sender_id=follower.id, receiver_id=target_user_id)
        db.add(new_req)
        db.commit()
        return "requested"

    # Public account, follow instantly
    follower.following.append(target_user)
    db.commit()
    return "following"

def unfollow_user(follower: User, target_user_id: str, db: Session):
    """Remove a follow relationship or cancel a follow request."""
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User to unfollow not found.")

    # If following, remove it
    if target_user in follower.following:
        follower.following.remove(target_user)
        db.commit()
        return

    # If requested, cancel request
    pending_req = db.query(FollowRequest).filter(
        FollowRequest.sender_id == follower.id,
        FollowRequest.receiver_id == target_user_id
    ).first()
    if pending_req:
        db.delete(pending_req)
        db.commit()
        return

    raise HTTPException(status_code=400, detail="You do not follow this user and have no pending requests.")

def get_followers(user_id: str, db: Session, limit: int = 50, offset: int = 0) -> list[User]:
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Needs to handle the Appended Lazy collection
    return target_user.followers[offset : offset + limit]

def get_following(user_id: str, db: Session, limit: int = 50, offset: int = 0) -> list[User]:
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Needs to handle the Appended Lazy collection
    return target_user.following.limit(limit).offset(offset).all()
