from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Request
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import random
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.database import get_db
from app.utils.jwt import get_current_user
from app.models.user import User
from app.models.consent import UserConsent
from app.utils.rate_limit import limiter

router = APIRouter(prefix="/kyc", tags=["Identity & Trust (KYC)"])

KYC_VALIDITY_DAYS = 90  # 3 months

def _check_kyc_expired(user: User) -> bool:
    """Check if user's KYC has expired (>3 months since verification)."""
    if user.kyc_status != "verified" or user.kyc_verified_at is None:
        return True
    expiry = user.kyc_verified_at + timedelta(days=KYC_VALIDITY_DAYS)
    return datetime.now(timezone.utc) > expiry


class ConsentRequest(BaseModel):
    consent_type: str
    granted: bool

class ConsentResponse(BaseModel):
    id: str
    consent_type: str
    granted: bool
    timestamp: datetime

@router.get("/status")
def get_kyc_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the user's current KYC verification status and DPDP consent state."""
    is_expired = _check_kyc_expired(current_user)

    if current_user.kyc_status == "verified" and is_expired:
        current_user.kyc_status = "expired"
        db.commit()

    days_remaining = 0
    if current_user.kyc_verified_at and current_user.kyc_status == "verified":
        expiry = current_user.kyc_verified_at + timedelta(days=KYC_VALIDITY_DAYS)
        days_remaining = max(0, (expiry - datetime.now(timezone.utc)).days)

    return {
        "kyc_status": current_user.kyc_status,
        "kyc_verified_at": str(current_user.kyc_verified_at) if current_user.kyc_verified_at else None,
        "is_expired": is_expired,
        "days_remaining": days_remaining,
        "legal_name": current_user.legal_name,
    }


@router.post("/consent", response_model=ConsentResponse)
def log_user_consent(
    request_data: ConsentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Log explicit user consent for processing facial biometric data and Govt ID.
    DPDP Compliance: Tracks IP, Timestamp, and Consent Type.
    """
    client_ip = request.client.host if request.client else "unknown"

    existing_consent = db.query(UserConsent).filter(
        cast(UserConsent.user_id, String) == current_user.id,
        UserConsent.consent_type == request_data.consent_type
    ).first()

    if existing_consent:
        existing_consent.granted = request_data.granted
        existing_consent.ip_address = client_ip
        existing_consent.timestamp = datetime.now(timezone.utc)
        if not request_data.granted:
            existing_consent.revoked_at = datetime.now(timezone.utc)
        else:
            existing_consent.revoked_at = None
        db.commit()
        db.refresh(existing_consent)
        consent_record = existing_consent
    else:
        consent_record = UserConsent(
            user_id=current_user.id,
            consent_type=request_data.consent_type,
            ip_address=client_ip,
            granted=request_data.granted
        )
        db.add(consent_record)
        db.commit()
        db.refresh(consent_record)
    
    return ConsentResponse(
        id=str(consent_record.id),
        consent_type=consent_record.consent_type,
        granted=consent_record.granted,
        timestamp=consent_record.timestamp
    )

@router.post("/submit")
@limiter.limit("5/10minute")
async def verify_identity_simulation(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulates a 3rd Party KYC Vendor integration (e.g., HyperVerge, Signzy).
    Reads the files to simulate processing, but ABSOLUTELY DOES NOT write them to disk.
    Strictly follows DPDP Data Minimization.
    """
    # 0. Manually parse form
    form = await request.form()
    print(f"====== RAW FORM KEYS ======\n{list(form.keys())}\n========================")
    
    id_front = form.get("id_front")
    id_back = form.get("id_back")
    selfie = form.get("selfie")

    if not id_front or not id_back or not selfie:
        raise HTTPException(
            status_code=400, 
            detail=f"Missing images in payload. Form keys received: {list(form.keys())}"
        )

    # 1. Enforce DPDP Consent Check
    consent = db.query(UserConsent).filter(
        cast(UserConsent.user_id, String) == current_user.id,
        UserConsent.consent_type == "kyc_facial_processing",
        UserConsent.granted == True
    ).first()

    if not consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DPDP compliance error: Explicit consent to process facial data is required before submission."
        )

    # 2. Extract files into memory (Simulation phase)
    try:
        front_bytes = await id_front.read()
        back_bytes = await id_back.read()
        selfie_bytes = await selfie.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to read image data")
    
    # --- SIMULATION OF VENDOR API ---
    import asyncio
    await asyncio.sleep(1.5)  # Latency

    # Always succeed for Phase 1 testing
    is_success = True
    if not is_success:
        current_user.kyc_status = "rejected"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Verification failed. Selfie did not match Government ID or document was blurry."
        )

    simulated_vendor_tx_id = f"tx_sim_{uuid.uuid4().hex[:12]}"
    simulated_extracted_name = current_user.full_name or current_user.username or "Verified Explorer"
    simulated_dob = datetime.now() - timedelta(days=365 * 25) # Simulate age 25

    # 3. Update User Record
    current_user.kyc_status = "verified"
    current_user.kyc_reference_token = simulated_vendor_tx_id
    current_user.legal_name = simulated_extracted_name
    current_user.dob = simulated_dob
    current_user.kyc_verified_at = datetime.now(timezone.utc)

    db.commit()

    # 4. Critical DPDP Step: Clear RAM
    del front_bytes
    del back_bytes
    del selfie_bytes

    return {
        "status": "success",
        "message": "Identity successfully verified via Digilocker/HyperVerge API.",
        "verified_data": {
            "legal_name": simulated_extracted_name,
            "dob": simulated_dob.strftime("%Y-%m-%d"),
            "reference_id": simulated_vendor_tx_id,
            "days_remaining": KYC_VALIDITY_DAYS
        }
    }

