from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = Column(String, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reviewee_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    rating = Column(Float, nullable=False)
    text_review = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    trip = relationship("Trip", backref="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id], backref="reviews_given")
    reviewee = relationship("User", foreign_keys=[reviewee_id], backref="reviews_received")
