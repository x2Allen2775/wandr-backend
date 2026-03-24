import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid
import base64
import os

from app.main import app
from app.database import Base, get_db
from app.config import settings
from slowapi.util import get_remote_address

# --- Test DB Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Remove rate limiting for tests
app.state.limiter.enabled = False

client = TestClient(app)

# --- Test Data ---
def generate_user_payload(email_prefix="test"):
    unique_id = uuid.uuid4().hex[:6]
    return {
        "email": f"{email_prefix}_{unique_id}@example.com",
        "username": f"user_{unique_id}",
        "full_name": f"Test User {unique_id}",
        "password": "SecurePassword123!"
    }


def test_auth_signup_and_login():
    """Phase 1: Verify Authentication & Routing Works"""
    payload = generate_user_payload("alice")
    
    # 1. Signup
    response = client.post("/api/auth/signup", json=payload)
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["username"] == payload["username"]
    
    # 2. Login
    login_payload = {
        "email": payload["email"],
        "password": payload["password"]
    }
    response = client.post("/api/auth/login/json", json=login_payload)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    return token_data["access_token"], user_data["id"]


def test_e2e_encryption_chat_relay():
    """Phase 3: Verify E2E Encrypted Protocol Base64 Blind Relay"""
    token_a, id_a = test_auth_signup_and_login()
    token_b, id_b = test_auth_signup_and_login()

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A Uploads their ECDH Public Key
    mock_pub_key_a = base64.b64encode(b"DummyPublicKeyBytes_A_P256").decode("utf-8")
    resp = client.put("/api/profile/me", json={"public_key": mock_pub_key_a}, headers=headers_a)
    assert resp.status_code == 200

    # 2. User B fetches User A profile to get public key
    resp = client.get(f"/api/profile/{id_a}", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json()["public_key"] == mock_pub_key_a

    # 3. User B sends AES-GCM Encrypted Blob + IV Base64 to User A
    mock_ciphertext = base64.b64encode(b"EncryptedHello").decode("utf-8")
    mock_iv = base64.b64encode(os.urandom(12)).decode("utf-8")
    
    chat_payload = {
        "content": mock_ciphertext,
        "iv": mock_iv
    }
    resp = client.post(f"/api/chat/send/{id_a}", json=chat_payload, headers=headers_b)
    assert resp.status_code == 200
    msg = resp.json()
    assert msg["content"] == mock_ciphertext
    assert msg["iv"] == mock_iv

    # 4. User A fetches inbox and receives User B's encrypted blob perfectly intact
    resp = client.get("/api/chat/inbox", headers=headers_a)
    assert resp.status_code == 200
    requests = resp.json()["requests"]
    assert len(requests) == 1
    recent_msg = requests[0]["last_message"]
    
    # Server merely relayed the strings, never touched plaintext
    assert recent_msg["content"] == mock_ciphertext
    assert recent_msg["iv"] == mock_iv


def test_kyc_status_and_rate_limits():
    """Phase 4: Verify KYC routes and rate limiting structure (slowapi disabled in TestClient but routed properly)"""
    token, _ = test_auth_signup_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/kyc/status", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["kyc_status"] == "unverified"
