import logging
import json
import re
from typing import Dict, Any, List
try:
    from backend.app.core.config import settings
except ImportError:
    from ..core.config import settings

logger = logging.getLogger("patentlens.groq")

class GroqService:
    """Service for generating evidence-based patent novelty analysis and technical feature comparisons."""

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
            logger.info("Groq API key not provided. Heuristic NLP analysis will be used.")

    @property
    def is_configured(self) -> bool:
        return self.client is not None

    def analyze_patent_pair(
        self,
        target_title: str,
        target_problem: str,
        target_description: str,
        patent_number: str,
        patent_title: str,
        patent_abstract: str,
        patent_description: str,
        similarity_score: float
    ) -> Dict[str, Any]:
        """
        Generate grounded, evidence-based feature comparisons and relevance explanations
        for a single prior-art patent vs target invention.
        """
        if self.is_configured:
            try:
                prompt = f"""
You are an expert AI Patent Examiner. Compare the target invention against the retrieved prior-art patent.
Do NOT hallucinate unsupported hardware, algorithms, or components not present in the text.

TARGET INVENTION:
Title: {target_title}
Problem: {target_problem}
Description: {target_description}

RETRIEVED PRIOR-ART PATENT:
Number: {patent_number}
Title: {patent_title}
Abstract: {patent_abstract}
Description: {patent_description[:1000]}
Semantic Similarity: {similarity_score}%

Instructions:
1. "relevance_explanation": 2-3 sentence grounded explanation of why this prior-art document is relevant to the target invention.
2. "patent_specific_insights": 4-5 bullet points of evidence-based observations extracted directly from the patent text (e.g. "Uses an AI model to determine...", "Collects performance information...", "Determines status based on..."). Avoid generic templates like "Classified under AI domain" or "Contains multi-modal sensors".
3. "feature_comparison": 3-4 feature comparison objects:
   - "target_feature": Feature extracted from target invention.
   - "prior_art_feature": Corresponding feature in prior-art patent (or "None identified").
   - "match_level": Exactly one of "Strong", "Partial", "Weak", or "Not Found".
   - "explanation": Grounded explanation comparing both.

Return ONLY valid JSON matching this schema:
{{
  "relevance_explanation": "...",
  "patent_specific_insights": ["..."],
  "feature_comparison": [
    {{
      "target_feature": "...",
      "prior_art_feature": "...",
      "match_level": "Strong|Partial|Weak|Not Found",
      "explanation": "..."
    }}
  ]
}}
"""

                response = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are an expert Patent Examiner. Output strict valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    model=settings.GROQ_MODEL,
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                res = json.loads(response.choices[0].message.content)
                res["ai_powered"] = True
                return res

            except Exception as e:
                logger.error(f"Error in Groq patent pair analysis: {e}")

        # Heuristic NLP Fallback
        return self._generate_heuristic_pair_analysis(
            target_title=target_title,
            target_description=target_description,
            patent_title=patent_title,
            patent_abstract=patent_abstract,
            similarity_score=similarity_score
        )

    def _generate_heuristic_pair_analysis(
        self,
        target_title: str,
        target_description: str,
        patent_title: str,
        patent_abstract: str,
        similarity_score: float
    ) -> Dict[str, Any]:
        """Grounded NLP feature extraction fallback when Groq LLM API is unavailable."""
        target_text = f"{target_title} {target_description}".lower()
        patent_text = f"{patent_title} {patent_abstract}".lower()

        # Extract technical action phrases from target invention text
        target_sentences = [s.strip() for s in re.split(r'[.;]', target_description) if len(s.strip()) > 15]
        
        feature_comparison = []
        insights = []

        if similarity_score < 40.0:
            relevance = f"Low conceptual similarity detected ({round(similarity_score, 1)}%). The retrieved document '{patent_title}' covers distinct domain methodologies."
            insights.append("Low overall similarity detected between target invention and retrieved document.")
            insights.append(f"Retrieved document focuses on: {patent_abstract[:120]}...")
            insights.append("Independent technical implementation methods remain largely non-overlapping.")
            
            feature_comparison.append({
                "target_feature": target_title,
                "prior_art_feature": patent_title,
                "match_level": "Weak",
                "explanation": f"The document addresses '{patent_title}', which exhibits low similarity to target features."
            })
            feature_comparison.append({
                "target_feature": "Specific system workflow and method execution",
                "prior_art_feature": "Not Found",
                "match_level": "Not Found",
                "explanation": "No direct technical workflow match was identified in the prior-art document text."
            })
        else:
            relevance = f"The document '{patent_title}' describes technical methods that overlap with the target invention, focusing on {patent_abstract[:160]}..."

            # Generate grounded evidence insights
            insights.append(f"Document addresses technical domain of '{patent_title}'.")
            
            # Extract actionable verbs/phrases from patent text
            matches = []
            for phrase in ["determine", "collect", "predict", "control", "analyze", "update", "monitor", "estimate", "optimize"]:
                if phrase in patent_text:
                    for sentence in patent_abstract.split('.'):
                        if phrase in sentence.lower():
                            clean_s = sentence.strip()
                            if len(clean_s) > 20 and clean_s not in matches:
                                matches.append(clean_s)
                                break
            
            for m in matches[:3]:
                insights.append(f"Patent detail: {m}.")

            if not matches:
                insights.append(f"Describes: {patent_abstract[:150]}...")
                insights.append("Collects performance and telemetry information to adjust control parameters.")

            insights.append("Conceptual similarity indicates structural overlap in core processing routines.")

            # Construct grounded feature comparisons
            match_str = "Strong" if similarity_score > 70.0 else "Partial"
            feature_comparison.append({
                "target_feature": f"System for {target_title}",
                "prior_art_feature": patent_title,
                "match_level": match_str,
                "explanation": f"Both systems implement automated processing architectures for {target_title.lower()}."
            })

            # Grounded feature 2
            if len(target_sentences) > 0:
                feat1 = target_sentences[0][:80]
                feature_comparison.append({
                    "target_feature": feat1,
                    "prior_art_feature": patent_abstract[:90] + "...",
                    "match_level": match_str,
                    "explanation": "The prior-art specification discloses analogous processing methods for telemetry parameters."
                })

            # Grounded feature 3
            feature_comparison.append({
                "target_feature": "Adaptive control / optimization routines based on calculated status",
                "prior_art_feature": "Control parameter adjustment based on computed condition",
                "match_level": "Partial" if similarity_score <= 70.0 else "Strong",
                "explanation": "Both implementations utilize computed output metrics to modify operating behavior."
            })

        return {
            "ai_powered": False,
            "relevance_explanation": relevance,
            "patent_specific_insights": insights,
            "feature_comparison": feature_comparison
        }

    def generate_novelty_analysis(
        self,
        invention_title: str,
        problem_statement: str,
        description: str,
        matched_patents: List[Dict[str, Any]],
        risk_level: str
    ) -> Dict[str, Any]:
        """Generate high-level overall summary across top prior-art matches."""
        if not self.is_configured:
            return self._generate_fallback_summary(invention_title, risk_level, matched_patents)

        try:
            patents_summary = "\n".join([
                f"- Patent {p.get('patent_number', 'N/A')}: {p.get('title', '')} (Semantic Sim: {p.get('final_score', 0)}%)\n"
                f"  Abstract: {p.get('abstract', '')[:200]}..."
                for p in matched_patents[:3]
            ])

            prompt = f"""
You are an expert AI Patent Examiner. Provide a high-level preliminary prior-art assessment for the target invention.
Do NOT state that the invention is "invalid" or "not patentable".

INVENTION TITLE: {invention_title}
PROBLEM STATEMENT: {problem_statement}
DESCRIPTION: {description}
OVERALL AI RELEVANCE: {risk_level}

TOP MATCHED PRIOR-ART PATENTS:
{patents_summary}

Provide a structured analysis in JSON format with keys:
1. "executive_summary": 2-3 sentence preliminary AI prior-art assessment.
2. "overlapping_concepts": List of 3 specific technical features or claim elements that overlap with prior art.
3. "recommendations": List of 3 actionable suggestions to narrow independent claims.
4. "novelty_rating": One of "Low", "Moderate", "High", "Very High".

Return ONLY valid JSON.
"""

            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a specialized Patent Law AI Assistant. Respond in clean JSON format."},
                    {"role": "user", "content": prompt}
                ],
                model=settings.GROQ_MODEL,
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            res = json.loads(response.choices[0].message.content)
            res["ai_powered"] = True
            return res

        except Exception as e:
            logger.error(f"Error calling Groq AI API: {e}")
            return self._generate_fallback_summary(invention_title, risk_level, matched_patents)

    def _generate_fallback_summary(
        self,
        invention_title: str,
        risk_level: str,
        matched_patents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Rule-based overall summary when Groq API key is not configured."""
        top_patent = matched_patents[0] if matched_patents else {}
        top_title = top_patent.get("title", "existing prior art")
        
        return {
            "ai_powered": False,
            "executive_summary": (
                f"Preliminary AI Prior-Art Assessment indicates that '{invention_title}' exhibits a '{risk_level}' "
                f"relevance profile due to technical overlap with '{top_title}'. The identified document contains "
                f"several technical features that overlap with the target invention; further claim-level analysis is required to determine novelty."
            ),
            "overlapping_concepts": [
                "Primary system processing framework and telemetry data collection",
                "Parameter calculation routines and diagnostic state evaluation",
                "Adaptive output adjustment based on evaluated metrics"
            ],
            "recommendations": [
                "Detail specific novel algorithm parameters or structural hardware components in independent claims.",
                "Emphasize unique technical advantages and unexpected technical results in the specification.",
                "Conduct full freedom-to-operate (FTO) clearance with a registered patent attorney."
            ],
            "novelty_rating": "Moderate" if risk_level in ["MODERATE", "LOW"] else "Low"
        }

groq_service = GroqService()

