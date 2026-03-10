# 🌍 Wandr — Pillar 1: Auth & Identity System

> The bedrock of the Wandr travel community platform. If users can't sign up and log in securely, nothing else works.

---

## 📁 Project Structure

```
wandr-auth/
├── app/
│   ├── main.py              ← FastAPI app, CORS, router registration
│   ├── config.py            ← Environment settings via pydantic
│   ├── database.py          ← SQLAlchemy engine, session, Base
│   ├── models/
│   │   └── user.py          ← User DB model (future-proofed with KYC fields)
│   ├── schemas/
│   │   └── user.py          ← Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py          ← /auth/signup, /auth/login
│   │   └── profile.py       ← /profile/me (GET, PUT, interests)
│   ├── services/
│   │   ├── auth_service.py  ← Signup/login business logic
│   │   └── user_service.py  ← Profile update, interests, deserialization
│   └── utils/
│       ├── hashing.py       ← bcrypt password hash/verify
│       └── jwt.py           ← JWT create/decode + auth dependency
├── .env.example             ← Copy to .env and fill in values
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & setup environment

```bash
cd wandr-auth
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set your DATABASE_URL and SECRET_KEY
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

Visit **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 🗄️ Database Options

### SQLite (quick local dev — zero setup)
```env
DATABASE_URL=sqlite:///./wandr.db
```

### PostgreSQL (recommended for production)
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/wandr_db
```
Create the DB first:
```sql
CREATE DATABASE wandr_db;
```

---

## 🔌 API Endpoints

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| `POST` | `/auth/signup` | Public | Register new account |
| `POST` | `/auth/login` | Public | Login, receive JWT token |
| `GET` | `/profile/me` | 🔒 Bearer | Fetch own profile |
| `PUT` | `/profile/me` | 🔒 Bearer | Update profile fields |
| `POST` | `/profile/me/interests` | 🔒 Bearer | Save travel interests (onboarding) |

---

## 🧪 Sample Requests

### Signup
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"alex@wandr.io","username":"alex_travels","password":"Secure123","full_name":"Alex"}'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alex@wandr.io","password":"Secure123"}'
```

### Get Profile (protected)
```bash
curl http://localhost:8000/profile/me \
  -H "Authorization: Bearer <your_token_here>"
```

### Set Travel Interests (onboarding)
```bash
curl -X POST http://localhost:8000/profile/me/interests \
  -H "Authorization: Bearer <your_token_here>" \
  -H "Content-Type: application/json" \
  -d '{
    "travel_interests": ["solo", "beaches", "mountains", "backpacking"],
    "travel_style": "budget",
    "languages": ["English", "Hindi"],
    "location": "Mumbai, India"
  }'
```

---

## 🔐 Security

| Feature | Implementation |
|---------|---------------|
| Password hashing | `bcrypt` via `passlib` |
| Authentication | `JWT` via `python-jose` |
| Token expiry | Configurable (default: 60 min) |
| Protected routes | `Depends(get_current_user)` |
| Input validation | Pydantic v2 validators |

---

## 🔮 Future-Proofing (Already in the DB)

- `kyc_status` field: `not_submitted → pending → verified`
- `kyc_document_ref` field: encrypted document reference
- `is_verified` flag for email verification
- UUID primary keys (ready for distributed systems)

---

## 🧩 What's Next (Pillar 2 Preview)

> Once users exist, we build the social layer:
> - Posts, Stories, Reels
> - Follow / Unfollow
> - Feed algorithm (interest-based)
> - Trip planning & community groups

---

*Built with ❤️ for Wandr — the social platform for travellers.*
