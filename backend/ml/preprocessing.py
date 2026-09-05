import re

def clean_text(text: str) -> str:
    """Clean and normalize raw text while preserving technical terminology."""
    if not text:
        return ""
    # Normalize multiple whitespace, tabs, and newlines
    normalized = re.sub(r'\s+', ' ', text).strip()
    return normalized

def validate_invention_input(title: str, description: str, min_desc_length: int = 20) -> dict:
    """Validate invention input parameters."""
    cleaned_title = clean_text(title)
    cleaned_desc = clean_text(description)
    
    if not cleaned_title:
        return {"valid": False, "error": "Invention title cannot be empty."}
    if len(cleaned_desc) < min_desc_length:
        return {
            "valid": False,
            "error": f"Invention description must be at least {min_desc_length} characters long for accurate AI processing."
        }
        
    return {"valid": True, "title": cleaned_title, "description": cleaned_desc}

def prepare_combined_text(title: str, problem_statement: str, description: str, keywords: list = None) -> str:
    """
    Combine invention fields into a rich semantic string for SBERT embedding generation.
    Preserves all domain-specific terminology.
    """
    parts = []
    if title:
        parts.append(f"Title: {clean_text(title)}")
    if problem_statement:
        parts.append(f"Problem Solved: {clean_text(problem_statement)}")
    if description:
        parts.append(f"Technical Description: {clean_text(description)}")
    if keywords and isinstance(keywords, list):
        kw_str = ", ".join([clean_text(k) for k in keywords if k])
        if kw_str:
            parts.append(f"Keywords: {kw_str}")
            
    return " | ".join(parts)
