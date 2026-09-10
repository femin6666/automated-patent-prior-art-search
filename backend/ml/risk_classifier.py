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
    """Return text label for similarity score using standardized thresholds (0-39 Low, 40-69 Moderate, 70-84 High, 85-100 Very High)."""
    val = max(0.0, min(100.0, float(score)))
    if val < 40.0:
        return "Low"
    elif val < 70.0:
        return "Moderate"
    elif val < 85.0:
        return "High"
    else:
        return "Very High"

def classify_prior_art_risk(highest_similarity_score: float) -> Dict[str, Any]:
    """
    Classify AI Prior-Art Relevance level based on the highest deterministic similarity score.
    Thresholds:
      0-39%: LOW Relevance / Low Risk
     40-69%: MODERATE Relevance / Moderate Risk
     70-84%: HIGH Relevance / High Risk
     85-100%: VERY HIGH Relevance / Very High Risk
    """
    score = max(0.0, min(100.0, float(highest_similarity_score)))
    
    if score < 40.0:
        level = "LOW"
        label = "Low Technical Relevance"
        color = "green"
        description = "Low prior-art relevance detected. Target invention shows low technical feature overlap with retrieved patents."
    elif score < 70.0:
        level = "MODERATE"
        label = "Moderate Technical Relevance"
        color = "yellow"
        description = "Moderate technical relevance detected. Overlap identified in general concepts; claim-level limitation analysis recommended."
    elif score < 85.0:
        level = "HIGH"
        label = "High Technical Relevance"
        color = "orange"
        description = "High technical relevance detected. Strong overlap in core technical mechanisms and component disclosures."
    else:
        level = "VERY HIGH"
        label = "Very High Technical Relevance"
        color = "red"
        description = "Very high technical relevance detected. Prior-art documents explicitly disclose multiple core technical limitations."

    return {
        "risk_level": level,
        "label": label,
        "color": color,
        "score": round(score, 1),
        "description": description,
        "disclaimer": RISK_DISCLAIMER
    }
