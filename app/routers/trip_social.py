from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.utils.jwt import get_current_user
from app.models.user import User
from app.models.trip import Trip
from app.models.trip_member import TripJoinRequest, TripMember, GroupMessage
from app.schemas.trip import TripWithUserResponse

router = APIRouter(prefix="/trips", tags=["Trip Social"])


# ─── Schemas ──────────────────────────────────────────────
class JoinRequestResponse(BaseModel):
    id: str
    trip_id: str
    sender_id: str
    sender_username: str
    sender_full_name: Optional[str] = None
    sender_profile_picture: Optional[str] = None
    status: str

class TripMemberResponse(BaseModel):
    id: str
    user_id: str
    username: str
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    role: str
    verified: bool

class GroupMessageResponse(BaseModel):
    id: str
    trip_id: str
    sender_id: str
    sender_username: str
    sender_profile_picture: Optional[str] = None
    content: str
    timestamp: str

class SendMessagePayload(BaseModel):
    content: str

class PhonePayload(BaseModel):
    phone_number: str
    
class PhoneVerifyPayload(BaseModel):
    phone_number: str
    otp_code: str


# ─── Trip Join Requests ───────────────────────────────────

@router.post("/{trip_id}/request", status_code=status.HTTP_201_CREATED)
def request_to_join(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a request to join a trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if not trip.open_to_join:
        raise HTTPException(status_code=400, detail="This trip is not open to join")
    if trip.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You own this trip")

    existing = db.query(TripJoinRequest).filter(
        TripJoinRequest.trip_id == trip_id,
        TripJoinRequest.sender_id == str(current_user.id)
    ).first()
    if existing:
        if existing.status == "pending":
            raise HTTPException(status_code=400, detail="Request already sent")
        elif existing.status == "declined":
            raise HTTPException(status_code=403, detail="Your request to join this trip was previously declined")

    # Check if already a member
    is_member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == str(current_user.id),
    ).first()
    if is_member:
        raise HTTPException(status_code=400, detail="Already a member")

    req = TripJoinRequest(trip_id=trip_id, sender_id=str(current_user.id))
    db.add(req)
    db.commit()
    return {"detail": "Join request sent", "request_id": req.id}


@router.get("/{trip_id}/requests", response_model=List[JoinRequestResponse])
def get_join_requests(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pending join requests for a trip (owner only)."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip or str(trip.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not the trip owner")

    requests = db.query(TripJoinRequest).filter(
        TripJoinRequest.trip_id == trip_id,
        TripJoinRequest.status == "pending"
    ).all()

    result = []
    for r in requests:
        sender = db.query(User).filter(User.id == r.sender_id).first()
        result.append(JoinRequestResponse(
            id=r.id,
            trip_id=r.trip_id,
            sender_id=r.sender_id,
            sender_username=sender.username if sender else "unknown",
            sender_full_name=sender.full_name if sender else None,
            sender_profile_picture=sender.profile_picture if sender else None,
            status=r.status,
        ))
    return result


