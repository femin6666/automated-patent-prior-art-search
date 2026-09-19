import pytest
import logging
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
logger = logging.getLogger("patentlens.test_10_domain")

BENCHMARK_DOMAINS = [
    {
        "id": 1,
        "title": "AI-Based Network Intrusion Detection and Automated Threat Response System",
        "domain": "Software / Cybersecurity",
        "problem": "Undetected malicious network traffic anomalies and slow manual threat mitigation.",
        "description": "An automated network security platform utilizing deep neural networks to monitor packet headers, detect zero-day intrusion anomalies in real-time, and trigger dynamic firewall rule updates and micro-segmentation quarantine."
    },
    {
        "id": 2,
        "title": "Smart Water Leak Detection System Using IoT Sensors",
        "domain": "IoT / Environmental Monitoring",
        "problem": "Undetected pipe burst and water distribution leakage causing building water damage.",
        "description": "A smart plumbing monitoring system comprising acoustic vibration sensors, ultrasonic flow rate meters, and an IoT gateway that calculates pressure differential anomalies to shut off solenoid valve actuators."
    },
    {
        "id": 3,
        "title": "Portable Food Freshness Detection Device Using Gas Sensors",
        "domain": "Electronics / Food Safety",
        "problem": "Spoilage of perishable meat and produce due to inaccurate expiration date labeling.",
        "description": "A handheld food quality analyzer integrating a metal-oxide volatile organic compound (VOC) gas sensor array, temperature sensor, and microcontroller that estimates total volatile basic nitrogen (TVB-N) levels."
    },
    {
        "id": 4,
        "title": "Autonomous Warehouse Inventory Robot",
        "domain": "Robotics / Automation",
        "problem": "Labor-intensive manual warehouse stocktaking and misplaced inventory pallet tracking.",
        "description": "An autonomous mobile robot (AMR) featuring 3D LiDAR spatial mapping, optical barcode scanning camera, UHF RFID antenna array, and obstacle avoidance motion planning controller for continuous inventory auditing."
    },
    {
        "id": 5,
        "title": "Noise-Based Machine Fault Detection System",
        "domain": "Industrial IoT / Predictive Maintenance",
        "problem": "Unexpected industrial rotating machinery breakdown and bearing fatigue failure.",
        "description": "A predictive maintenance platform that captures acoustic emissions using directional MEMS microphone arrays, computes Fast Fourier Transform (FFT) spectral frequencies, and classifies mechanical bearing vibration anomalies."
    },
    {
        "id": 6,
        "title": "Wearable Rehabilitation Motion Tracking Device",
        "domain": "Healthcare / Wearable Tech",
        "problem": "Inaccurate joint range-of-motion measurement during home physical therapy rehabilitation.",
        "description": "A flexible knee rehabilitation sleeve integrating 9-axis inertial measurement unit (IMU) sensors, surface electromyography (sEMG) muscle electrodes, and a Bluetooth Low Energy (BLE) telemetry module."
    },
    {
        "id": 7,
        "title": "AI-Based Traffic Signal Optimization System",
        "domain": "Smart City / Transportation",
        "problem": "Urban traffic congestion and excessive vehicle idling at fixed-timer intersection signals.",
        "description": "A smart traffic control system using computer vision camera feeds to estimate vehicle queue lengths, reinforcement learning to dynamically adjust green light phase duty cycles, and priority override for emergency vehicles."
    },
    {
        "id": 8,
        "title": "Solar Panel Cleaning Robot",
        "domain": "Renewable Energy / Robotics",
        "problem": "Dust accumulation reducing photovoltaic panel energy conversion efficiency in arid climates.",
        "description": "An autonomous track-driven solar panel cleaning robot comprising microfiber cleaning rollers, dry air jet blowers, edge-detection optical sensors, and onboard solar charging battery pack."
    },
    {
        "id": 9,
        "title": "Automated Medical Pill Dispensing Device",
        "domain": "Medical Devices / IoT",
        "problem": "Patient medication non-adherence and accidental incorrect dosage administration.",
        "description": "A smart medical pill dispenser featuring rotating carousel medication cartridges, optical pill verification drop sensors, automated locking compartment, and cellular alert gateway for caregiver notifications."
    },
    {
        "id": 10,
        "title": "Smart Building Energy Optimization System",
        "domain": "CleanTech / Building Automation",
        "problem": "High energy consumption in commercial HVAC and lighting systems during occupancy fluctuations.",
        "description": "A building management system integrating wireless CO2 occupancy sensors, ambient light sensors, thermal imaging cameras, and predictive model predictive control (MPC) algorithms to dynamically modulate damper actuators."
    }
]


