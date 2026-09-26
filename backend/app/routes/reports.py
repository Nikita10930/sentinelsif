"""
SentinelSIF – Incident Reports Route
=====================================
Endpoints for submitting safety incident reports with automatic NLP classification,
TF-IDF cosine duplicate detection, time-decay risk scoring, and database persistence.
"""

import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, List

import joblib
from fastapi import APIRouter, Depends, HTTPException, status
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Report
from ..schemas import ReportUploadRequest, ReportUploadResponse, ReportUpdateRequest
from ..services.risk_scoring import (
    calculate_risk_score,
    get_severity_weight,
    DUPLICATE_WEIGHT_MULTIPLIER,
)
from .classify import classify_text

# Paths for vectorizer artifact
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

VECTORIZER_PATH = BACKEND_DIR / "ml" / "artifacts" / "tfidf_vectorizer.pkl"

logger = logging.getLogger("sentinelsif.reports")
router = APIRouter(tags=["Reports"])

# In-memory cached vectorizer
_vectorizer = None


def _get_vectorizer():
    """Load or return the pre-trained TF-IDF vectorizer."""
    global _vectorizer
    if _vectorizer is None:
        if not VECTORIZER_PATH.exists():
            logger.warning(f"TF-IDF vectorizer artifact not found at {VECTORIZER_PATH}")
            return None
        _vectorizer = joblib.load(VECTORIZER_PATH)
    return _vectorizer


def check_duplicate(
    description: str,
    department: str,
    report_date: date,
    db: Session,
    threshold: float = 0.75
) -> Optional[int]:
    """
    Check if the report description is a likely duplicate of recent reports.

    Pulls up to 20 reports from the same department within the last 7 days,
    vectorizes them with the pre-trained TF-IDF vectorizer, and computes
    cosine similarity.

    Parameters
    ----------
    description : str
        New report description.
    department : str
        Department of the new report.
    report_date : date
        Report observation date.
    db : Session
        Database session.
    threshold : float
        Cosine similarity threshold to flag as duplicate (default 0.75).

    Returns
    -------
    Optional[int]
        report_id of the matching existing report if similarity > threshold, else None.
    """
    seven_days_ago = report_date - timedelta(days=7)

    recent_reports = (
        db.query(Report)
        .filter(Report.department == department)
        .filter(Report.date >= seven_days_ago)
        .order_by(Report.report_id.desc())
        .limit(20)
        .all()
    )

    if not recent_reports:
        return None

    try:
        vectorizer = _get_vectorizer()
        if vectorizer is None:
            return None

        recent_texts = [r.description for r in recent_reports]
        recent_vecs = vectorizer.transform(recent_texts)
        new_vec = vectorizer.transform([description])

        sims = cosine_similarity(new_vec, recent_vecs)[0]
        max_idx = int(sims.argmax())
        max_sim = float(sims[max_idx])

        if max_sim > threshold:
            dup_id = recent_reports[max_idx].report_id
            logger.info(
                f"Duplicate detected! Similarity {max_sim:.4f} > {threshold} "
                f"with report_id={dup_id}"
            )
            return dup_id

    except Exception as e:
        logger.warning(f"Duplicate detection comparison encountered an error: {e}")

    return None


