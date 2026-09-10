import pytest
from typing import Dict, Any
from backend.ml.similarity_engine import compute_hybrid_score, calculate_deterministic_final_score
from backend.ml.risk_classifier import classify_prior_art_risk
from backend.app.services.lens_api_service import lens_api_service

def test_wireless_ev_fod_ranking():
    """
    SPECIAL TEST B: Wireless EV Charging Foreign Object Detection
    Verifies that a patent disclosing wireless FOD ranks significantly higher than a generic
    EV charging scheduler patent or a mechanical gear patent. Zero hardcoded patent numbers.
    """
    user_domain = "Electrical Engineering"
    target_text = (
        "Adaptive Foreign Object Detection System for Wireless EV Charging. "
        "The controller dynamically adjusts foreign-object detection threshold based on transmitter/receiver coil alignment, "
        "monitoring impedance parameters and resonant frequency shifts."
    )
    distinctive_features = [
        "foreign object detection",
        "impedance-based abnormal condition detection",
        "resonant-frequency monitoring",
        "adaptive FOD threshold based on coil alignment"
    ]
    technical_features = [
        "wireless power transfer coil",
        "foreign object detection circuit",
        "impedance monitoring module",
        "adaptive detection threshold controller"
    ]

    # Patent 1: Relevant Wireless EV FOD Patent
    fod_patent = {
        "title": "Wireless Power Transfer Apparatus with Foreign Object Detection",
        "abstract": "A wireless charging system comprising transmitter and receiver coils, where an auxiliary detection bridge senses foreign object detection via coil impedance shifts.",
        "claims": "Claims a wireless power transfer transmitter coil, impedance-based foreign object detection circuit, and adaptive threshold adjustment.",
        "description": "Describing resonant charging coils, impedance monitoring, and foreign object detection routines.",
        "domain": "Electrical Engineering",
        "cpc_codes": "H02J50/60, H02J50/12"
    }

    # Patent 2: Generic EV Charging Scheduling Patent
    generic_ev_patent = {
        "title": "Method and System for Electric Vehicle Charging Schedule Management",
        "abstract": "A server manages electric vehicle charging queues and grid power load distribution based on peak electricity rates.",
        "claims": "Claims a charging station controller managing EV plug connection schedules.",
        "description": "Discloses grid power management and battery state of charge scheduling.",
        "domain": "Electrical Engineering",
        "cpc_codes": "B60L53/60"
    }

    # Patent 3: Unrelated Mechanical Motion Patent
    mechanical_patent = {
        "title": "Intermittent Motion Rotary Indexing Gear Mechanism",
        "abstract": "A mechanical gear assembly with dwell pinions and indexing cams for step-by-step rotary transmission.",
        "claims": "Claims a driving gear, driven gear, and Geneva wheel mechanism.",
        "description": "Describing mechanical torque transmission, shafts, bearings, and indexing cams.",
        "domain": "Mechanical Engineering",
        "cpc_codes": "F16H27/02"
    }

    dummy_vec = [1.0, 0.0, 0.0]

    score_fod = compute_hybrid_score(
        user_embedding=dummy_vec,
        patent_embedding=[0.85, 0.1, 0.0],
        user_keywords=["foreign object detection", "wireless power transfer"],
        user_concepts=technical_features,
        user_domain=user_domain,
        patent=fod_patent,
        target_text_for_concepts=target_text,
        distinctive_features=distinctive_features,
        technical_features=technical_features
    )

    score_generic = compute_hybrid_score(
        user_embedding=dummy_vec,
        patent_embedding=[0.70, 0.1, 0.0],
        user_keywords=["charging"],
        user_concepts=technical_features,
        user_domain=user_domain,
        patent=generic_ev_patent,
        target_text_for_concepts=target_text,
        distinctive_features=distinctive_features,
        technical_features=technical_features
    )

    score_mech = compute_hybrid_score(
        user_embedding=dummy_vec,
        patent_embedding=[0.20, 0.0, 0.0],
        user_keywords=[],
        user_concepts=technical_features,
        user_domain=user_domain,
        patent=mechanical_patent,
        target_text_for_concepts=target_text,
        distinctive_features=distinctive_features,
        technical_features=technical_features
    )

    assert score_fod["final_score"] > score_generic["final_score"]
    assert score_generic["final_score"] > score_mech["final_score"]
    assert score_fod["final_score"] >= 65.0
    assert score_mech["final_score"] <= 45.0  # Technical Relevance Gate active for mechanical patent