@router.post("/requests/{request_id}/accept")
def accept_join_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a join request — creates a TripMember and ensures owner is also a member."""
    req = db.query(TripJoinRequest).filter(TripJoinRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    trip = db.query(Trip).filter(Trip.id == req.trip_id).first()
    if not trip or str(trip.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not the trip owner")

    req.status = "accepted"

    # Ensure owner is also a member
    owner_member = db.query(TripMember).filter(
        TripMember.trip_id == str(trip.id),
        TripMember.user_id == str(current_user.id),
    ).first()
    if not owner_member:
        db.add(TripMember(
            trip_id=str(trip.id),
            user_id=str(current_user.id),
            role="owner",
            verified=current_user.phone_verified,
        ))

    # Add the requester as member
    db.add(TripMember(
        trip_id=str(trip.id),
        user_id=str(req.sender_id),
        role="member",
    ))

    db.commit()
    return {"detail": "Request accepted"}


@router.post("/requests/{request_id}/decline")
def decline_join_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Decline a join request."""
    req = db.query(TripJoinRequest).filter(TripJoinRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    trip = db.query(Trip).filter(Trip.id == req.trip_id).first()
    if not trip or str(trip.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not the trip owner")

    req.status = "declined"
    db.commit()
    return {"detail": "Request declined"}


# ─── Trip Members ─────────────────────────────────────────

@router.get("/{trip_id}/members", response_model=List[TripMemberResponse])
def get_trip_members(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all members of a trip."""
    members = db.query(TripMember).filter(cast(TripMember.trip_id, String) == trip_id).all()
    result = []
    for m in members:
        user = db.query(User).filter(User.id == str(m.user_id)).first()
        result.append(TripMemberResponse(
            id=str(m.id),
            user_id=str(m.user_id),
            username=user.username if user else "unknown",
            full_name=user.full_name if user else None,
            profile_picture=user.profile_picture if user else None,
            role=m.role,
            verified=bool(m.verified),
        ))
    return result


@router.get("/joined/me")
def get_joined_trips(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all trips the current user has joined (not owned)."""
    memberships = db.query(TripMember).filter(
        TripMember.user_id == str(current_user.id),
        TripMember.role == "member",
    ).all()

    trip_ids = [m.trip_id for m in memberships]
    if not trip_ids:
        return []

    trips = db.query(Trip).filter(Trip.id.in_(trip_ids)).all()
    results = []
    for t in trips:
        owner = db.query(User).filter(User.id == t.user_id).first()
        results.append({
            "id": t.id,
            "destination": t.destination,
            "country": t.country,
            "start_date": str(t.start_date),
            "end_date": str(t.end_date),
            "budget_type": t.budget_type,
            "notes": t.notes,
            "status": t.status,
            "open_to_join": t.open_to_join,
            "created_at": str(t.created_at),
            "user_id": t.user_id,
            "owner_username": owner.username if owner else "unknown",
            "owner_profile_picture": owner.profile_picture if owner else None,
        })
    return results


@router.delete("/{trip_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_trip(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Leave a trip you have joined."""
    member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == str(current_user.id)
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="You are not a member of this trip")
    if member.role == "owner":
        raise HTTPException(status_code=400, detail="The owner cannot leave the trip. Delete the trip instead.")
        
    db.delete(member)
    db.commit()
    return None

@router.delete("/{trip_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def kick_trip_member(
    trip_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kick a user from a trip (owner only)."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip or str(trip.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not the trip owner")
        
    if str(user_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="You cannot kick yourself.")

    member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="User is not a member of this trip")
        
    db.delete(member)
    db.commit()
    return None

# ─── Group Messages ───────────────────────────────────────

@router.get("/{trip_id}/messages", response_model=List[GroupMessageResponse])
def get_group_messages(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get group chat messages for a trip. User must be a member."""
    is_member = db.query(TripMember).filter(
        cast(TripMember.trip_id, String) == trip_id,
        TripMember.user_id == str(current_user.id),
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this trip")
    if not is_member.verified:
        raise HTTPException(status_code=403, detail="Phone verification required to read messages")

    messages = db.query(GroupMessage).filter(
        cast(GroupMessage.trip_id, String) == trip_id
    ).order_by(GroupMessage.timestamp.asc()).all()

    result = []
    for msg in messages:
        sender = db.query(User).filter(User.id == msg.sender_id).first()
        result.append(GroupMessageResponse(
            id=str(msg.id),
            trip_id=str(msg.trip_id),
            sender_id=str(msg.sender_id),
            sender_username=sender.username if sender else "unknown",
            sender_profile_picture=sender.profile_picture if sender else None,
            content=msg.content,
            timestamp=str(msg.timestamp),
        ))
    return result


@router.post("/{trip_id}/messages", status_code=status.HTTP_201_CREATED)
def send_group_message(
    trip_id: str,
    payload: SendMessagePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to the trip group chat. User must be a verified member."""
    member = db.query(TripMember).filter(
        TripMember.trip_id == trip_id,
        TripMember.user_id == current_user.id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this trip")
    if not member.verified:
        raise HTTPException(status_code=403, detail="Phone verification required to send messages")

    msg = GroupMessage(
        trip_id=trip_id,
        sender_id=current_user.id,
        content=payload.content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {
        "id": msg.id,
        "trip_id": msg.trip_id,
        "sender_id": msg.sender_id,
        "sender_username": current_user.username,
        "content": msg.content,
        "timestamp": str(msg.timestamp),
    }


# ─── Phone Verification ──────────────────────────────────

@router.post("/verify/phone/status")
def check_phone_status(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if user is phone-verified for a specific trip."""
    member = None
    try:
        member = db.query(TripMember).filter(
            cast(TripMember.trip_id, String) == trip_id,
            cast(TripMember.user_id, String) == str(current_user.id),
        ).first()
    except Exception:
        pass
    return {
        "phone_verified": getattr(current_user, "phone_verified", False) or False,
        "trip_verified": member.verified if member else False,
        "phone_number": getattr(current_user, "phone_number", None),
    }


@router.post("/verify/phone/confirm")
def confirm_phone_verification(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark user as phone verified (called after Firebase Auth succeeds on client)."""
    try:
        setattr(current_user, "phone_verified", True)
    except Exception:
        pass

    try:
        member = db.query(TripMember).filter(
            cast(TripMember.trip_id, String) == trip_id,
            cast(TripMember.user_id, String) == str(current_user.id),
        ).first()
        if member:
            member.verified = True
    except Exception:
        pass

    db.commit()
    return {"detail": "Phone verified, group chat unlocked"}

# ─── Phase 4: Emergency SOS Alert ────────────────────────

class SOSPayload(BaseModel):
    latitude: float
    longitude: float

@router.post("/{trip_id}/emergency/sos")
def trigger_sos_alert(
    trip_id: str,
    payload: SOSPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Triggered when a user hits the panic button in a Trip Group Chat.
    Finds the emergency contact, simulates an SMS dispatch, and injects an SOS message into the chat.
    """
    from app.models.emergency_contact import EmergencyContact

    # 1. Verify user is in trip
    is_member = db.query(TripMember).filter(
        cast(TripMember.trip_id, String) == trip_id,
        TripMember.user_id == str(current_user.id),
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="You must be a member of this trip to trigger SOS.")

    # 2. Fetch User's Emergency Contact
    contact = db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).first()
    google_maps_url = f"https://www.google.com/maps/search/?api=1&query={payload.latitude},{payload.longitude}"

    contact_name = contact.name if contact else "Emergency Services"
    contact_phone = contact.phone_number if contact else "911"

    # 3. Simulate SMS Gateway Dispatch (Print to Logs)
    print("\n" + "="*50)
    print("🚨 [SIMULATED SMS GATEWAY DISPATCH] 🚨")
    print(f"TO: {contact_name} ({contact_phone})")
    print(f"MESSAGE: URGENT SOS! {current_user.full_name or current_user.username} has triggered a panic button on a WANDR Trip.")
    print(f"LAST KNOWN LOCATION: {google_maps_url}")
    print("WARNING: This is an automated alert generated by the WANDR Trust & Safety System.")
    print("="*50 + "\n")

    # 4. Inject SOS into Group Chat
    chat_alert = (
        f"🚨 URGENT SOS ALERT 🚨\n"
        f"I have triggered the Panic Button and need immediate help!\n"
        f"📍 My Live Location: {google_maps_url}"
    )

    sos_msg = GroupMessage(
        trip_id=trip_id,
        sender_id=current_user.id,
        content=chat_alert,
    )
    db.add(sos_msg)
    db.commit()
    db.refresh(sos_msg)

    return {
        "status": "success",
        "detail": "Emergency SOS triggered. Alerts dispatched.",
        "simulated_recipients": [contact_phone],
        "message_injected": True
    }
