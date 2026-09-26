"""
SentinelSIF – Risk Scoring Service
===================================
Calculates time-decayed risk scores for department and location clusters
based on incident severities and recency.
"""

import math
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session

# Severity weight mapping as specified
SEVERITY_WEIGHTS = {
    "low": 1.0,
    "medium": 3.0,
    "high": 5.0,
}

# Weight multiplier applied to a report's severity weight when it is
# flagged as a likely duplicate of a recent report (see reports.py's
# check_duplicate()). A duplicate still represents a real, recurring
# hazard signal (so it isn't ignored entirely), but shouldn't count at
# full weight — otherwise a single worker accidentally double-submitting
# (e.g. double-click, retry after a slow network response) would
# artificially spike the department's aggregate risk score.
# NOTE: This is the single source of truth for this multiplier — both
# the per-report response calculation (reports.py) and the aggregate
# calculation here (used by /risk-summary and /alerts) import it from
# this module to stay consistent.
DUPLICATE_WEIGHT_MULTIPLIER = 0.3

# Default decay parameters
DEFAULT_DECAY_RATE = 0.05  # lambda for exponential decay exp(-lambda * days_old)

# Risk Level Thresholds (Calibrated for Workplace Precursor Safety):
#   Severity weights: Low = 1.0, Medium = 3.0, High = 5.0
#   
#   Rationale:
#     - Single High Severity incident (weight=5.0) must immediately register as at least
#       "Medium Risk" (5.0 > 4.0), ensuring serious near-misses (e.g., gas leaks, exposed machinery)
#       are never falsely flagged as "Low Risk".
#     - Single Medium Severity incident (weight=3.0) registers as "Low Risk" (3.0 <= 4.0).
#     - Single Low Severity observation (weight=1.0) registers as "Low Risk" (1.0 <= 4.0).
#     - Escalation / Precursor accumulation:
#         * Two High incidents: 5.0 + 5.0 = 10.0 > 8.0 -> "High Risk"
#         * Three Medium incidents: 3.0 + 3.0 + 3.0 = 9.0 > 8.0 -> "High Risk"
#         * Multiple Low incidents: 5 Lows (5.0) -> "Medium Risk"; 9 Lows (9.0) -> "High Risk"
#
#   Threshold values:
#     High Risk:   score > 8.0   (critical escalation or multiple severe precursors)
#     Medium Risk: score > 4.0   (single high incident or accumulating medium/low precursors)
#     Low Risk:    score <= 4.0  (isolated medium/low observations)
HIGH_RISK_THRESHOLD = 8.0
MEDIUM_RISK_THRESHOLD = 4.0


def get_severity_weight(severity: Optional[str]) -> float:
    """
    Map severity label to numerical base weight.
    """
    if not severity:
        return 1.0
    return SEVERITY_WEIGHTS.get(severity.strip().lower(), 1.0)


def calculate_risk_score(
    department: str,
    location: str,
    db: Session,
    target_date: Optional[date] = None,
    decay_rate: float = DEFAULT_DECAY_RATE,
    exclude_report_id: Optional[int] = None,
) -> float:
    """
    Calculate time-decayed aggregate risk score for a department + location combo.

    Pulls all reports matching department and location from the database,
    applies exponential decay weight = severity_weight * exp(-decay_rate * days_old),
    discounts reports flagged as duplicates by DUPLICATE_WEIGHT_MULTIPLIER,
    and sums the decayed weights.

    Parameters
    ----------
    department : str
        Department name (e.g. "Drilling", "Warehouse").
    location : str
        Specific site location (e.g. "Platform Alpha", "Maintenance Shed").
    db : Session
        SQLAlchemy database session.
    target_date : Optional[date]
        Reference date for age calculation (defaults to date.today()).
    decay_rate : float
        Exponential decay factor per day (default 0.05).
    exclude_report_id : Optional[int]
        If given, that report is excluded from the calculation. Used when
        recomputing a report's own risk_score after editing it (PUT
        /reports/{id}), so the report isn't counted against itself.

    Returns
    -------
    float
        Aggregated time-decayed risk score, rounded to 2 decimal places.
    """
    from ..models import Report

    if target_date is None:
        target_date = date.today()

    # Query all reports for this department and location
    query = db.query(Report).filter(
        Report.department == department,
        Report.location == location
    )
    if exclude_report_id is not None:
        query = query.filter(Report.report_id != exclude_report_id)
    reports = query.all()

    if not reports:
        return 0.0

    total_score = 0.0
    for rep in reports:
        sev_weight = get_severity_weight(rep.severity)

        # Discount duplicates so accidental double-submissions don't
        # inflate the aggregate risk score.
        if getattr(rep, "is_duplicate", False):
            sev_weight = sev_weight * DUPLICATE_WEIGHT_MULTIPLIER

        # Calculate days since report date
        report_date = rep.date
        if isinstance(report_date, datetime):
            report_date = report_date.date()

        days_old = max(0, (target_date - report_date).days) if report_date else 0
        decayed_weight = sev_weight * math.exp(-decay_rate * days_old)
        total_score += decayed_weight

    return round(total_score, 2)


def get_risk_level(score: float) -> str:
    """
    Determine risk tier label from a continuous risk score.

    Thresholds:
      - score > 8.0:  "High Risk"
      - score > 4.0:  "Medium Risk"
      - otherwise:    "Low Risk"

    Parameters
    ----------
    score : float
        Calculated risk score.

    Returns
    -------
    str
        "High Risk", "Medium Risk", or "Low Risk".
    """
    if score > HIGH_RISK_THRESHOLD:
        return "High Risk"
    elif score > MEDIUM_RISK_THRESHOLD:
        return "Medium Risk"
    else:
        return "Low Risk"