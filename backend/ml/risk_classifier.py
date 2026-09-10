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
    """Return text label for similarity score using Phase 22 thresholds (0-29 Low, 30-49 Moderate, 50-69 High, 70-100 Very High)."""
    val = max(0.0, min(100.0, float(score)))
    if val < 30.0:
        return "Low"
    elif val < 50.0:
        return "Moderate"
    elif val < 70.0:
        return "High"
    else:
        return "Very High"

def classify_prior_art_risk(highest_similarity_score: float) -> Dict[str, Any]:
    """
    Classify AI Prior-Art Technical Relevance level based on the single canonical score.
    Phase 22 Thresholds:
       0–29%: LOW TECHNICAL RELEVANCE
      30–49%: MODERATE TECHNICAL RELEVANCE
      50–69%: HIGH TECHNICAL RELEVANCE
      70–100%: VERY HIGH TECHNICAL RELEVANCE
    """
    score = max(0.0, min(100.0, float(highest_similarity_score)))
    
    if score < 30.0:
        level = "LOW"
        label = "Low Technical Relevance"
        color = "green"
        description = "Low prior-art technical relevance detected. Target invention shows low technical feature overlap with retrieved patents."
    elif score < 50.0:
        level = "MODERATE"
        label = "Moderate Technical Relevance"
        color = "yellow"
        description = "Moderate technical relevance detected. Overlap identified in general concepts; claim-level limitation analysis recommended."
    elif score < 70.0:
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
