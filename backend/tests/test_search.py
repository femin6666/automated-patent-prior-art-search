import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.core.database import engine, Base
from backend.scripts.seed_database import seed_patents_if_needed

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    seed_patents_if_needed()

def test_prior_art_search_workflow():
    with TestClient(app) as client:
        email = "search.tester@patentlens.ai"
        password = "SearchTesterPass123!"

        reg_payload = {
            "name": "Search Tester",
            "email": email,
            "password": password,
            "confirm_password": password
        }
        res_reg = client.post("/api/auth/register", json=reg_payload)
        if res_reg.status_code == 201:
            token = res_reg.json()["access_token"]
        else:
            res_login = client.post("/api/auth/login", json={"email": email, "password": password})
            token = res_login.json()["access_token"]

        auth_headers = {"Authorization": f"Bearer {token}"}

        search_payload = {
            "title": "AI-Based Smart Irrigation System",
            "domain": "Agriculture",
            "problem_statement": "Reduce unnecessary agricultural water consumption through automated soil telemetry.",
            "description": "A machine learning system that analyzes subterranean soil moisture sensor data and automatically controls irrigation solenoid valves based on predictive evapotranspiration models.",
            "keywords": ["Machine Learning", "IoT", "Sensors", "Automation"]
        }

        # 1. Submit Search
        res_search = client.post("/api/search", json=search_payload, headers=auth_headers)
        assert res_search.status_code == 201
        search_data = res_search.json()
        assert "search_id" in search_data
        assert search_data["invention_title"] == "AI-Based Smart Irrigation System"
        assert len(search_data["results"]) == 10
        assert search_data["is_demo_dataset"] is True
        assert "disclaimer" in search_data

        search_id = search_data["search_id"]

        # 2. Get Search Details
        res_detail = client.get(f"/api/search/{search_id}", headers=auth_headers)
        assert res_detail.status_code == 200
        assert res_detail.json()["search_id"] == search_id

        # 3. Get Search History
        res_hist = client.get("/api/search/history", headers=auth_headers)
        assert res_hist.status_code == 200
        history_items = res_hist.json()
        assert any(h["id"] == search_id for h in history_items)

        # 4. Save first patent result
        patent_id = search_data["results"][0]["patent"]["id"]
        res_save = client.post(f"/api/patents/{patent_id}/save", json={"notes": "Key prior art candidate"}, headers=auth_headers)
        assert res_save.status_code == 200

        # 5. Retrieve saved patents
        res_saved = client.get("/api/patents/saved", headers=auth_headers)
        assert res_saved.status_code == 200
        saved_items = res_saved.json()
        assert any(s["patent_id"] == patent_id for s in saved_items)

        # 6. Generate PDF report
        res_report = client.post(f"/api/reports/{search_id}", headers=auth_headers)
        assert res_report.status_code == 201
        report_id = res_report.json()["id"]

        # 7. Download PDF report
        res_dl = client.get(f"/api/reports/{report_id}/download", headers=auth_headers)
        assert res_dl.status_code == 200
        assert res_dl.headers["content-type"] == "application/pdf"
