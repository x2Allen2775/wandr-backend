import requests
import uuid

BASE_URL = "http://localhost:8000/api"

with open("test.jpg", "wb") as f: f.write(b"data")

test_email = f"kyctest_{uuid.uuid4().hex[:8]}@example.com"
requests.post(f"{BASE_URL}/auth/signup", json={"email": test_email, "username": test_email.split('@')[0], "password": "password123"})
resp = requests.post(f"{BASE_URL}/auth/login/json", json={"email": test_email, "password": "password123"})
token = resp.json().get("access_token", "")
headers = {"Authorization": f"Bearer {token}"}
requests.post(f"{BASE_URL}/kyc/consent", json={"consent_type": "kyc_facial_processing", "granted": True}, headers=headers)

files = [
    ("id_front", ("test.jpg", open("test.jpg", "rb"), "image/jpeg")),
    ("id_back", ("test.jpg", open("test.jpg", "rb"), "image/jpeg")),
    ("selfie", ("test.jpg", open("test.jpg", "rb"), "image/jpeg")),
]
res = requests.post(f"{BASE_URL}/kyc/submit", headers=headers, files=files)
print(f"Status: {res.status_code}")
print(f"Body: {res.text}")

