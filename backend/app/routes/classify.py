"""
SentinelSIF – Classification Route
===================================
Endpoint for classifying incident reports with ML inference and
rule-based keyword fallback on low confidence.
"""

import logging
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, status

from ..schemas import ClassifyRequest, ClassifyResponse
from ..services.keyword_fallback import keyword_classify, get_default_severity
# Ensure backend root is in sys.path for ml imports
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

logger = logging.getLogger("sentinelsif.classify")
router = APIRouter(tags=["Classification"])


def classify_text(description: str) -> dict:
    """
    Internal helper to classify text using ML with keyword fallback.
    Used by both /classify and /upload-report.
    """
    try:
        from ml.predict import predict_report
        ml_result = predict_report(description)
    except Exception as e:
        logger.error(f"Error executing ML predict_report: {e}", exc_info=True)
        # Fallback entirely to keyword classification if ML models fail
        kw_hazard = keyword_classify(description)
        if kw_hazard != "Unclassified":
            return {
                "hazard_type": kw_hazard,
                "hazard_confidence": 0.50,
                "severity": "Medium",
                "severity_confidence": 0.50,
                "used_fallback": True,
                "top_keywords": [],
            }
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Classification model unavailable: {str(e)}"
        )

    hazard_type = ml_result["hazard_type"]
    hazard_confidence = ml_result["hazard_confidence"]
    severity = ml_result["severity"]
    severity_confidence = ml_result["severity_confidence"]
    used_fallback = False
    top_keywords = ml_result.get("top_keywords", []) 

    # CONFIDENCE-BASED FALLBACK LOGIC:
    # If hazard_confidence < 0.6, call keyword_classify() as a backup.
    #
    # IMPORTANT (bug fix): only OVERRIDE the ML result if the keyword
    # classifier actually finds a match. Previously this block blindly
    # assigned hazard_type = kw_result even when kw_result was
    # "Unclassified", which meant a low-confidence-but-correct ML guess
    # (e.g. "Fire" at 0.55) could get silently downgraded to
    # "Unclassified" just because the keyword list had no overlap
    # (e.g. description used "smoking"/"flammable" instead of
    # "smoke"/"fire"). Keeping the ML result as a fallback-of-last-resort
    # is strictly better than discarding a real prediction.
    if hazard_confidence < 0.60:
        kw_result = keyword_classify(description)
        if kw_result != "Unclassified":
            hazard_type = kw_result
            used_fallback = True
            logger.info(
                f"Low ML confidence ({hazard_confidence:.4f} < 0.60). "
                f"Fell back to keyword classifier: '{kw_result}'"
            )
        else:
            # Keyword classifier found nothing better — keep the ML
            # model's original (low-confidence) prediction instead of
            # downgrading to "Unclassified".
            logger.info(
                f"Low ML confidence ({hazard_confidence:.4f} < 0.60) but "
                f"keyword classifier found no match. Retaining ML prediction "
                f"'{hazard_type}' instead of downgrading to Unclassified."
            )

    # SEVERITY FALLBACK LOGIC:
    # If severity_confidence < 0.50, the ML severity prediction is too
    # unreliable to trust as-is. Since severity directly drives the
    # department's risk_score (see risk_scoring.py), a wrong severity here
    # can silently produce a wrong risk level downstream. Instead of using
    # the low-confidence ML guess, fall back to a rule-based default
    # severity keyed off the (already-resolved) hazard_type.
    if severity_confidence < 0.50:
        original_severity = severity
        severity = get_default_severity(hazard_type)
        logger.info(
            f"Low severity confidence ({severity_confidence:.4f} < 0.50). "
            f"Defaulting severity from '{original_severity}' to '{severity}' "
            f"based on hazard_type='{hazard_type}'."
        )

    return {
        "hazard_type": hazard_type,
        "hazard_confidence": hazard_confidence,
        "severity": severity,
        "severity_confidence": severity_confidence,
        "used_fallback": used_fallback,
        "top_keywords": top_keywords,
    }

@router.post(
    "/classify",
    response_model=ClassifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Classify safety observation text"
)
async def classify_report(payload: ClassifyRequest):
    """
    Classify a safety report description into hazard_type and severity.

    - Validates description is non-empty and at least 5 characters.
    - Runs ML Naive Bayes classifier.
    - If hazard_confidence < 0.60, applies keyword-based fallback —
      but only overrides the ML prediction if the keyword classifier
      actually finds a matching hazard category.
    - Returns 503 if ML artifacts are inaccessible or fail.
    """
    logger.info(f"POST /classify received: '{payload.description[:60]}...'")
    result = classify_text(payload.description)
    return result