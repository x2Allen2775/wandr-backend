from fastapi import APIRouter, Depends, status, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid
import datetime

from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.schemas.user import UserSignup, UserLogin, TokenResponse, MessageResponse, UserProfile
from app.services.auth_service import signup_user, login_user, login_user_json
from app.services.user_service import _deserialize_user
from app.models.user import User, PasswordReset, EmailVerification
from app.services.email_service import send_reset_email, send_verification_email, send_otp_email
from app.utils.hashing import hash_password, verify_password
from app.utils.jwt import get_current_user
from app.config import settings
import random

from app.utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserProfile,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Wandr account",
)
@limiter.limit("5/10minute")
def signup(request: Request, payload: UserSignup, db: Session = Depends(get_db)):
    """
    Create a new user account.

    - **email**: must be unique
    - **username**: 3–30 chars, alphanumeric + underscores, must be unique
    - **password**: min 8 characters (bcrypt hashed before storage)
    """
    user = signup_user(payload, db)
    return _deserialize_user(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT token",
)
@limiter.limit("10/10minute")
def login(request: Request, payload: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate with email + password (OAuth2 Form Flow).

    Returns a **Bearer JWT token**.
    """
    result = login_user(payload, db)
    result["user"] = _deserialize_user(result["user"])
    return result


@router.post(
    "/login/json",
    response_model=TokenResponse,
    summary="Login and see JWT token in response body (JSON)",
)
@limiter.limit("10/10minute")
def login_json(request: Request, payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate with JSON email + password.

    Use this route if you explicitly want to view and copy the raw **access_token** text 
    directly within the Swagger UI response rather than using the Authorize popup.
    """
    result = login_user_json(payload, db)
    result["user"] = _deserialize_user(result["user"])
    return result


# ── Password Reset Flow ────────────────────────────────────────

@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/10minute")
def forgot_password(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    """
    Trigger a password reset email to the user.
    """
    user = db.query(User).filter_by(email=email).first()
    if not user:
        # Prevent email enumeration attacks by silently succeeding
        return {"message": "If that email exists, a reset link has been sent."}
    
    # Generate token
    token = str(uuid.uuid4())
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    
    reset_entry = PasswordReset(email=user.email, token=token, expires_at=expiration)
    db.add(reset_entry)
    db.commit()
    
    # Create absolute URL (Assuming standard local development, update for production)
    reset_link = f"http://127.0.0.1:8000/api/auth/reset-password?token={token}"
    
    send_reset_email(user.email, reset_link)
    
    return {"message": "If that email exists, a reset link has been sent."}


@router.get("/reset-password", response_class=HTMLResponse)
def render_reset_password_form(token: str, db: Session = Depends(get_db)):
    """
    Serve a standalone web page for the user to securely enter their new password.
    """
    # Verify token
    reset_entry = db.query(PasswordReset).filter_by(token=token).first()
    if not reset_entry or reset_entry.expires_at < datetime.datetime.now(datetime.timezone.utc):
        return HTMLResponse(
            content="""
            <html><body style='font-family: sans-serif; text-align: center; margin-top: 50px;'>
            <h1 style='color: red;'>Invalid or Expired Link</h1>
            <p>Please return to the Wandr App and request a new password reset link.</p>
            </body></html>
            """, status_code=400
        )
        
    # Serve Beautiful UI
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Password | WANDR</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 flex items-center justify-center min-h-screen p-4">
        <div class="bg-white p-8 rounded-2xl shadow-lg max-w-sm w-full">
            <h1 class="text-2xl font-black tracking-widest text-center text-blue-600 mb-2">WANDR</h1>
            <h2 class="text-lg text-gray-700 text-center mb-6 font-semibold">Change Password</h2>
            
            <form action="/api/auth/reset-password" method="POST" class="space-y-4">
                <input type="hidden" name="token" value="{token}">
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">New Password</label>
                    <input type="password" name="new_password" required minlength="8" 
                           class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                           placeholder="••••••••">
                </div>
                
                <button type="submit" 
                        class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition shadow-md mt-4">
                    Update Password
                </button>
            </form>
            <p class="text-xs text-gray-400 text-center mt-6">Secure link verified for {reset_entry.email}</p>
        </div>
    </body>
    </html>
    """
    return html_content


@router.post("/reset-password", response_class=HTMLResponse)
def execute_password_reset(token: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)):
    """
    Validates form data, updates the password hash, and deletes the token.
    """
    reset_entry = db.query(PasswordReset).filter_by(token=token).first()
    if not reset_entry or reset_entry.expires_at < datetime.datetime.now(datetime.timezone.utc):
        return HTMLResponse(content="<h1 style='color:red;'>Token invalid or expired.</h1>", status_code=400)
        
    user = db.query(User).filter_by(email=reset_entry.email).first()
    if not user:
        return HTMLResponse(content="<h1 style='color:red;'>User no longer exists.</h1>", status_code=400)
    
    # Hash and apply
    user.hashed_password = hash_password(new_password)
    
    # Delete all tokens for this user
    db.query(PasswordReset).filter_by(email=user.email).delete()
    db.commit()
    
    return HTMLResponse(
        content="""
        <html><body style='font-family: sans-serif; text-align: center; margin-top: 50px; background-color: #f3f4f6;'>
        <h1 style='color: #16a34a; font-size: 2.5rem;'>Success! &#10004;</h1>
        <p style='font-size: 1.2rem;'>Your Wandr password has been successfully updated.</p>
        <p style='color: #6b7280;'>You may now return to the app and log in.</p>
        </body></html>
        """
    )


# ── Email Verification Flow (Signup) ────────────────────────────

@router.post("/send-verification-code", response_model=MessageResponse)
def send_verification_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a 6-digit verification code to the authenticated user's email.
    Used during signup before the onboarding interests screen.
    """
    # Delete any existing codes for this user + purpose
    db.query(EmailVerification).filter_by(user_id=current_user.id, purpose="signup").delete()
    
    code = str(random.randint(100000, 999999))
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    
    entry = EmailVerification(
        user_id=current_user.id,
        code=code,
        purpose="signup",
        expires_at=expiration,
    )
    db.add(entry)
    db.commit()
    
    if not send_verification_email(current_user.email, code):
        # Prevent silent failure where user is locked waiting for a code that never sent
        raise HTTPException(status_code=500, detail="Failed to dispatch verification email. Please try again later.")
    
    # In development, include the code in the response for convenience
    if settings.APP_ENV == "development":
        return {"message": f"Verification code sent! (Dev code: {code})"}
    return {"message": "Verification code sent to your email."}


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(
    code: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify the 6-digit code sent to the user's email during signup.
    Sets user.is_verified = True on success.
    """
    entry = db.query(EmailVerification).filter_by(
        user_id=current_user.id, purpose="signup"
    ).order_by(EmailVerification.created_at.desc()).first()
    
    if not entry:
        raise HTTPException(status_code=400, detail="No verification code found. Please request a new one.")
    
    if entry.expires_at < datetime.datetime.now(datetime.timezone.utc):
        raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")
    
    # Debug: log code comparison
    print(f"\n🔍 CODE DEBUG: received=[{code}] (len={len(code)}), stored=[{entry.code}] (len={len(entry.code)}), match={entry.code == code}")
    
    if entry.code != code.strip():
        raise HTTPException(status_code=400, detail="Invalid verification code.")
    
    current_user.is_verified = True
    db.query(EmailVerification).filter_by(user_id=current_user.id, purpose="signup").delete()
    db.commit()
    
    return {"message": "Email verified successfully!"}


# ── Password Change via OTP (In-App) ───────────────────────────

@router.post("/send-password-change-code", response_model=MessageResponse)
def send_password_change_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a 6-digit OTP to the authenticated user's email for password change.
    """
    db.query(EmailVerification).filter_by(user_id=current_user.id, purpose="password_change").delete()
    
    code = str(random.randint(100000, 999999))
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    
    entry = EmailVerification(
        user_id=current_user.id,
        code=code,
        purpose="password_change",
        expires_at=expiration,
    )
    db.add(entry)
    db.commit()
    
    if not send_otp_email(current_user.email, code, "password change"):
        # Prevent silent failure
        raise HTTPException(status_code=500, detail="Failed to dispatch OTP email. Please try again later.")
    
    if settings.APP_ENV == "development":
        return {"message": f"Password change code sent! (Dev code: {code})"}
    return {"message": "Password change code sent to your email."}


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    code: str = Form(...),
    new_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change password after verifying the 6-digit OTP code.
    """
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    
    entry = db.query(EmailVerification).filter_by(
        user_id=current_user.id, purpose="password_change"
    ).order_by(EmailVerification.created_at.desc()).first()
    
    if not entry:
        raise HTTPException(status_code=400, detail="No password change code found. Please request one first.")
    
    if entry.expires_at < datetime.datetime.now(datetime.timezone.utc):
        raise HTTPException(status_code=400, detail="Code has expired. Please request a new one.")
    
    if entry.code != code:
        raise HTTPException(status_code=400, detail="Invalid code.")
    
    current_user.hashed_password = hash_password(new_password)
    db.query(EmailVerification).filter_by(user_id=current_user.id, purpose="password_change").delete()
    db.commit()
    
    return {"message": "Password changed successfully!"}
