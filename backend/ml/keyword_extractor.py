import re
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer

GENERIC_DOMAIN_NOISE = {
    "vehicle", "vehicles", "charging", "system", "systems", "method", "methods",
    "device", "devices", "apparatus", "comprising", "includes", "including",
    "provides", "provided", "configured", "based", "monitoring", "control",
    "controlling", "data", "algorithm", "algorithms", "application", "applications",
    "process", "processing", "unit", "units", "module", "modules", "operation",
    "operating", "user", "time", "real", "high", "low", "new", "improved"
}

TECHNICAL_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "from", "up", "down", "out", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "s", "t", "can", "will", "just", "don", "should", "now", "using", "used",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having",
    "do", "does", "did", "doing", "would", "could", "ought"
}

# Domain-specific highly distinctive technical terms that signal specialized technical IP
DISTINCTIVE_TECHNICAL_TERMS = {
    # Mechanical Engineering & Indexing
    "continuous rotary input", "intermittent rotary output", "multiple gear arrangement",
    "gears connected by links", "orbital gear movement", "indexed/step-by-step movement",
    "step-by-step movement", "dwell period", "cam and follower", "reverse-motion prevention",
    "indexing mechanism", "geneva drive", "geneva wheel", "ratchet and pawl", "globoidal cam",
    "roller follower", "intermittent motion mechanism", "epicyclic gear", "holding pawl",

    # Electrical & Wireless Power
    "wireless power transfer", "foreign object detection", "impedance measurement",
    "impedance matching", "resonant frequency", "charging coil", "transmitter coil",
    "receiver coil", "electromagnetic field", "inductive charging", "resonant charging",
    "abnormal condition detection", "dynamic threshold", "temperature compensation",
    "automatic power reduction", "power interruption", "spiking neural network",
    "vertical-cavity surface-emitting laser", "gan power transistor",

    # AI, Robotics & Software
    "sensor fusion", "multispectral", "hyperspectral", "piezoelectric", "thermoelectric",
    "galvo-steered", "solenoid", "impedance", "inductance", "capacitance", "reactance",
    "telemetry", "convolutional neural network", "spatial transformer network", "lidar point cloud",
    "4-bit quantization", "unsupervised generative adversarial network", "proximal policy optimization",
    "contrastive learning", "impedance control", "stereo fisheye camera", "9-axis imu",
    "solid-state electrolyte", "bifacial tandem photovoltaic cell", "melt pool thermal monitoring",
    "zero-copy memory management", "zero-knowledge proof", "cas12 trans-cleavage"
}

def extract_atomic_technical_features(text: str, top_n: int = 9) -> List[str]:
    """
    Extract atomic technical feature items (6-9 items) from target invention text.
    Combines domain-specific matching with TF-IDF phrase decomposition.
    """
    if not text or len(text.strip()) < 5:
        return []

    lower_text = text.lower()
    features = []

    # 1. Direct matched distinctive phrases from domain vocabulary
    for d_term in DISTINCTIVE_TECHNICAL_TERMS:
        if d_term in lower_text:
            title_case = d_term.title()
            if not any(title_case.lower() in f.lower() or f.lower() in title_case.lower() for f in features):
                features.append(title_case)

    # 2. Key structural patterns (e.g. "x arrangement", "x mechanism", "x control")
    pattern_matches = re.findall(
        r'\b(?:continuous|intermittent|rotary|linear|orbital|gear|link|cam|follower|indexing|dwell|sensor|coil|circuit|signal|valve|laser|module|node|driver)\s+[a-z\-]+(?:\s+[a-z\-]+)?\b',
        lower_text
    )
    for p in pattern_matches:
        if len(p.split()) >= 2 and p not in GENERIC_DOMAIN_NOISE:
            p_title = p.title()
            if not any(p.lower() in f.lower() or f.lower() in p.lower() for f in features):
                features.append(p_title)

    # 3. TF-IDF Extracted phrases & distinct terms
    extracted_concepts = extract_technical_concepts(text, top_n=8)
    for c in extracted_concepts:
        if not any(c.lower() in f.lower() or f.lower() in c.lower() for f in features):
            features.append(c)

    # Clean & format nicely
    clean_features = []
    for f in features:
        if f.lower() in GENERIC_DOMAIN_NOISE:
            continue
        clean_features.append(f)
        if len(clean_features) >= top_n:
            break

    return clean_features if clean_features else [text.split()[0].title()]

