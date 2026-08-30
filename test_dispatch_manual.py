from datetime import datetime, timezone
from fastapi.testclient import TestClient
from backend.app.main import create_app

now = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
app = create_app("sqlite:///tmp_dispatch_debug2.db", clock=lambda: now[0])
client = TestClient(app)

# Login
admin_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-password"})
admin_token = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}

doctor_resp = client.post("/api/v1/auth/login", json={"username": "doctor", "password": "doctor-password"})
doctor_token = {"Authorization": f"Bearer {doctor_resp.json()['access_token']}"}

# Create alert using the updated create_alert logic
print("Tick 0:")
resp0 = client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": 0}, headers=admin_token)
print(f"  Status: {resp0.status_code}")

print("\nPatch configuration:")
patch_resp = client.patch("/api/v1/admin/configuration/risk-thresholds", json={"critical_risk_threshold": 0.2, "high_risk_threshold": 0.15}, headers=admin_token)
print(f"  Status: {patch_resp.status_code}")

for tick in range(1, 4):
    print(f"\nTick {tick}:")
    resp = client.post("/api/v1/patients/P-1042/vitals/advance", json={"tick": tick}, headers=admin_token)
    print(f"  Status: {resp.status_code}")

# Get alert
print("\nGet alert:")
alert_resp = client.get("/api/v1/patients/P-1042/alert", headers=doctor_token)
print(f"  Status: {alert_resp.status_code}")
if alert_resp.status_code == 200:
    print(f"  Alert ID: {alert_resp.json().get('alert_id')}")
    print(f"  State: {alert_resp.json().get('state')}")

# Get evaluation
print("\nGet evaluation:")
eval_resp = client.get("/api/v1/patients/P-1042/dispatch/evaluation", headers=doctor_token)
print(f"  Status: {eval_resp.status_code}")
if eval_resp.status_code == 200:
    eval_data = eval_resp.json()
    print(f"  Evaluation ID: {eval_data.get('evaluation_id')}")
    print(f"  Status: {eval_data.get('status')}")
    print(f"  Recommendation nurse: {eval_data.get('recommendation_nurse_id')}")
    print(f"  Candidate score: {eval_data['candidates'][0]['score'] if eval_data.get('candidates') else 'N/A'}")

    # Try to confirm
    print("\nConfirm decision:")
    confirm_resp = client.post(
        "/api/v1/patients/P-1042/dispatch/confirm",
        json={"evaluation_id": eval_data["evaluation_id"], "nurse_id": "N-SARAH", "reason": "Doctor reviewed recommendation"},
        headers=doctor_token
    )
    print(f"  Status: {confirm_resp.status_code}")
    if confirm_resp.status_code != 200:
        print(f"  Error: {confirm_resp.json()}")
