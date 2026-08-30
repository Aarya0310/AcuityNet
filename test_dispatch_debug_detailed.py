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
app = create_app("sqlite:///tmp_dispatch_debug3.db", clock=lambda: now[0])
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
print("\nGetting evaluation...")
eval_resp = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor_token)
eval_data = eval_resp.json()
evaluation_id = eval_data["evaluation_id"]

print(f"Evaluation ID: {evaluation_id}")
print(f"Alert ID: {eval_data['alert_id']}")
print(f"Evidence ID: {eval_data['evidence_id']}")
print(f"Candidate score: {eval_data['candidates'][0]['score']}")

# Get DB details
engine = create_engine("sqlite:///tmp_dispatch_debug3.db")
Session = sessionmaker(bind=engine)

with Session() as session:
    # Get the evaluation snapshot
    snapshot = session.get(DispatchEvaluation, evaluation_id)
    print(f"\nSnapshot fingerprint: {snapshot.source_fingerprint}")
    print(f"Snapshot alert_id: {snapshot.alert_id}")
    print(f"Snapshot evidence_id: {snapshot.evidence_id}")
    
    # Get current alert and evidence
    alert = session.scalar(select(Alert).where(Alert.patient_id == "P-1042", Alert.state != "resolved").order_by(Alert.alert_id.desc()))
    print(f"\nCurrent alert_id: {alert.alert_id}")
    print(f"Current alert state: {alert.state}")
    print(f"Current alert evidence_id: {alert.evidence_id}")
    
    evidence = session.get(PredictionEvidence, alert.evidence_id)
    print(f"Evidence timestamp: {evidence.server_timestamp}")
    
    # Check the staleness conditions
    print(f"\nStaleness checks:")
    print(f"  Alert ID match: {alert.alert_id == snapshot.alert_id}")
    print(f"  Alert state == 'generated': {alert.state == 'generated'}")
    print(f"  Evidence ID match: {evidence.evidence_id == snapshot.evidence_id}")
    
    # Compute fingerprint the way decide() does
    from backend.app.dispatch.service import DispatchService
    dispatch_service = DispatchService(lambda: now[0], None, None, None)
    
    # Get all candidates
    candidates = []
    for nurse in session.scalars(select(Nurse).order_by(Nurse.nurse_id)):
        # Call _candidate_data - we need to manually build it since it's private
        # For now just get nurse data
        print(f"  Nurse {nurse.nurse_id}: available={nurse.available}, workload={nurse.workload_active}/{nurse.workload_capacity}")
    
    # Recompute fingerprint
    try:
        current_fingerprint = dispatch_service.evaluate_inputs(session, alert, evidence)
        print(f"\nRecomputed fingerprint: {current_fingerprint}")
        print(f"Fingerprint match: {current_fingerprint == snapshot.source_fingerprint}")
    except Exception as e:
        print(f"Error recomputing fingerprint: {e}")

# Try the confirm
print("\n\nAttempting confirm...")
confirm_resp = client.post(
    "/api/v1/patients/P-1042/dispatch/confirm",
    json={"evaluation_id": evaluation_id, "nurse_id": "N-SARAH", "reason": "Doctor reviewed recommendation"},
    headers=doctor_token
)
print(f"Confirm status: {confirm_resp.status_code}")
if confirm_resp.status_code != 200:
    print(f"Error: {confirm_resp.json()}")
