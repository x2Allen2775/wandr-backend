from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import json
from app.models.trip import Trip
from app.models.user import User
from app.models.interest import Interest
from app.models.notification import Notification
from app.schemas.trip import TripCreate
from sqlalchemy import or_, and_
from datetime import date

def create_trip(payload: TripCreate, user: User, db: Session) -> Trip:
    """Create a new future trip declaration."""
    db_trip = Trip(
        user_id=user.id,
        destination=payload.destination,
        country=payload.country,
        countries=json.dumps(payload.countries) if payload.countries else None,
        states=json.dumps(payload.states) if payload.states else None,
        cities=json.dumps(payload.cities) if payload.cities else None,
        travel_interests=json.dumps(payload.travel_interests) if payload.travel_interests else None,
        start_date=payload.start_date,
        end_date=payload.end_date,
        budget_type=payload.budget_type,
        notes=payload.notes,
        status="planned"
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip

def get_trips_by_user(user_id: str, db: Session) -> list[Trip]:
    """Get all trips planned by a specific user, and auto-complete past trips."""
    trips = db.query(Trip).filter(Trip.user_id == user_id).order_by(Trip.start_date.desc()).all()
    
    # Auto-request a trip review if the end date has passed.
    today = date.today()
    dirty = False
    for t in trips:
        if t.end_date < today and t.status == "planned":
            t.status = "needs_review"
            location_name = t.country if t.country else t.destination
            notif = Notification(
                user_id=t.user_id,
                type="trip_review",
                content=f"How was your trip to {location_name}? Would you like to add it to your travel passport?",
                target_id=t.id
            )
            db.add(notif)
            dirty = True
            
    if dirty:
        db.commit()
        
    return trips

def discover_trips(
    db: Session,
    current_user: User,
    destination: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    budget_types: list[str] | None = None,
    travel_styles: list[str] | None = None,
    interests: list[str] | None = None,
    limit: int = 20,
    offset: int = 0
) -> list[Trip]:
    """
    Core Discovery Engine for Pillar 5.
    Find other users' trips based on destination, overlapping dates, or budget.
    """
    query = db.query(Trip).filter(
        Trip.user_id != current_user.id,
        Trip.end_date >= date.today() # Hide past trips from Discovery completely
    )
    
    if destination:
        query = query.filter(Trip.destination.ilike(f"%{destination}%"))
        
    if start_date and end_date:
        # Overlap Logic: (Trip A starts before Trip B ends) AND (Trip A ends after Trip B starts)
        query = query.filter(
            and_(
                Trip.start_date <= end_date,
                Trip.end_date >= start_date
            )
        )
        
    if budget_types:
        query = query.filter(Trip.budget_type.in_(budget_types))
        
    if travel_styles:
        query = query.filter(Trip.user.has(User.travel_style.in_(travel_styles)))
        
    if interests:
        query = query.filter(Trip.user.has(User.interests.any(Interest.name.in_(interests))))
        
    return query.order_by(Trip.start_date.asc()).limit(limit).offset(offset).all()
