import requests
import uuid

BASE_URL = "http://localhost:8000/api"

# 1. Login
test_email = f"kyctest_{uuid.uuid4().hex[:8]}@example.com"
requests.post(f"{BASE_URL}/auth/signup", json={"email": test_email, "username": test_email.split('@')[0], "password": "password123"})
resp = requests.post(f"{BASE_URL}/auth/login/json", json={"email": test_email, "password": "password123"})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Consent
requests.post(f"{BASE_URL}/kyc/consent", json={"consent_type": "kyc_facial_processing", "granted": True}, headers=headers)

# 3. Create dummy files
with open("test_front.jpg", "wb") as f: f.write(b"data")
with open("test_back.jpg", "wb") as f: f.write(b"data")
with open("test_selfie.jpg", "wb") as f: f.write(b"data")

# 4. Submit
files = {
    "id_front": ("test_front.jpg", open("test_front.jpg", "rb"), "image/jpeg"),
    "id_back": ("test_back.jpg", open("test_back.jpg", "rb"), "image/jpeg"),
    "selfie": ("test_selfie.jpg", open("test_selfie.jpg", "rb"), "image/jpeg"),
}
res = requests.post(f"{BASE_URL}/kyc/submit", headers=headers, files=files)
print(f"Status: {res.status_code}")
print(f"Body: {res.text}")

