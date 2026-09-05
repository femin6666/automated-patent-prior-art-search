from typing import List, Dict, Any, Tuple
import numpy as np

# Configurable default weights
SEMANTIC_WEIGHT = 0.70
KEYWORD_WEIGHT = 0.20
DOMAIN_WEIGHT = 0.10

RELATED_DOMAINS_MAP = {
    "Artificial Intelligence": {"Software", "Robotics", "Electronics", "IoT"},
    "Software": {"Artificial Intelligence", "Electronics", "IoT"},
    "Agriculture": {"IoT", "Biotechnology", "Robotics"},
    "Healthcare": {"Biotechnology", "Electronics", "IoT"},
    "IoT": {"Electronics", "Software", "Robotics", "Artificial Intelligence"},
    "Robotics": {"Electronics", "Software", "Manufacturing", "Artificial Intelligence"},
    "Energy": {"Electronics", "Manufacturing", "IoT"},
    "Manufacturing": {"Robotics", "Electronics", "Energy"},
    "Electronics": {"IoT", "Robotics", "Software", "Energy"},
    "Biotechnology": {"Healthcare", "Agriculture"}
}

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
    # Cosine similarity for normalized SBERT embeddings ranges from ~0.0 to 1.0
    return max(0.0, min(1.0, similarity))

def calculate_keyword_similarity(
    user_keywords: List[str],
    user_concepts: List[str],
    patent_abstract: str,
    patent_description: str
) -> Tuple[float, List[str]]:
    """
    Calculate keyword/concept overlap score and return matched concepts.
    """
    all_user_terms = set(
        [k.lower().strip() for k in user_keywords if k] +
        [c.lower().strip() for c in user_concepts if c]
    )
    
    if not all_user_terms:
        return 0.0, []
        
    patent_text = (patent_abstract + " " + patent_description).lower()
    
    matched_terms = []
    for term in all_user_terms:
        if term and term in patent_text:
            matched_terms.append(term.title())
            
    overlap_ratio = len(matched_terms) / len(all_user_terms)
    keyword_score = max(0.0, min(1.0, overlap_ratio))
    
    return keyword_score, matched_terms

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
        return 0.5
        
    return 0.1

def compute_hybrid_score(
    user_embedding: List[float],
    patent_embedding: List[float],
    user_keywords: List[str],
    user_concepts: List[str],
    user_domain: str,
    patent: Dict[str, Any],
    w_semantic: float = SEMANTIC_WEIGHT,
    w_keyword: float = KEYWORD_WEIGHT,
    w_domain: float = DOMAIN_WEIGHT
) -> Dict[str, Any]:
    """
    Compute hybrid similarity score using formula:
    Final Score = (w_semantic * Semantic) + (w_keyword * Keyword) + (w_domain * Domain)
    All return scores scaled from 0.0 to 100.0%
    """
    semantic_sim = calculate_cosine_similarity(user_embedding, patent_embedding)
    keyword_sim, matched_concepts = calculate_keyword_similarity(
        user_keywords, user_concepts, patent.get("abstract", ""), patent.get("description", "")
    )
    domain_sim = calculate_domain_similarity(user_domain, patent.get("domain", ""))
    
    final_raw = (
        (w_semantic * semantic_sim) +
        (w_keyword * keyword_sim) +
        (w_domain * domain_sim)
    )
    
    final_score = round(final_raw * 100.0, 1)
    semantic_score = round(semantic_sim * 100.0, 1)
    keyword_score = round(keyword_sim * 100.0, 1)
    domain_score = round(domain_sim * 100.0, 1)
    
    return {
        "final_score": final_score,
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "domain_score": domain_score,
        "matched_concepts": matched_concepts
    }
