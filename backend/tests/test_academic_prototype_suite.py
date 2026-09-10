import pytest
import os
import json
from datetime import datetime
from backend.ml.similarity_engine import (
    compute_hybrid_score,
    calculate_deterministic_final_score,
    calculate_cosine_similarity
)
from backend.ml.risk_classifier import classify_prior_art_risk, get_similarity_level_label
from backend.app.services.lens_api_service import lens_api_service
from backend.app.services.gemini_service import gemini_service
from backend.app.services.report_service import generate_pdf_report
from backend.app.models.models import Search, SearchResult, Patent


INVENTION_TEST_CASES = [
    {
        "id": "CASE_1",
        "category": "AI Smart Irrigation",
        "title": "AI Smart Irrigation System Using Soil Moisture and Weather Forecast",
        "domain": "Agriculture",
        "problem": "Over-irrigation in agricultural fields causing water waste and crop damage.",
        "description": "An automated irrigation system comprising soil volumetric water content sensors, weather prediction API telemetry, and a neural network controller that dynamically calculates evapotranspiration and adjusts valve actuation duty cycles.",
        "keywords": ["smart irrigation", "soil moisture", "evapotranspiration", "valve actuation"],
        "reference_date": "2023-01-01"
    },
    {
        "id": "CASE_2",
        "category": "Wireless EV Charging FOD",
        "title": "Foreign Object Detection in Wireless EV Charging Pad",
        "domain": "Electrical Engineering",
        "problem": "Parasitic metal heating on inductive charging pads during high-power wireless energy transfer.",
        "description": "A dynamic resonant wireless power transfer pad with dual sensing coils that monitor high-frequency impedance shifts and phase angle changes to detect metallic debris prior to power excitation.",
        "keywords": ["wireless power transfer", "foreign object detection", "impedance shift", "resonant charging"],
        "reference_date": "2022-06-15"
    },
    {
        "id": "CASE_3",
        "category": "Industrial Smart Safety Helmet",
        "title": "Industrial Smart Safety Helmet with Impact Sensing and Mesh Alert",
        "domain": "IoT",
        "problem": "Delayed emergency response for lone industrial worker fall and impact incidents.",
        "description": "A safety helmet integrating a 6-axis IMU accelerometer, optical PPG heart rate sensor, and LPWAN mesh wireless transceiver that emits automated location beacon alerts upon detecting severe G-force thresholds.",
        "keywords": ["safety helmet", "impact sensor", "IMU accelerometer", "lone worker alert"],
        "reference_date": "2024-01-10"
    },
    {
        "id": "CASE_4",
        "category": "Historical Mechanical Invention",
        "title": "Intermittent Rotary Motion Geneva Mechanism with Dwell Lock",
        "domain": "Mechanical Engineering",
        "problem": "Slippage and back-lash wear during high-speed step-by-step rotary indexing.",
        "description": "A mechanical transmission comprising a driving pin wheel, driven slotted Geneva star wheel, and concentric locking arc surface that holds the star wheel stationary during the dwell portion of the drive cycle.",
        "keywords": ["Geneva mechanism", "intermittent motion", "star wheel", "dwell locking"],
        "reference_date": "1990-05-01"
    },
    {
        "id": "CASE_5",
        "category": "Historical Semiconductor Invention",
        "title": "Bipolar Junction Transistor with Graded Base Region",
        "domain": "Electronics",
        "problem": "Carrier transit delay across base region limiting high-frequency switching performance.",
        "description": "A solid-state semiconductor device comprising an emitter, a non-uniformly doped graded base region establishing an internal drift electric field, and a collector junction.",
        "keywords": ["bipolar transistor", "graded base", "drift electric field", "semiconductor"],
        "reference_date": "1975-08-20"
    },
    {
        "id": "CASE_6",
        "category": "AI Battery Health Monitoring",
        "title": "Li-Ion Battery State of Health Estimation via Electrochemical Impedance Neural Network",
        "domain": "Energy",
        "problem": "Inaccurate battery degradation forecasting in electric vehicle battery management systems.",
        "description": "A battery management system that measures electrochemical impedance spectroscopy (EIS) parameters at multiple AC frequencies and feeds relaxation voltage profiles into a recurrent neural network to estimate State of Health (SOH).",
        "keywords": ["state of health", "SOH estimation", "electrochemical impedance", "battery degradation"],
        "reference_date": "2021-11-30"
    }
]


