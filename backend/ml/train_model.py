r"""
SentinelSIF – NLP Classification Pipeline
==========================================
Trains two MultinomialNB classifiers from safety report descriptions:
  1. hazard_type  – what kind of hazard was observed
  2. severity     – how severe the observation is

Run:
    python backend/ml/train_model.py
or (from the backend/ directory):
    .\.venv\Scripts\python ml/train_model.py
"""

import os
import re
import string
import pathlib

import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, accuracy_score

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent   # backend/
DATA_PATH = BASE_DIR / "data" / "synthetic_safety_reports.csv"
ARTIFACTS_DIR = BASE_DIR / "ml" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

VECTORIZER_PATH   = ARTIFACTS_DIR / "tfidf_vectorizer.pkl"
HAZARD_CLF_PATH   = ARTIFACTS_DIR / "nb_classifier.pkl"
LABEL_CLASSES_PATH= ARTIFACTS_DIR / "label_classes.pkl"
SEVERITY_CLF_PATH = ARTIFACTS_DIR / "severity_classifier.pkl"

# ─── Preprocessing ────────────────────────────────────────────────────────────
def preprocess(text: str) -> str:
    """
    Lowercase → remove punctuation → remove English stopwords only.
    Hindi/Hinglish tokens are intentionally preserved as meaningful signal.
    """
    # 1. Lowercase
    text = text.lower()
    # 2. Remove punctuation (replace with space to avoid merging adjacent words)
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    # 3. Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    # 4. Remove English stopwords only (sklearn's built-in list)
    tokens = [t for t in text.split() if t not in ENGLISH_STOP_WORDS]
    return " ".join(tokens)


def load_and_clean(path: pathlib.Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"[data] Loaded {len(df)} rows from {path}")

    # Drop rows with missing labels or empty description
    before = len(df)
    df = df.dropna(subset=["description", "hazard_type", "severity"])
    df = df[df["description"].str.strip() != ""]
    df = df[df["hazard_type"].str.strip() != ""]
    df = df[df["severity"].str.strip() != ""]
    after = len(df)
    if before != after:
        print(f"[data] Dropped {before - after} rows with missing values → {after} remaining")

    df["clean_description"] = df["description"].apply(preprocess)
    return df


# ─── Train + Evaluate ─────────────────────────────────────────────────────────
def train_classifier(X_train, X_test, y_train, y_test, label: str) -> MultinomialNB:
    clf = MultinomialNB()
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    print(f"\n{'='*60}")
    print(f"  {label.upper()} CLASSIFIER — Test Accuracy: {acc:.4f} ({acc*100:.1f}%)")
    print(f"{'='*60}")
    print(classification_report(y_test, y_pred, zero_division=0))
    return clf


def main():
    # ── 1. Load & clean ─────────────────────────────────────────────────────
    df = load_and_clean(DATA_PATH)

    X_text = df["clean_description"]
    y_hazard   = df["hazard_type"]
    y_severity = df["severity"]

    print(f"\n[data] Hazard type distribution:\n{y_hazard.value_counts().to_string()}")
    print(f"\n[data] Severity distribution:\n{y_severity.value_counts().to_string()}")

    # ── 2. Train/test split stratified on hazard_type ───────────────────────
    # Note: We stratify on hazard_type for the primary split; severity split
    # uses the same indices for a fair comparison.
    (X_train_raw, X_test_raw,
     y_hazard_train, y_hazard_test,
     y_sev_train, y_sev_test) = train_test_split(
        X_text, y_hazard, y_severity,
        test_size=0.20,
        stratify=y_hazard,
        random_state=42,
    )
    print(f"\n[split] Train: {len(X_train_raw)}, Test: {len(X_test_raw)}")

    # ── 3. TF-IDF Vectorization (fit on train ONLY) ─────────────────────────
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=2000)
    X_train = vectorizer.fit_transform(X_train_raw)
    X_test  = vectorizer.transform(X_test_raw)
    print(f"[tfidf] Vocabulary size: {len(vectorizer.vocabulary_)}")
    print(f"[tfidf] Feature matrix: train={X_train.shape}, test={X_test.shape}")

    # ── 4. Train hazard_type classifier ─────────────────────────────────────
    hazard_clf = train_classifier(
        X_train, X_test, y_hazard_train, y_hazard_test,
        label="hazard_type",
    )
    label_classes = list(hazard_clf.classes_)

    # ── 5. Train severity classifier ────────────────────────────────────────
    severity_clf = train_classifier(
        X_train, X_test, y_sev_train, y_sev_test,
        label="severity",
    )

    # ── 6. Save artifacts ───────────────────────────────────────────────────
    joblib.dump(vectorizer,    VECTORIZER_PATH)
    joblib.dump(hazard_clf,    HAZARD_CLF_PATH)
    joblib.dump(label_classes, LABEL_CLASSES_PATH)
    joblib.dump(severity_clf,  SEVERITY_CLF_PATH)

    print(f"\n[artifacts] Saved to {ARTIFACTS_DIR}/")
    print(f"  [OK]  {VECTORIZER_PATH.name}")
    print(f"  [OK]  {HAZARD_CLF_PATH.name}")
    print(f"  [OK]  {LABEL_CLASSES_PATH.name}")
    print(f"  [OK]  {SEVERITY_CLF_PATH.name}")
    print("\n[done] Training complete.")


if __name__ == "__main__":
    main()
