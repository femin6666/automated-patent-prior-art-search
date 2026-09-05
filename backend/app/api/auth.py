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
        UserRegisterRequest, UserLoginRequest, TokenResponse, UserOut
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
        UserRegisterRequest, UserLoginRequest, TokenResponse, UserOut
    )

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(request: UserRegisterRequest, response: Response, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(User).filter(User.email == request.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    user = User(
        name=request.name.strip(),
        email=request.email.lower().strip(),
        password_hash=hash_password(request.password)
    )
    db.add(user)
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
        user=UserOut.model_validate(user)
    )

@router.post("/login", response_model=TokenResponse)
def login_user(request: UserLoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticate user credentials and issue JWT tokens."""
    user = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"}
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
