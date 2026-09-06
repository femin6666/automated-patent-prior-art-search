from typing import Dict, Any
try:
    from backend.app.core.config import settings
except ImportError:
    from ..app.core.config import settings

RISK_DISCLAIMER = (
    "PatentLens AI provides AI-assisted preliminary prior-art search and comparison results "
    "for informational and research purposes only. The results do not constitute legal advice, "
    "a patentability determination, or a professional patent opinion."
)

def get_similarity_level_label(score: float) -> str:
    """Return text label for similarity score using configurable application thresholds."""
    val = max(0.0, min(100.0, float(score)))
    if val <= settings.SIMILARITY_THRESHOLD_LOW:
        return "Low"
    elif val <= settings.SIMILARITY_THRESHOLD_MODERATE:
        return "Moderate"
    elif val <= settings.SIMILARITY_THRESHOLD_HIGH:
        return "High"
    else:
        return "Very High"

def classify_prior_art_risk(highest_similarity_score: float) -> Dict[str, Any]:
    """
    Classify AI Prior-Art Relevance level based on the highest similarity score (0 - 100).
    Thresholds: 0-40% Low, 40-70% Moderate, 70-85% High, 85-100% Very High.
    """
    score = max(0.0, min(100.0, float(highest_similarity_score)))
    
    if score <= settings.SIMILARITY_THRESHOLD_LOW:
        level = "LOW"
        label = "Low Conceptual Overlap"
        color = "green"
        description = "Low conceptual similarity detected with existing documents in the database."
    elif score <= settings.SIMILARITY_THRESHOLD_MODERATE:
        level = "MODERATE"
        label = "Moderate Technical Overlap"
        color = "yellow"
        description = "Moderate overlap detected in technical concepts or system architecture."
    elif score <= settings.SIMILARITY_THRESHOLD_HIGH:
        level = "HIGH"
        label = "High Technical Overlap"
        color = "orange"
        description = "High overlap found in core technical methods and processing workflows."
    else:
        level = "VERY HIGH"
        label = "Very High Technical Overlap"
        color = "red"
        description = "Very high similarity across multiple technical dimensions and vector representations."

    return {
        "risk_level": level,
        "label": label,
        "color": color,
        "score": round(score, 1),
        "description": description,
        "disclaimer": RISK_DISCLAIMER
    }
