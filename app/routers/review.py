from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.utils.jwt import get_current_user
from app.models.user import User
from app.models.trip import Trip
from app.models.trip_member import TripMember
from app.models.review import Review

router = APIRouter(prefix="/reviews", tags=["Reviews"])

class ReviewPayload(BaseModel):
    rating: float
    text_review: Optional[str] = None

class ReviewResponse(BaseModel):
    id: str
    trip_id: str
    reviewer_id: str
    reviewee_id: str
    rating: float
    text_review: Optional[str]
    created_at: str

@router.post("/trip/{trip_id}/user/{reviewee_id}")
def create_review(
    trip_id: str,
    reviewee_id: str,
    payload: ReviewPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rate a fellow trip member after a completed trip.
    Calculates the new global trust aggregate score.
    """
    if payload.rating < 1.0 or payload.rating > 5.0:
        raise HTTPException(status_code=400, detail="Rating must be between 1.0 and 5.0")
        
    if str(current_user.id) == reviewee_id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")

    # Verify both were members of the trip
    reviewer_member = db.query(TripMember).filter(
        cast(TripMember.trip_id, String) == trip_id,
        cast(TripMember.user_id, String) == str(current_user.id)
    ).first()
    
    reviewee_member = db.query(TripMember).filter(
        cast(TripMember.trip_id, String) == trip_id,
        cast(TripMember.user_id, String) == reviewee_id
    ).first()

    if not reviewer_member or not reviewee_member:
        raise HTTPException(status_code=403, detail="Both users must be members of the trip to review each other")

    # Lock the reviewee user row first to prevent race conditions on score aggregation
    reviewee = db.query(User).filter(cast(User.id, String) == reviewee_id).with_for_update().first()
    if not reviewee:
        raise HTTPException(status_code=404, detail="User to review not found")

    # Check if review already exists
    existing = db.query(Review).filter(
        cast(Review.trip_id, String) == trip_id,
        cast(Review.reviewer_id, String) == str(current_user.id),
        cast(Review.reviewee_id, String) == reviewee_id
    ).first()
    
    if existing:
        db.rollback() # Release the row lock early
        raise HTTPException(status_code=400, detail="You have already reviewed this user for this trip")

    # Create Review
    new_review = Review(
        trip_id=trip_id,
        reviewer_id=str(current_user.id),
        reviewee_id=reviewee_id,
        rating=payload.rating,
        text_review=payload.text_review
    )
    db.add(new_review)
    db.flush() # Flush to DB so the len(all_reviews) catches it
    
    # Recalculate reviewee's trust score
    all_reviews = db.query(Review).filter(cast(Review.reviewee_id, String) == reviewee_id).all()
        
    total_score = sum(r.rating for r in all_reviews)
    new_count = len(all_reviews)
        
    reviewee.trust_score = round(total_score / new_count, 1) if new_count > 0 else 5.0
    reviewee.review_count = new_count

    db.commit()
    return {"message": "Review submitted successfully", "trust_score": reviewee.trust_score}

@router.get("/user/{user_id}", response_model=List[ReviewResponse])
def get_user_reviews(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all reviews received by a user.
    """
    reviews = db.query(Review).filter(cast(Review.reviewee_id, String) == user_id).order_by(Review.created_at.desc()).all()
    
    return [
        ReviewResponse(
            id=str(r.id),
            trip_id=str(r.trip_id),
            reviewer_id=str(r.reviewer_id),
            reviewee_id=str(r.reviewee_id),
            rating=r.rating,
            text_review=r.text_review,
            created_at=str(r.created_at)
        ) for r in reviews
    ]
