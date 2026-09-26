"""
SentinelSIF – Database Seeder Script (Optional Demo Helper)
===========================================================
Populates the SentinelSIF database with historical reports from
backend/data/synthetic_safety_reports.csv so the Risk Heatmap,
Trend Line Chart, and KPI Cards are immediately rich with live data for demo.

Usage:
    python seed_data.py
"""

import sys
import pathlib
import pandas as pd
from datetime import datetime

# Setup paths
BACKEND_DIR = pathlib.Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base, engine, SessionLocal
from app.models import Report
from app.services.risk_scoring import calculate_risk_score, get_severity_weight

CSV_PATH = BACKEND_DIR / "data" / "synthetic_safety_reports.csv"


def seed():
    print(f"[Seeder] Loading records from {CSV_PATH}...")
    if not CSV_PATH.exists():
        print(f"[Error] Dataset not found at {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)
    print(f"[Seeder] Found {len(df)} records.")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check existing count
        existing = db.query(Report).count()
        if existing > 0:
            print(f"[Seeder] Notice: Database already contains {existing} reports.")
            ans = input("Do you want to clear and re-seed? (y/n): ").strip().lower()
            if ans == 'y':
                db.query(Report).delete()
                db.commit()
                print("[Seeder] Cleared previous records.")
            else:
                print("[Seeder] Aborting seed.")
                return

        print("[Seeder] Inserting reports with time-decay risk scores...")
        count = 0
        for _, row in df.iterrows():
            report_date = datetime.strptime(str(row['date']), "%Y-%m-%d").date()
            sev = str(row['severity'])
            base_weight = get_severity_weight(sev)

            new_rep = Report(
                date=report_date,
                department=str(row['department']),
                location=str(row['location']),
                description=str(row['description']),
                hazard_type=str(row['hazard_type']),
                severity=sev,
                risk_score=base_weight,
            )
            db.add(new_rep)
            count += 1

        db.commit()

        # Recalculate aggregated risk scores for each department & location
        print("[Seeder] Recalculating aggregated time-decay scores for all clusters...")
        all_reps = db.query(Report).all()
        for rep in all_reps:
            score = calculate_risk_score(rep.department, rep.location, db=db)
            rep.risk_score = score
        db.commit()

        print(f"[Seeder] Successfully seeded {count} reports across facility zones!")
        print("[Seeder] Open http://localhost:5173 to view the populated SCADA command center.")

    except Exception as e:
        db.rollback()
        print(f"[Error] Seeding failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
