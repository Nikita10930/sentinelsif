"""
SentinelSIF – NLP Inference Module
====================================
Loads trained artifacts and exposes predict_report() for use by the
FastAPI backend (future task) or directly from the command line.

CLI usage:
    python backend/ml/predict.py "H2S alarm baj raha tha near compressor"
"""

import re
import string
import pathlib
import sys
import json

import joblib
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent   # backend/
ARTIFACTS_DIR = BASE_DIR / "ml" / "artifacts"

VECTORIZER_PATH    = ARTIFACTS_DIR / "tfidf_vectorizer.pkl"
HAZARD_CLF_PATH    = ARTIFACTS_DIR / "nb_classifier.pkl"
SEVERITY_CLF_PATH  = ARTIFACTS_DIR / "severity_classifier.pkl"

# ─── Lazy-load artifacts once on first use ───────────────────────────────────
_vectorizer = None
_hazard_clf = None
_severity_clf = None


def _load_models():
    """Load all artifacts from disk (called once on first predict)."""
    global _vectorizer, _hazard_clf, _severity_clf

    if _vectorizer is None:
        if not VECTORIZER_PATH.exists():
            raise FileNotFoundError(
                f"Vectorizer not found at {VECTORIZER_PATH}. "
                "Run train_model.py first."
            )
        _vectorizer   = joblib.load(VECTORIZER_PATH)
        _hazard_clf   = joblib.load(HAZARD_CLF_PATH)
        _severity_clf = joblib.load(SEVERITY_CLF_PATH)

def _get_top_keywords(vectorizer, clf, X, predicted_class_idx, top_n=5):
    """
    Identify the words in the input that most drove the classifier toward
    the predicted class, versus the other classes.

    For each word present in the doc (non-zero TF-IDF value), computes:
        contribution = tfidf_value * (log P(word|predicted_class) - mean(log P(word|other_classes)))

    A high positive contribution means the word is both present in the
    text AND disproportionately associated with the predicted class
    relative to the alternatives — i.e. it's genuinely explanatory, not
    just a word that happens to appear in every class.
    """
    feature_names = vectorizer.get_feature_names_out()
    x_arr = X.toarray()[0]

    log_probs = clf.feature_log_prob_  # shape: (n_classes, n_features)
    n_classes = log_probs.shape[0]

    if n_classes <= 1:
        other_class_mean = log_probs[predicted_class_idx]
    else:
        other_idx = [i for i in range(n_classes) if i != predicted_class_idx]
        other_class_mean = log_probs[other_idx].mean(axis=0)

    log_odds = log_probs[predicted_class_idx] - other_class_mean

    nonzero_idx = x_arr.nonzero()[0]
    contributions = [
        (feature_names[i], float(x_arr[i] * log_odds[i]))
        for i in nonzero_idx
    ]
    contributions.sort(key=lambda pair: pair[1], reverse=True)

    return [word for word, score in contributions[:top_n] if score > 0]

# ─── Preprocessing (mirrors train_model.py exactly) ──────────────────────────
def _preprocess(text: str) -> str:
    """
    Lowercase → remove punctuation → remove English stopwords only.
    Hindi/Hinglish tokens are intentionally preserved.
    """
    text = text.lower()
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [t for t in text.split() if t not in ENGLISH_STOP_WORDS]
    return " ".join(tokens)


# ─── Public API ──────────────────────────────────────────────────────────────
def predict_report(description: str) -> dict:
    """
    Classify a safety report description.

    Parameters
    ----------
    description : str
        Raw text of the safety observation / incident report.

    Returns
    -------
    dict with keys:
        hazard_type         – predicted hazard category
        hazard_confidence   – model's max class probability (0–1)
        severity            – predicted severity level
        severity_confidence – model's max class probability (0–1)
    """
    _load_models()

    clean = _preprocess(description)
    X = _vectorizer.transform([clean])

    hazard_probs   = _hazard_clf.predict_proba(X)[0]
    severity_probs = _severity_clf.predict_proba(X)[0]

    hazard_idx   = hazard_probs.argmax()
    top_keywords = _get_top_keywords(_vectorizer, _hazard_clf, X, hazard_idx, top_n=5)
    severity_idx = severity_probs.argmax()

    return {
        "hazard_type":          _hazard_clf.classes_[hazard_idx],
        "hazard_confidence":    round(float(hazard_probs[hazard_idx]), 4),
        "severity":             _severity_clf.classes_[severity_idx],
        "severity_confidence":  round(float(severity_probs[severity_idx]), 4),
        "top_keywords":         top_keywords,
    }


# ─── CLI entry point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python predict.py \"<safety report description>\"")
        sys.exit(1)

    description = " ".join(sys.argv[1:])
    result = predict_report(description)
    print(json.dumps(result, indent=2))
