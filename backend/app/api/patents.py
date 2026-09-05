from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from backend.app.core.database import get_db
    from backend.app.core.security import get_current_user
    from backend.app.models.models import User, Patent, SavedPatent
    from backend.app.schemas.schemas import PatentOut, SavedPatentOut, SavePatentRequest
except ImportError:
    from ..core.database import get_db
    from ..core.security import get_current_user
    from ..models.models import User, Patent, SavedPatent
    from ..schemas.schemas import PatentOut, SavedPatentOut, SavePatentRequest

router = APIRouter(prefix="/patents", tags=["Patents"])

@router.get("/saved", response_model=List[SavedPatentOut])
def get_user_saved_patents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all saved patents for the authenticated user."""
    saved = (
        db.query(SavedPatent)
        .filter(SavedPatent.user_id == current_user.id)
        .order_by(SavedPatent.created_at.desc())
        .all()
    )
    return [SavedPatentOut.model_validate(s) for s in saved]

@router.get("/{patent_id}", response_model=PatentOut)
def get_patent_details(patent_id: str, db: Session = Depends(get_db)):
    """Get single patent details by patent_id."""
    patent = db.query(Patent).filter(Patent.id == patent_id).first()
    if not patent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patent not found.")
    return PatentOut.model_validate(patent)

@router.post("/{patent_id}/save", response_model=SavedPatentOut)
def save_patent(
    patent_id: str,
    request: SavePatentRequest = SavePatentRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a patent to user's saved list with optional notes."""
    patent = db.query(Patent).filter(Patent.id == patent_id).first()
    if not patent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patent not found.")

    existing = (
        db.query(SavedPatent)
        .filter(SavedPatent.user_id == current_user.id, SavedPatent.patent_id == patent_id)
        .first()
    )
    if existing:
        if request.notes is not None:
            existing.notes = request.notes
            db.commit()
            db.refresh(existing)
        return SavedPatentOut.model_validate(existing)

    saved = SavedPatent(
        user_id=current_user.id,
        patent_id=patent_id,
        notes=request.notes
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return SavedPatentOut.model_validate(saved)

@router.delete("/{patent_id}/save")
def unsave_patent(
    patent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a patent from user's saved patents list."""
    saved = (
        db.query(SavedPatent)
        .filter(SavedPatent.user_id == current_user.id, SavedPatent.patent_id == patent_id)
        .first()
    )
    if not saved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patent not found in saved list.")

    db.delete(saved)
    db.commit()
    return {"success": True, "message": "Patent removed from saved list."}
