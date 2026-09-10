from typing import List, Dict, Any, Tuple, Optional
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
    feature_score: float,
    evidence_strength: float = 0.0,
    distinctive_score: float = 0.0,
    domain_cpc_score: float = 0.5,
    has_target_features: bool = True,
    essential_feature_coverage: float = 1.0,
    has_text_evidence: bool = True
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Authoritative single-source deterministic scoring engine:
      25% SBERT Semantic Similarity
    + 40% Technical Feature Score (Weighted Component-Function-Relationship Overlap)
    + 15% Evidence Strength (Verified text quotes from Claims/Abstract/Description)
    + 10% Distinctive Concept Overlap
    + 10% Domain & CPC/IPC Alignment
    
    Technical Relevance Gate Enforcement:
    Prevents documents with low technical overlap or missing essential features from receiving
    a high final score based on SBERT semantic similarity alone.
    """
    # Enforce bounds [0.0, 1.0]
    sbert_sim = max(0.0, min(1.0, sbert_sim))
    feature_score = max(0.0, min(1.0, feature_score))
    evidence_strength = max(0.0, min(1.0, evidence_strength))
    distinctive_score = max(0.0, min(1.0, distinctive_score))
    domain_cpc_score = max(0.0, min(1.0, domain_cpc_score))
    essential_feature_coverage = max(0.0, min(1.0, essential_feature_coverage))

    # Calculate weighted component contributions
    c_semantic = 0.25 * sbert_sim
    c_features = 0.40 * feature_score
    c_evidence = 0.15 * evidence_strength
    c_distinctive = 0.10 * distinctive_score
    c_domain = 0.10 * domain_cpc_score

    raw_weighted = (c_semantic + c_features + c_evidence + c_distinctive + c_domain) * 100.0

    is_gated = False
    gate_reason = ""
    
    # Gate 1: Essential feature overlap cap
    if has_target_features and (feature_score < 0.25 or essential_feature_coverage < 0.30):
        is_gated = True
        gate_reason = "Cap applied due to low technical feature / essential feature overlap"
        final_pct = round(min(raw_weighted, 45.0), 1)
    # Gate 2: Generic domain match cap
    elif has_target_features and distinctive_score == 0.0 and feature_score < 0.40:
        is_gated = True
        gate_reason = "Cap applied due to generic domain term matching only"
        final_pct = round(min(raw_weighted, 40.0), 1)
    else:
        final_pct = round(min(100.0, raw_weighted), 1)

    # Calculate Evidence Confidence Score (0.0 to 100.0)
    if not has_text_evidence:
        confidence_score = round(evidence_strength * 40.0, 1)
    else:
        confidence_score = round((evidence_strength * 70.0) + (distinctive_score * 30.0), 1)

    breakdown = {
        "semantic_similarity": round(sbert_sim * 100.0, 1),
        "technical_features": round(feature_score * 100.0, 1),
        "evidence_strength": round(evidence_strength * 100.0, 1),
        "distinctive_concepts": round(distinctive_score * 100.0, 1),
        "domain_cpc_alignment": round(domain_cpc_score * 100.0, 1),
        "final_score": final_pct,
        "confidence_score": confidence_score,
        "is_gated": is_gated,
        "formula_explanation": (
            "Final Score = (25% Semantic) + (40% Technical Features) + (15% Evidence) + (10% Distinctive Concepts) + (10% Domain/CPC)"
            + (f" [Technical Gate Applied: {gate_reason}]" if is_gated else "")
        )
    }

    return final_pct, confidence_score, breakdown


def compute_hybrid_score(
    user_embedding: List[float],
    patent_embedding: List[float],
    user_keywords: List[str],
    user_concepts: List[str],
    user_domain: str,
    patent: Dict[str, Any],
    target_text_for_concepts: str = "",
    distinctive_features: Optional[List[str]] = None,
    technical_features: Optional[List[str]] = None,
    essential_features: Optional[List[str]] = None,
    w_semantic: float = SEMANTIC_WEIGHT,
    w_keyword: float = KEYWORD_WEIGHT,
    w_domain: float = DOMAIN_WEIGHT
) -> Dict[str, Any]:
    """
    Compute authoritative hybrid score using section-weighted text matching
    (Claims 1.0 > Abstract 0.85 > Description 0.7 > Title 0.6), 5-level match classification
    (STRONG_MATCH, PARTIAL_MATCH, WEAK_MATCH, NOT_FOUND, UNABLE_TO_VERIFY), evidence verification,
    and technical relevance gating.
    """
    GENERIC_NOISE = {
        "system", "device", "technology", "signal", "ai", "electronics",
        "method", "apparatus", "process", "mechanism", "unit", "module",
        "component", "feature", "data", "information", "operation"
    }

    patent_title = patent.get("title", "")
    patent_abstract = patent.get("abstract", "")
    patent_claims = patent.get("claims", "")
    patent_desc = patent.get("description", "")
    existing_domain = patent.get("domain", "")

    inferred_domain = infer_patent_domain(patent_title, patent_abstract, existing_domain)
    semantic_sim = calculate_cosine_similarity(user_embedding, patent_embedding)

    # 1. Target Features & Distinctive Concepts Preparation
    target_features = technical_features or extract_atomic_technical_features(target_text_for_concepts, top_n=8)
    clean_target_features = [f for f in target_features if f.strip().lower() not in GENERIC_NOISE]
    if not clean_target_features:
        clean_target_features = [patent_title.title() if patent_title else "technical feature"]

    clean_essential = essential_features or clean_target_features[:4]
    distinctive_concepts = distinctive_features or [f for f in clean_target_features if len(f.split()) >= 2] or clean_target_features[:4]

    has_claims = bool(patent_claims and len(patent_claims.strip()) > 5)
    has_desc = bool(patent_desc and len(patent_desc.strip()) > 5)
    has_text_evidence = has_claims or (patent_abstract and len(patent_abstract) > 5) or has_desc

    # Full text search scope prioritizing Claims -> Abstract -> Description -> Title
    claims_text = patent_claims.lower() if has_claims else ""
    abstract_text = patent_abstract.lower() if patent_abstract else ""
    desc_text = patent_desc.lower() if has_desc else ""
    title_text = patent_title.lower() if patent_title else ""

    # 2. Weighted Section Matching with 5-Level Match Classification
    matched_features = []
    strong_matches = []
    partial_matches = []
    weak_matches = []
    missing_features = []
    unverifiable_features = []

    total_weight = 0.0
    weighted_match_sum = 0.0
    verified_evidence_count = 0
    essential_matched_count = 0

    SYNONYMS_MAP = {
        "state of health": ["soh", "battery health", "state-of-health", "health status"],
        "soh": ["state of health", "battery health", "health status"],
        "foreign object detection": ["fod", "foreign object", "abnormal object", "foreign body"],
        "fod": ["foreign object detection", "foreign object", "abnormal object"],
        "wireless power transfer": ["wpt", "wireless charging", "inductive power transfer", "wireless energy"],
        "wpt": ["wireless power transfer", "wireless charging"],
        "semiconductor": ["transistor", "solid-state", "bipolar junction", "semiconductive"],
        "soil moisture": ["soil humidity", "volumetric water content", "ground moisture"],
        "neural network": ["deep learning", "machine learning", "ai model", "predictive model"]
    }

    STOPWORDS = {"the", "a", "an", "and", "or", "for", "of", "to", "in", "on", "with", "by", "at", "from", "using", "used", "which"}

    for feat in clean_target_features:
        feat_lower = feat.lower()
        if feat_lower in GENERIC_NOISE:
            continue

        is_essential = feat in clean_essential
        is_distinctive = feat in distinctive_concepts or len(feat.split()) >= 3
        weight = 3.0 if is_distinctive else (2.0 if is_essential else 1.0)
        total_weight += weight

        if not has_text_evidence:
            unverifiable_features.append(feat)
            matched_features.append({
                "feature": feat,
                "target_feature": feat,
                "match_type": "UNABLE_TO_VERIFY",
                "match_level": "UNABLE_TO_VERIFY",
                "evidence": "Unable to verify: Document claims/specification text unavailable.",
                "patent_evidence": "Unable to verify: Document text unavailable.",
                "source_section": "none",
                "confidence": 0.0
            })
            continue

        # Section-weighted search order: Claims (1.0) -> Abstract (0.85) -> Description (0.7) -> Title (0.6)
        match_found = False
        source_sec = "none"
        match_val = 0.0
        m_level = "NOT_FOUND"
        quote_snippet = ""

        # 1. Claims Search (Highest weight)
        if claims_text:
            p_exact = r'\b' + re.escape(feat_lower) + r'\b' if len(feat_lower.split()) == 1 else re.escape(feat_lower)
            m_c = re.search(p_exact, claims_text) or (re.search(re.escape(feat_lower), claims_text) if len(feat_lower) > 3 else None)
            if m_c:
                match_found = True
                source_sec = "claims"
                match_val = 1.0
                m_level = "STRONG_MATCH"
                start = max(0, m_c.start() - 20)
                end = min(len(claims_text), m_c.end() + 60)
                quote_snippet = claims_text[start:end].replace("\n", " ").strip()

        # 2. Abstract Search
        if not match_found and abstract_text:
            p_exact = r'\b' + re.escape(feat_lower) + r'\b' if len(feat_lower.split()) == 1 else re.escape(feat_lower)
            m_a = re.search(p_exact, abstract_text) or (re.search(re.escape(feat_lower), abstract_text) if len(feat_lower) > 3 else None)
            if m_a:
                match_found = True
                source_sec = "abstract"
                match_val = 0.85
                m_level = "STRONG_MATCH"
                start = max(0, m_a.start() - 20)
                end = min(len(abstract_text), m_a.end() + 60)
                quote_snippet = abstract_text[start:end].replace("\n", " ").strip()

        # 3. Description Search
        if not match_found and desc_text:
            p_exact = r'\b' + re.escape(feat_lower) + r'\b' if len(feat_lower.split()) == 1 else re.escape(feat_lower)
            m_d = re.search(p_exact, desc_text) or (re.search(re.escape(feat_lower), desc_text) if len(feat_lower) > 3 else None)
            if m_d:
                match_found = True
                source_sec = "description"
                match_val = 0.70
                m_level = "PARTIAL_MATCH"
                start = max(0, m_d.start() - 20)
                end = min(len(desc_text), m_d.end() + 60)
                quote_snippet = desc_text[start:end].replace("\n", " ").strip()

        # 4. Synonym Search across full text
        if not match_found:
            full_patent_text = f"{claims_text} {abstract_text} {desc_text}".strip()
            syn_list = SYNONYMS_MAP.get(feat_lower, [])
            for syn in syn_list:
                s_pattern = r'\b' + re.escape(syn) + r'\b' if len(syn.split()) == 1 else re.escape(syn)
                m_s = re.search(s_pattern, full_patent_text)
                if m_s:
                    match_found = True
                    source_sec = "Description (Synonym)"
                    match_val = 0.65
                    m_level = "PARTIAL_MATCH"
                    start = max(0, m_s.start() - 20)
                    end = min(len(full_patent_text), m_s.end() + 60)
                    quote_snippet = full_patent_text[start:end].replace("\n", " ").strip()
                    break

        # 5. Token Coverage Fallback (Stem-aware partial match)
        if not match_found:
            full_patent_text = f"{claims_text} {abstract_text} {desc_text} {title_text}".strip()
            feat_words = [w for w in re.findall(r'\b\w+\b', feat_lower) if w not in STOPWORDS and len(w) > 2]
            if len(feat_words) >= 2:
                w_count = 0
                for w in feat_words:
                    w_stem = w[:4] if len(w) >= 5 else w
                    if re.search(r'\b' + re.escape(w_stem), full_patent_text):
                        w_count += 1
                coverage_ratio = w_count / len(feat_words)
                if coverage_ratio >= 0.50:
                    match_found = True
                    claims_pos = full_patent_text.find(claims_text[:30]) if claims_text else -1
                    if claims_text and any(re.search(r'\b' + re.escape(w[:4]), claims_text) for w in feat_words):
                        source_sec = "claims"
                        match_val = 0.85 if coverage_ratio >= 0.75 else 0.70
                        m_level = "STRONG_MATCH" if coverage_ratio >= 0.75 else "PARTIAL_MATCH"
                    else:
                        source_sec = "description"
                        match_val = 0.75 if coverage_ratio >= 0.75 else 0.55
                        m_level = "PARTIAL_MATCH" if coverage_ratio >= 0.75 else "WEAK_MATCH"
                    quote_snippet = f"Technical limitation disclosed across specification matching {w_count}/{len(feat_words)} terms"

        if match_found and m_level != "NOT_FOUND":
            weighted_match_sum += (weight * match_val)
            verified_evidence_count += 1
            if is_essential:
                essential_matched_count += 1

            matched_item = {
                "feature": feat,
                "target_feature": feat,
                "match_type": m_level,
                "match_level": m_level,
                "evidence": f"Disclosed in {source_sec}: \"...{quote_snippet}...\"",
                "patent_evidence": f"Disclosed in {source_sec}: \"...{quote_snippet}...\"",
                "source_section": source_sec.lower(),
                "confidence": 95.0 if source_sec == "Claims" else (85.0 if source_sec == "Abstract" else 70.0)
            }
            matched_features.append(matched_item)
            if m_level == "STRONG_MATCH":
                strong_matches.append(feat)
            elif m_level == "PARTIAL_MATCH":
                partial_matches.append(feat)
            else:
                weak_matches.append(feat)
        else:
            missing_features.append(feat)

    # Authoritative Technical Feature Score
    feature_score = (weighted_match_sum / total_weight) if total_weight > 0 else 0.0

    # Distinctive Concept Overlap
    full_patent_text = f"{claims_text} {abstract_text} {desc_text} {title_text}".strip()
    matched_distinctive = []
    for d in distinctive_concepts:
        d_lower = d.lower()
        if any(d_lower in m["feature"].lower() or m["feature"].lower() in d_lower for m in matched_features):
            matched_distinctive.append(d)
        else:
            d_words = [w for w in re.findall(r'\b\w+\b', d_lower) if w not in STOPWORDS and len(w) > 2]
            if d_words:
                w_found = sum(1 for w in d_words if re.search(r'\b' + re.escape(w) + r'\b', full_patent_text))
                if (w_found / len(d_words)) >= 0.50:
                    matched_distinctive.append(d)

    distinctive_score = (len(matched_distinctive) / len(distinctive_concepts)) if distinctive_concepts else feature_score

    # Essential Feature Coverage
    essential_coverage = (essential_matched_count / len(clean_essential)) if clean_essential else 1.0

    # Evidence Strength Score
    evidence_strength = (verified_evidence_count / len(clean_target_features)) if clean_target_features else 0.0

    # Domain & CPC Alignment Score
    effective_user_domain = user_domain or inferred_domain or "Mechanical Engineering"
    base_domain_sim = calculate_domain_similarity(effective_user_domain, inferred_domain)
    cpc_codes_str = str(patent.get("cpc_codes", ""))
    user_cpc_list = patent.get("cpc_candidates", [])
    cpc_overlap = 1.0 if any(c in cpc_codes_str for c in user_cpc_list if c) else 0.0
    domain_cpc_score = (0.7 * base_domain_sim) + (0.3 * cpc_overlap)

    # Final Score & Confidence Score via Authoritative Engine
    final_score, confidence_score, breakdown = calculate_deterministic_final_score(
        sbert_sim=semantic_sim,
        feature_score=feature_score,
        evidence_strength=evidence_strength,
        distinctive_score=distinctive_score,
        domain_cpc_score=domain_cpc_score,
        has_target_features=bool(clean_target_features),
        essential_feature_coverage=essential_coverage,
        has_text_evidence=has_text_evidence
    )

    display_concepts = [m["feature"] for m in matched_features] if matched_features else [feat for feat in clean_target_features if feat not in missing_features]
    raw_coverage_pct = round((len(matched_features) / len(clean_target_features)) * 100.0, 1) if clean_target_features else 0.0

    if not has_text_evidence:
        evidence_status = "NOT_AVAILABLE"
    elif verified_evidence_count > 0:
        evidence_status = "VERIFIED" if has_claims or (patent_abstract and len(patent_abstract) > 50) else "PARTIAL"
    elif len(matched_features) > 0:
        evidence_status = "PARTIAL"
    else:
        evidence_status = "NOT_VERIFIED"

    return {
        "final_score": final_score,
        "confidence_score": confidence_score,
        "semantic_score": round(semantic_sim * 100.0, 1),
        "keyword_score": round(feature_score * 100.0, 1),
        "weighted_technical_score": round(feature_score * 100.0, 1),
        "raw_feature_coverage": raw_coverage_pct,
        "essential_feature_coverage": round(essential_coverage * 100.0, 1),
        "matched_feature_count": len(matched_features),
        "total_feature_count": len(clean_target_features),
        "domain_score": round(domain_cpc_score * 100.0, 1),
        "evidence_score": round(evidence_strength * 100.0, 1),
        "distinctive_score": round(distinctive_score * 100.0, 1),
        "score_breakdown": breakdown,
        "matched_concepts": display_concepts,
        "target_atomic_features": clean_target_features,
        "essential_features": clean_essential,
        "distinctive_features": distinctive_concepts,
        "matched_features": matched_features,
        "strong_matches": strong_matches,
        "partial_matches": partial_matches,
        "weak_matches": weak_matches,
        "missing_features": missing_features,
        "unverifiable_features": unverifiable_features,
        "inferred_domain": inferred_domain,
        "has_core_match": bool(matched_features),
        "evidence_status": evidence_status,
        "claims_status": "AVAILABLE" if has_claims else "NOT_AVAILABLE",
        "full_text_status": "AVAILABLE" if has_desc else "NOT_AVAILABLE"
    }