def test_mechanical_false_positive_prevention():
    """
    SPECIAL TEST C: Mechanical Intermittent Motion False Positive Rejection
    Verifies that generic words ('system', 'control', 'mechanism', 'device') do not produce
    a strong match between an AI Smart Irrigation invention and a mechanical gear patent.
    """
    user_domain = "Agriculture"
    target_text = "AI-based smart irrigation control system using soil moisture sensors and predictive neural networks."
    tech_features = [
        "soil moisture sensor network",
        "predictive neural network irrigation controller",
        "automated solenoid valve control",
        "weather telemetry integration"
    ]
    distinctive_features = [
        "soil-moisture-based irrigation control",
        "machine-learning-based irrigation prediction"
    ]

    mechanical_patent = {
        "title": "Intermittent Motion Rotary Gear Mechanism and Control Device",
        "abstract": "A mechanical system and control mechanism for intermittent indexing motion.",
        "claims": "Claims a mechanical drive unit, control gear, and indexing system.",
        "description": "System for controlling mechanical movement using gears.",
        "domain": "Mechanical Engineering",
        "cpc_codes": "F16H27/00"
    }

    dummy_vec = [1.0, 0.0, 0.0]
    res = compute_hybrid_score(
        user_embedding=dummy_vec,
        patent_embedding=[0.75, 0.0, 0.0],  # High vector sim to test gate
        user_keywords=["system", "control"],
        user_concepts=tech_features,
        user_domain=user_domain,
        patent=mechanical_patent,
        target_text_for_concepts=target_text,
        distinctive_features=distinctive_features,
        technical_features=tech_features
    )

    # Technical Relevance Gate must cap score because 0 technical features matched
    assert res["score_breakdown"]["is_gated"] is True
    assert res["final_score"] <= 45.0
    assert len(res["strong_matches"]) == 0


def test_patent_family_deduplication():
    """
    Verifies that multiple publications of the same patent family (WO, US app, EP)
    are deduplicated into distinct representative families. Zero hardcoded patent IDs.
    """
    raw_candidates = [
        {
            "patent_number": "WO-2024077400",
            "title": "Wireless Charging Foreign Object Detection",
            "abstract": "System for foreign object detection.",
            "claims": "Claims independent coil detection.",
            "description": "Full technical description.",
            "publication_date": "2024-01-15",
            "family_id": "FAM_1001",
            "jurisdiction": "WO"
        },
        {
            "patent_number": "US-20240012345",
            "title": "Wireless Charging Foreign Object Detection",
            "abstract": "US application for foreign object detection.",
            "claims": "",
            "description": "Short description.",
            "publication_date": "2024-03-20",
            "family_id": "FAM_1001",
            "jurisdiction": "US"
        },
        {
            "patent_number": "EP-3987654",
            "title": "European Publication for FOD System",
            "abstract": "European patent publication.",
            "claims": "",
            "description": "EP specification.",
            "publication_date": "2024-05-10",
            "family_id": "FAM_1001",
            "jurisdiction": "EP"
        },
        {
            "patent_number": "US-11223344",
            "title": "Unrelated Semiconductor Bipolar Transistor",
            "abstract": "Three terminal semiconductor transistor.",
            "claims": "Claims emitter collector base current control.",
            "description": "Semiconductor fabrication.",
            "publication_date": "2023-11-05",
            "family_id": "FAM_1002",
            "jurisdiction": "US"
        }
    ]

    families = lens_api_service.group_by_patent_family(raw_candidates)

    assert len(families) == 2  # Exactly 2 distinct families
    fam_1001_rep = next(f for f in families if f["family_id"] == "FAM_1001")
    assert fam_1001_rep["family_size"] == 3
    assert len(fam_1001_rep["family_members"]) == 3
    assert fam_1001_rep["patent_number"] == "WO-2024077400"  # Representative with claims