def test_10_domain_benchmark_suite():
    """Execute fast 10-domain regression test suite under TESTING=true mode."""
    import os
    from app.core.config import settings
    os.environ["TESTING"] = "true"
    settings.TESTING = True

    results_summary = []

    print("\n\n" + "=" * 195)
    print(" PATENTLENS AI — FAST 10-DOMAIN DETERMINISTIC REGRESSION SUITE (TESTING=true) ")
    print("=" * 195)

    headers = [
        "DOMAIN", "LENS HTTP STATUS", "LENS RETR", "PARSED", "DB FALLBACK",
        "FAMILIES", "SBERT CAND", "TECH CAND", "VERIFIED EV", "SHORTLISTED",
        "FINAL CONF", "FINAL SOURCE STATUS"
    ]
    print(
        f"{headers[0]:<35} | {headers[1]:<17} | {headers[2]:<9} | {headers[3]:<6} | {headers[4]:<11} | "
        f"{headers[5]:<8} | {headers[6]:<10} | {headers[7]:<9} | {headers[8]:<11} | {headers[9]:<11} | "
        f"{headers[10]:<10} | {headers[11]:<22}"
    )
    print("-" * 195)

    for item in BENCHMARK_DOMAINS:
        payload = {
            "title": item["title"],
            "domain": item["domain"],
            "problem_statement": item["problem"],
            "description": item["description"],
            "keywords": [item["domain"].split("/")[0].strip()]
        }

        res = client.post("/api/search", json=payload)
        assert res.status_code == 201, f"Search failed for {item['title']}: {res.text}"

        data = res.json()
        summary = data.get("summary", {})
        pipeline = summary.get("pipeline_metrics", {})
        results = data.get("results", [])

        api_retrieved = pipeline.get("lens_records_retrieved", pipeline.get("patents_retrieved", 0))
        lens_status = pipeline.get("lens_api_status", "LENS_TESTING_MODE")
        http_status_label = "200 (TESTING_MODE)"

        parsed_cnt = api_retrieved
        db_fallback_cnt = pipeline.get("database_fallback_candidates", 0)
        families_cnt = pipeline.get("unique_families", 0)
        sbert_cand_cnt = pipeline.get("semantic_candidates", 0)
        tech_cand_cnt = pipeline.get("technical_candidates", 0)

        shortlisted = len(results)
        evidence_verified_count = sum(1 for r in results if r.get("verification_status") == "VERIFIED" or any(e.get("verified") for e in r.get("evidence_items", [])))
        first_conf = results[0].get("confidence_score", 0.0) if results else 0.0

        first_src_status = results[0].get("source_status", "DATABASE") if results else "DATABASE"
        source_label = f"DATABASE/TEST_FIXTURE ({lens_status})"

        # Strict testing mode assertions: must NEVER be reported as LIVE_API in TESTING mode
        assert first_src_status != "LIVE_API", f"Regresssion test fixture returned LIVE_API provenance: {first_src_status}"
        assert "Live API" not in data.get("data_source", ""), f"Data source claimed Live API in testing mode: {data.get('data_source')}"
        if results:
            assert results[0].get("source_status") in ["DATABASE", "CACHE", "FALLBACK", "TEST_FIXTURE"]

        # Verify zero verified evidence yields confidence <= 25%
        for r in results:
            ver_count = sum(1 for e in r.get("evidence_items", []) if e.get("verified"))
            if ver_count == 0 and r.get("verification_status") != "VERIFIED":
                assert r.get("confidence_score", 0.0) <= 25.0, f"Unverified record got high confidence {r.get('confidence_score')}"

        # Verify no synthetic evidence quotes in response
        for r in results:
            for f_comp in r.get("feature_comparison", []):
                q = f_comp.get("evidence_quote")
                if q:
                    assert "Disclosed in prior-art technical specification" not in q

        domain_short_title = item['title'][:33]
        print(
            f"{domain_short_title:<35} | {http_status_label:<17} | {api_retrieved:<9} | {parsed_cnt:<6} | {db_fallback_cnt:<11} | "
            f"{families_cnt:<8} | {sbert_cand_cnt:<10} | {tech_cand_cnt:<9} | {evidence_verified_count:<11} | {shortlisted:<11} | "
            f"{first_conf:>8.1f}% | {source_label:<22}"
        )

        results_summary.append({
            "domain": item["domain"],
            "title": item["title"],
            "http_status": http_status_label,
            "api_retrieved": api_retrieved,
            "parsed_count": parsed_cnt,
            "db_fallback": db_fallback_cnt,
            "families_count": families_cnt,
            "sbert_candidates": sbert_cand_cnt,
            "technical_candidates": tech_cand_cnt,
            "shortlisted": shortlisted,
            "evidence_verified": evidence_verified_count,
            "final_confidence": first_conf,
            "source_status": source_label
        })

    print("=" * 195 + "\n")
    assert len(results_summary) == 10

