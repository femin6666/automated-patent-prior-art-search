import re
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer

TECHNICAL_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "in", "out", "on",
    "off", "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should",
    "now", "using", "used", "system", "method", "device", "apparatus", "comprising",
    "includes", "including", "provides", "provided", "configured", "based", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "having",
    "do", "does", "did", "doing", "would", "should", "could", "ought"
}

def extract_technical_concepts(text: str, top_n: int = 8) -> List[str]:
    """
    Extract AI-detected technical concepts using TF-IDF and n-gram analysis.
    Labels concepts as AI-Detected Technical Concepts (not legal claim terms).
    """
    if not text or len(text.strip()) < 10:
        return []
        
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', text.lower())
    words = [w for w in cleaned.split() if w not in TECHNICAL_STOP_WORDS and len(w) > 2]
    
    if not words:
        return []
        
    documents = [text]
    
    try:
        vectorizer = TfidfVectorizer(
            stop_words=list(TECHNICAL_STOP_WORDS),
            ngram_range=(1, 3),
            max_features=50,
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform(documents)
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        # Sort features by TF-IDF score
        ranked_concepts = [
            feature_names[i].title()
            for i in scores.argsort()[::-1]
            if len(feature_names[i]) > 3
        ]
        
        # Deduplicate overlapping phrases
        unique_concepts = []
        for concept in ranked_concepts:
            if not any(concept in existing or existing in concept for existing in unique_concepts):
                unique_concepts.append(concept)
            if len(unique_concepts) >= top_n:
                break
                
        return unique_concepts
    except Exception:
        # Fallback to word frequency if TF-IDF fails
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq.keys(), key=lambda k: freq[k], reverse=True)
        return [w.title() for w in sorted_words[:top_n]]