def test_deterministic_scoring_formula_consistency():
    """
    Verifies that the backend deterministic formula produces 100% consistent results
    across score breakdowns and risk level classifications.
    """
    final_score, confidence_score, bd = calculate_deterministic_final_score(
        sbert_sim=0.80,
        feature_score=0.75,
        evidence_strength=0.90,
        distinctive_score=0.80,
        domain_cpc_score=1.0,
        has_target_features=True
    )

    # 25% * 80 + 35% * 75 + 20% * 90 + 10% * 80 + 10% * 100 = 20 + 26.25 + 18 + 8 + 10 = 82.25% (82.3%)
    assert final_score == 82.3
    assert bd["final_score"] == 82.3
    assert bd["is_gated"] is False

    risk_info = classify_prior_art_risk(final_score)
    assert risk_info["risk_level"] == "VERY HIGH"


def test_semiconductor_three_terminal_relevance():
    """
    TEST 3: Three-Terminal Semiconductor Signal Amplifying Device
    Verifies that a historical semiconductor transistor patent ranks significantly higher
    than a generic IoT device patent.
    """
    user_domain = "Electronics"
    target_text = (
        "Three-Terminal Semiconductor Signal Amplifying Device. "
        "A semiconductor substrate having emitter, collector, and base control electrodes "
        "for controlling output current and high frequency signal amplification."
    )
    tech_features = [
        "three terminal semiconductor substrate",
        "emitter collector base control electrodes",
        "signal amplification current control circuit",
        "semiconductor junction amplification mechanism"
    ]
    distinctive_features = [
        "three-terminal semiconductor amplification",
        "emitter-collector base current control"
    ]

    transistor_patent = {
        "title": "Three-Terminal Semiconductor Bipolar Transistor Amplifier",
        "abstract": "A semiconductor signal amplifying device comprising base, emitter, and collector terminals.",
        "claims": "Claims a three-terminal semiconductor substrate, emitter electrode, collector electrode, and base signal control.",
        "description": "Describing semiconductor amplification and current modulation across p-n junctions.",
        "domain": "Electronics",
        "cpc_codes": "H01L29/70"
    }

    generic_iot = {
        "title": "Smart Home IoT Gateway with Wireless Communication Module",
        "abstract": "An IoT gateway connecting smart sensors to cloud servers via WiFi.",
        "claims": "Claims a microprocessor, WiFi antenna, and housing.",
        "description": "Discloses wireless data packet routing.",
        "domain": "Electronics",
        "cpc_codes": "H04L12/28"
    }

    dummy_vec = [1.0, 0.0, 0.0]
    score_semi = compute_hybrid_score(
        user_embedding=dummy_vec,
        patent_embedding=[0.85, 0.1, 0.0],
        user_keywords=["semiconductor", "transistor"],
        user_concepts=tech_features,
        user_domain=user_domain,
        patent=transistor_patent,
        target_text_for_concepts=target_text,
        distinctive_features=distinctive_features,
        technical_features=tech_features
    )

    score_iot = compute_hybrid_score(
        user_embedding=dummy_vec,
        patent_embedding=[0.60, 0.0, 0.0],
        user_keywords=["device"],
        user_concepts=tech_features,
        user_domain=user_domain,
        patent=generic_iot,
        target_text_for_concepts=target_text,
        distinctive_features=distinctive_features,
        technical_features=tech_features
    )

    assert score_semi["final_score"] > score_iot["final_score"]
    assert score_semi["final_score"] >= 65.0
    assert score_iot["final_score"] <= 45.0  # Gated due to lack of semiconductor feature matches


