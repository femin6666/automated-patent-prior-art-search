from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

try:
    from backend.app.core.database import get_db
    from backend.app.core.security import get_current_user
    from backend.app.models.models import User, Search, SearchResult, Report
    from backend.app.schemas.schemas import ReportOut
    from backend.app.services.report_service import generate_pdf_report
except ImportError:
    from ..core.database import get_db
    from ..core.security import get_current_user
    from ..models.models import User, Search, SearchResult, Report
    from ..schemas.schemas import ReportOut
    from ..services.report_service import generate_pdf_report

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/{search_id}", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report_for_search(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a downloadable PDF report for a search result."""
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search record not found.")

    if search.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access.")

    results = (
        db.query(SearchResult)
        .filter(SearchResult.search_id == search_id)
        .order_by(SearchResult.rank.asc())
        .all()
    )

    pdf_path = generate_pdf_report(search, results)

    report = Report(
        user_id=current_user.id,
        search_id=search_id,
        report_path=pdf_path
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportOut.model_validate(report)

@router.get("", response_model=List[ReportOut])
def get_user_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve report catalog for the current user."""
    reports = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return [ReportOut.model_validate(r) for r in reports]

@router.get("/{report_id}/download")
def download_report_file(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download generated PDF report file."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if report.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access.")

    import os
    if not os.path.exists(report.report_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF report file missing on disk.")

    return FileResponse(
        path=report.report_path,
        media_type="application/pdf",
        filename=os.path.basename(report.report_path)
    )
