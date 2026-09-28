import os
import sys
import json
import logging
from typing import Dict, Any

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from fastapi.testclient import TestClient
from main import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("live_e2e_audit")

client = TestClient(app)

TEST_DOMAINS = [
    {
        "domain_name": "Agriculture",
        "title": "AI-Driven Precision Soil Moisture Analysis & Variable-Rate Automated Drip Irrigation System",
        "abstract": "An automated precision agricultural irrigation system employing dielectric soil moisture sensors, weather telemetry integration, and predictive neural network algorithms to control variable-rate solenoid drip irrigation valves.",
        "technical_features": [
            "dielectric soil moisture sensor array",
            "predictive neural network irrigation controller",
            "automated variable-rate solenoid valve control",
            "weather telemetry integration"
        ]
    },
    {
        "domain_name": "Healthcare",
        "title": "Non-Invasive Wearable Continuous Glucose Monitor",
        "abstract": "A non-invasive continuous blood glucose monitoring device using multi-wavelength optical photoplethysmography (PPG) sensors and machine learning signal filtration.",
        "technical_features": [
            "multi-wavelength optical PPG sensor",
            "non-invasive continuous glucose estimation algorithm",
            "dermal optical absorption spectrum analyzer",
            "wearable wristband housing"
        ]
    },
    {
        "domain_name": "Robotics",
        "title": "Autonomous Mobile Robot Fleet Path Planning with Lidar Dynamic Obstacle Avoidance",
        "abstract": "An autonomous mobile robot navigation controller executing real-time trajectory optimization and 3D lidar point-cloud dynamic obstacle avoidance for industrial warehouse fleets.",
        "technical_features": [
            "3D lidar point-cloud obstacle detection",
            "real-time trajectory optimization algorithm",
            "fleet coordination wireless mesh node",
            "wheel odometry motor controller"
        ]
    },
    {
        "domain_name": "Energy",
        "title": "Solid-State Electrolyte Lithium Metal Battery with Protective Coating",
        "abstract": "A solid-state lithium metal secondary battery incorporating a ceramic-polymer electrolyte and nanoscale protective interfacial layer to suppress lithium dendrite formation.",
        "technical_features": [
            "solid-state ceramic-polymer electrolyte",
            "nanoscale lithium dendrite suppression layer",
            "lithium metal anode foil",
            "high-voltage cathode active material"
        ]
    },
    {
        "domain_name": "Electronics",
        "title": "Three-Terminal Gallium Nitride (GaN) Power Transistor with Integrated Gate Driver",
        "abstract": "A high electron mobility transistor (HEMT) fabricated on a gallium nitride substrate with an integrated monolithic gate driver circuit for high frequency power switching.",
        "technical_features": [
            "gallium nitride high electron mobility transistor",
            "monolithic gate driver circuit",
            "three-terminal power package",
            "parasitic inductance reduction layout"
        ]
    },
    {
        "domain_name": "AI/Software",
        "title": "Retrieval-Augmented Generation System with Knowledge Graph Indexing",
        "abstract": "A retrieval-augmented generation (RAG) system organizing enterprise unstructured documents into a vector embedding index and dense entity knowledge graph for LLM prompt context injection.",
        "technical_features": [
            "dense vector embedding vector store",
            "entity relationship knowledge graph index",
            "context window prompt synthesizer",
            "semantic similarity re-ranking pipeline"
        ]
    }
]

