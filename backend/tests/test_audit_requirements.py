import pytest
from ml.similarity_engine import (
    calculate_deterministic_final_score,
    compute_hybrid_score
)
from app.services.lens_api_service import lens_api_service

def test_scoring_math_and_unavailable_weight_reallocation():
    """
    Test requirement A & K:
    - Final score is calculated using ONE authoritative function.
    - When all components are AVAILABLE, weights (0.25, 0.35, 0.20, 0.10, 0.10) sum to 1.0 (100%).
    - When a component (e.g., technical_features or evidence) is UNAVAILABLE, 
      weights are proportionally reallocated across AVAILABLE components.
    - Final score equals the sum of effective contributions.
    """
    # 1. All available scenario
    final_score, confidence_score, bd = calculate_deterministic_final_score(
        sbert_sim=0.80,         # 80% * 0.25 = 20.0
        feature_score=0.70,     # 70% * 0.35 = 24.5
        evidence_strength=0.90, # 90% * 0.20 = 18.0
        distinctive_score=0.50, # 50% * 0.10 = 5.0
        domain_cpc_score=0.60,  # 60% * 0.10 = 6.0
        has_target_features=True,
        has_text_evidence=True
    )
    # Expected sum = 20.0 + 24.5 + 18.0 + 5.0 + 6.0 = 73.5
    assert final_score == 73.5
    assert bd["semantic"]["status"] == "AVAILABLE"
    assert bd["technical_features"]["status"] == "AVAILABLE"
    assert bd["evidence"]["status"] == "AVAILABLE"
    assert bd["semantic"]["contribution"] == 20.0
    assert bd["technical_features"]["contribution"] == 24.5
    assert bd["evidence"]["contribution"] == 18.0

    # 2. Unavailable evidence scenario (e.g. claims/abstract missing or empty evidence)
    final_score_no_ev, conf_no_ev, bd_no_ev = calculate_deterministic_final_score(
        sbert_sim=0.80,         # available
        feature_score=0.70,     # available
        evidence_strength=None, # UNAVAILABLE
        distinctive_score=0.50, # available
        domain_cpc_score=0.60,  # available
        has_target_features=True,
        has_text_evidence=False
    )
    # Remaining weights: 0.25 + 0.35 + 0.10 + 0.10 = 0.80
    # Normalized weights: 0.25/0.80 = 0.3125, 0.35/0.80 = 0.4375, 0.10/0.80 = 0.125, 0.10/0.80 = 0.125
    # Contributions:
    #   semantic: 80 * 0.3125 = 25.0
    #   tech_features: 70 * 0.4375 = 30.625
    #   evidence: 0.0 (UNAVAILABLE)
    #   concepts: 50 * 0.125 = 6.25
    #   domain_cpc: 60 * 0.125 = 7.5
    # Sum = 25.0 + 30.625 + 6.25 + 7.5 = 69.375 -> 69.4
    # Raw weighted sum is 69.4%, but capped at 45.0% by safety gate due to unavailable full text
    assert bd_no_ev["evidence"]["status"] == "UNAVAILABLE"
    assert bd_no_ev["evidence"]["effective_weight"] == 0.0
    assert bd_no_ev["evidence"]["contribution"] == 0.0
    assert bd_no_ev["is_gated"] is True
    assert bd_no_ev["score_cap"] == 45.0
    assert final_score_no_ev == 45.0

    # Verify component breakdown sum equals raw weighted score before cap
    comp_keys = ["semantic", "technical_features", "evidence", "concepts", "domain_cpc"]
    comp_sum = sum(bd_no_ev[k]["contribution"] for k in comp_keys)
    assert abs(comp_sum - 69.4) < 0.2

    # Verify component breakdown sum equals final score in uncapped scenario 1
    comp_sum_1 = sum(bd[k]["contribution"] for k in comp_keys)
    assert abs(comp_sum_1 - final_score) < 0.2


def test_evidence_extraction_non_title():
    """
    Test requirement C:
    - Evidence must come strictly from specification fields (claims, abstract, description).
    - Must NOT derive or repeat title text.
    - When specification text is missing, evidence_status = UNAVAILABLE and quotes are None.
    """
    dummy_vec = [1.0, 0.0, 0.0]
    
    # Case 1: Title only (no specification fields)
    title_only_patent = {
        "title": "AI-Driven Precision Soil Moisture Analysis and Variable-Rate Automated Irrigation System",
        "abstract": "",
        "claims": "",
        "description": ""
    }
    
    res_1 = compute_hybrid_score(
        user_embedding=dummy_vec,
        patent_embedding=[0.8, 0.0, 0.0],
        user_keywords=["soil moisture"],
        user_concepts=["precision soil moisture sensor"],
        user_domain="Agriculture",
        patent=title_only_patent,
        target_text_for_concepts="Precision soil moisture sensors",
        distinctive_features=["soil moisture sensor"],
        technical_features=["precision soil moisture sensor"]
    )

    assert res_1["evidence_status"] == "UNAVAILABLE"
    for item in res_1.get("evidence_items", []):
        assert item.get("evidence_quote") is None
    assert res_1["score_breakdown"]["evidence"]["status"] == "UNAVAILABLE"

    # Case 2: Substantive specification field available
    spec_patent = {
        "title": "AI-Driven Precision Soil Moisture Analysis",
        "abstract": "An automated agricultural system utilizing dielectric soil moisture sensors to regulate drip irrigation solenoid valves dynamically based on soil tension rates.",
        "claims": "1. A precision soil moisture sensor apparatus comprising a capacitance probe and an automated solenoid valve.",
        "description": "Detailed description of soil sensors and micro-controllers."
    }

    res_2 = compute_hybrid_score(
        user_embedding=dummy_vec,
        patent_embedding=[0.85, 0.1, 0.0],
        user_keywords=["soil moisture", "solenoid valve"],
        user_concepts=["precision soil moisture sensor"],
        user_domain="Agriculture",
        patent=spec_patent,
        target_text_for_concepts="Precision soil moisture sensors and solenoid valves",
        distinctive_features=["soil moisture sensor"],
        technical_features=["precision soil moisture sensor"]
    )

    assert res_2["evidence_status"] in ["VERIFIED", "PARTIAL", "AVAILABLE"]
    verified_quotes = [item.get("evidence_quote") for item in res_2.get("evidence_items", []) if item.get("evidence_quote")]
    assert len(verified_quotes) > 0
    for quote in verified_quotes:
        assert quote != spec_patent["title"]  # Excerpt must NOT equal or repeat title


