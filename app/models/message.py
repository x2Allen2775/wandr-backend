from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user1_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user2_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # "pending" means user1 sent user2 a message, but user2 hasn't accepted it yet.
    # "accepted" means it is an active inbox thread.
    status = Column(String, default="pending") 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    sender_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    content = Column(Text, nullable=True) # Text content. Nullable if only sending media
    media_url = Column(String, nullable=True) # Optional URL for attached images
    
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
