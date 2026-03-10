from sqlalchemy import Column, String, Boolean, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    destination = Column(String, nullable=False, index=True) # Full displayed location string
    country = Column(String, nullable=True)
    countries = Column(Text, nullable=True) # JSON list
    states = Column(Text, nullable=True) # JSON list
    cities = Column(Text, nullable=True) # JSON list
    travel_interests = Column(Text, nullable=True) # JSON list
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    
    budget_type = Column(String, nullable=False)  # budget, mid, luxury
    notes = Column(Text, nullable=True)
    status = Column(String, default="planned")  # planned, completed
    open_to_join = Column(Boolean, default=False)  # Allow others to request joining

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="trips")
