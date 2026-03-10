from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
import uuid

from app.database import Base


class SavedPost(Base):
    __tablename__ = "saved_posts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    post_id = Column(String, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    saved_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='uq_user_saved_post'),
    )
