from typing import Dict, Any

RISK_DISCLAIMER = (
    "This classification is generated using AI similarity analysis "
    "and is not a legal patentability determination."
)

def classify_prior_art_risk(highest_similarity_score: float) -> Dict[str, Any]:
    """
    Classify novelty / prior-art risk level based on the highest hybrid similarity score (0 - 100).
    """
    score = max(0.0, min(100.0, float(highest_similarity_score)))
    
    if score <= 40.0:
        level = "LOW"
        label = "Potentially Distinct"
        color = "green"
        description = "Low overall similarity detected with existing documents in the dataset."
    elif score <= 65.0:
        level = "MODERATE"
        label = "Further Review Recommended"
        color = "yellow"
        description = "Moderate overlap detected in technical concepts or terminology."
    elif score <= 80.0:
        level = "HIGH"
        label = "Strong Similarities Found"
        color = "orange"
        description = "Significant overlap found in core technical methods or domain concepts."
    else:
        level = "VERY HIGH"
        label = "Potentially Significant Prior Art"
        color = "red"
        description = "High similarity across multiple technical dimensions and vector representations."

    return {
        "risk_level": level,
        "label": label,
        "color": color,
        "score": round(score, 1),
        "description": description,
        "disclaimer": RISK_DISCLAIMER
    }
