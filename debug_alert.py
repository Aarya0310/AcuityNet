#!/usr/bin/env python
"""Debug script to test alert generation."""
import os
import tempfile
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

os.environ['ACUITYNET_JWT_SECRET'] = 'test-secret-key-at-least-32-chars-long!!!'
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import create_app
from backend.app.persistence.database import migrate_database
from backend.app.seed.demo_data import seed_demo_data

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    db_path = tmpdir / 'test.db'
    database_url = f'sqlite:///{db_path}'
    
    migrate_database(database_url)
    engine = create_engine(database_url)
    Sessions = sessionmaker(bind=engine)
    with Sessions() as session:
        seed_demo_data(session)
        session.commit()
    engine.dispose()
    
    app = create_app(database_url)
    client = TestClient(app)
    
    r = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'admin-password'})
    admin_h = {'Authorization': f'Bearer {r.json().get("access_token")}'}
    
    r = client.post('/api/v1/auth/login', json={'username': 'doctor', 'password': 'doctor-password'})
    doctor_h = {'Authorization': f'Bearer {r.json().get("access_token")}'}
    
    print("[DEBUG] Testing alert generation workflow...")
    for tick in range(4):
        r = client.post('/api/v1/patients/P-1042/vitals/advance', json={'tick': tick}, headers=admin_h)
        print(f'  Tick {tick}: {r.status_code}')
        if r.status_code != 200:
            print(f'    Error: {r.text}')
    
    r = client.patch('/api/v1/admin/configuration/risk-thresholds', 
        json={'critical_risk_threshold': 0.2, 'high_risk_threshold': 0.15}, headers=admin_h)
    print(f'  Config: {r.status_code}')
    if r.status_code != 200:
        print(f'    Error: {r.text}')
    
    r = client.get('/api/v1/patients/P-1042/alert', headers=doctor_h)
    print(f'  Alert GET: {r.status_code}')
    alert = r.json()
    if alert:
        print(f'  Alert found: state={alert.get("state")}, priority={alert.get("priority")}')
    else:
        print(f'  No alert generated')
    
    engine.dispose()
