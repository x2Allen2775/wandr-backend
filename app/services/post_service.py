from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate
import json

def create_post(payload: PostCreate, user: User, db: Session) -> Post:
    """Create a new social post for the authenticated user."""
    db_post = Post(
        user_id=user.id,
        caption=payload.caption,
        media_urls=json.dumps(payload.media_urls) if payload.media_urls else None,
        location=payload.location,
        visibility=payload.visibility,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def get_post_by_id(post_id: str, db: Session) -> Post:
    """Fetch a single post by ID."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post

def get_posts_by_user(user_id: str, current_user: User, db: Session, limit: int = 20, offset: int = 0) -> list[Post]:
    """Fetch paginated posts belonging to a specific user, respecting privacy locks."""
    # Enforce privacy check
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not target_user.is_public and target_user.id != current_user.id:
        if target_user not in current_user.following:
            return [] # Locked out
            
    posts = (
        db.query(Post)
        .filter(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return posts

def delete_post(post_id: str, current_user: User, db: Session):
    """Delete a post, enforcing absolute ownership validation."""
    post = get_post_by_id(post_id, db)
    
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this post."
        )
        
    db.delete(post)
    db.commit()

def get_timeline_feed(current_user: User, db: Session, limit: int = 20, offset: int = 0) -> list[Post]:
    """
    Project 5: Discovery Feed Algorithm.
    Fetches the timeline feed prioritizing:
      1. People the user directly follows.
      2. The user's own posts.
      3. Posts from global users who share the SAME Travel Interests (Discovery).
    """
    
    # Phase 1: Core Graph (Following + Self)
    target_ids = {u.id for u in current_user.following}
    target_ids.add(current_user.id)

    # Phase 2: Discovery Graph (Pillar 2 Fusion)
    # Extract the user's saved travel interests (e.g., ["Mountains", "Solo Backpacker"])
    my_interest_names = [interest.name for interest in current_user.interests]
    
    if my_interest_names:
        # We need to find other users who have AT LEAST ONE intersecting interest
        from app.models.interest import Interest  # Late import to avoid edge case circle loops if any
        
        # Query global users who are NOT the current user, joining on interests
        similar_users = (
            db.query(User.id)
            .join(User.interests)
            .filter(User.id != current_user.id)
            .filter(User.is_public == True)
            .filter(Interest.name.in_(my_interest_names))
            .distinct()
            .all()
        )
        
        # Add these discovery users to the target pool!
        for similar in similar_users:
            target_ids.add(similar.id)

    # Phase 3: Fetch and Sort
    # Now we fetch all public posts authored by ANYONE in our massive Target IDs pool.
    posts = (
        db.query(Post)
        .filter(Post.user_id.in_(list(target_ids)))
        .filter(Post.visibility == "public")
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    return posts