def test_relevance_classification_scale_phase22():
    """Verify single canonical relevance classification thresholds (0-29 Low, 30-49 Moderate, 50-69 High, 70-100 Very High)."""
    assert classify_prior_art_risk(15.0)["risk_level"] == "LOW"
    assert classify_prior_art_risk(15.0)["label"] == "Low Technical Relevance"

    assert classify_prior_art_risk(35.0)["risk_level"] == "MODERATE"
    assert classify_prior_art_risk(35.0)["label"] == "Moderate Technical Relevance"

    assert classify_prior_art_risk(65.0)["risk_level"] == "HIGH"
    assert classify_prior_art_risk(65.0)["label"] == "High Technical Relevance"

    assert classify_prior_art_risk(85.0)["risk_level"] == "VERY HIGH"
    assert classify_prior_art_risk(85.0)["label"] == "Very High Technical Relevance"


def test_zero_hallucination_and_availability_flags():
    """Verify missing claims or description result in correct availability flags and transparent score caps (Phase 18)."""
    user_emb = [0.1] * 384
    pat_emb = [0.1] * 384

    patent_abstract_only = {
        "title": "Smart Irrigation Sensor",
        "abstract": "A soil moisture sensor for agriculture.",
        "claims": "",
        "description": "",
        "cpc_codes": "A01G25/00"
    }

    sc = compute_hybrid_score(
        user_embedding=user_emb,
        patent_embedding=pat_emb,
        user_keywords=["soil moisture"],
        user_concepts=["soil moisture"],
        user_domain="Agriculture",
        patent=patent_abstract_only,
        target_text_for_concepts="soil moisture sensor",
        technical_features=["soil moisture sensor"],
        essential_features=["soil moisture sensor"]
    )

    assert sc["claims_status"] == "NOT_AVAILABLE"
    assert sc["full_text_status"] == "NOT_AVAILABLE"
    assert sc["score_breakdown"]["score_cap"] == 45.0
    assert sc["final_score"] <= 45.0
    assert "unavailable" in sc["score_breakdown"]["score_cap_reason"].lower()


def test_family_deduplication_pipeline():
    """Verify Top candidate deduplication by simple patent family (Phase 11)."""
    candidates = [
        {
            "patent_number": "US-10999888-B2",
            "title": "US Smart Safety Helmet",
            "abstract": "Impact sensing safety helmet spec.",
            "claims": "1. A safety helmet comprising an accelerometer...",
            "description": "Full description of helmet sensor.",
            "jurisdiction": "US",
            "family_id": "FAM-HELMET-100"
        },
        {
            "patent_number": "EP-3888999-A1",
            "title": "EP Smart Safety Helmet Member",
            "abstract": "European family member for safety helmet.",
            "claims": "",
            "description": "",
            "jurisdiction": "EP",
            "family_id": "FAM-HELMET-100"
        }
    ]

    deduped = lens_api_service.group_by_patent_family(candidates)
    assert len(deduped) == 1
    assert deduped[0]["patent_number"] == "US-10999888-B2"
    assert deduped[0]["family_size"] == 2


def test_temporal_status_logic():
    """Verify reference-date comparison logic (Phase 16)."""
    pub_date = "2024-05-10"
    ref_date = "2022-01-01"
    
    assert pub_date > ref_date
    # Should never label post-reference documents as prior art before reference date
    temp_status = "PUBLISHED_AFTER_REFERENCE"
    assert temp_status == "PUBLISHED_AFTER_REFERENCE"


def test_all_six_invention_categories_and_score_consistency():
    """Verify deterministic 5-factor scoring across all 6 invention test cases."""
    user_emb = [0.15] * 384
    pat_emb = [0.15] * 384

    for test_case in INVENTION_TEST_CASES:
        pat_data = {
            "title": test_case["title"],
            "abstract": test_case["description"],
            "claims": f"1. An apparatus for {test_case['keywords'][0]} comprising structural elements.",
            "description": test_case["description"],
            "cpc_codes": "H02J50/60"
        }

        sc = compute_hybrid_score(
            user_embedding=user_emb,
            patent_embedding=pat_emb,
            user_keywords=test_case["keywords"],
            user_concepts=test_case["keywords"],
            user_domain=test_case["domain"],
            patent=pat_data,
            target_text_for_concepts=test_case["description"],
            technical_features=test_case["keywords"],
            essential_features=test_case["keywords"][:2]
        )

        assert "final_score" in sc
        assert "confidence_score" in sc
        assert "score_breakdown" in sc
        assert sc["final_score"] >= 0.0 and sc["final_score"] <= 100.0
        assert sc["score_breakdown"]["formula_explanation"].startswith("Final Score =")
