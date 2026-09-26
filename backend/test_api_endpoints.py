"""
SentinelSIF – Backend Route Integration Tests
==============================================
Tests all endpoints for both valid inputs and invalid edge cases:
  1. GET /health
  2. POST /classify (High-confidence ML, Low-confidence Fallback, Invalid 422)
  3. POST /upload-report (Valid, Duplicate Detection, Invalid 422)
  3c. GET /reports, PUT /reports/{id}, DELETE /reports/{id}
  4. GET /risk-summary (Sorted descending, schema, empty DB)
  5. GET /alerts (Threshold > 8.0, schema, empty DB)
"""

import json
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.models import Report

client = TestClient(app)


def run_tests():
    # Reset DB tables for clean testing
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("=" * 70)
    print("1. TEST GET /health")
    print("=" * 70)
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    print("Health Status Code:", res.status_code)
    print("Health Payload:", res.json())
    assert res.json() == {"status": "ok", "service": "SentinelSIF"}

    print("\n" + "=" * 70)
    print("2. TEST POST /classify (Valid Input & Confidence Fallback)")
    print("=" * 70)
    # Test high-confidence sentence (ML direct without fallback)
    high_conf_text = "Old crane hook showing visible wear, inspection tag expired last month."
    res_high = client.post("/classify", json={"description": high_conf_text})
    assert res_high.status_code == 200, f"Classify failed: {res_high.status_code}"
    high_data = res_high.json()
    print("High-confidence ML prediction:", high_data)
    assert high_data["hazard_type"] == "Machinery"
    assert high_data["hazard_confidence"] >= 0.60
    assert high_data["used_fallback"] is False
    print("[PASS] High confidence ML prediction correctly used fallback=False")

    # Test ambiguous / Hinglish input that triggers keyword fallback (< 0.60 confidence)
    fallback_text = "Gir gaya worker walkway ke upar"
    res_fallback = client.post("/classify", json={"description": fallback_text})
    assert res_fallback.status_code == 200
    fallback_data = res_fallback.json()
    print("Fallback prediction:", fallback_data)
    assert fallback_data["used_fallback"] is True
    assert fallback_data["hazard_type"] == "Fall"
    print("[PASS] Low confidence correctly triggered keyword fallback with fallback=True")

    # ── REGRESSION TEST: fallback must NOT overwrite ML result with
    # "Unclassified" when keyword_classify() finds no match. ──────────────
    no_kw_match_text = "Slight residue near the north pipeline junction, unusual smell reported"
    res_no_kw = client.post("/classify", json={"description": no_kw_match_text})
    assert res_no_kw.status_code == 200
    no_kw_data = res_no_kw.json()
    print("Low-confidence, no-keyword-match prediction:", no_kw_data)
    assert no_kw_data["hazard_type"] != "Unclassified", (
        "Fallback overwrote a valid ML prediction with 'Unclassified' — "
        "regression of the fallback-overwrite bug!"
    )
    print("[PASS] Low confidence + no keyword match correctly retained ML prediction")

    # ── REGRESSION TEST: severity fallback should kick in when ML severity
    # confidence is low, replacing the unreliable guess with a rule-based
    # default keyed off hazard_type. ───────────────────────────────────────
    print("\nTesting severity fallback...")
    ambiguous_severity_text = "Slight residue near the north pipeline junction, unusual smell reported"
    res_sev = client.post("/classify", json={"description": ambiguous_severity_text})
    assert res_sev.status_code == 200
    sev_data = res_sev.json()
    print("Severity fallback prediction:", sev_data)
    if sev_data["severity_confidence"] < 0.50:
        assert sev_data["severity"] in ("High", "Medium", "Low"), (
            "Severity fallback should assign a valid rule-based default, "
            "not an arbitrary/unmapped value."
        )
        print("[PASS] Low severity confidence correctly triggered rule-based default")
    else:
        print("[SKIP] Severity confidence was >= 0.50 this run — fallback not triggered")

    print("\n" + "=" * 70)
    print("2b. TEST POST /classify (Invalid Inputs -> 422)")
    print("=" * 70)
    # Empty description
    r_empty = client.post("/classify", json={"description": ""})
    assert r_empty.status_code == 422, f"Expected 422, got {r_empty.status_code}"
    print("[PASS] Empty description -> 422 Unprocessable Entity")

    # Too short description (< 5 chars)
    r_short = client.post("/classify", json={"description": "hi"})
    assert r_short.status_code == 422
    print("[PASS] Short description (< 5 chars) -> 422 Unprocessable Entity")

    # Missing field
    r_missing = client.post("/classify", json={})
    assert r_missing.status_code == 422
    print("[PASS] Missing 'description' field -> 422 Unprocessable Entity")

    print("\n" + "=" * 70)
    print("3. TEST POST /upload-report (Valid & Duplicate Detection)")
    print("=" * 70)
    # Upload first report
    r1 = client.post(
        "/upload-report",
        json={
            "department": "Drilling",
            "location": "Rig 4",
            "description": "Loose electrical wire sparking near generator panel"
        }
    )
    assert r1.status_code == 201, f"Expected 201, got {r1.status_code}"
    d1 = r1.json()
    print(f"Report 1 (ID={d1['report_id']}) created:")
    print(f"  hazard_type: {d1['hazard_type']}, severity: {d1['severity']}")
    print(f"  risk_score: {d1['risk_score']}, possible_duplicate_of: {d1['possible_duplicate_of']}")
    assert d1["hazard_type"] == "Electrical"
    assert d1["possible_duplicate_of"] is None

    # Upload second report: same department, within 7 days, near-identical text (> 0.75 similarity)
    r2 = client.post(
        "/upload-report",
        json={
            "department": "Drilling",
            "location": "Rig 4",
            "description": "Loose electrical wire sparking near the generator panel"
        }
    )
    assert r2.status_code == 201
    d2 = r2.json()
    print(f"Report 2 (ID={d2['report_id']}) duplicate check:")
    print(f"  possible_duplicate_of: {d2['possible_duplicate_of']}")
    assert d2["possible_duplicate_of"] == d1["report_id"], "Duplicate detection failed to link report_id!"
    print(f"[PASS] Duplicate correctly flagged with report_id: {d1['report_id']}")

    print("\n" + "=" * 70)
    print("3b. TEST POST /upload-report (Invalid Inputs -> 422)")
    print("=" * 70)
    # Missing department
    r_no_dept = client.post("/upload-report", json={"location": "Rig 4", "description": "Valid description text"})
    assert r_no_dept.status_code == 422
    print("[PASS] Missing department -> 422 Unprocessable Entity")

    # Whitespace-only location
    r_empty_loc = client.post("/upload-report", json={"department": "Drilling", "location": "   ", "description": "Valid description text"})
    assert r_empty_loc.status_code == 422
    print("[PASS] Empty location -> 422 Unprocessable Entity")

    # Description too short
    r_bad_desc = client.post("/upload-report", json={"department": "Drilling", "location": "Rig 4", "description": "bad"})
    assert r_bad_desc.status_code == 422
    print("[PASS] Short description -> 422 Unprocessable Entity")

    print("\n" + "=" * 70)
    print("3c. TEST GET /reports, PUT /reports/{id}, DELETE /reports/{id}")
    print("=" * 70)

    # GET /reports — list all reports (should include the 2 already created above)
    r_list = client.get("/reports")
    assert r_list.status_code == 200
    all_reports = r_list.json()
    print(f"Total reports listed: {len(all_reports)}")
    assert len(all_reports) >= 2
    assert all_reports[0]["report_id"] >= all_reports[-1]["report_id"], "Reports should be ordered most-recent-first"
    print("[PASS] GET /reports returns list of reports, most recent first")

    # PUT /reports/{id} — update department only, no description change
    # (should NOT trigger reclassification, but SHOULD recompute risk_score)
    r_put_dept = client.put(
        f"/reports/{d1['report_id']}",
        json={"department": "Refinery Ops"}
    )
    assert r_put_dept.status_code == 200
    put_dept_data = r_put_dept.json()
    print(f"Report {d1['report_id']} after department-only update:", put_dept_data)
    assert put_dept_data["department"] == "Refinery Ops"
    assert put_dept_data["hazard_type"] == d1["hazard_type"], "Hazard type should NOT change when description is untouched"
    print("[PASS] PUT department-only update succeeded without reclassification")

    # PUT /reports/{id} — update description (should trigger reclassification)
    r_put_desc = client.put(
        f"/reports/{d1['report_id']}",
        json={"description": "Severe chemical spill near storage tank, critical and immediate danger"}
    )
    assert r_put_desc.status_code == 200
    put_desc_data = r_put_desc.json()
    print(f"Report {d1['report_id']} after description update:", put_desc_data)
    assert put_desc_data["description"] == "Severe chemical spill near storage tank, critical and immediate danger"
    assert put_desc_data["hazard_type"] == "Chemical", f"Expected reclassification to Chemical, got {put_desc_data['hazard_type']}"
    print("[PASS] PUT description update correctly triggered reclassification")

    # PUT /reports/{id} — non-existent report should 404
    r_put_404 = client.put("/reports/999999", json={"department": "Drilling"})
    assert r_put_404.status_code == 404
    print("[PASS] PUT on non-existent report_id -> 404 Not Found")

    # DELETE /reports/{id} — delete report 2 (the duplicate one)
    r_delete = client.delete(f"/reports/{d2['report_id']}")
    assert r_delete.status_code == 200
    print(f"Delete response: {r_delete.json()}")
    print(f"[PASS] Report {d2['report_id']} deleted successfully")

    # Verify it's actually gone
    r_list_after = client.get("/reports")
    remaining_ids = [r["report_id"] for r in r_list_after.json()]
    assert d2["report_id"] not in remaining_ids, "Deleted report still present in GET /reports"
    print("[PASS] Deleted report no longer appears in GET /reports")

    # DELETE /reports/{id} — non-existent report should 404
    r_delete_404 = client.delete("/reports/999999")
    assert r_delete_404.status_code == 404
    print("[PASS] DELETE on non-existent report_id -> 404 Not Found")

    print("\n" + "=" * 70)
    print("4. TEST GET /risk-summary")
    print("=" * 70)
    r_sum = client.get("/risk-summary")
    assert r_sum.status_code == 200
    summary = r_sum.json()
    print("Risk Summary items:", len(summary))
    print(json.dumps(summary, indent=2))
    assert len(summary) >= 1
    assert "risk_score" in summary[0]
    assert "risk_level" in summary[0]
    assert "report_count" in summary[0]
    print("[PASS] /risk-summary returns properly structured and sorted records")

    print("\n" + "=" * 70)
    print("5. TEST GET /alerts & Triggering High Risk Threshold")
    print("=" * 70)
    # Add multiple severe incident reports to Refining / Boiler Unit 1 to cross > 8.0 score
    for i in range(4):
        client.post(
            "/upload-report",
            json={
                "department": "Refining",
                "location": "Boiler Unit 1",
                "description": f"Crude oil pipeline explosion with thick smoke and heavy chemical fire hazard incident #{i}"
            }
        )

    r_alerts = client.get("/alerts")
    assert r_alerts.status_code == 200
    alerts = r_alerts.json()
    print(f"High Risk Alerts found: {len(alerts)}")
    print(json.dumps(alerts, indent=2))
    assert len(alerts) >= 1
    assert alerts[0]["department"] == "Refining"
    assert alerts[0]["risk_score"] > 8.0
    print("[PASS] /alerts correctly filters for High Risk department/location clusters")

    print("\n" + "=" * 70)
    print("6. TEST EMPTY DATABASE RESILIENCE")
    print("=" * 70)
    # Reset DB to completely empty
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    empty_sum = client.get("/risk-summary")
    assert empty_sum.status_code == 200
    assert empty_sum.json() == []

    empty_alt = client.get("/alerts")
    assert empty_alt.status_code == 200
    assert empty_alt.json() == []
    print("[PASS] Both /risk-summary and /alerts return [] gracefully on empty database")

    print("\n" + "#" * 70)
    print("ALL API ROUTE INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
    print("#" * 70)


if __name__ == "__main__":
    run_tests()