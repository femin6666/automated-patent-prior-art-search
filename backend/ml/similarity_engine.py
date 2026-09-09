from typing import List, Dict, Any, Tuple
import numpy as np
import re

try:
    from backend.ml.keyword_extractor import (
        get_weighted_technical_concepts,
        extract_atomic_technical_features,
        GENERIC_DOMAIN_NOISE,
        DISTINCTIVE_TECHNICAL_TERMS
    )
except ImportError:
    from .keyword_extractor import (
        get_weighted_technical_concepts,
        extract_atomic_technical_features,
        GENERIC_DOMAIN_NOISE,
        DISTINCTIVE_TECHNICAL_TERMS
    )

# Configurable default weights (Prioritizing distinctive technical feature overlap)
SEMANTIC_WEIGHT = 0.30
KEYWORD_WEIGHT = 0.50
DOMAIN_WEIGHT = 0.20

RELATED_DOMAINS_MAP = {
    "Mechanical Engineering": {"Robotics", "Manufacturing", "Electronics", "Energy"},
    "Electrical Engineering": {"Electronics", "Energy", "IoT", "Robotics", "Software", "Artificial Intelligence"},
    "Electronics": {"Electrical Engineering", "IoT", "Robotics", "Software", "Energy", "Artificial Intelligence"},
    "Energy": {"Electrical Engineering", "Electronics", "Manufacturing", "IoT", "Mechanical Engineering"},
    "Artificial Intelligence": {"Software", "Robotics", "Electronics", "IoT", "Electrical Engineering"},
    "Software": {"Artificial Intelligence", "Electronics", "IoT", "Electrical Engineering"},
    "Agriculture": {"IoT", "Biotechnology", "Robotics"},
    "Healthcare": {"Biotechnology", "Electronics", "IoT"},
    "IoT": {"Electronics", "Software", "Robotics", "Artificial Intelligence", "Electrical Engineering"},
    "Robotics": {"Electronics", "Software", "Manufacturing", "Artificial Intelligence", "Electrical Engineering", "Mechanical Engineering"},
    "Manufacturing": {"Robotics", "Electronics", "Energy", "Mechanical Engineering"},
    "Biotechnology": {"Healthcare", "Agriculture"}
}

def infer_patent_domain(title: str, abstract: str, existing_domain: str = "") -> str:
    """Dynamically infer patent technical domain if unset or generic."""
    text = f"{title} {abstract}".lower()
    
    if any(term in text for term in [
        "gear", "gears", "rotary", "intermittent motion", "indexing", "cam", "follower",
        "dwell", "linkage", "ratchet", "pawl", "shaft", "clutch", "sprocket", "pinion",
        "gearing", "step-by-step rotary", "mechanism"
    ]):
        return "Mechanical Engineering"

    if any(term in text for term in [
        "wireless power", "impedance", "charging coil", "inductive", "resonant",
        "electromagnetic", "transmitter coil", "receiver coil", "foreign object"
    ]):
        return "Electrical Engineering"
        
    if any(term in text for term in ["circuit", "semiconductor", "voltage", "current", "inverter", "signal"]):
        return "Electronics"

    if any(term in text for term in ["crop", "soil", "irrigation", "agricultural", "farming", "weed"]):
        return "Agriculture"
        
    if any(term in text for term in ["patient", "genomic", "biomedical", "medical", "clinical", "pathology"]):
        return "Healthcare"

    if any(term in text for term in ["robot", "quadrupedal", "gait", "locomotion", "kinematic", "manipulator"]):
        return "Robotics"

    return existing_domain or "Mechanical Engineering"

def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two float vectors (0.0 to 1.0)."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)
    
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    dot = np.dot(a, b)
    similarity = float(dot / (norm_a * norm_b))
    return max(0.0, min(1.0, similarity))

def calculate_keyword_similarity(
    user_keywords: List[str],
    user_concepts: List[str],
    target_full_text: str,
    patent_abstract: str,
    patent_description: str
) -> Tuple[float, List[str]]:
    """
    Calculate weighted technical concept overlap score. Distinctive technical terms
    carry high weight.
    """
    weighted_concepts = get_weighted_technical_concepts(user_keywords, user_concepts, target_full_text)
    if not weighted_concepts:
        return 0.0, []
        
    patent_text = f"{patent_abstract} {patent_description}".lower()
    
    matched_terms = []
    matched_weight_sum = 0.0
    total_weight_sum = sum(weighted_concepts.values())
    
    for term, weight in weighted_concepts.items():
        if not term:
            continue
        pattern = r'\b' + re.escape(term) + r'\b' if len(term.split()) == 1 else re.escape(term)
        if re.search(pattern, patent_text):
            matched_terms.append(term.title())
            matched_weight_sum += weight
            
    if total_weight_sum <= 0:
        return 0.0, []
        
    raw_ratio = matched_weight_sum / total_weight_sum
    keyword_score = max(0.0, min(1.0, raw_ratio))
    
    unique_matched = []
    for m in matched_terms:
        if not any(m.lower() != u.lower() and m.lower() in u.lower() for u in matched_terms):
            if m not in unique_matched:
                unique_matched.append(m)
                
    return keyword_score, unique_matched

