import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportDetailOut, ReportOut
from app.services.groq_service import summarize_report
from app.services.report_parser import extract_text

router = APIRouter(prefix="/reports", tags=["reports"])

ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/jpg", "text/plain"}


@router.post("/upload", response_model=ReportDetailOut)
async def upload_report(
    file: UploadFile = File(...),
    language: str = Form("en"),  # "en" or "hi" — language of the AI summary
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, PNG, JPG, TXT.",
        )

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_MB}MB limit")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    stored_name = f"{current_user.id}_{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f:
        f.write(contents)

    extracted = extract_text(stored_path, file.content_type)
    summary = None
    if extracted.strip():
        try:
            summary = summarize_report(extracted, language=language)
        except Exception as e:
            summary = f"(AI summary unavailable: {e})"
    else:
        summary = (
            "Could not extract text automatically from this file "
            "(scanned image OCR may not be configured on the server)."
        )

    report = Report(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_path=stored_path,
        content_type=file.content_type,
        extracted_text=extracted,
        ai_summary=summary,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("", response_model=list[ReportOut])
def list_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.uploaded_at.desc())
        .all()
    )


@router.post("/{report_id}/resummarize", response_model=ReportDetailOut)
def resummarize_report(
    report_id: int,
    language: str = "en",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Regenerate the AI summary for an already-uploaded report in a different
    language, without re-uploading the file. Handy for an English/Hindi toggle."""
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.extracted_text or not report.extracted_text.strip():
        raise HTTPException(
            status_code=400, detail="No extracted text available to summarize for this report"
        )

    try:
        report.ai_summary = summarize_report(report.extracted_text, language=language)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to generate summary: {e}")

    db.commit()
    db.refresh(report)
    return report


@router.get("/{report_id}", response_model=ReportDetailOut)
def get_report(
    report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if os.path.exists(report.stored_path):
        os.remove(report.stored_path)
    db.delete(report)
    db.commit()
