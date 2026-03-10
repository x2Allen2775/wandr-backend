import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserSignup, UserLogin
from fastapi.security import OAuth2PasswordRequestForm
from app.utils.hashing import hash_password, verify_password
from app.utils.jwt import create_access_token


def signup_user(payload: UserSignup, db: Session) -> User:
    """Register a new Wandr user."""

    # Check email uniqueness
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Check username uniqueness
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken. Try another one.",
        )

    new_user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def login_user(payload: OAuth2PasswordRequestForm, db: Session) -> dict:
    """Authenticate and return a JWT token."""

    # Note: OAuth2 defines the field as 'username', but we use it for their email
    user = db.query(User).filter(User.email == payload.username).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.id})
    return {"access_token": token, "token_type": "bearer", "user": user}


def login_user_json(payload: UserLogin, db: Session) -> dict:
    """Authenticate and return a JWT token (Using JSON Payload)."""

    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.id})
    return {"access_token": token, "token_type": "bearer", "user": user}