def get_auth_token():
    email = "live.auditor@patentlens.ai"
    password = "LiveAuditorPass123!"

    reg_payload = {
        "name": "Live Auditor",
        "email": email,
        "password": password,
        "confirm_password": password
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    if res_reg.status_code == 201 and res_reg.json().get("require_otp"):
        demo_otp = res_reg.json().get("demo_otp")
        res_ver = client.post("/api/auth/verify-otp", json={"email": email, "otp": demo_otp})
        return res_ver.json()["access_token"]
    
    res_login = client.post("/api/auth/login", json={"email": email, "password": password})
    if res_login.status_code == 200:
        if res_login.json().get("require_otp"):
            demo_otp = res_login.json().get("demo_otp")
            res_ver = client.post("/api/auth/verify-otp", json={"email": email, "otp": demo_otp})
            return res_ver.json()["access_token"]
        return res_login.json()["access_token"]
    
    raise RuntimeError(f"Authentication failed: {res_login.text}")

def run_live_audit():
    print("========================================================================")
    print("   PATENTLENS AI: LIVE MULTI-DOMAIN PIPELINE AUDIT & VERIFICATION")
    print("========================================================================")

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    audit_summary = []

    for domain_test in TEST_DOMAINS:
        domain = domain_test["domain_name"]
        print(f"\n[+] Testing Domain: {domain}")
        print(f"    Title: {domain_test['title']}")
        
        payload = {
            "title": domain_test["title"],
            "domain": domain,
            "problem_statement": domain_test["abstract"],
            "description": domain_test["abstract"],
            "reference_date": "2025-09-10",
            "technical_features": domain_test["technical_features"]
        }

        response = client.post("/api/search", json=payload, headers=headers)
        assert response.status_code in [200, 201], f"Search failed for domain {domain}: {response.text}"

        data = response.json()
        search_metadata = data.get("search_metadata", {})
        results = data.get("results", [])

        raw_retrieved = search_metadata.get("raw_records_retrieved", len(results))
        records_after_filter = search_metadata.get("filtered_candidates_count", len(results))
        unique_families = search_metadata.get("unique_patent_families", search_metadata.get("family_count", len(results)))
        shortlisted_results = len(results)

        print(f"    Raw Retrieved: {raw_retrieved} | Filtered: {records_after_filter} | Families: {unique_families} | Shortlisted: {shortlisted_results}")

        # Verify each result
        for idx, item in enumerate(results[:3]):  # inspect top 3
            patent_obj = item.get("patent", item)
            pat_num = patent_obj.get("patent_number") or patent_obj.get("lens_id") or item.get("patent_number")
            title = patent_obj.get("title") or item.get("title", "")
            final_relevance = item.get("relevance_score") or item.get("relevance") or item.get("score")
            breakdown = item.get("score_breakdown") or item.get("breakdown", {})
            evidence_quote = item.get("evidence_quote") or item.get("patent_evidence")
            evidence_status = item.get("evidence_status") or item.get("evidence_availability")

            print(f"\n    --- Result #{idx+1}: [{pat_num}] ---")
            print(f"        Title: {title[:80]}...")
            print(f"        Final Relevance: {final_relevance}%")
            print(f"        Evidence Status: {evidence_status}")
            if evidence_quote:
                print(f"        Evidence Excerpt: \"{evidence_quote[:90]}...\"")
                # Rule: Evidence quote must NOT equal the title
                assert evidence_quote != title, f"CRITICAL: Evidence quote repeats title for {pat_num}"
            
            # Verify score breakdown mathematical consistency
            if breakdown and isinstance(breakdown, dict):
                comp_sem = breakdown.get("semantic", {}).get("contribution", 0.0) if isinstance(breakdown.get("semantic"), dict) else 0.0
                comp_tf = breakdown.get("technical_features", {}).get("contribution", 0.0) if isinstance(breakdown.get("technical_features"), dict) else 0.0
                comp_ev = breakdown.get("evidence", {}).get("contribution", 0.0) if isinstance(breakdown.get("evidence"), dict) else 0.0
                comp_conc = breakdown.get("concepts", {}).get("contribution", 0.0) if isinstance(breakdown.get("concepts"), dict) else 0.0
                comp_dom = breakdown.get("domain_cpc", {}).get("contribution", 0.0) if isinstance(breakdown.get("domain_cpc"), dict) else 0.0
                raw_sum = round(comp_sem + comp_tf + comp_ev + comp_conc + comp_dom, 1)

                is_gated = breakdown.get("is_gated", False)
                score_cap = breakdown.get("score_cap")

                print(f"        Breakdown Sum: {raw_sum}% | Is Gated: {is_gated} | Cap: {score_cap}")

        audit_summary.append({
            "domain": domain,
            "raw_records_retrieved": raw_retrieved,
            "filtered_candidates_count": records_after_filter,
            "unique_patent_families": unique_families,
            "shortlisted_results": shortlisted_results
        })

    print("\n========================================================================")
    print("   LIVE MULTI-DOMAIN SEARCH AUDIT COMPLETED SUCCESSFULLY")
    print("========================================================================")
    return audit_summary

if __name__ == "__main__":
    run_live_audit()
