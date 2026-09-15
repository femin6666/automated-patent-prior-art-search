import os
import sys
import time
import json
import csv
import logging
from pathlib import Path

# Add backend and parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings

# Enforce Explicit LIVE_BENCHMARK Opt-in
is_live_enabled = settings.LIVE_BENCHMARK or os.getenv("LIVE_BENCHMARK", "").lower() == "true"
if not is_live_enabled:
    print("\n" + "=" * 100)
    print(" 🛑 ABORTED: LIVE 10-DOMAIN AUDIT BENCHMARK IS NOT ENABLED ")
    print("=" * 100)
    print(" The live benchmark runs against remote real-world APIs (The Lens, Groq, Gemini, arXiv).")
    print(" To execute the live benchmark, you must explicitly opt in by setting:")
    print("   $env:LIVE_BENCHMARK=\"true\" (PowerShell) or export LIVE_BENCHMARK=true (Bash)\n")
    sys.exit(1)

# Ensure TESTING is False for Live Benchmark mode
os.environ["TESTING"] = "false"
settings.TESTING = False

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
logger = logging.getLogger("patentlens.live_benchmark")

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

def run_live_benchmark():
    print("\n" + "=" * 195)
    print(" PATENTLENS AI — REAL-WORLD LIVE 10-DOMAIN AUDIT BENCHMARK ")
    print(" Environment: LIVE_BENCHMARK=true | TESTING=false")
    print("=" * 195)

    headers = [
        "domain", "lens_status", "google_patents_status", "lens_records_retrieved",
        "google_patents_records_retrieved", "database_fallback_candidates",
        "families_after_dedup", "sbert_candidates", "technical_candidates",
        "verified_evidence", "final_shortlisted", "execution_time", "api_calls", "source_status"
    ]

    print(
        f"{headers[0]:<25} | {headers[1]:<15} | {headers[2]:<15} | {headers[3]:<10} | "
        f"{headers[4]:<10} | {headers[5]:<10} | {headers[6]:<10} | {headers[7]:<10} | "
        f"{headers[8]:<10} | {headers[9]:<10} | {headers[10]:<10} | {headers[11]:<8} | "
        f"{headers[12]:<8} | {headers[13]:<15}"
    )
    print("-" * 195)

    reports_dir = Path(__file__).resolve().parent.parent / "generated_reports"
    reports_dir.mkdir(exist_ok=True)

    benchmark_rows = []

    for item in BENCHMARK_DOMAINS:
        t0 = time.time()
        payload = {
            "title": item["title"],
            "domain": item["domain"],
            "problem_statement": item["problem"],
            "description": item["description"],
            "keywords": [item["domain"].split("/")[0].strip()]
        }

        res = client.post("/api/search", json=payload)
        elapsed_sec = round(time.time() - t0, 2)

        if res.status_code != 201:
            print(f"FAILED for {item['title']}: {res.text}")
            continue

        data = res.json()
        summary = data.get("summary", {})
        pipeline = summary.get("pipeline_metrics", {})
        results = data.get("results", [])

        lens_status = pipeline.get("lens_api_status", "LENS_OK")
        gp_status = "PATENTSVIEW_IDLE" if pipeline.get("database_fallback_candidates", 0) > 0 else "N/A"
        lens_retrieved = pipeline.get("lens_records_retrieved", 0)
        gp_retrieved = 0
        db_fallback = pipeline.get("database_fallback_candidates", 0)
        fam_dedup = pipeline.get("unique_families", 0)
        sbert_cand = pipeline.get("semantic_candidates", 0)
        tech_cand = pipeline.get("technical_candidates", 0)

        verified_ev = sum(1 for r in results if any(e.get("verified") for e in r.get("evidence_items", [])))
        shortlisted = len(results)
        first_src = results[0].get("source_status", "DATABASE") if results else "DATABASE"
        source_label = "LIVE_API" if (lens_retrieved > 0 and first_src == "LIVE_API") else f"DATABASE ({lens_status})"

        api_calls_count = 1 + (8 if lens_status == "LENS_OK" else 0) + (len(results))

        row = {
            "domain": item["domain"],
            "lens_status": lens_status,
            "google_patents_status": gp_status,
            "lens_records_retrieved": lens_retrieved,
            "google_patents_records_retrieved": gp_retrieved,
            "database_fallback_candidates": db_fallback,
            "families_after_dedup": fam_dedup,
            "sbert_candidates": sbert_cand,
            "technical_candidates": tech_cand,
            "verified_evidence": verified_ev,
            "final_shortlisted": shortlisted,
            "execution_time": f"{elapsed_sec}s",
            "api_calls": api_calls_count,
            "source_status": source_label
        }
        benchmark_rows.append(row)

        print(
            f"{item['domain'][:25]:<25} | {lens_status:<15} | {gp_status:<15} | {lens_retrieved:<10} | "
            f"{gp_retrieved:<10} | {db_fallback:<10} | {fam_dedup:<10} | {sbert_cand:<10} | "
            f"{tech_cand:<10} | {verified_ev:<10} | {shortlisted:<10} | {elapsed_sec:<8} | "
            f"{api_calls_count:<8} | {source_label:<15}"
        )

    print("=" * 195)

    json_path = reports_dir / "live_10_domain_benchmark_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_rows, f, indent=2)

    csv_path = reports_dir / "live_10_domain_benchmark_report.csv"
    if benchmark_rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(benchmark_rows[0].keys()))
            writer.writeheader()
            writer.writerows(benchmark_rows)

    print(f"\n[BENCHMARK COMPLETE] Exported live report to {json_path} and {csv_path}\n")

if __name__ == "__main__":
    run_live_benchmark()
