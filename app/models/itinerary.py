from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    destination = Column(String(255), nullable=True) # Initially null until AI figures it out
    days = Column(String(50), nullable=True)         # Keep track of requested length
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    user = relationship("User")
    messages = relationship("ItineraryMessage", back_populates="itinerary", cascade="all, delete-orphan")


class ItineraryMessage(Base):
    __tablename__ = "itinerary_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    itinerary_id = Column(String(36), ForeignKey("itineraries.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False) # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    itinerary = relationship("Itinerary", back_populates="messages")
