from datetime import datetime, timezone
import sys
from fastapi.testclient import TestClient
from backend.app.main import create_app
from sqlalchemy import select
from backend.app.persistence.models import PredictionEvidence, Alert

now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
app = create_app("sqlite:///tmp_dispatch_debug.db", clock=lambda: now[0])
client = TestClient(app)

# Get DB session
from backend.app.persistence.database import session_factory, make_engine
engine = make_engine("sqlite:///tmp_dispatch_debug.db")
sessions = session_factory(engine)

# Login
admin_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-password"})
admin_token = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}

doctor_resp = client.post("/api/v1/auth/login", json={"username": "doctor", "password": "doctor-password"})
doctor_token = {"Authorization": f"Bearer {doctor_resp.json()['access_token']}"}

# Advance vitals
for tick in range(5):  # Try 5 ticks instead of 4
    resp = client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin_token)
    print(f"Advance tick {tick}: {resp.status_code}")

# Check predictions in DB
with sessions() as session:
    predictions = list(session.scalars(select(PredictionEvidence).where(PredictionEvidence.patient_id == "P-1042")))
    print(f"\nTotal predictions: {len(predictions)}")
    for p in predictions:
        print(f"  Evidence {p.evidence_id}: score={p.score}, level={p.level}, observation_seq={p.observation_sequence}")
    
    alerts = list(session.scalars(select(Alert).where(Alert.patient_id == "P-1042")))
    print(f"\nTotal alerts: {len(alerts)}")
    for a in alerts:
        print(f"  Alert {a.alert_id}: state={a.state}, priority={a.priority}")

# Get alert via API
alert_resp = client.get("/api/v1/patients/P-1042/alert", headers=doctor_token)
print(f"\nAPI Alert response: {alert_resp.status_code}")
if alert_resp.status_code == 200 and alert_resp.json():
    print(f"  Alert: {alert_resp.json()['alert_id']}")
