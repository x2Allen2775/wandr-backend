import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey

from datetime import datetime, timezone
from app.database import Base

class UserConsent(Base):
    __tablename__ = "user_consents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String, nullable=False, index=True) # e.g., 'kyc_facial_processing'
    ip_address = Column(String, nullable=True)
    granted = Column(Boolean, default=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    revoked_at = Column(DateTime, nullable=True)
