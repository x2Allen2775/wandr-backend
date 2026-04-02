# 🌍 WANDR — The Social Network for Modern Explorers

**WANDR** is a production-ready travel platform designed to connect verified travellers through interest-based matching, secure community trips, and a robust identity-first social feed.

---

## 🏗️ Tech Stack

### **Backend (API)**
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Database**: PostgreSQL (Production) / SQLite (Local Dev)
- **ORM**: SQLAlchemy 2.0
- **Security**: JWT Authentication, bcrypt hashing, `slowapi` rate limiting
- **Compliance**: DPDP (Digital Personal Data Protection) compliant KYC pipeline
- **Hosting**: Render (Web Service)

### **Frontend (Mobile & Web)**
- **Framework**: [Flutter](https://flutter.dev/) (Dart)
- **State Management**: Provider / Riverpod
- **Authentication**: Firebase Auth (Phone/OTP)
- **Identity**: Google OAuth Integration
- **Hosting**: Firebase Hosting (Web)

---

## ✨ Key Features

### **🔐 Tri-Level Trust & Safety (KYC)**
WANDR implements a strict "Verified Only" policy for high-risk social interactions:
1. **Lvl 1: Government Identity** — OCR & Selfie matching (Simulated via HyperVerge/Digilocker patterns).
2. **Lvl 2: Social Proof** — Mandatory Google Account linking to prevent bot farms.
3. **Lvl 3: Accountability** — Emergency Contact verification.

### **📍 Smart Trip Matching**
- Join "Open to Join" trips created by verified members.
- Automatic location-based discovery.
- Interest-based compatibility filtering (Solo, Budget, Luxury, etc.).

### **💬 Secure Community Chat**
- Group chats automatically unlocked upon trip acceptance.
- Mandatory phone verification (Firebase OTP) for chat access to ensure real-world accountability.

### **📸 Explorers Feed**
- High-performance social feed with media uploads.
- Nested commenting system.
- Travel-style tagging and interest-based recommendations.

---

## 📁 Project Structure

```bash
wandr/
├── app/                  # FastAPI Backend source
│   ├── models/           # SQLAlchemy DB Models (User, Trip, Post, etc.)
│   ├── routers/          # API Endpoints (Auth, KYC, Trips, Social)
│   ├── services/         # Business Logic (Auth, User, Post services)
│   ├── schemas/          # Pydantic Request/Response models
│   ├── utils/            # JWT, Hashing, Rate Limiting
│   └── main.py          # App Entry point & Auto-migration engine
├── wandr_app/            # Flutter Frontend source
│   ├── lib/
│   │   ├── screens/      # UI Views (Login, Feed, KYC, Trips)
│   │   ├── services/     # API Clients & Firebase Logic
│   │   ├── models/       # Frontend Data Classes
│   │   └── widgets/      # Reusable UI Components
│   └── pubspec.yaml      # Flutter dependencies
├── requirements.txt      # Backend dependencies
└── README.md             # You are here
```

---

## 🚀 Installation & Setup

### **Backend Setup**
1. **Navigate to root** and create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Configure `.env`**:
   ```env
   DATABASE_URL=postgresql://user:pass@localhost:5432/wandr
   SECRET_KEY=your_super_secret_jwt_key
   ```
3. **Run Dev Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

### **Frontend Setup**
1. **Navigate to `wandr_app`**:
   ```bash
   cd wandr_app
   flutter pub get
   ```
2. **Run on Device/Web**:
   ```bash
   flutter run -d chrome  # For Web
   flutter run            # For Mobile (iOS/Android)
   ```

---

## 🛡️ Security & Compliance
- **Zero-Storage Media Logic**: In-memory processing for KYC selfies (DPDP compliance).
- **Graceful Degradation**: Backend is built with "Crash-Proof" logic to handle intermittent DB connectivity or missing production columns during migrations.
- **Rate Limiting**: Protection against brute-force attacks on Auth and OTP endpoints.

---

## 🌐 Current Deployments
- **API (Production)**: (https://wandr-c75a5.web.app/)
- **Status Page**: `/health` returns `{"status": "ok"}`

---

*Built with ❤️ for the global travel community.*
