from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

# Many-to-Many association table
user_interests = Table(
    "user_interests",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("interest_id", String, ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True),
)

class Interest(Base):
    __tablename__ = "interests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True, nullable=False)  # e.g., "beaches", "solo", "food"

    # Relationship back to Users
    users = relationship("User", secondary=user_interests, back_populates="interests")
