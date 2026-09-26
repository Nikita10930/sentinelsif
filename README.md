# SentinelSIF

**NLP-Based Workplace Hazard Precursor Detection System**

Smart India Hackathon 2026 — Problem Statement **SIH26165** (Oil India Limited)
Team **GridMinds_SCET** — Team ID **121756**

---

## Overview

SentinelSIF is a full-stack Serious Injury & Fatality (SIF) precursor detection system built to help industrial safety teams catch high-risk hazard signals *before* they escalate into serious incidents.

Workers and supervisors submit free-text hazard observation reports. SentinelSIF automatically classifies each report by **hazard type** and **severity** using a trained NLP pipeline, computes a **risk score**, and surfaces high-risk clusters on a live operations dashboard — giving safety teams an early warning system instead of a purely reactive one.

Built for the Oil India Limited use case, but designed to generalize to any industrial or facility-based safety reporting workflow.

## The Problem

Serious workplace injuries and fatalities are rarely sudden — they're usually preceded by a pattern of smaller, unaddressed hazard signals (near-misses, unsafe conditions, recurring complaints). In practice, these precursor reports are scattered across paper logs, spreadsheets, or informal channels, making it hard to spot the pattern before it results in an incident.

SentinelSIF addresses this by centralizing hazard reporting and using NLP to automatically flag high-severity precursors, detect duplicate/recurring reports, and surface risk trends by department and time.

## Key Features

- **Automated Hazard Classification** — TF-IDF + Multinomial Naive Bayes pipeline classifies incoming reports by hazard type (Electrical, Fire, Fall, Machinery, Chemical) and severity (Low/Medium/High), trained on a 290-row bilingual (English + Hinglish) dataset
- **Confidence-Based Fallback** — when the ML model's confidence is low, rule-based keyword logic (`keyword_fallback.py`) provides a safety-net classification instead of silently returning a low-confidence label
- **Explainability Panel** — every classification shows the top keywords that drove the model's decision, computed from per-word log-odds contribution against the trained Naive Bayes model, so safety officers can see *why* a report was flagged
- **Risk Scoring Engine** — combines severity, confidence, and time-decay (older reports weighted less) into a single risk score, calibrated against tuned HIGH/MEDIUM thresholds
- **Duplicate Detection** — flags recurring reports from the same department within a 7-day window (cosine similarity > 0.75) so repeated hazards get compounded weight instead of being treated as isolated events
- **Live Operations Dashboard** — SCADA-inspired dark UI with real-time KPIs, a facility risk heatmap, active alert panel, and multi-date risk trend chart
- **Full Report Lifecycle** — create, list, edit, and delete hazard reports via a REST API, with automatic re-classification and risk recomputation on edit

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | React + Vite |
| Database | SQLite |
| NLP / ML | scikit-learn (TF-IDF + Multinomial Naive Bayes) |
| Styling | Custom dark ops-center theme (SCADA-inspired: navy/charcoal base, cyan/amber/red accents) |

## Architecture

```
Hazard Report (text input)
        │
        ▼
 NLP Classification (classify.py)
   ├─ ML prediction (TF-IDF + Naive Bayes)
   └─ Keyword fallback (low-confidence cases)
        │
        ▼
 Risk Scoring Engine (risk_scoring.py)
   ├─ Severity weight
   ├─ Confidence adjustment
   ├─ Time-decay factor
   └─ Duplicate detection multiplier
        │
        ▼
 SQLite (reports, computed risk_score, alerts)
        │
        ▼
 React Dashboard — KPIs · Heatmap · Alerts · Trend Chart · Explainability
```

## Model Performance

- Hazard type classification accuracy: **~94.8%**
- Severity classification accuracy: **~86.2%**

Severity classification was the harder problem — early versions suffered from class imbalance and memorization on underrepresented "Low" severity examples. This was resolved by adding diverse training rows with explicit severity-signaling language rather than simply increasing dataset size.

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Copy `.env.example` to `.env` and configure as needed before running.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
cd backend
python test_api_endpoints.py
```

## Team — GridMinds_SCET

Team ID: **121756**
Problem Statement: **SIH26165** (Oil India Limited)

