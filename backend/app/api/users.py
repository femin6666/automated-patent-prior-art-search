from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from backend.app.core.database import get_db
    from backend.app.core.security import get_current_user, hash_password, verify_password
    from backend.app.models.models import User
    from backend.app.schemas.schemas import UserOut, UserUpdateRequest, ChangePasswordRequest
except ImportError:
    from ..core.database import get_db
    from ..core.security import get_current_user, hash_password, verify_password
    from ..models.models import User
    from ..schemas.schemas import UserOut, UserUpdateRequest, ChangePasswordRequest

router = APIRouter(prefix="/users", tags=["Users Profile"])

@router.get("/profile", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    """View current user profile."""
    return UserOut.model_validate(current_user)

@router.put("/profile", response_model=UserOut)
def update_profile(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile name and email address."""
    if request.email.lower() != current_user.email.lower():
        existing = db.query(User).filter(User.email == request.email.lower()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already in use by another account."
            )
        current_user.email = request.email.lower().strip()

    current_user.name = request.name.strip()
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)

@router.put("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user account password."""
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password entered is incorrect."
        )

    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    return {"success": True, "message": "Password successfully updated."}

@router.delete("/account")
def delete_account(
    confirm: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account and all associated data."""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation flag 'confirm=true' required to proceed with permanent account deletion."
        )

    db.delete(current_user)
    db.commit()
    return {"success": True, "message": "Account successfully deleted."}
