"""
SentinelSIF – Analytics & Alerts Route
=======================================
Endpoints for risk score aggregation across facility departments and locations,
as well as active high-risk safety alerts.
"""

import logging
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Report
from ..schemas import AlertItem, RiskSummaryItem
from ..services.risk_scoring import calculate_risk_score, get_risk_level

logger = logging.getLogger("sentinelsif.analytics")
router = APIRouter(tags=["Analytics"])


@router.get(
    "/risk-summary",
    response_model=List[RiskSummaryItem],
    status_code=status.HTTP_200_OK,
    summary="Get aggregated risk scores and levels by department and location"
)
async def get_risk_summary(db: Session = Depends(get_db)):
    """
    Retrieve risk score and tier grouped by department and location.

    - Computes current time-decayed risk score for each department/location.
    - Determines risk level ('High Risk', 'Medium Risk', 'Low Risk').
    - Returns list sorted descending by risk_score.
    - Resilient to empty database (returns empty list []).
    """
    logger.info("GET /risk-summary invoked")

    # Fetch unique (department, location) pairs and counts
    clusters = (
        db.query(
            Report.department,
            Report.location,
            func.count(Report.report_id).label("report_count")
        )
        .group_by(Report.department, Report.location)
        .all()
    )

    if not clusters:
        logger.info("No reports found in database; returning empty risk summary.")
        return []

    today = date.today()
    summary_items = []

    for dept, loc, count in clusters:
        score = calculate_risk_score(department=dept, location=loc, db=db, target_date=today)
        level = get_risk_level(score)

        summary_items.append(
            RiskSummaryItem(
                department=dept,
                location=loc,
                risk_score=score,
                risk_level=level,
                report_count=count,
            )
        )

    # Sort descending by risk_score
    summary_items.sort(key=lambda x: x.risk_score, reverse=True)
    return summary_items


@router.get(
    "/alerts",
    response_model=List[AlertItem],
    status_code=status.HTTP_200_OK,
    summary="Get active High Risk alerts for facility departments and locations"
)
async def get_alerts(db: Session = Depends(get_db)):
    """
    Retrieve all department/location combinations currently at 'High Risk' level (> 8.0).

    - Returns department, location, risk_score, report_count, and most_recent_report_date.
    - Sorted descending by risk_score.
    - Resilient to empty database (returns empty list []).
    """
    logger.info("GET /alerts invoked")

    # Fetch unique (department, location) pairs, counts, and max dates
    clusters = (
        db.query(
            Report.department,
            Report.location,
            func.count(Report.report_id).label("report_count"),
            func.max(Report.date).label("most_recent_date")
        )
        .group_by(Report.department, Report.location)
        .all()
    )

    if not clusters:
        logger.info("No reports found in database; returning empty alerts list.")
        return []

    today = date.today()
    alerts = []

    for dept, loc, count, max_date in clusters:
        score = calculate_risk_score(department=dept, location=loc, db=db, target_date=today)
        level = get_risk_level(score)

        if level == "High Risk":
            alerts.append(
                AlertItem(
                    department=dept,
                    location=loc,
                    risk_score=score,
                    report_count=count,
                    most_recent_report_date=max_date,
                )
            )

    # Sort descending by risk_score
    alerts.sort(key=lambda x: x.risk_score, reverse=True)
    return alerts
