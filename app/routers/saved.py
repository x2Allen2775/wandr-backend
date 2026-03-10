from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.utils.jwt import get_current_user
from app.models.user import User
from app.models.post import Post
from app.models.saved_post import SavedPost
from app.schemas.post import PostResponse

router = APIRouter(tags=["Saved Posts"])


@router.post("/saved/{post_id}", status_code=status.HTTP_201_CREATED)
def save_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bookmark / save a post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = (
        db.query(SavedPost)
        .filter(SavedPost.user_id == current_user.id, SavedPost.post_id == post_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Post already saved")

    saved = SavedPost(user_id=current_user.id, post_id=post_id)
    db.add(saved)
    db.commit()
    return {"detail": "Post saved"}


@router.delete("/saved/{post_id}", status_code=status.HTTP_200_OK)
def unsave_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a post from saved / bookmarks."""
    saved = (
        db.query(SavedPost)
        .filter(SavedPost.user_id == current_user.id, SavedPost.post_id == post_id)
        .first()
    )
    if not saved:
        raise HTTPException(status_code=404, detail="Post not in saved")

    db.delete(saved)
    db.commit()
    return {"detail": "Post removed from saved"}


@router.get("/saved", response_model=List[PostResponse])
def get_saved_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all saved posts for the current user, newest saved first."""
    saved_entries = (
        db.query(SavedPost)
        .filter(SavedPost.user_id == current_user.id)
        .order_by(SavedPost.saved_at.desc())
        .all()
    )
    post_ids = [s.post_id for s in saved_entries]
    if not post_ids:
        return []

    posts = db.query(Post).filter(Post.id.in_(post_ids)).all()
    # Maintain saved order
    post_map = {p.id: p for p in posts}
    return [post_map[pid] for pid in post_ids if pid in post_map]


@router.get("/saved/check/{post_id}")
def check_saved(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if a post is saved by the current user."""
    exists = (
        db.query(SavedPost)
        .filter(SavedPost.user_id == current_user.id, SavedPost.post_id == post_id)
        .first()
    )
    return {"is_saved": exists is not None}
