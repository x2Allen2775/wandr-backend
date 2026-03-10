from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    caption = Column(Text, nullable=True)
    media_urls = Column(Text, nullable=True) # JSON mapped list
    location = Column(String, nullable=True)
    visibility = Column(String, default="public")  # public | private
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to the author
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan", lazy="dynamic")
