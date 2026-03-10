from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.utils.jwt import get_current_user
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.schemas.post import PostCreate, PostResponse, CommentCreate, CommentResponse
from app.services import post_service

router = APIRouter(tags=["Posts & Feed"])

@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new post with a caption and media URL."""
    return post_service.create_post(payload, current_user, db)

@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: str, db: Session = Depends(get_db)):
    """Fetch a single post by its ID."""
    return post_service.get_post_by_id(post_id, db)

@router.get("/posts/user/{user_id}", response_model=List[PostResponse])
def get_user_posts(
    user_id: str, 
    limit: int = Query(20, ge=1, le=100), 
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch a paginated list of posts for a specific user (like a profile view)."""
    return post_service.get_posts_by_user(user_id, current_user, db, limit, offset)

@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a post. Enforces ownership — you can only delete your own posts."""
    post_service.delete_post(post_id, current_user, db)
    return None

@router.get("/feed", response_model=List[PostResponse], summary="Get the Global Timeline Feed")
def get_feed(
    limit: int = Query(20, ge=1, le=100), 
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires auth to see feed
):
    """
    Fetch the main social feed. 
    Currently returns a chronological list of posts from followed users.
    """
    return post_service.get_timeline_feed(current_user, db, limit, offset)


# ─── Comments ─────────────────────────────────────────

@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: str,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a comment or reply to a post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        text=payload.text,
        parent_id=payload.parent_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(
    post_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get top-level comments for a post, newest first. Replies are nested."""
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .filter(Comment.parent_id == None)
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return comments

@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete your own comment."""
    from fastapi import HTTPException
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    db.delete(comment)
    db.commit()
    return None