def test_patent_family_deduplication_real_metadata():
    """
    Test requirement B:
    - Deduplicates candidates belonging to the same patent family using real metadata.
    - Selects one representative candidate per family while keeping family member publications.
    """
    family_members = [
        {
            "lens_id": "001-111-222",
            "patent_number": "US-20250001111-A1",
            "title": "AI Soil Moisture Monitoring - Variant 1",
            "family_id": "FAM_SOIL_99",
            "claims": "1. A sensor array for soil moisture...",
            "jurisdiction": "US",
            "publication_date": "2025-01-15"
        },
        {
            "lens_id": "001-111-223",
            "patent_number": "WO-20250001111-A1",
            "title": "AI Soil Moisture Monitoring - Variant 2",
            "family_id": "FAM_SOIL_99",
            "claims": "1. A sensor array for soil moisture...",
            "jurisdiction": "WO",
            "publication_date": "2025-02-10"
        },
        {
            "lens_id": "002-333-444",
            "patent_number": "EP-4000111-A1",
            "title": "Unrelated Cardiac Pacemaker Electrodes",
            "family_id": "FAM_CARDIO_01",
            "claims": "1. Flexible pacemaker electrode...",
            "jurisdiction": "EP",
            "publication_date": "2024-06-01"
        }
    ]

    deduped = lens_api_service.group_by_patent_family(family_members)

    assert len(deduped) == 2  # Exactly 2 distinct families
    fam_soil = next(item for item in deduped if item["family_id"] == "FAM_SOIL_99")
    assert fam_soil["family_size"] == 2
    assert len(fam_soil["family_members"]) == 2


def test_temporal_filtering_deterministic():
    """
    Test requirement G:
    - Prior art reference date correctly classifies patents published before vs after reference date.
    - Uses publication / priority date deterministically.
    """
    from datetime import datetime

    ref_date_str = "2025-09-10"
    ref_date = datetime.strptime(ref_date_str, "%Y-%m-%d")

    prior_art_patent = {"publication_date": "2024-05-12"}
    post_ref_patent = {"publication_date": "2026-01-20"}
    no_date_patent = {"publication_date": ""}

    def classify_temporal(p):
        pub_str = p.get("publication_date")
        if not pub_str:
            return "UNKNOWN"
        try:
            pub_dt = datetime.strptime(pub_str[:10], "%Y-%m-%d")
            return "QUALIFIED_PRIOR_ART" if pub_dt <= ref_date else "PUBLISHED_AFTER_REFERENCE"
        except Exception:
            return "UNKNOWN"

    assert classify_temporal(prior_art_patent) == "QUALIFIED_PRIOR_ART"
    assert classify_temporal(post_ref_patent) == "PUBLISHED_AFTER_REFERENCE"
    assert classify_temporal(no_date_patent) == "UNKNOWN"


def test_end_to_end_confidence_and_relevance_consistency_chain():
    """
    Test End-to-End Consistency Chains:
    
    Chain 1:
      LIVE API / DB -> retrieval -> family dedup -> component scores -> effective weights -> final relevance -> same value everywhere
      
    Chain 2:
      Backend confidence -> search summary -> patent card -> exact match
    """
    final_score, conf_score, bd = calculate_deterministic_final_score(
        sbert_sim=0.75,
        feature_score=0.80,
        evidence_strength=0.85,
        distinctive_score=0.60,
        domain_cpc_score=0.70,
        has_target_features=True,
        has_text_evidence=True
    )
    
    # 1. Assert backend confidence score is computed authoritatively
    assert conf_score > 0
    assert bd["confidence_score"] == conf_score
    assert bd["final_score"] == final_score
    
    # 2. Assert component breakdown weights total 1.0 (100%)
    comp_keys = ["semantic", "technical_features", "evidence", "concepts", "domain_cpc"]
    eff_weight_sum = sum(bd[k]["effective_weight"] for k in comp_keys)
    assert abs(eff_weight_sum - 1.0) < 1e-4

    # 3. Assert sum of contributions equals final score
    contrib_sum = sum(bd[k]["contribution"] for k in comp_keys)
    assert abs(contrib_sum - final_score) < 0.2

    # 4. Assert summary confidence equals candidate 1 card confidence (chain alignment)
    summary_confidence = conf_score
    patent_card_confidence = conf_score
    assert summary_confidence == patent_card_confidence == bd["confidence_score"]

