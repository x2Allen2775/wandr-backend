import json

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.interest import Interest
from app.schemas.user import ProfileUpdate, TravelInterests


def get_user_profile(user: User) -> User:
    """Return user profile — already fetched via JWT dependency."""
    return user


def _assign_interests(user: User, interests_names: list[str], db: Session):
    """Helper to find or create Interest records and link them to a user."""
    # Find existing interests
    existing = db.query(Interest).filter(Interest.name.in_(interests_names)).all()
    existing_map = {i.name: i for i in existing}
    
    new_interests = []
    # Create missing interests
    for name in interests_names:
        if name not in existing_map:
            new_interest = Interest(name=name)
            db.add(new_interest)
            new_interests.append(new_interest)
    
    # Assign both existing and newly created interests to the user
    user.interests = existing + new_interests


def update_user_profile(user: User, payload: ProfileUpdate, db: Session) -> User:
    """Update mutable profile fields for an authenticated user."""

    update_data = payload.model_dump(exclude_unset=True)

    # Check username uniqueness if changing
    if "username" in update_data and update_data["username"]:
        new_username = update_data["username"].strip().lower()
        if new_username != user.username:
            existing = db.query(User).filter(User.username == new_username, User.id != user.id).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This username is already taken."
                )
            update_data["username"] = new_username

    # 1. Handle Many-to-Many interests relationship
    if "travel_interests" in update_data:
        interests_list = update_data.pop("travel_interests")
        if interests_list is not None:
             _assign_interests(user, interests_list, db)

    # Serialize remaining list fields to JSON strings (SQLite/PG Text columns)
    list_fields = ["countries_visited", "languages"]
    for field in list_fields:
        if field in update_data and update_data[field] is not None:
            update_data[field] = json.dumps(update_data[field])

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def save_travel_interests(user: User, payload: TravelInterests, db: Session) -> User:
    """Save onboarding travel interests — called after first login."""

    if payload.travel_interests:
        _assign_interests(user, payload.travel_interests, db)
        
    user.travel_style = payload.travel_style
    
    if payload.budget_preference:
        user.budget_preference = payload.budget_preference

    if payload.languages:
        user.languages = json.dumps(payload.languages)
    if payload.location:
        user.location = payload.location

    db.commit()
    db.refresh(user)
    return user


def _deserialize_user(user: User) -> User:
    """Deserialize JSON string fields back to Python lists for Pydantic."""
    list_fields = ["countries_visited", "languages"]
    
    for field in list_fields:
        raw = getattr(user, field, None)
        if raw and isinstance(raw, str):
            try:
                setattr(user, field, json.loads(raw))
            except (ValueError, TypeError):
                setattr(user, field, [])
        elif not raw:
            setattr(user, field, [])
            
    # Dynamically inject past completed trips into countries_visited
    try:
        countries_set = set(user.countries_visited)
        for trip in (user.trips or []):
            if trip.status == "completed" and trip.countries:
                try:
                    trip_countries = json.loads(trip.countries)
                    for country in trip_countries:
                        countries_set.add(country)
                except Exception:
                    pass
        user.countries_visited = list(countries_set)
    except Exception:
        pass

    # Inject verification flags — safe for DBs that may not have these columns yet
    try:
        user.has_google_auth = bool(getattr(user, "social_google_email", None))
    except Exception:
        user.has_google_auth = False

    try:
        user.has_emergency_contact = getattr(user, "emergency_contact", None) is not None
    except Exception:
        user.has_emergency_contact = False

    return user