@router.post(
    "/upload-report",
    response_model=ReportUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a safety incident report"
)
async def upload_report(
    payload: ReportUploadRequest,
    db: Session = Depends(get_db)
):
    """
    Upload and process a new workplace safety report.

    1. Validates required fields (department, location, description).
    2. Auto-fills hazard_type and severity via NLP classifier (with fallback).
    3. Runs duplicate detection against department reports within last 7 days.
    4. Calculates aggregate time-decayed risk score for department/location,
       applying a reduced weight if the report is a likely duplicate.
    5. Saves report transactionally to database, persisting the duplicate
       flag so later aggregate queries (/risk-summary, /alerts) also apply
       the discount consistently.
    """
    logger.info(f"POST /upload-report received for department='{payload.department}', location='{payload.location}'")

    report_date = payload.date if payload.date is not None else date.today()

    # 1. Classify description to auto-fill hazard_type and severity
    classification = classify_text(payload.description)
    hazard_type = classification["hazard_type"]
    severity = classification["severity"]

    # 2. Duplicate detection
    possible_duplicate_of = check_duplicate(
        description=payload.description,
        department=payload.department,
        report_date=report_date,
        db=db,
        threshold=0.75
    )
    is_duplicate = possible_duplicate_of is not None

    # 3. Calculate time-decay risk score for this department + location
    base_weight = get_severity_weight(severity)

    # If this report is a likely duplicate of an existing one, reduce its
    # contribution to the risk score instead of counting it at full weight.
    if is_duplicate:
        original_weight = base_weight
        base_weight = round(base_weight * DUPLICATE_WEIGHT_MULTIPLIER, 4)
        logger.info(
            f"Report flagged as duplicate of report_id={possible_duplicate_of}. "
            f"Reducing risk weight from {original_weight} to {base_weight} "
            f"(x{DUPLICATE_WEIGHT_MULTIPLIER})."
        )

    existing_risk = calculate_risk_score(
        department=payload.department,
        location=payload.location,
        db=db,
        target_date=report_date
    )
    report_risk_score = round(existing_risk + base_weight, 2)

    # 4. Create and persist report record (is_duplicate is saved so that
    # calculate_risk_score() applies the same discount consistently on
    # every future aggregate query, not just in this response).
    new_report = Report(
        date=report_date,
        department=payload.department,
        location=payload.location,
        description=payload.description,
        hazard_type=hazard_type,
        severity=severity,
        risk_score=report_risk_score,
        is_duplicate=is_duplicate,
    )

    try:
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        logger.info(f"Report successfully saved with report_id={new_report.report_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Database error writing report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database write failure: {str(e)}"
        )

    # Build response including duplicate flag
    return ReportUploadResponse(
        report_id=new_report.report_id,
        date=new_report.date,
        department=new_report.department,
        location=new_report.location,
        description=new_report.description,
        hazard_type=new_report.hazard_type,
        severity=new_report.severity,
        risk_score=new_report.risk_score,
        created_at=new_report.created_at,
        possible_duplicate_of=possible_duplicate_of,
    )

@router.get(
    "/reports",
    response_model=List[ReportUploadResponse],
    status_code=status.HTTP_200_OK,
    summary="List all safety incident reports"
)
async def list_reports(db: Session = Depends(get_db)):
    """Retrieve all reports, most recent first."""
    reports = db.query(Report).order_by(Report.report_id.desc()).all()
    return [
        ReportUploadResponse(
            report_id=r.report_id,
            date=r.date,
            department=r.department,
            location=r.location,
            description=r.description,
            hazard_type=r.hazard_type,
            severity=r.severity,
            risk_score=r.risk_score,
            created_at=r.created_at,
            possible_duplicate_of=None,
        )
        for r in reports
    ]


@router.put(
    "/reports/{report_id}",
    response_model=ReportUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing safety incident report"
)
async def update_report(
    report_id: int,
    payload: ReportUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a report's fields. If the description changes, the hazard_type
    and severity are re-classified. In both cases, the report's risk_score
    snapshot is recomputed against the current state of other reports in
    the same department/location, excluding itself to avoid double-counting.
    """
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )

    description_changed = (
        payload.description is not None
        and payload.description != report.description
    )

    if payload.department is not None:
        report.department = payload.department
    if payload.location is not None:
        report.location = payload.location
    if payload.date is not None:
        report.date = payload.date
    if payload.description is not None:
        report.description = payload.description

    if description_changed:
        classification = classify_text(report.description)
        report.hazard_type = classification["hazard_type"]
        report.severity = classification["severity"]
        logger.info(f"Report {report_id} description changed — reclassified as {report.hazard_type}/{report.severity}")

    # Recompute this report's risk_score snapshot against the current
    # state of other reports in its (possibly new) department/location.
    base_weight = get_severity_weight(report.severity)
    if report.is_duplicate:
        base_weight = round(base_weight * DUPLICATE_WEIGHT_MULTIPLIER, 4)

    other_reports_risk = calculate_risk_score(
        department=report.department,
        location=report.location,
        db=db,
        target_date=report.date,
        exclude_report_id=report.report_id,
    )
    report.risk_score = round(other_reports_risk + base_weight, 2)

    try:
        db.commit()
        db.refresh(report)
        logger.info(f"Report {report_id} updated successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Database error updating report {report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database update failure: {str(e)}"
        )

    return ReportUploadResponse(
        report_id=report.report_id,
        date=report.date,
        department=report.department,
        location=report.location,
        description=report.description,
        hazard_type=report.hazard_type,
        severity=report.severity,
        risk_score=report.risk_score,
        created_at=report.created_at,
        possible_duplicate_of=None,
    )


@router.delete(
    "/reports/{report_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a safety incident report"
)
async def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a report by ID."""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )

    try:
        db.delete(report)
        db.commit()
        logger.info(f"Report {report_id} deleted successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Database error deleting report {report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database delete failure: {str(e)}"
        )

    return {"detail": f"Report {report_id} deleted successfully.", "report_id": report_id}