"""
SentinelSIF – Keyword Fallback Classifier Service
==================================================
Rule-based classifier acting as a safety net when the ML model confidence
is below threshold (< 0.60) or when ML prediction fails.
"""

import re
import string
from typing import Dict, List

# Dictionary mapping hazard_type -> list of English + Hinglish keywords
HAZARD_KEYWORDS: Dict[str, List[str]] = {
    "Electrical": [
        "wire", "shock", "spark", "circuit", "socket", "current",
        "bijli", "tar", "switchboard", "short", "voltage", "cable",
        "grounding", "earthing", "panel"
    ],
    "Fire": [
        "fire", "flame", "smoke", "jal", "dhuaan", "spark",
        "aag", "cylinder", "explosion", "blaze", "burning", "heater"
    ],
    "Fall": [
        "gir", "slip", "fall", "phisal", "height", "ladder",
        "harness", "scaffolding", "manhole", "tripped", "stumble",
        "parapet", "railing", "walkway"
    ],
    "Machinery": [
        "machine", "conveyor", "crane", "pump", "rotating", "gear",
        "shaft", "belt", "engine", "pinch", "compressor", "motor",
        "blade", "guard"
    ],
    "Chemical": [
        "chemical", "acid", "leak", "fumes", "spill", "gas",
        "toxic", "h2s", "poison", "solvent", "vapor", "hazmat",
        "caustic", "corrosive"
    ],
}


def _tokenize(text: str) -> List[str]:
    """
    Clean and tokenize input text into lowercase alphanumeric tokens.
    """
    text = text.lower()
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    tokens = [token.strip() for token in text.split() if token.strip()]
    return tokens


def keyword_classify(description: str) -> str:
    """
    Classify safety report description using keyword overlap matching.

    Parameters
    ----------
    description : str
        Text description of the safety observation.

    Returns
    -------
    str
        Best-matching hazard_type ("Electrical", "Fire", "Fall", "Machinery", "Chemical"),
        or "Unclassified" if no keywords match.
    """
    if not description or not description.strip():
        return "Unclassified"

    tokens = set(_tokenize(description))
    clean_text = " " + " ".join(tokens) + " "

    best_category = "Unclassified"
    max_matches = 0

    for category, keywords in HAZARD_KEYWORDS.items():
        # Count token matches or substring matches
        match_count = 0
        for kw in keywords:
            kw_clean = kw.lower()
            if kw_clean in tokens or f" {kw_clean} " in clean_text:
                match_count += 1

        if match_count > max_matches:
            max_matches = match_count
            best_category = category

    return best_category

# Default severity mapping used when ML severity confidence is low (<0.50).
# Based on general oil-industry risk profile: electrical, fire, and chemical
# hazards default to High (fast-escalating, life-threatening potential),
# while fall and machinery default to Medium (serious but typically slower
# to escalate without compounding factors).
DEFAULT_SEVERITY_BY_HAZARD = {
    "Electrical": "High",
    "Fire": "High",
    "Chemical": "High",
    "Fall": "Medium",
    "Machinery": "Medium",
}


def get_default_severity(hazard_type: str) -> str:
    """
    Return a rule-based default severity for a given hazard_type, used as a
    safety-net fallback when the ML severity classifier's confidence is too
    low to trust (<0.50). Defaults to "Medium" for unrecognized/Unclassified
    hazard types as a conservative middle-ground.
    """
    return DEFAULT_SEVERITY_BY_HAZARD.get(hazard_type, "Medium")