def test_battery_predictive_health_relevance():
    """
    TEST 4: AI-Based Predictive Battery Health Monitoring and Adaptive Charging System
    Verifies that a battery health diagnostic patent outranks a generic AI web search paper.
    """
    user_domain = "Energy"
    target_text = (
        "AI-Based Predictive Battery Health Monitoring and Adaptive Charging System. "
        "A neural network monitors state-of-health (SOH), internal resistance, and temperature, "
        "dynamically adjusting charging current profiles to mitigate lithium plating."
    )
    tech_features = [
        "battery state of health neural network monitor",
        "adaptive charging current controller",
        "internal resistance and thermal parameter sensor",
        "lithium plating mitigation charging routine"
    ]
    distinctive_features = [
        "AI-based battery state-of-health prediction",
        "adaptive charging current profile optimization"
    ]

    battery_patent = {
        "title": "Method and Apparatus for Battery State of Health (SOH) Estimation and Adaptive Fast Charging",
        "abstract": "System evaluating internal resistance and temperature to predict battery state of health (SOH) and adjust adaptive charging current.",
        "claims": "Claims neural network monitoring of battery state of health SOH, internal impedance measurement, and adaptive charging current control.",
        "description": "Discloses battery management systems, SOH prediction algorithms, and charging profile adaptation.",
        "domain": "Energy",
        "cpc_codes": "H02J7/00, H01M10/44"
    }

    generic_ai_paper = {
        "title": "Deep Learning Neural Networks for Natural Language Translation",
        "abstract": "A transformer-based neural network model for multi-language text translation.",
        "claims": "",
        "description": "Discloses attention mechanisms, word embeddings, and text translation training.",
        "domain": "Artificial Intelligence",
        "cpc_codes": "G06F40/28"
    }

    dummy_vec = [1.0, 0.0, 0.0]
    score_bat = compute_hybrid_score(
        user_embedding=dummy_vec,
        patent_embedding=[0.85, 0.1, 0.0],
        user_keywords=["battery health", "adaptive charging"],
        user_concepts=tech_features,
        user_domain=user_domain,
        patent=battery_patent,
        target_text_for_concepts=target_text,
        distinctive_features=distinctive_features,
        technical_features=tech_features
    )

    score_ai = compute_hybrid_score(
        user_embedding=dummy_vec,
        patent_embedding=[0.65, 0.0, 0.0],
        user_keywords=["neural network"],
        user_concepts=tech_features,
        user_domain=user_domain,
        patent=generic_ai_paper,
        target_text_for_concepts=target_text,
        distinctive_features=distinctive_features,
        technical_features=tech_features
    )

    assert score_bat["final_score"] > score_ai["final_score"]


def test_feature_coverage_transparency():
    """
    Verifies that raw_feature_coverage and matched_feature_count are calculated deterministically
    to resolve the 80% vs 2/9 coverage display problem.
    """
    dummy_vec = [1.0, 0.0, 0.0]
    tech_features = [
        "Alpha Device Assembly", "Beta Sensor Circuit", "Gamma Valve Module",
        "Delta Control Node", "Epsilon Gear Train", "Zeta Cam Follower",
        "Eta Linkage Arm", "Theta Charging Coil", "Iota Driver Circuit"
    ]

    partial_patent = {
        "title": "Partial Feature Patent",
        "abstract": "Discloses Alpha Device Assembly and Beta Sensor Circuit only.",
        "claims": "Claims Alpha Device Assembly and Beta Sensor Circuit.",
        "description": "Description covering Alpha Device Assembly and Beta Sensor Circuit.",
        "domain": "Mechanical Engineering"
    }

    res = compute_hybrid_score(
        user_embedding=dummy_vec,
        patent_embedding=[0.80, 0.0, 0.0],
        user_keywords=[],
        user_concepts=tech_features,
        user_domain="Mechanical Engineering",
        patent=partial_patent,
        target_text_for_concepts=" ".join(tech_features),
        distinctive_features=["Alpha Device Assembly", "Beta Sensor Circuit"],
        technical_features=tech_features
    )

    assert res["matched_feature_count"] == 2
    assert res["total_feature_count"] == 9

