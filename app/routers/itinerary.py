from fastapi import APIRouter, Depends, HTTPException, Header
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.jwt import get_current_user
from app.models.user import User
from app.models.itinerary import Itinerary, ItineraryMessage
from app.schemas.itinerary import ItineraryResponse, AIChatRequest, ItineraryMessageResponse, ItineraryCreate
from app.services.itinerary_service import IterinaryService

router = APIRouter(tags=["AI Itineraries"])

@router.get("/", response_model=list[ItineraryResponse])
def get_user_itineraries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch all itineraries created by the user"""
    return db.query(Itinerary).filter(Itinerary.user_id == current_user.id).order_by(Itinerary.created_at.desc()).all()


@router.post("/", response_model=ItineraryResponse)
def create_new_itinerary(payload: ItineraryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Starts a new empty Itinerary chat thread"""
    itinerary = Itinerary(
        user_id=current_user.id,
        destination=payload.destination,
        days=payload.days
    )
    db.add(itinerary)
    db.commit()
    db.refresh(itinerary)
    return itinerary


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
def get_itinerary(itinerary_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a specific itinerary and its chat history"""
    itinerary = db.query(Itinerary).filter(Itinerary.id == itinerary_id, Itinerary.user_id == current_user.id).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return itinerary


@router.post("/{itinerary_id}/chat", response_model=ItineraryMessageResponse)
def chat_with_ai(
    itinerary_id: str, 
    payload: AIChatRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    x_gemini_key: str | None = Header(None)
):
    """Send a message to the AI, and get the AI's response in return."""
    itinerary = db.query(Itinerary).filter(Itinerary.id == itinerary_id, Itinerary.user_id == current_user.id).first()
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    # 1. Save user's message
    user_msg = ItineraryMessage(
        itinerary_id=itinerary.id,
        role="user",
        content=payload.content,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(user_msg)
    db.commit()

    # 2. Call Gemini Service
    ai_response_text = IterinaryService.generate_response(db, current_user, itinerary, payload.content, x_gemini_key)

    # 3. Save AI's response
    ai_msg = ItineraryMessage(
        itinerary_id=itinerary.id,
        role="assistant",
        content=ai_response_text,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(ai_msg)
    
    # Try to extract a destination if we don't have one
    if not itinerary.destination:
        itinerary.destination = IterinaryService.extract_destination(ai_response_text) or "New Trip"
        
    db.commit()
    db.refresh(ai_msg)

    return ai_msg
