from sqlalchemy import Column, String, Boolean, DateTime, Text, Table, ForeignKey, Float, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

# Self-referential Many-to-Many association table for Followers
follows = Table(
    "follows",
    Base.metadata,
    Column("follower_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("following_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)

class User(Base):
    __tablename__ = "users"

    # ── Core Identity ──────────────────────────────────────────
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)         # Privacy toggle

    # ── Profile ────────────────────────────────────────────────
    full_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    profile_picture = Column(String, nullable=True)          # URL / path
    location = Column(String, nullable=True)                 # Current city/country
    website = Column(String, nullable=True)

    # ── One-to-Many Relationships ──────────────────────────────────
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")
    emergency_contact = relationship("EmergencyContact", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # ── Many-to-Many Relationships ─────────────────────────────────
    # The users that THIS user is following
    following = relationship(
        "User",
        secondary=follows,
        primaryjoin=id == follows.c.follower_id,
        secondaryjoin=id == follows.c.following_id,
        backref="followers",
        lazy="dynamic"
    )

    # ── Travel Identity (Wandr-specific) ───────────────────────
    # The many-to-many relationship to Interest model
    interests = relationship("Interest", secondary="user_interests", back_populates="users")
    
    countries_visited = Column(Text, nullable=True)          # JSON string list
    travel_style = Column(String, nullable=True)             # solo | group | adventure | chill
    budget_preference = Column(String, nullable=True)        # budget | mid | luxury
    languages = Column(Text, nullable=True)                  # JSON string list

    # ── Future-proofing ────────────────────────────────────────
    public_key = Column(String, nullable=True)               # ECDH P-256 public key for E2E Encrypted Chat (Base64 length ~90)
    kyc_status = Column(String, default="unverified")        # unverified | pending | verified | rejected
    kyc_reference_token = Column(String, nullable=True)      # vendor transaction id
    kyc_document_url = Column(String, nullable=True)         # URL to uploaded KYC document (temporary)
    kyc_verified_at = Column(DateTime(timezone=True), nullable=True)  # Last KYC verification date
    legal_name = Column(String, nullable=True)               # DPDP compliant extraction
    dob = Column(DateTime, nullable=True)                    # DPDP compliant age verification
    phone_number = Column(String, nullable=True)             # For SMS OTP verification
    phone_verified = Column(Boolean, default=False)          # True after OTP verified
    social_google_email = Column(String, nullable=True)      # Level 2 Social Trust
    trust_score = Column(Float, default=5.0)                 # Aggregated peer review score
    review_count = Column(Integer, default=0)                # Total number of peer reviews received

    # ── Timestamps ─────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    @property
    def following_count(self) -> int:
        # self.following is lazy="dynamic", so we can call .count() on it efficiently
        return self.following.count()

    @property
    def followers_count(self) -> int:
        from app.database import SessionLocal
        db = SessionLocal()
        count = db.query(follows).filter(follows.c.following_id == self.id).count()
        db.close()
        return count

# ── Follow Requests ────────────────────────────────────────────
class FollowRequest(Base):
    __tablename__ = "follow_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ── Password Reset Tokens ────────────────────────────────────────
class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, index=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ── Email Verification / OTP Codes ───────────────────────────────
class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(6), nullable=False)
    purpose = Column(String, nullable=False, default="signup")  # signup | password_change
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