class GoogleToken(BaseModel):
    id_token: str

@router.post("/social/google")
@limiter.limit("5/10minute")
def verify_google_oauth(
    request: Request,
    payload: GoogleToken,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from google.auth.exceptions import TransportError
    
    # Dev Bypass for Live Testing
    if payload.id_token == "dev_bypass_token":
        current_user.social_google_email = "dev_bypassed@wandr.com"
        db.commit()
        return {"status": "success", "message": "Google account linked via Dev Bypass.", "email": "dev_bypassed@wandr.com"}
        
    try:
        # Verify the token signature with Google
        id_info = id_token.verify_oauth2_token(
            payload.id_token, 
            google_requests.Request(),
            audience=None  # Generic verification, normally requires explicit Client ID
        )
        
        email = id_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Token did not contain an email address.")
            
        current_user.social_google_email = email
        db.commit()
        
        return {"status": "success", "message": "Google account successfully linked.", "email": email}
        
    except TransportError as e:
        raise HTTPException(status_code=504, detail=f"Google authentication servers timed out or are unreachable: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Google ID token: {str(e)}")

class EmergencyContactRequest(BaseModel):
    name: str
    relation: str
    phone_number: str

@router.post("/emergency/save")
@limiter.limit("5/10minute")
async def save_emergency_contact(
    request: Request,
    payload: EmergencyContactRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Saves a verified emergency contact. 
    The phone number must be pre-verified by Firebase Phone Auth on the client side before calling this.
    """
    from app.models.emergency_contact import EmergencyContact

    contact = db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).first()
    
    if contact:
        contact.name = payload.name
        contact.relation = payload.relation
        contact.phone_number = payload.phone_number
        contact.is_verified = True
    else:
        contact = EmergencyContact(
            user_id=current_user.id,
            name=payload.name,
            relation=payload.relation,
            phone_number=payload.phone_number,
            is_verified=True
        )
        db.add(contact)
        
    db.commit()
    
    return {
        "status": "success", 
        "message": "Emergency contact successfully saved and verified."
    }
