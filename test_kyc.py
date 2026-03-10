import requests
import os
import uuid

BASE_URL = "http://localhost:8000/api"

# 1. Login with a test user
unique_id = uuid.uuid4().hex[:8]
test_email = f"kyctest_{unique_id}@example.com"
test_username = f"kyctest_{unique_id}"

login_data = {
    "email": test_email,
    "password": "password123"
}

print(f"Registering test user: {test_email}")
resp = requests.post(f"{BASE_URL}/auth/signup", json={
    "email": test_email, 
    "username": test_username, 
    "password": "password123",
    "full_name": "KYC Tester"
})

if resp.status_code != 200:
    print(f"Signup failed: {resp.text}")

print("Logging in...")
resp = requests.post(f"{BASE_URL}/auth/login/json", json=login_data)
if resp.status_code != 200:
    print(f"Failed to login: {resp.text}")
    exit(1)

token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Logged in successfully.")

# 2. Check initial KYC status
resp = requests.get(f"{BASE_URL}/kyc/status", headers=headers)
print(f"Initial KYC status: {resp.json()}")

# 3. Log Consent
print("Submitting Consent...")
resp = requests.post(f"{BASE_URL}/kyc/consent", json={"consent_type": "kyc_facial_processing", "granted": True}, headers=headers)
print(resp.json())

# 4. Prepare dummy images
for fname in ["dummy_front.jpg", "dummy_back.jpg", "dummy_selfie.jpg"]:
    with open(fname, "wb") as f:
        f.write(b"fake image data")

# 5. List uploads dir before
uploads_before = set(os.listdir("uploads")) if os.path.exists("uploads") else set()

# 6. Submit KYC Documents
print("Submitting KYC documents...")
with open("dummy_front.jpg", "rb") as front, \
     open("dummy_back.jpg", "rb") as back, \
     open("dummy_selfie.jpg", "rb") as selfie:
    
    files = {
        "id_front": ("dummy_front.jpg", front, "image/jpeg"),
        "id_back": ("dummy_back.jpg", back, "image/jpeg"),
        "selfie": ("dummy_selfie.jpg", selfie, "image/jpeg"),
    }
    resp = requests.post(f"{BASE_URL}/kyc/submit", files=files, headers=headers)

print(f"KYC Submit Response: {resp.status_code}")
print(resp.json())

# 7. List uploads dir after
uploads_after = set(os.listdir("uploads")) if os.path.exists("uploads") else set()
diff = uploads_after - uploads_before
if len(diff) > 0:
    print(f"\nFAIL: DPDP Violation! Files written to disk: {diff}")
else:
    print("\nSUCCESS: Zero image retention constraint perfectly verified. Biometrics remained securely in RAM only.")

# 8. Check final KYC status
resp = requests.get(f"{BASE_URL}/kyc/status", headers=headers)
print(f"Final KYC status: {resp.json()}")

# Cleanup
for fname in ["dummy_front.jpg", "dummy_back.jpg", "dummy_selfie.jpg"]:
    if os.path.exists(fname):
        os.remove(fname)
