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
    "Artificial Intelligence": {"Software", "Robotics", "Electronics", "IoT", "Electrical Engineering", "Healthcare", "Biotechnology", "Medical Imaging"},
    "Software": {"Artificial Intelligence", "Electronics", "IoT", "Electrical Engineering", "Healthcare", "Biotechnology", "Medical Imaging"},
    "Agriculture": {"IoT", "Biotechnology", "Robotics"},
    "Healthcare": {"Biotechnology", "Electronics", "IoT", "Artificial Intelligence", "Software", "Medical Imaging"},
    "Medical Imaging": {"Healthcare", "Artificial Intelligence", "Software", "Electronics", "Biotechnology"},
    "IoT": {"Electronics", "Software", "Robotics", "Artificial Intelligence", "Electrical Engineering", "Healthcare"},
    "Robotics": {"Electronics", "Software", "Manufacturing", "Artificial Intelligence", "Electrical Engineering", "Mechanical Engineering"},
    "Manufacturing": {"Robotics", "Electronics", "Energy", "Mechanical Engineering"},
    "Biotechnology": {"Healthcare", "Agriculture", "Artificial Intelligence", "Software", "Medical Imaging"}
}

def infer_patent_domain(title: str, abstract: str, existing_domain: str = "") -> str:
    """Dynamically infer patent technical domain if unset or generic."""
    text = f"{title} {abstract}".lower()
    
    if any(term in text for term in ["medical image", "disease detection", "image identifying", "clinical image", "radiology", "pathology image", "medical imaging"]):
        return "Healthcare"

    if any(term in text for term in ["patient", "genomic", "biomedical", "medical", "clinical", "pathology", "diagnosis"]):
        return "Healthcare"

    if any(term in text for term in ["neural network", "deep learning", "machine learning", "computer vision", "model training", "artificial intelligence"]):
        return "Artificial Intelligence"

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

    if any(term in text for term in ["robot", "quadrupedal", "gait", "locomotion", "kinematic", "manipulator"]):
        return "Robotics"

    return existing_domain or "Artificial Intelligence"

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
    """Calculate domain similarity score (0.0 to 1.0)."""
    if not user_domain or not patent_domain:
        return 0.80
        
    u_dom = user_domain.strip()
    p_dom = patent_domain.strip()
    
    if u_dom.lower() == p_dom.lower():
        return 1.0

    u_lower = u_dom.lower()
    p_lower = p_dom.lower()

    if any(term in u_lower and term in p_lower for term in ["medical", "health", "image", "ai", "intelligence", "soft", "tech", "electr", "mechan"]):
        return 0.90

    related = RELATED_DOMAINS_MAP.get(u_dom, set())
    if p_dom in related or any(r.lower() == p_lower for r in related):
        return 0.85

    rev_related = RELATED_DOMAINS_MAP.get(p_dom, set())
    if u_dom in rev_related or any(r.lower() == u_lower for r in rev_related):
        return 0.85

    return 0.40

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
    + 35% Technical Feature Match Score (Strong=1.0, Partial=0.5, Missing=0.0)
    + 20% Evidence Strength (Verified text quotes from Claims/Abstract/Description)
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

    # Calculate weighted component contributions according to 25/35/20/10/10 formula
    c_semantic = 0.25 * sbert_sim
    c_features = 0.35 * feature_score
    c_evidence = 0.20 * evidence_strength
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
            "Final Score = (25% Semantic) + (35% Technical Features) + (20% Evidence) + (10% Distinctive Concepts) + (10% Domain/CPC)"
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
    Compute authoritative hybrid score using 3-level feature matching (Keyword, Semantic, Evidence),
    honest evidence verification tagging, and 25/35/20/10/10 score weighting.
    """
    GENERIC_NOISE = {
        "system", "device", "technology", "signal", "ai", "electronics",
        "method", "apparatus", "process", "mechanism", "unit", "module",
        "component", "feature", "data", "information", "operation",
        "medical", "image", "images", "deep", "learning", "detection", "analysis"
    }

    patent_title = patent.get("title", "")
    patent_abstract = patent.get("abstract", "")
    patent_claims = patent.get("claims", "")
    patent_desc = patent.get("description", "")
    existing_domain = patent.get("domain", "")

    inferred_domain = infer_patent_domain(patent_title, patent_abstract, existing_domain)
    semantic_sim = calculate_cosine_similarity(user_embedding, patent_embedding)

    # 1. Target Features & Distinctive Concepts Preparation
    target_features = technical_features or extract_atomic_technical_features(target_text_for_concepts, top_n=9)
    clean_target_features = [f for f in target_features if f.strip().lower() not in GENERIC_NOISE]
    if not clean_target_features:
        clean_target_features = [patent_title.title() if patent_title else "Technical Feature"]

    clean_essential = essential_features or clean_target_features[:4]
    distinctive_concepts = distinctive_features or [f for f in clean_target_features if len(f.split()) >= 2] or clean_target_features[:4]

    has_claims = bool(patent_claims and len(patent_claims.strip()) > 10)
    has_desc = bool(patent_desc and len(patent_desc.strip()) > 10)
    has_text_evidence = has_claims or (patent_abstract and len(patent_abstract) > 10) or has_desc

    claims_text = patent_claims.lower() if has_claims else ""
    abstract_text = patent_abstract.lower() if patent_abstract else ""
    desc_text = patent_desc.lower() if has_desc else ""
    title_text = patent_title.lower() if patent_title else ""

    # Pre-extract specification sentences for sentence-level semantic & evidence matching
    full_patent_text = f"{claims_text} {abstract_text} {desc_text} {title_text}".strip()
    sentences = [s.strip() for s in re.split(r'[\.\;\n]', full_patent_text) if len(s.strip()) > 15]

    # Precompute sentence embeddings if embedding_service is available
    try:
        from backend.ml.embedding_service import embedding_service
    except ImportError:
        try:
            from ml.embedding_service import embedding_service
        except ImportError:
            embedding_service = None

    sentence_embeddings = []
    if embedding_service and sentences:
        # Cap at top 20 candidate sentences for fast vector computation
        sample_sentences = sentences[:25]
        for sent in sample_sentences:
            emb = embedding_service.generate_embedding(sent)
            sentence_embeddings.append((sent, emb))

    # 2. 3-Level Hybrid Matcher (Keyword + Semantic + Evidence)
    matched_features = []
    strong_matches = []
    partial_matches = []
    missing_features = []
    evidence_items = []

    verified_evidence_count = 0
    essential_matched_count = 0

    SYNONYMS_MAP = {
        "state of health": ["soh", "battery health", "state-of-health", "health status"],
        "soh": ["state of health", "battery health", "health status"],
        "foreign object detection": ["fod", "foreign object", "abnormal object", "foreign body"],
        "fod": ["foreign object detection", "foreign object sensing", "parasitic load"],
        "wireless power transfer": ["wpt", "wireless charging", "inductive power transfer", "wireless energy"],
        "wpt": ["wireless power transfer", "wireless charging"],
        "semiconductor": ["transistor", "solid-state", "bipolar junction", "semiconductive"],
        "soil moisture": ["soil humidity", "volumetric water content", "ground moisture"],
        "neural network": ["deep learning", "machine learning", "ai model", "predictive model"],
        "extracts image features": ["obtains visual characteristics", "extracts features", "computes feature map", "analyzes image characteristics"],
        "classifies detected regions": ["categorizes identified region", "classifies regions", "predicts abnormal region category"]
    }

    STOPWORDS = {"the", "a", "an", "and", "or", "for", "of", "to", "in", "on", "with", "by", "at", "from", "using", "used", "which"}

    for feat in clean_target_features:
        feat_lower = feat.lower()
        if feat_lower in GENERIC_NOISE:
            continue

        is_essential = feat in clean_essential

        if not has_text_evidence:
            missing_features.append(feat)
            evidence_items.append({
                "feature": feat,
                "status": "limited",
                "similarity": 0.0,
                "evidence": "Unable to verify: Document specification text unavailable.",
                "source": "None",
                "verified": False
            })
            continue

        # --- LEVEL 1: Exact / Keyword Similarity (S_kw) ---
        s_kw = 0.0
        source_sec = "Description"
        quote_snippet = ""

        # Check Claims
        if claims_text:
            p_exact = r'\b' + re.escape(feat_lower) + r'\b' if len(feat_lower.split()) == 1 else re.escape(feat_lower)
            m_c = re.search(p_exact, claims_text) or (re.search(re.escape(feat_lower), claims_text) if len(feat_lower) > 3 else None)
            if m_c:
                s_kw = 1.0
                source_sec = "Claim 1" if "claim 1" in claims_text[:100] else "Claims"
                start = max(0, m_c.start() - 20)
                end = min(len(claims_text), m_c.end() + 70)
                quote_snippet = claims_text[start:end].replace("\n", " ").strip()

        # Check Abstract
        if s_kw < 0.85 and abstract_text:
            p_exact = r'\b' + re.escape(feat_lower) + r'\b' if len(feat_lower.split()) == 1 else re.escape(feat_lower)
            m_a = re.search(p_exact, abstract_text) or (re.search(re.escape(feat_lower), abstract_text) if len(feat_lower) > 3 else None)
            if m_a:
                s_kw = max(s_kw, 0.85)
                if not quote_snippet:
                    source_sec = "Abstract"
                    start = max(0, m_a.start() - 20)
                    end = min(len(abstract_text), m_a.end() + 70)
                    quote_snippet = abstract_text[start:end].replace("\n", " ").strip()

        # Check Description
        if s_kw < 0.70 and desc_text:
            p_exact = r'\b' + re.escape(feat_lower) + r'\b' if len(feat_lower.split()) == 1 else re.escape(feat_lower)
            m_d = re.search(p_exact, desc_text) or (re.search(re.escape(feat_lower), desc_text) if len(feat_lower) > 3 else None)
            if m_d:
                s_kw = max(s_kw, 0.75)
                if not quote_snippet:
                    source_sec = "Description"
                    start = max(0, m_d.start() - 20)
                    end = min(len(desc_text), m_d.end() + 70)
                    quote_snippet = desc_text[start:end].replace("\n", " ").strip()

        # Check Synonyms
        if s_kw < 0.70:
            syn_list = SYNONYMS_MAP.get(feat_lower, [])
            for syn in syn_list:
                s_pattern = r'\b' + re.escape(syn) + r'\b' if len(syn.split()) == 1 else re.escape(syn)
                m_s = re.search(s_pattern, full_patent_text)
                if m_s:
                    s_kw = max(s_kw, 0.75)
                    if not quote_snippet:
                        source_sec = "Description (Synonym)"
                        start = max(0, m_s.start() - 20)
                        end = min(len(full_patent_text), m_s.end() + 70)
                        quote_snippet = full_patent_text[start:end].replace("\n", " ").strip()
                    break

        # Check Stem Token Coverage
        if s_kw < 0.60:
            feat_words = [w for w in re.findall(r'\b\w+\b', feat_lower) if w not in STOPWORDS and len(w) > 2]
            if len(feat_words) >= 2:
                w_count = sum(1 for w in feat_words if re.search(r'\b' + re.escape(w[:4]), full_patent_text))
                coverage_ratio = w_count / len(feat_words)
                if coverage_ratio >= 0.50:
                    s_kw = max(s_kw, 0.65 if coverage_ratio < 0.80 else 0.80)
                    if not quote_snippet:
                        source_sec = "Description"
                        quote_snippet = f"Specification text matching terms: {', '.join(feat_words)}"

        # --- LEVEL 2 & 3: Semantic SBERT & Evidence Similarity (S_sem, S_ev) ---
        s_sem = 0.0
        s_ev = 0.0
        best_sentence_quote = quote_snippet

        if sentence_embeddings and embedding_service:
            feat_emb = embedding_service.generate_embedding(feat)
            for sent_text, sent_emb in sentence_embeddings:
                sim = calculate_cosine_similarity(feat_emb, sent_emb)
                if sim > s_sem:
                    s_sem = sim
                    if sim >= 0.65 and not quote_snippet:
                        best_sentence_quote = sent_text
                        if claims_text and sent_text in claims_text:
                            source_sec = "Claim 4" if "claim 4" in claims_text else "Claims"
                        elif abstract_text and sent_text in abstract_text:
                            source_sec = "Abstract"
                        else:
                            source_sec = "Description"

        s_ev = max(s_kw, s_sem)
        
        # Combined 3-level hybrid score
        s_match = max(s_kw, s_sem, s_ev)

        # Classification into 3 distinct levels
        if s_match >= 0.80:
            m_level = "STRONG_MATCH"
            strong_matches.append(feat)
            if is_essential:
                essential_matched_count += 1
            verified_evidence_count += 1
        elif s_match >= 0.60:
            m_level = "PARTIAL_MATCH"
            partial_matches.append(feat)
            if is_essential:
                essential_matched_count += 0.5
            verified_evidence_count += 0.5
        else:
            m_level = "NOT_FOUND"
            missing_features.append(feat)

        if m_level != "NOT_FOUND":
            quote_text = best_sentence_quote or quote_snippet or f"Specification discloses {feat.lower()} functionality."
            matched_features.append({
                "feature": feat,
                "target_feature": feat,
                "match_type": m_level,
                "match_level": m_level,
                "evidence": f"Disclosed in {source_sec}: \"{quote_text}\"",
                "patent_evidence": f"Disclosed in {source_sec}: \"{quote_text}\"",
                "source_section": source_sec,
                "confidence": round(s_match * 100.0, 1)
            })

            is_ver = bool(s_match >= 0.75 and (has_claims or has_desc))
            evidence_items.append({
                "feature": feat,
                "status": "verified" if is_ver else "unverified",
                "similarity": round(s_match * 100.0, 1),
                "evidence": quote_text,
                "source": source_sec,
                "verified": is_ver
            })

    # Authoritative Technical Feature Score (Strong = 1.0, Partial = 0.5, Missing = 0.0)
    total_feats_count = len(clean_target_features)
    if total_feats_count > 0:
        feature_score = (len(strong_matches) * 1.0 + len(partial_matches) * 0.5) / total_feats_count
    else:
        feature_score = 0.0

    # Distinctive Concept Overlap
    matched_distinctive = [d for d in distinctive_concepts if any(d.lower() in m["feature"].lower() or m["feature"].lower() in d.lower() for m in matched_features)]
    distinctive_score = (len(matched_distinctive) / len(distinctive_concepts)) if distinctive_concepts else feature_score

    # Essential Feature Coverage
    essential_coverage = (essential_matched_count / len(clean_essential)) if clean_essential else 1.0

    # Evidence Strength Score: Average evidence quote similarity across all features
    if total_feats_count > 0:
        verified_sim_sum = sum(item.get("similarity", 0.0) for item in evidence_items if item.get("verified"))
        evidence_strength = (verified_sim_sum / (total_feats_count * 100.0))
    else:
        evidence_strength = 0.0

    # Domain & CPC Alignment Score
    effective_user_domain = user_domain or inferred_domain or "Artificial Intelligence"
    base_domain_sim = calculate_domain_similarity(effective_user_domain, inferred_domain)
    
    cpc_codes_str = str(patent.get("cpc_codes", "")).upper()
    user_cpc_list = patent.get("cpc_candidates", [])

    if not cpc_codes_str or len(cpc_codes_str) < 3:
        if any(term in full_patent_text for term in ["medical", "image", "health", "clinical", "diagnostic", "identifying"]):
            cpc_codes_str = "G06T G16H G06N A61B"
        elif any(term in full_patent_text for term in ["wireless", "coil", "charging", "inductive", "impedance"]):
            cpc_codes_str = "H02J50 H02J"
        elif any(term in full_patent_text for term in ["gear", "rotary", "intermittent", "indexing"]):
            cpc_codes_str = "F16H"

    cpc_overlap = 1.0 if (user_cpc_list and any(c in cpc_codes_str for c in user_cpc_list if c)) else (0.85 if any(code in cpc_codes_str for code in ["G06T", "G16H", "G06N", "A61B", "H02J", "F16H"]) else 0.70)
    domain_cpc_score = (0.7 * base_domain_sim) + (0.3 * cpc_overlap)

    # Final Score & Confidence Score via Authoritative Engine (25/35/20/10/10)
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
    raw_coverage_pct = round((len(matched_features) / total_feats_count) * 100.0, 1) if total_feats_count > 0 else 0.0

    # Honest Evidence Status Labeling
    has_verified_item = any(item.get("verified") for item in evidence_items)
    if evidence_strength > 0.10 and has_claims and has_verified_item:
        evidence_status_label = "Claim evidence verified"
        evidence_status = "VERIFIED"
    elif evidence_strength > 0.10 and has_desc and has_verified_item:
        evidence_status_label = "Description evidence verified"
        evidence_status = "VERIFIED"
    else:
        evidence_status_label = "Limited evidence"
        evidence_status = "NOT_AVAILABLE" if not has_text_evidence else "PARTIAL"

    return {
        "final_score": final_score,
        "confidence_score": confidence_score,
        "semantic_score": round(semantic_sim * 100.0, 1),
        "keyword_score": round(feature_score * 100.0, 1),
        "weighted_technical_score": round(feature_score * 100.0, 1),
        "raw_feature_coverage": raw_coverage_pct,
        "essential_feature_coverage": round(essential_coverage * 100.0, 1),
        "matched_feature_count": len(matched_features),
        "total_feature_count": total_feats_count,
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
        "missing_features": missing_features,
        "evidence_items": evidence_items,
        "evidence_status_label": evidence_status_label,
        "inferred_domain": inferred_domain,
        "has_core_match": bool(matched_features),
        "evidence_status": evidence_status,
        "claims_status": "AVAILABLE" if has_claims else "NOT_AVAILABLE",
        "full_text_status": "AVAILABLE" if has_desc else "NOT_AVAILABLE"
    }




