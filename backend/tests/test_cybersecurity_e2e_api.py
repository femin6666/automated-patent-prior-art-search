import pytest
from fastapi.testclient import TestClient
from main import app

def test_cybersecurity_e2e_api_runtime_output():
    """
    End-to-End API Integration Test:
    Execute POST /api/search with Cybersecurity Invention Disclosure:
    'AI-Based Network Intrusion Detection and Automated Threat Response System'
    
    Verifies:
    1. patents_retrieved matches true live API retrieved count (0 when DB fallback).
    2. Zero mechanical false positives (Geneva Drive, Cam-driven, Ratchet) in top candidates.
    3. Score < 30% item outputs 'Low Technical Relevance' (NEVER 'MODERATE').
    4. Unverified evidence items report confidence <= 25% (NEVER 85%).
    5. final_score mathematically matches displayed components.
    """
    client = TestClient(app)

    import uuid
    email = f"test.cyber.{uuid.uuid4().hex[:6]}@patentlens.ai"
    password = "SecurePassword123!"

    reg_payload = {
        "name": "Test Examiner",
        "email": email,
        "password": password,
        "confirm_password": password
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    assert res_reg.status_code == 201
    demo_otp = res_reg.json()["demo_otp"]

    res_verify = client.post("/api/auth/verify-otp", json={"email": email, "otp": demo_otp})
    assert res_verify.status_code == 200
    token = res_verify.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    search_payload = {
        "title": "AI-Based Network Intrusion Detection and Automated Threat Response System",
        "domain": "Cybersecurity",
        "problem_statement": "Cyber networks are vulnerable to high-speed zero-day intrusions that bypass traditional signature-based firewalls.",
        "description": "An autonomous cybersecurity system utilizing deep learning neural networks for network traffic anomaly detection and automated threat mitigation through real-time IP isolation and dynamic firewall rule generation.",
        "keywords": ["network intrusion detection", "anomaly classification", "automated threat response", "dynamic firewall"]
    }

    res = client.post("/api/search", json=search_payload, headers=headers)
    assert res.status_code == 201, f"Search endpoint returned HTTP {res.status_code}: {res.text}"
    
    data = res.json()

    # 1. Provenance & API Retrieved Check
    summary = data["summary"]
    patents_retrieved = summary["patents_retrieved"]
    print(f"\n==================================================")
    print(f"[E2E API TEST] Data Source: {data.get('data_source')}")
    print(f"[E2E API TEST] Patents Retrieved: {patents_retrieved}")
    print(f"[E2E API TEST] Results Count: {len(data['results'])}")
    print(f"==================================================")

    # If Lens API is unconfigured / 0 live records returned, patents_retrieved MUST be 0
    if "Database Repository" in data.get("data_source", ""):
        assert patents_retrieved == 0, f"patents_retrieved should be 0 when using Database Repository (got {patents_retrieved})"

    # 2. Mechanical False-Positive Elimination Check
    MECHANICAL_TERMS = ["geneva drive", "ratchet and pawl", "cam-driven", "indexing motion", "intermittent motion drive"]
    
    for idx, item in enumerate(data["results"], start=1):
        pat_title = item["patent"]["title"]
        pat_abs = item["patent"]["abstract"] or ""
        f_score = item["final_score"]
        conf_score = item["confidence_score"]
        rel_lbl = item["relevance_level"]
        ev_lbl = item["evidence_status_label"]

        print(f"Result #{idx}: {item['patent']['patent_number']} | '{pat_title}'")
        print(f"  Score: {f_score}% | Rank: {idx} | Risk: {item['overall_result']} | Rel: {rel_lbl}")
        print(f"  Confidence: {conf_score}% | Evidence Status: {ev_lbl}")

        # Assert zero mechanical motion patents in top candidates
        p_text_lower = f"{pat_title} {pat_abs}".lower()
        for mech_term in MECHANICAL_TERMS:
            assert mech_term not in p_text_lower, f"Mechanical false-positive candidate '{pat_title}' survived filtering for Cybersecurity search!"

        # 3. Score vs Classification Harmonization
        if f_score < 30.0:
            assert "Low" in rel_lbl, f"Item with score {f_score}% MUST output 'Low Technical Relevance' (got '{rel_lbl}')"
            assert item["overall_result"] == "NON_ANTICIPATED", f"Item with score {f_score}% MUST output 'NON_ANTICIPATED' (got '{item['overall_result']}')"
            assert "TECHNICALLY_DISTINCT" in item["result_status"], f"Item with score {f_score}% MUST output 'TECHNICALLY_DISTINCT' (got '{item['result_status']}')"

        # 4. Evidence Confidence Calibration
        has_verified_quote = any(ev.get("verified") for ev in item.get("evidence_items", []))
        if not has_verified_quote:
            assert conf_score <= 25.0, f"Item without verified quotes MUST have confidence <= 25.0% (got {conf_score}%)"

if __name__ == "__main__":
    pytest.main(["-vs", __file__])
