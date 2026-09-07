from typing import List, Dict, Any, Tuple
import numpy as np
import re

try:
    from backend.ml.keyword_extractor import (
        get_weighted_technical_concepts,
        GENERIC_DOMAIN_NOISE,
        DISTINCTIVE_TECHNICAL_TERMS
    )
except ImportError:
    from .keyword_extractor import (
        get_weighted_technical_concepts,
        GENERIC_DOMAIN_NOISE,
        DISTINCTIVE_TECHNICAL_TERMS
    )

# Configurable default weights (Prioritizing distinctive technical feature overlap)
SEMANTIC_WEIGHT = 0.40
KEYWORD_WEIGHT = 0.45
DOMAIN_WEIGHT = 0.15

RELATED_DOMAINS_MAP = {
    "Electrical Engineering": {"Electronics", "Energy", "IoT", "Robotics", "Software", "Artificial Intelligence"},
    "Electronics": {"Electrical Engineering", "IoT", "Robotics", "Software", "Energy", "Artificial Intelligence"},
    "Energy": {"Electrical Engineering", "Electronics", "Manufacturing", "IoT"},
    "Artificial Intelligence": {"Software", "Robotics", "Electronics", "IoT", "Electrical Engineering"},
    "Software": {"Artificial Intelligence", "Electronics", "IoT", "Electrical Engineering"},
    "Agriculture": {"IoT", "Biotechnology", "Robotics"},
    "Healthcare": {"Biotechnology", "Electronics", "IoT"},
    "IoT": {"Electronics", "Software", "Robotics", "Artificial Intelligence", "Electrical Engineering"},
    "Robotics": {"Electronics", "Software", "Manufacturing", "Artificial Intelligence", "Electrical Engineering"},
    "Manufacturing": {"Robotics", "Electronics", "Energy"},
    "Biotechnology": {"Healthcare", "Agriculture"}
}

def infer_patent_domain(title: str, abstract: str, existing_domain: str = "") -> str:
    """Dynamically infer patent technical domain if unset or generic."""
    text = f"{title} {abstract}".lower()
    
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

    if any(term in text for term in ["robot", "quadrupedal", "gait", "locomotion", "kinematic"]):
        return "Robotics"

    return existing_domain or "Electrical Engineering"

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
    (e.g., 'wireless power transfer', 'foreign object detection', 'impedance') carry high weight.
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
        # Exact word boundary matching for single words, clean phrase matching for multi-word n-grams
        pattern = r'\b' + re.escape(term) + r'\b' if len(term.split()) == 1 else re.escape(term)
        if re.search(pattern, patent_text):
            matched_terms.append(term.title())
            matched_weight_sum += weight
            
    if total_weight_sum <= 0:
        return 0.0, []
        
    raw_ratio = matched_weight_sum / total_weight_sum
    keyword_score = max(0.0, min(1.0, raw_ratio))
    
    # Format matched concepts nicely for display (deduplicating substrings)
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
        
    return 0.2

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
    Compute hybrid similarity score using formula:
    Final Score = (w_semantic * Semantic) + (w_keyword * FeatureOverlap) + (w_domain * Domain)
    Applies core technical feature gate penalty to patents missing essential core concepts.
    """
    patent_title = patent.get("title", "")
    patent_abstract = patent.get("abstract", "")
    patent_desc = patent.get("description", "")
    existing_domain = patent.get("domain", "")
    
    inferred_domain = infer_patent_domain(patent_title, patent_abstract, existing_domain)
    
    semantic_sim = calculate_cosine_similarity(user_embedding, patent_embedding)
    
    keyword_sim, matched_concepts = calculate_keyword_similarity(
        user_keywords=user_keywords,
        user_concepts=user_concepts,
        target_full_text=target_text_for_concepts,
        patent_abstract=patent_abstract,
        patent_description=patent_desc
    )
    
    effective_user_domain = user_domain or "Electrical Engineering"
    domain_sim = calculate_domain_similarity(effective_user_domain, inferred_domain)
    
    # Adaptive Dynamic Weights:
    # If user provided 0 explicit keywords, shift weight to SBERT Semantic similarity
    has_user_keywords = bool(user_keywords and any(k.strip() for k in user_keywords))
    if not has_user_keywords and w_semantic == SEMANTIC_WEIGHT:
        w_semantic = 0.70
        w_keyword = 0.15
        w_domain = 0.15
    
    # Core Distinctive Feature Gate:
    # Identify high-importance distinctive terms in target invention
    target_lower = target_text_for_concepts.lower()
    core_distinctive_target_terms = [
        dt for dt in DISTINCTIVE_TECHNICAL_TERMS if dt in target_lower
    ]
    
    patent_text_lower = f"{patent_title} {patent_abstract} {patent_desc}".lower()
    has_any_core_match = any(dt in patent_text_lower for dt in core_distinctive_target_terms)
    
    # If target invention has core technical features (e.g. 'wireless power transfer', 'foreign object detection')
    # and patent matches NONE of them, penalize keyword & final score
    if core_distinctive_target_terms and not has_any_core_match:
        keyword_sim *= 0.15
        distinctive_penalty = 0.65
    else:
        distinctive_penalty = 1.0

    # If candidate patent MATCHES core distinctive features, give feature bonus
    if core_distinctive_target_terms and has_any_core_match:
        matched_core_count = sum(1 for dt in core_distinctive_target_terms if dt in patent_text_lower)
        bonus_ratio = matched_core_count / len(core_distinctive_target_terms)
        keyword_sim = min(1.0, keyword_sim + (0.35 * bonus_ratio))

    final_raw = (
        (w_semantic * semantic_sim) +
        (w_keyword * keyword_sim) +
        (w_domain * domain_sim)
    ) * distinctive_penalty
    
    final_score = round(min(1.0, final_raw) * 100.0, 1)
    semantic_score = round(semantic_sim * 100.0, 1)
    keyword_score = round(keyword_sim * 100.0, 1)
    domain_score = round(domain_sim * 100.0, 1)
    
    return {
        "final_score": final_score,
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "domain_score": domain_score,
        "matched_concepts": matched_concepts,
        "inferred_domain": inferred_domain,
        "has_core_match": has_any_core_match
    }

