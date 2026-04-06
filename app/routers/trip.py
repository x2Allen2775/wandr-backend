from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List
import json
from pydantic import BaseModel

class TripReviewPayload(BaseModel):
    was_successful: bool

from app.database import get_db
from app.models.user import User
from app.utils.jwt import get_current_user
from app.schemas.trip import TripCreate, TripResponse, TripWithUserResponse
from app.services import trip_service

router = APIRouter(
    prefix="/trips",
    tags=["Trips"]
)

@router.post("/create", response_model=TripResponse)
def create_trip(
    payload: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Declare a new upcoming trip to the network."""
    return trip_service.create_trip(payload, current_user, db)

@router.get("/user/{user_id}", response_model=list[TripResponse])
def get_user_trips(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all trips belonging to a specific user ID."""
    return trip_service.get_trips_by_user(user_id, db)

@router.get("/discover", response_model=list[TripWithUserResponse])
def discover_trips(
    destination: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    budget_types: Optional[List[str]] = Query(None),
    travel_styles: Optional[List[str]] = Query(None),
    interests: Optional[List[str]] = Query(None),
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search the global network for overlapping trips based on location and date.
    Returns the Trip data along with the attached User profile.
    """
    return trip_service.discover_trips(
        db=db,
        current_user=current_user,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        budget_types=budget_types,
        travel_styles=travel_styles,
        interests=interests,
        limit=limit,
        offset=offset
    )

@router.post("/{trip_id}/review")
def review_trip(
    trip_id: str,
    payload: TripReviewPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Handle the post-trip evaluation notification.
    If 'was_successful' is true, inject the Trip's Country into the User's Passport.
    """
    from app.models.trip import Trip
    
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    if trip.status != "needs_review":
        raise HTTPException(status_code=400, detail="Trip does not need a review.")
        
    trip.status = "completed"
    
    if payload.was_successful and (trip.country or trip.destination):
        country_to_add = trip.country if trip.country else trip.destination
        
        # safely deserialize current json array
        visited = []
        if current_user.countries_visited:
            try:
                visited = json.loads(current_user.countries_visited)
            except:
                pass
                
        if country_to_add not in visited:
            visited.append(country_to_add)
            current_user.countries_visited = json.dumps(visited)
            
    db.commit()
    return {"message": "Review appended to passport successfully"}

@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a trip entirely (Owner only).
    Cascades down wiping members, chat history, and requests to preserve database hygiene.
    """
    from app.models.trip import Trip
    from app.models.trip_member import TripMember, TripJoinRequest, GroupMessage
    from sqlalchemy import cast, String

    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if str(trip.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You do not have permission to delete this trip.")

    # Manual cascade delete for associated tables
    db.query(GroupMessage).filter(cast(GroupMessage.trip_id, String) == trip_id).delete(synchronize_session=False)
    db.query(TripJoinRequest).filter(cast(TripJoinRequest.trip_id, String) == trip_id).delete(synchronize_session=False)
    db.query(TripMember).filter(cast(TripMember.trip_id, String) == trip_id).delete(synchronize_session=False)

    # Delete the trip itself
    db.delete(trip)
    db.commit()

    return None
