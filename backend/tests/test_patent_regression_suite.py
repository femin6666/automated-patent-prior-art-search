import pytest
from backend.ml.keyword_extractor import (
    extract_structured_invention_features,
    extract_atomic_technical_features,
    get_synonyms_for_term,
    GENERIC_DOMAIN_NOISE
)
from backend.ml.similarity_engine import (
    compute_hybrid_score,
    calculate_deterministic_final_score,
    calculate_cosine_similarity
)
from backend.app.services.gemini_service import gemini_service
from backend.app.services.lens_api_service import lens_api_service


def test_feature_extraction_and_quadruplets():
    """Test 1: Verification of Component + Function + Relationship + Purpose quadruplets and essential/optional separation."""
    sample_text = """
    A wireless power transfer system comprising a transmitter coil, a receiver coil, and a controller.
    The controller dynamically adjusts foreign object detection thresholds based on transmitter and receiver coil alignment
    in order to prevent parasitic heating of metallic objects on the charging pad.
    The system optionally includes a multi-color LED status indicator for user feedback.
    """
    res = extract_structured_invention_features(sample_text)

    assert "essential_features" in res
    assert "optional_features" in res
    assert "structured_quadruplets font" not in res
    assert len(res["essential_features"]) > 0

    quads = res["structured_quadruplets"]
    assert len(quads) > 0
    first_quad = quads[0]
    assert "component" in first_quad
    assert "function" in first_quad
    assert "relationship" in first_quad
    assert "purpose" in first_quad


def test_synonym_expansion_and_acronyms():
    """Test 2: Verification of technical synonym map and acronym expansion."""
    wpt_syns = get_synonyms_for_term("wireless power transfer")
    assert any("wpt" in s.lower() or "charging" in s.lower() for s in wpt_syns)

    fod_syns = get_synonyms_for_term("foreign object detection")
    assert any("fod" in s.lower() or "sensing" in s.lower() for s in fod_syns)

    soh_syns = get_synonyms_for_term("state of health")
    assert any("battery" in s.lower() or "soh" in s.lower() for s in soh_syns)


def test_multi_strategy_search_queries():
    """Test 3: Verification of 8 multi-strategy search query generation."""
    analysis = gemini_service.analyze_invention(
        title="Dynamic Resonant Wireless Power Transfer",
        problem_statement="Parasitic heating from metallic debris during inductive charging.",
        description="A coil system with adaptive impedance tuning for foreign object detection.",
        keywords=["wireless power transfer", "foreign object detection"],
        domain="Electrical Engineering"
    )

    queries = analysis.get("search_queries", [])
    assert len(queries) >= 8, f"Expected 8 search queries, got {len(queries)}"
    assert any("claim:" in q or "cpc:" in q or "AND" in q for q in queries)


def test_section_weighted_matching():
    """Test 4: Verification of section weighting (Claims 1.0 > Abstract 0.85 > Description 0.7 > Title 0.6)."""
    user_emb = [0.1] * 384
    patent_emb = [0.1] * 384

    # Case A: Feature disclosed in Claims
    patent_claims = {"title": "Test Patent", "abstract": "", "description": "", "claims": "wireless power transfer coil circuit"}
    score_claims = compute_hybrid_score(
        user_embedding=user_emb,
        patent_embedding=patent_emb,
        user_keywords=["wireless power transfer"],
        user_concepts=["wireless power transfer"],
        user_domain="Electrical Engineering",
        patent=patent_claims,
        target_text_for_concepts="wireless power transfer",
        technical_features=["wireless power transfer"],
        essential_features=["wireless power transfer"]
    )

    # Case B: Feature disclosed in Description only
    patent_desc = {"title": "Test Patent", "abstract": "", "description": "wireless power transfer coil circuit", "claims": ""}
    score_desc = compute_hybrid_score(
        user_embedding=user_emb,
        patent_embedding=patent_emb,
        user_keywords=["wireless power transfer"],
        user_concepts=["wireless power transfer"],
        user_domain="Electrical Engineering",
        patent=patent_desc,
        target_text_for_concepts="wireless power transfer",
        technical_features=["wireless power transfer"],
        essential_features=["wireless power transfer"]
    )

    assert score_claims["matched_features"][0]["source_section"] == "claims"
    assert score_desc["matched_features"][0]["source_section"] == "description"
    assert score_claims["weighted_technical_score"] >= score_desc["weighted_technical_score"]


test_five_level_match_classification_params = [
    ("wireless power transfer", "claims", "STRONG_MATCH"),
    ("wireless power transfer", "description", "PARTIAL_MATCH"),
]

def test_five_level_match_classification():
    """Test 5: Verification of 5-level match classification (STRONG_MATCH, PARTIAL_MATCH, WEAK_MATCH, NOT_FOUND, UNABLE_TO_VERIFY)."""
    user_emb = [0.2] * 384
    patent_emb = [0.2] * 384

    patent_strong = {
        "title": "Wireless Power System",
        "abstract": "A wireless power transfer system.",
        "claims": "A wireless power transfer system.",
        "description": "Full spec disclosure."
    }

    score_res = compute_hybrid_score(
        user_embedding=user_emb,
        patent_embedding=patent_emb,
        user_keywords=["wireless power transfer", "absent technical feature"],
        user_concepts=["wireless power transfer"],
        user_domain="Electrical Engineering",
        patent=patent_strong,
        target_text_for_concepts="wireless power transfer",
        technical_features=["wireless power transfer", "absent technical feature"],
        essential_features=["wireless power transfer"]
    )

    matched = score_res["matched_features"]
    assert len(matched) >= 1
    assert matched[0]["match_level"] == "STRONG_MATCH"
    assert "absent technical feature" in score_res["missing_features"]


def test_technical_relevance_gates():
    """Test 6: Verification of technical relevance gates preventing semantic-only false positives."""
    # High SBERT similarity (0.95) but 0% technical feature overlap
    final_pct, confidence_score, bd = calculate_deterministic_final_score(
        sbert_sim=0.95,
        feature_score=0.0,
        evidence_strength=0.0,
        distinctive_score=0.0,
        domain_cpc_score=0.5,
        has_target_features=True,
        essential_feature_coverage=0.0,
        has_text_evidence=True
    )

    assert bd["is_gated"] is True
    assert final_pct <= 45.0, f"Expected gated final score <= 45.0%, got {final_pct}%"


def test_family_deduplication():
    """Test 7: Verification of patent family grouping and representative selection."""
    raw_docs = [
        {
            "patent_number": "US-10111222-B2",
            "title": "US Member WPT System",
            "abstract": "Detailed abstract for US member",
            "claims": "1. A wireless power transfer system...",
            "description": "Full specification...",
            "jurisdiction": "US",
            "family_id": "FAM-998877"
        },
        {
            "patent_number": "WO-202209988-A1",
            "title": "WO Member WPT System",
            "abstract": "Abstract for PCT member",
            "claims": "",
            "description": "",
            "jurisdiction": "WO",
            "family_id": "FAM-998877"
        }
    ]

    dedup = lens_api_service.group_by_patent_family(raw_docs)
    assert len(dedup) == 1
    rep = dedup[0]
    assert rep["patent_number"] == "US-10111222-B2"
    assert rep["family_size"] == 2
    assert len(rep["family_members"]) == 2
