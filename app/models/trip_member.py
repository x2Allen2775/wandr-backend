from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class TripJoinRequest(Base):
    """A request from a user to join an open-to-join trip."""
    __tablename__ = "trip_join_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, default="pending")  # pending | accepted | declined
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trip = relationship("Trip")
    sender = relationship("User")


class TripMember(Base):
    """A confirmed member of a trip (owner or accepted joiner)."""
    __tablename__ = "trip_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, default="member")  # owner | member
    verified = Column(Boolean, default=False)  # phone verified for this trip

    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    trip = relationship("Trip")
    user = relationship("User")


class GroupMessage(Base):
    """A message in a trip's group chat."""
    __tablename__ = "group_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    trip = relationship("Trip")
    sender = relationship("User")