def calculate_domain_similarity(user_domain: str, patent_domain: str) -> float:
    """Calculate domain similarity score."""
    if not user_domain or not patent_domain:
        return 0.5
        
    u_dom = user_domain.strip()
    p_dom = patent_domain.strip()
    
    if u_dom.lower() == p_dom.lower():
        return 1.0
        
    related = RELATED_DOMAINS_MAP.get(u_dom, set())
    if p_dom in related:
        return 0.7
        
    return 0.1

def calculate_deterministic_final_score(
    sbert_sim: float,
    feature_overlap_ratio: float,
    evidence_strength: float = 0.0,
    cpc_overlap: float = 0.0,
    concept_overlap: float = 0.0,
    domain_sim: float = 0.5,
    has_target_features: bool = True
) -> float:
    """
    Deterministic backend calculation for final AI Prior-Art Match score.
    Formula:
      35% SBERT Cosine Similarity
    + 35% Technical Feature Overlap (Groq/Gemini limitation match)
    + 15% Evidence Strength (Exact supporting quotes present)
    + 10% Domain & Concept Overlap
    +  5% CPC/IPC Classification Match
    
    Applies zero-overlap gate penalty (0.35x) if target has explicit features but patent discloses 0 matches.
    """
    # Enforce bounds
    sbert_sim = max(0.0, min(1.0, sbert_sim))
    feature_overlap_ratio = max(0.0, min(1.0, feature_overlap_ratio))
    evidence_strength = max(0.0, min(1.0, evidence_strength))
    cpc_overlap = max(0.0, min(1.0, cpc_overlap))
    concept_overlap = max(0.0, min(1.0, concept_overlap))
    domain_sim = max(0.0, min(1.0, domain_sim))

    raw_weighted = (
        (0.35 * sbert_sim) +
        (0.35 * feature_overlap_ratio) +
        (0.15 * evidence_strength) +
        (0.10 * max(concept_overlap, domain_sim)) +
        (0.05 * cpc_overlap)
    )

    # Gate penalty for zero matching technical features
    if has_target_features and feature_overlap_ratio == 0.0 and concept_overlap == 0.0:
        penalty = 0.35
    else:
        penalty = 1.0

    final_pct = round(min(1.0, raw_weighted * penalty) * 100.0, 1)
    return final_pct

def compute_hybrid_score(
    user_embedding: List[float],
    patent_embedding: List[float],
    user_keywords: List[str],
    user_concepts: List[str],
    user_domain: str,
    patent: Dict[str, Any],
    target_text_for_concepts: str = "",
    w_semantic: float = SEMANTIC_WEIGHT,
    w_keyword: float = KEYWORD_WEIGHT,
    w_domain: float = DOMAIN_WEIGHT
) -> Dict[str, Any]:
    """
    Compute hybrid similarity score using deterministic scoring formula.
    """
    patent_title = patent.get("title", "")
    patent_abstract = patent.get("abstract", "")
    patent_desc = patent.get("description", "")
    existing_domain = patent.get("domain", "")
    
    inferred_domain = infer_patent_domain(patent_title, patent_abstract, existing_domain)
    
    semantic_sim = calculate_cosine_similarity(user_embedding, patent_embedding)
    
    # Target Atomic Technical Features Matching
    target_atomic_features = extract_atomic_technical_features(target_text_for_concepts, top_n=9)
    patent_full_text_lower = f"{patent_title} {patent_abstract} {patent_desc}".lower()

    matched_atomic_features = []
    for feat in target_atomic_features:
        feat_lower = feat.lower()
        pattern = r'\b' + re.escape(feat_lower) + r'\b' if len(feat_lower.split()) == 1 else re.escape(feat_lower)
        if re.search(pattern, patent_full_text_lower):
            matched_atomic_features.append(feat)

    # Calculate keyword & concept overlap
    keyword_sim, fallback_matched_concepts = calculate_keyword_similarity(
        user_keywords=user_keywords,
        user_concepts=user_concepts,
        target_full_text=target_text_for_concepts,
        patent_abstract=patent_abstract,
        patent_description=patent_desc
    )

    feature_overlap_ratio = (len(matched_atomic_features) / len(target_atomic_features)) if target_atomic_features else keyword_sim

    effective_user_domain = user_domain or inferred_domain or "Mechanical Engineering"
    domain_sim = calculate_domain_similarity(effective_user_domain, inferred_domain)

    # Check CPC match if available
    cpc_codes_str = str(patent.get("cpc_codes", ""))
    user_cpc_list = patent.get("cpc_candidates", [])
    cpc_overlap = 1.0 if any(c in cpc_codes_str for c in user_cpc_list if c) else 0.0

    # Calculate deterministic final score
    final_score = calculate_deterministic_final_score(
        sbert_sim=semantic_sim,
        feature_overlap_ratio=feature_overlap_ratio,
        evidence_strength=1.0 if matched_atomic_features else 0.0,
        cpc_overlap=cpc_overlap,
        concept_overlap=keyword_sim,
        domain_sim=domain_sim,
        has_target_features=bool(target_atomic_features)
    )

    semantic_score = round(semantic_sim * 100.0, 1)
    keyword_score = round(feature_overlap_ratio * 100.0, 1)
    domain_score = round(domain_sim * 100.0, 1)

    display_matched_concepts = matched_atomic_features if matched_atomic_features else fallback_matched_concepts

    return {
        "final_score": final_score,
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "domain_score": domain_score,
        "matched_concepts": display_matched_concepts,
        "target_atomic_features": target_atomic_features,
        "inferred_domain": inferred_domain,
        "has_core_match": bool(matched_atomic_features)
    }


