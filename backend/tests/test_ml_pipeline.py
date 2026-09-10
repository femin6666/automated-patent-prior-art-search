import pytest
from backend.ml.preprocessing import clean_text, validate_invention_input, prepare_combined_text
from backend.ml.keyword_extractor import extract_technical_concepts
from backend.ml.risk_classifier import classify_prior_art_risk
from backend.ml.similarity_engine import (
    calculate_cosine_similarity, calculate_domain_similarity, compute_hybrid_score
)

def test_text_preprocessing():
    raw = "  AI-based   Smart Irrigation   System \n\n with   Sensors "
    cleaned = clean_text(raw)
    assert cleaned == "AI-based Smart Irrigation System with Sensors"

def test_validate_invention_input():
    res_invalid = validate_invention_input("Short", "Tiny")
    assert not res_invalid["valid"]
    
    res_valid = validate_invention_input("Smart Irrigation", "A machine learning system that analyzes soil moisture data and controls irrigation.")
    assert res_valid["valid"]

def test_extract_technical_concepts():
    text = "Machine learning system that analyzes soil moisture and automatically controls irrigation using sensor networks."
    concepts = extract_technical_concepts(text)
    assert isinstance(concepts, list)
    assert len(concepts) > 0

def test_risk_classifier():
    res_low = classify_prior_art_risk(25.0)
    assert res_low["risk_level"] == "LOW"
    
    res_mod = classify_prior_art_risk(50.0)
    assert res_mod["risk_level"] == "MODERATE"

    res_high = classify_prior_art_risk(75.0)
    assert res_high["risk_level"] == "HIGH"

    res_vhigh = classify_prior_art_risk(90.0)
    assert res_vhigh["risk_level"] == "VERY HIGH"

def test_similarity_engine():
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    sim = calculate_cosine_similarity(vec1, vec2)
    assert sim == 1.0
    
    dom_sim = calculate_domain_similarity("Agriculture", "Agriculture")
    assert dom_sim == 1.0

def test_keyword_regex_boundary_matching():
    from backend.ml.similarity_engine import calculate_keyword_similarity
    # "cellular" should NOT match keyword "cell" via exact word boundaries
    score_no_match, _ = calculate_keyword_similarity(
        user_keywords=["cell"],
        user_concepts=[],
        target_full_text="cell",
        patent_abstract="Cellular communication tower technology",
        patent_description=""
    )
    assert score_no_match == 0.0
    
    # "cell" as a standalone word should match
    score_match, matched = calculate_keyword_similarity(
        user_keywords=["cell"],
        user_concepts=[],
        target_full_text="cell",
        patent_abstract="Primary fuel cell energy storage unit",
        patent_description=""
    )
    assert score_match > 0.0
    assert "Cell" in matched

def test_adaptive_hybrid_scoring():
    from backend.ml.similarity_engine import compute_hybrid_score
    # When no keywords are supplied (user_keywords=[]), weight automatically shifts to 70% semantic SBERT similarity
    result = compute_hybrid_score(
        user_embedding=[1.0, 0.0, 0.0],
        patent_embedding=[1.0, 0.0, 0.0],
        user_keywords=[],
        user_concepts=[],
        user_domain="Electrical Engineering",
        patent={
            "title": "Wireless Power Transfer System",
            "abstract": "A system for transmitting wireless energy.",
            "description": "Describing resonant charging coils and power transmitters.",
            "domain": "Electrical Engineering"
        },
        target_text_for_concepts="Wireless power transfer energy transmission system"
    )
    # Hybrid score should reflect deterministic formula with high semantic similarity
    assert result["final_score"] >= 50.0
    assert result["semantic_score"] == 100.0


