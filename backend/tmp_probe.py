import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# First create
res = client.post("/user/register", json={
    "email": "testuser_probe_2@example.com",
    "full_name": "Test User Probe",
    "username": "testuser_probe_2",
    "password": "password123",
    "phone": "1234567890"
})
print("Create Status:", res.status_code)
print("Create JSON:", res.json())

# Second create (duplicate)
res2 = client.post("/user/register", json={
    "email": "testuser_probe_2@example.com",
    "full_name": "Test User Probe",
    "username": "testuser_probe_2",
    "password": "password123",
    "phone": "1234567890"
})
print("Duplicate Status:", res2.status_code)
print("Duplicate JSON:", res2.json())
