from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from backend.app.core.database import get_db
    from backend.app.core.security import get_current_user
    from backend.app.models.models import User, Patent, SavedPatent
    from backend.app.schemas.schemas import PatentOut, SavedPatentOut, SavePatentRequest, CreateCustomPatentRequest
    from backend.ml.embedding_service import embedding_service
    from backend.ml.preprocessing import prepare_combined_text
except ImportError:
    from ..core.database import get_db
    from ..core.security import get_current_user
    from ..models.models import User, Patent, SavedPatent
    from ..schemas.schemas import PatentOut, SavedPatentOut, SavePatentRequest, CreateCustomPatentRequest
    from ...ml.embedding_service import embedding_service
    from ...ml.preprocessing import prepare_combined_text

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
    """Get single patent details by patent_id or patent_number."""
    patent = db.query(Patent).filter((Patent.id == patent_id) | (Patent.patent_number == patent_id)).first()
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
    """Save a patent to authenticated user's saved list under their specific logged-in user_id."""
    patent = db.query(Patent).filter((Patent.id == patent_id) | (Patent.patent_number == patent_id)).first()
    if not patent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patent not found.")

    existing = (
        db.query(SavedPatent)
        .filter(SavedPatent.user_id == current_user.id, SavedPatent.patent_id == patent.id)
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
        patent_id=patent.id,
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
    """Remove a patent from authenticated user's saved patents list."""
    patent = db.query(Patent).filter((Patent.id == patent_id) | (Patent.patent_number == patent_id)).first()
    if patent:
        saved = (
            db.query(SavedPatent)
            .filter(SavedPatent.user_id == current_user.id, SavedPatent.patent_id == patent.id)
            .first()
        )
    else:
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


@router.post("/custom", response_model=PatentOut, status_code=status.HTTP_201_CREATED)
def create_custom_patent(
    request: CreateCustomPatentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save user-created custom invention into PostgreSQL database with vector embeddings."""
    import uuid
    from datetime import datetime

    pat_number = f"US-USER-{uuid.uuid4().hex[:8].upper()}"

    combined_text = prepare_combined_text(
        title=request.title,
        problem_statement="",
        description=f"{request.abstract} {request.description}"
    )
    
    if not embedding_service.is_loaded:
        embedding_service.load_model()
        
    embedding_vec = embedding_service.generate_embedding(combined_text)

    new_patent = Patent(
        patent_number=pat_number,
        title=request.title,
        abstract=request.abstract,
        description=request.description,
        inventors=request.inventors or current_user.name,
        assignee=request.assignee or "User Invention",
        publication_date=datetime.utcnow().strftime("%Y-%m-%d"),
        domain=request.domain,
        source_url=f"https://patentlens.ai/user/patent/{pat_number}",
        embedding=embedding_vec
    )
    
    db.add(new_patent)
    db.commit()
    db.refresh(new_patent)

    # Automatically add to user's saved patents
    saved_link = SavedPatent(user_id=current_user.id, patent_id=new_patent.id, notes="User Submitted Invention")
    db.add(saved_link)
    db.commit()

    return PatentOut.model_validate(new_patent)
