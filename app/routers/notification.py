from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.models.trip_member import TripJoinRequest, TripMember
from app.models.trip import Trip
from app.utils.jwt import get_current_user
from app.schemas.notification import NotificationResponse

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

@router.get("/", response_model=list[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch all notifications for the current user, ordered by most recent."""
    return db.query(Notification).filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()

@router.get("/counts")
def get_notification_counts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch unread counts for badges (notifications, join requests, messages)"""
    # 1. Unread generic notifications
    unread_notifs = db.query(Notification).filter_by(
        user_id=current_user.id, 
        is_read=False
    ).count()

    # 2. Pending Join Requests for trips the user owns
    my_trips = db.query(Trip.id).filter(Trip.user_id == current_user.id).all()
    my_trip_ids = [str(t.id) for t in my_trips]
    
    pending_requests = 0
    if my_trip_ids:
        pending_requests = db.query(TripJoinRequest).filter(
            TripJoinRequest.trip_id.in_(my_trip_ids),
            TripJoinRequest.status == "pending"
        ).count()

    # 3. Unread Messages (placeholder for now, returning 0 until message read state is added)
    unread_msgs = 0

    return {
        "unread_notifications": unread_notifs,
        "pending_join_requests": pending_requests,
        "unread_messages": unread_msgs
    }

@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a specific notification as read so the bell icon updates."""
    notif = db.query(Notification).filter_by(id=notification_id, user_id=current_user.id).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif
