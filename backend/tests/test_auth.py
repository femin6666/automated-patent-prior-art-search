import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.core.database import engine, Base

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)

def test_health_check():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["service"] == "PatentLens AI"

def test_user_registration_and_login():
    with TestClient(app) as client:
        email = "test.inventor@patentlens.ai"
        password = "SecurePassword123!"

        # 1. Register
        reg_payload = {
            "name": "Test Inventor",
            "email": email,
            "password": password,
            "confirm_password": password
        }
        res_reg = client.post("/api/auth/register", json=reg_payload)
        if res_reg.status_code == 400:
            pass
        else:
            assert res_reg.status_code == 201
            data_reg = res_reg.json()
            assert "access_token" in data_reg
            assert data_reg["user"]["email"] == email

        # 2. Login
        login_payload = {
            "email": email,
            "password": password
        }
        res_login = client.post("/api/auth/login", json=login_payload)
        assert res_login.status_code == 200
        data_login = res_login.json()
        assert "access_token" in data_login
        token = data_login["access_token"]

        # 3. Get Current User Profile
        headers = {"Authorization": f"Bearer {token}"}
        res_me = client.get("/api/auth/me", headers=headers)
        assert res_me.status_code == 200
        assert res_me.json()["email"] == email

def test_invalid_login():
    with TestClient(app) as client:
        login_payload = {
            "email": "nonexistent@patentlens.ai",
            "password": "wrongpassword"
        }
        res = client.post("/api/auth/login", json=login_payload)
        assert res.status_code == 401
