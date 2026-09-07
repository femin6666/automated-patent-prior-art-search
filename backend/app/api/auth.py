import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

try:
    from backend.app.core.database import get_db
    from backend.app.core.security import (
        hash_password, verify_password, create_access_token, create_refresh_token,
        get_current_user, decode_token
    )
    from backend.app.core.config import settings
    from backend.app.models.models import User
    from backend.app.schemas.schemas import (
        UserRegisterRequest, UserLoginRequest, GoogleAuthRequest, TokenResponse, UserOut,
        OTPVerifyRequest, OTPResendRequest
    )
except ImportError:
    from ..core.database import get_db
    from ..core.security import (
        hash_password, verify_password, create_access_token, create_refresh_token,
        get_current_user, decode_token
    )
    from ..core.config import settings
    from ..models.models import User
    from ..schemas.schemas import (
        UserRegisterRequest, UserLoginRequest, GoogleAuthRequest, TokenResponse, UserOut,
        OTPVerifyRequest, OTPResendRequest
    )

router = APIRouter(prefix="/auth", tags=["Authentication"])

def generate_otp_code() -> str:
    """Generate a 6-digit numeric OTP code."""
    return f"{random.randint(100000, 999999)}"

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(request: UserRegisterRequest, response: Response, db: Session = Depends(get_db)):
    """Register a new user account and initiate first-time OTP verification."""
    existing = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if existing:
        if existing.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists and is verified."
            )
        # Update unverified user with new password and fresh OTP
        existing.name = request.name.strip()
        existing.password_hash = hash_password(request.password)
        existing.otp_code = generate_otp_code()
        existing.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.commit()
        db.refresh(existing)
        return TokenResponse(
            require_otp=True,
            otp_sent_to=existing.email,
            demo_otp=existing.otp_code,
            user=UserOut.model_validate(existing)
        )

    otp = generate_otp_code()
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    user = User(
        name=request.name.strip(),
        email=request.email.lower().strip(),
        password_hash=hash_password(request.password),
        is_verified=False,
        otp_code=otp,
        otp_expires_at=expires
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        require_otp=True,
        otp_sent_to=user.email,
        demo_otp=user.otp_code,
        user=UserOut.model_validate(user)
    )

@router.post("/login", response_model=TokenResponse)
def login_user(request: UserLoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticate user credentials and issue JWT tokens (or request OTP if unverified)."""
    user = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check if first-time verification is required
    if not user.is_verified:
        user.otp_code = generate_otp_code()
        user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.commit()
        return TokenResponse(
            require_otp=True,
            otp_sent_to=user.email,
            demo_otp=user.otp_code,
            user=UserOut.model_validate(user)
        )

    access_token = create_access_token({"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token({"sub": user.id, "email": user.email})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        samesite="lax",
        secure=False
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        require_otp=False,
        user=UserOut.model_validate(user)
    )

@router.post("/google", response_model=TokenResponse)
def google_auth(request: GoogleAuthRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticate or auto-register user via Google OAuth 2.0."""
    email_clean = request.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user:
        user = User(
            name=request.name.strip() if request.name else email_clean.split("@")[0],
            email=email_clean,
            password_hash=hash_password(f"GoogleOAuth2Secured_{email_clean}"),
            is_verified=True,
            otp_code=None,
            otp_expires_at=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # User already exists! Ensure is_verified is True since Google verified the identity
        if not user.is_verified:
            user.is_verified = True
            user.otp_code = None
            user.otp_expires_at = None
            db.commit()
            db.refresh(user)

    access_token = create_access_token({"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token({"sub": user.id, "email": user.email})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        samesite="lax",
        secure=False
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        require_otp=False,
        user=UserOut.model_validate(user)
    )

@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(request: OTPVerifyRequest, response: Response, db: Session = Depends(get_db)):
    """Verify 6-digit OTP for first-time user email verification."""
    user = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    if user.is_verified:
        # Already verified, proceed to generate tokens
        pass
    else:
        now_utc = datetime.now(timezone.utc)
        # Convert DB naive datetime to UTC if needed
        otp_exp = user.otp_expires_at
        if otp_exp and otp_exp.tzinfo is None:
            otp_exp = otp_exp.replace(tzinfo=timezone.utc)

        is_valid_otp = (
            (settings.DEMO_MODE and request.otp == "123456") or
            (user.otp_code and user.otp_code == request.otp and otp_exp and otp_exp > now_utc)
        )

        if not is_valid_otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP code. Please check your email or request a new code."
            )

        user.is_verified = True
        user.otp_code = None
        user.otp_expires_at = None
        db.commit()
        db.refresh(user)

    access_token = create_access_token({"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token({"sub": user.id, "email": user.email})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        samesite="lax",
        secure=False
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        require_otp=False,
        user=UserOut.model_validate(user)
    )

@router.post("/resend-otp", response_model=TokenResponse)
def resend_otp(request: OTPResendRequest, db: Session = Depends(get_db)):
    """Resend a fresh 6-digit OTP code to user's email."""
    user = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    if user.is_verified:
        return TokenResponse(require_otp=False, user=UserOut.model_validate(user))

    user.otp_code = generate_otp_code()
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    return TokenResponse(
        require_otp=True,
        otp_sent_to=user.email,
        demo_otp=user.otp_code,
        user=UserOut.model_validate(user)
    )

@router.post("/logout")
def logout_user(response: Response):
    """Clear refresh token cookies and end session."""
    response.delete_cookie(key="refresh_token")
    return {"success": True, "message": "Successfully logged out."}

@router.post("/refresh")
def refresh_token_endpoint(refresh_token: str = None, response: Response = None, db: Session = Depends(get_db)):
    """Issue a new access token using a valid refresh token."""
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required.")
    
    payload = decode_token(refresh_token, settings.JWT_REFRESH_SECRET)
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    new_access_token = create_access_token({"sub": user.id, "email": user.email})
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve currently authenticated user profile."""
    return UserOut.model_validate(current_user)