def extract_technical_concepts(text: str, top_n: int = 8) -> List[str]:
    """
    Extract AI-detected distinctive technical concepts prioritizing multi-word n-grams
    (e.g., 'Wireless Power Transfer', 'Foreign Object Detection', 'Impedance Measurement').
    """
    if not text or len(text.strip()) < 10:
        return []
        
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', text.lower())
    stop_set = TECHNICAL_STOP_WORDS.union(GENERIC_DOMAIN_NOISE)
    
    words = [w for w in cleaned.split() if w not in TECHNICAL_STOP_WORDS and len(w) > 2]
    if not words:
        return []
        
    documents = [cleaned]
    
    try:
        # Extract 2-gram and 3-gram phrases first to capture distinctive technical terms
        phrase_vec = TfidfVectorizer(
            stop_words=list(TECHNICAL_STOP_WORDS),
            ngram_range=(2, 3),
            max_features=40,
            min_df=1
        )
        p_matrix = phrase_vec.fit_transform(documents)
        p_names = phrase_vec.get_feature_names_out()
        p_scores = p_matrix.toarray()[0]
        
        phrases = [
            (p_names[i].title(), p_scores[i] * 3.0)
            for i in p_scores.argsort()[::-1]
            if len(p_names[i].split()) >= 2
        ]
        
        # Extract single word terms, filtering out generic noise
        single_vec = TfidfVectorizer(
            stop_words=list(stop_set),
            ngram_range=(1, 1),
            max_features=30,
            min_df=1
        )
        s_matrix = single_vec.fit_transform(documents)
        s_names = single_vec.get_feature_names_out()
        s_scores = s_matrix.toarray()[0]
        
        singles = [
            (s_names[i].title(), s_scores[i])
            for i in s_scores.argsort()[::-1]
            if s_names[i] not in GENERIC_DOMAIN_NOISE and len(s_names[i]) > 3
        ]
        
        # Combine phrases (weighted higher) and distinct single terms
        combined = sorted(phrases + singles, key=lambda x: x[1], reverse=True)
        
        unique_concepts = []
        for concept, score in combined:
            concept_str = concept.strip()
            if not any(concept_str.lower() in u.lower() or u.lower() in concept_str.lower() for u in unique_concepts):
                unique_concepts.append(concept_str)
            if len(unique_concepts) >= top_n:
                break
                
        return unique_concepts
        
    except Exception:
        # Fallback keyword extraction
        words_no_noise = [w for w in words if w not in GENERIC_DOMAIN_NOISE]
        target_words = words_no_noise if words_no_noise else words
        freq = {}
        for w in target_words:
            freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq.keys(), key=lambda k: freq[k], reverse=True)
        return [w.title() for w in sorted_words[:top_n]]

def get_weighted_technical_concepts(user_keywords: List[str], user_concepts: List[str], text_input: str) -> Dict[str, float]:
    """
    Construct a dictionary of technical concepts with associated importance weights.
    Multi-word technical phrases & distinctive terms receive 3.0x - 5.0x higher weight
    than generic unigrams.
    """
    weighted_terms = {}
    
    # 1. Add explicitly passed user keywords
    for kw in (user_keywords or []):
        if not kw or not kw.strip():
            continue
        term = kw.strip().lower()
        if term in GENERIC_DOMAIN_NOISE:
            weighted_terms[term] = 0.1
        elif len(term.split()) >= 2 or term in DISTINCTIVE_TECHNICAL_TERMS:
            weighted_terms[term] = 4.0
        else:
            weighted_terms[term] = 1.5
            
    # 2. Add extracted technical concepts & atomic features
    atomic = extract_atomic_technical_features(text_input, top_n=9)
    for f in atomic:
        term = f.strip().lower()
        weighted_terms[term] = 5.0

    extracted = extract_technical_concepts(text_input, top_n=10)
    for c in extracted:
        term = c.strip().lower()
        if term in GENERIC_DOMAIN_NOISE:
            weighted_terms[term] = min(weighted_terms.get(term, 0.1), 0.1)
        elif len(term.split()) >= 2 or any(d in term for d in DISTINCTIVE_TECHNICAL_TERMS):
            weighted_terms[term] = max(weighted_terms.get(term, 0.0), 4.5)
        else:
            weighted_terms[term] = max(weighted_terms.get(term, 0.0), 2.0)
            
    # 3. Explicit check for known distinctive concepts in target text_input
    lower_text = text_input.lower()
    for d_term in DISTINCTIVE_TECHNICAL_TERMS:
        if d_term in lower_text:
            weighted_terms[d_term] = 5.0

    return weighted_terms


