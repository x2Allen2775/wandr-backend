from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.utils.rate_limit import limiter

from app.config import settings
from app.database import engine, Base
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Initialize Cloudinary if credentials are provided
if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )
    logging.info("Cloudinary successfully configured.")
else:
    logging.warning("Cloudinary credentials missing. Falling back to local/ephemeral storage.")

from app.routers.auth import router as auth_router
from app.routers.profile import router as profile_router
from app.routers.community import router as community_router
from app.routers.post import router as post_router
from app.routers.follow import router as follow_router
from app.routers.trip import router as trip_router
from app.routers.match import router as match_router
from app.routers.chat import router as chat_router
from app.routers.itinerary import router as itinerary_router
from app.routers.explore import router as explore_router
from app.routers.notification import router as notification_router
from app.routers.upload import router as upload_router
from app.routers.saved import router as saved_router
from app.routers.trip_social import router as trip_social_router
from app.routers.kyc import router as kyc_router
from app.routers.review import router as review_router

from app.models.message import Message, Conversation
from app.models.itinerary import Itinerary, ItineraryMessage
from app.models.comment import Comment
from app.models.trip import Trip
from app.models.review import Review
# Import ALL models so create_all creates every table on cold start
from app.models.user import User
from app.models.post import Post
from app.models.interest import Interest
from app.models.notification import Notification
from app.models.saved_post import SavedPost
from app.models.trip_member import TripMember
from app.models.consent import UserConsent
from app.models.emergency_contact import EmergencyContact

# Auto-create tables on startup (use Alembic migrations for production)
Base.metadata.create_all(bind=engine)

# ── Auto-migration: safely add missing columns to existing tables ──────
def _auto_migrate():
    """Add columns that may be missing from an older DB schema."""
    from sqlalchemy import text, inspect
    with engine.connect() as conn:
        inspector = inspect(engine)
        existing_cols = {c["name"] for c in inspector.get_columns("users")}
        migrations = {
            "phone_number": "VARCHAR",
            "phone_verified": "BOOLEAN DEFAULT FALSE",
            "social_google_email": "VARCHAR",
            "legal_name": "VARCHAR",
            "dob": "TIMESTAMP",
            "kyc_verified_at": "TIMESTAMP",
            "kyc_reference_token": "VARCHAR",
            "trust_score": "FLOAT DEFAULT 5.0",
            "review_count": "INTEGER DEFAULT 0",
            "public_key": "VARCHAR",
        }
        for col_name, col_type in migrations.items():
            if col_name not in existing_cols:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    logging.info(f"Auto-migrated column: users.{col_name}")
                except Exception as e:
                    logging.warning(f"Column migration skipped ({col_name}): {e}")
        conn.commit()

try:
    _auto_migrate()
    logging.info("Auto-migration complete.")
except Exception as e:
    logging.warning(f"Auto-migration skipped: {e}")

# Ensure upload directory exists before static mount
os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="🌍 Wandr — Auth & Identity API",
    description="""
## Wandr — Pillar 1: Authentication & User Identity

The foundation of the **Wandr** travel community platform.

### Endpoints
| Route | Method | Auth | Description |
|---|---|---|---|
| `/auth/signup` | POST | Public | Register new account |
| `/auth/login` | POST | Public | Login, get JWT token |
| `/profile/me` | GET | 🔒 Bearer | Get own profile |
| `/profile/me` | PUT | 🔒 Bearer | Update profile |
| `/profile/me/interests` | POST | 🔒 Bearer | Save travel interests (onboarding) |
| `/community/users` | GET | 🔒 Bearer | Find matching users by interest |
| `/posts` | POST | 🔒 Bearer | Create a new post |
| `/feed` | GET | 🔒 Bearer | View chronologically ordered feed limit/offset |
| `/follow/{uid}` | POST/DEL | 🔒 Bearer | Follow or unfollow a user |
| `/followers/{uid}` | GET | 🔒 Bearer | Get users following a user |
| `/following/{uid}` | GET | 🔒 Bearer | Get users a user is following |

### Auth Flow
1. **Signup** → get user object
2. **Login** → get `access_token`
3. All protected routes → `Authorization: Bearer <token>`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logging.error(f"====== KYC Validation Error ======\nBody: {await request.body()}\nErrors: {exc.errors()}\n===============================")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    logging.error(f"====== FATAL UNHANDLED EXCEPTION ======\nPath: {request.url.path}\nMethod: {request.method}\nTraceback: {traceback.format_exc()}\n=======================================")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# ── Static File Hosting ────────────────────────────────────────────────
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Routers ────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(community_router, prefix="/api")
app.include_router(post_router, prefix="/api")
app.include_router(follow_router, prefix="/api")
app.include_router(trip_router, prefix="/api")
app.include_router(match_router, prefix="/api/match")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(itinerary_router, prefix="/api/itinerary")
app.include_router(explore_router, prefix="/api")
app.include_router(notification_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(saved_router, prefix="/api")
app.include_router(trip_social_router, prefix="/api")
app.include_router(kyc_router, prefix="/api")
app.include_router(review_router, prefix="/api")


@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "pillar": "1 — Auth & Identity",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
