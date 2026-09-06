import logging
from typing import Dict, Any, List
from backend.app.core.config import settings

logger = logging.getLogger("patentlens.groq")

class GroqService:
    """Service for generating LLM patent novelty analysis and claim insights via Groq API."""

    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        api_key = settings.GROQ_API_KEY
        if api_key and not api_key.startswith("gsk_your_groq_api_key"):
            try:
                from groq import Groq
                self.client = Groq(api_key=api_key)
                logger.info("Groq AI Service initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize Groq SDK: {e}")
                self.client = None
        else:
            logger.info("Groq API key not provided or set to default placeholder. AI Insights will use heuristic summaries.")

    @property
    def is_configured(self) -> bool:
        return self.client is not None

    def generate_novelty_analysis(
        self,
        invention_title: str,
        problem_statement: str,
        description: str,
        matched_patents: List[Dict[str, Any]],
        risk_level: str
    ) -> Dict[str, Any]:
        """
        Generate AI-driven patent novelty assessment & claim comparison using Groq LLM (Llama 3.3).
        Falls back to rule-based analysis if Groq is not configured.
        """
        if not self.is_configured:
            return self._generate_fallback_analysis(invention_title, risk_level, matched_patents)

        try:
            patents_summary = "\n".join([
                f"- Patent {p.get('patent_number', 'N/A')}: {p.get('title', '')} (Similarity: {p.get('final_score', 0)}%)\n"
                f"  Abstract: {p.get('abstract', '')[:200]}..."
                for p in matched_patents[:3]
            ])

            prompt = f"""
You are an expert Patent Attorney and AI Patent Examiner. Analyze the following invention against top prior-art patents.

INVENTION TITLE: {invention_title}
PROBLEM STATEMENT: {problem_statement}
DESCRIPTION: {description}
OVERALL RISK LEVEL: {risk_level}

TOP MATCHED PRIOR-ART PATENTS:
{patents_summary}

Provide a structured analysis in JSON format with the following keys:
1. "executive_summary": A concise 2-3 sentence legal assessment of patentability and overlap.
2. "overlapping_concepts": A list of 3 specific technical features or claim elements that overlap with prior art.
3. "recommendations": A list of 3 actionable suggestions to modify or rewrite the invention claims to avoid patent infringement.
4. "novelty_rating": A rating from "Low", "Moderate", "High", to "Very High".

Return ONLY valid JSON.
"""

            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a specialized Patent Law & Prior-Art AI Assistant. Respond in clean JSON format."},
                    {"role": "user", "content": prompt}
                ],
                model=settings.GROQ_MODEL,
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            import json
            result_json = json.loads(response.choices[0].message.content)
            result_json["ai_powered"] = True
            return result_json

        except Exception as e:
            logger.error(f"Error calling Groq AI API: {e}")
            return self._generate_fallback_analysis(invention_title, risk_level, matched_patents)

    def _generate_fallback_analysis(
        self,
        invention_title: str,
        risk_level: str,
        matched_patents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Rule-based fallback summary when Groq API key is not configured."""
        top_patent = matched_patents[0] if matched_patents else {}
        top_title = top_patent.get("title", "existing prior art")
        
        return {
            "ai_powered": False,
            "executive_summary": (
                f"Based on hybrid semantic and keyword analysis, '{invention_title}' exhibits a '{risk_level}' "
                f"risk profile due to overlap with {top_title}. Further claim narrowing is recommended before filing."
            ),
            "overlapping_concepts": [
                "Primary system architecture and method workflow",
                "Domain-specific data processing steps",
                "Automated feature classification routines"
            ],
            "recommendations": [
                "Detail specific novel hardware/software implementation algorithms in independent claims.",
                "Emphasize unique technical advantages in the problem statement section.",
                "Conduct full freedom-to-operate (FTO) clearance with a registered patent practitioner."
            ],
            "novelty_rating": "Moderate" if risk_level in ["MODERATE", "LOW"] else "Low"
        }

groq_service = GroqService()
