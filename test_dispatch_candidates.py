from datetime import datetime, timezone
import json
import hashlib
from fastapi.testclient import TestClient
from backend.app.main import create_app
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.persistence.models import (
    Alert, PredictionEvidence, DispatchEvaluation, Nurse
)

now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
app = create_app("sqlite:///tmp_dispatch_debug4.db", clock=lambda: now[0])
client = TestClient(app)

# Login
admin_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-password"})
admin_token = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}

doctor_resp = client.post("/api/v1/auth/login", json={"username": "doctor", "password": "doctor-password"})
doctor_token = {"Authorization": f"Bearer {doctor_resp.json()['access_token']}"}

# Create alert
print("Creating alert...")
resp0 = client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 0}, headers=admin_token)
patch_resp = client.patch("/api/v1/admin/configuration/risk-thresholds", json={"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, headers=admin_token)

for tick in range(1, 4):
    client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin_token)

# Get evaluation
print("Getting evaluation...")
eval_resp = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor_token)
eval_data = eval_resp.json()
evaluation_id = eval_data["evaluation_id"]

print(f"Evaluation candidates:")
for candidate in eval_data["candidates"]:
    print(f"  {candidate['nurse_id']}: score={candidate['score']}, eligible={candidate['eligible']}, components={candidate['components']}")

print(f"\nEvaluation exclusions:")
for excl in eval_data["exclusions"]:
    print(f"  {excl['nurse_id']}: eligible={excl['eligible']}, reasons={excl.get('exclusion_reasons', [])}")

# Get DB snapshot candidates
engine = create_engine("sqlite:///tmp_dispatch_debug4.db")
Session = sessionmaker(bind=engine)

with Session() as session:
    snapshot = session.get(DispatchEvaluation, evaluation_id)
    
    print(f"\nSnapshot candidates JSON:")
    snapshot_candidates = json.loads(snapshot.candidates)
    for candidate in snapshot_candidates:
        print(f"  {candidate['nurse_id']}: score={candidate['score']}, eligible={candidate['eligible']}, components={candidate['components']}")
    
    # Get all candidates from DB to recompute
    alert = session.scalar(select(Alert).where(Alert.patient_id == "P-1042", Alert.state != "resolved").order_by(Alert.alert_id.desc()))
    evidence = session.get(PredictionEvidence, alert.evidence_id)
    
    from backend.app.dispatch.service import DispatchService
    dispatch_service = DispatchService(lambda: now[0], None, None, None)
    
    # Get all nurses and their candidate data
    print(f"\nRecomputed candidate data:")
    candidates_recomputed = [dispatch_service._candidate_data(session, nurse, dispatch_service._utc(now[0]), dispatch_service._settings(session)) 
                             for nurse in session.scalars(select(Nurse).order_by(Nurse.nurse_id))]
    for candidate in candidates_recomputed:
        print(f"  {candidate['nurse_id']}: score={candidate.get('score')}, eligible={candidate['eligible']}, components={candidate.get('components', {})}")
    
    # Compute both fingerprints
    snapshot_candidates_sorted = sorted(json.loads(snapshot.candidates + '[]') if snapshot.candidates else [], key=lambda item: item["nurse_id"])  # This won't work, let me fix it
    
    print(f"\n\nComputing fingerprints...")
    
    # Snapshot fingerprint (what was saved)
    print(f"Snapshot fingerprint: {snapshot.source_fingerprint}")
    
    # Recomputed fingerprint
    candidates_sorted = sorted(candidates_recomputed, key=lambda item: item["nurse_id"])
    payload = {"alert_id": alert.alert_id, "state": alert.state, "evidence_id": evidence.evidence_id, "evidence_timestamp": dispatch_service._utc(evidence.server_timestamp).isoformat(), "candidates": candidates_sorted}
    payload_json = json.dumps(payload, default=str, sort_keys=True)
    recomputed_fp = hashlib.sha256(payload_json.encode()).hexdigest()
    print(f"Recomputed fingerprint: {recomputed_fp}")
    
    print(f"\nPayload snippet (first 500 chars):")
    print(payload_json[:500])
