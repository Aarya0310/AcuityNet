from datetime import datetime, timezone
import sys
from fastapi.testclient import TestClient
from backend.app.main import create_app

now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
app = create_app("sqlite:///tmp_dispatch_debug.db", clock=lambda: now[0])
client = TestClient(app)

# Login
admin_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-password"})
print(f"Admin login: {admin_resp.status_code}")
admin_token = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}

doctor_resp = client.post("/api/v1/auth/login", json={"username": "doctor", "password": "doctor-password"})
print(f"Doctor login: {doctor_resp.status_code}")
doctor_token = {"Authorization": f"Bearer {doctor_resp.json()['access_token']}"}

# Advance vitals
for tick in range(4):
    resp = client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin_token)
    print(f"Advance tick {tick}: {resp.status_code}")
    if resp.status_code != 200:
        print(f"  Error: {resp.text}")

# Get current alert
alert_resp = client.get("/api/v1/patients/P-1042/alert", headers=doctor_token)
print(f"\nCurrent alert: {alert_resp.status_code}")
if alert_resp.status_code == 200:
    alert_data = alert_resp.json()
    if alert_data:
        print(f"  Alert ID: {alert_data.get('alert_id')}")
        print(f"  Alert state: {alert_data.get('state')}")
    else:
        print("  No alert (null)")
else:
    print(f"  Error: {alert_resp.text}")

# Get dispatch evaluation
eval_resp = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor_token)
print(f"\nDispatch evaluation: {eval_resp.status_code}")
print(f"  Response: {eval_resp.text[:500]}")
if eval_resp.status_code == 200:
    try:
        eval_data = eval_resp.json()
        print(f"  Evaluation ID: {eval_data.get('evaluation_id')}")
        print(f"  Status: {eval_data.get('status')}")
    except Exception as e:
        print(f"  JSON parse error: {e}")
