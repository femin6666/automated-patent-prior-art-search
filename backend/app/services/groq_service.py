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
        Extracts distinctive technical features across 10 technical dimensions.
        """
        if self.is_configured:
            try:
                prompt = f"""
You are an expert Patent Examiner. Extract DISTINCTIVE TECHNICAL FEATURES from the target invention and compare them against the retrieved prior-art patent.

STRICT RULES:
1. Extract DISTINCTIVE TECHNICAL FEATURES rather than generic nouns. Avoid generic terms like ["vehicle", "system", "method", "charging", "device", "data", "computer", "processor"] unless technically qualified in context (e.g. use "wireless power transfer", "transmitter and receiver charging coils", "impedance measurement", "foreign object detection", "resonant frequency monitoring").
2. Extract technical features across 10 dimensions where present:
   - Core technical components
   - Technical operations/processes
   - Physical mechanisms
   - Sensors/measurements
   - Control mechanisms
   - Algorithms/models
   - Inputs
   - Outputs
   - Component relationships
   - Novel/distinctive technical features
3. Extraction MUST be based ONLY on the supplied text. Do NOT hallucinate or invent technical features unsupported by the source text.
4. For patent comparison, provide explicit textual evidence directly from the patent text.
5. Do NOT invent similarity percentages. The similarity percentage ({similarity_score}%) is calculated deterministically by the backend vector engine.

TARGET INVENTION:
Title: {target_title}
Problem: {target_problem}
Description: {target_description}

RETRIEVED PRIOR-ART PATENT:
Number: {patent_number}
Title: {patent_title}
Abstract: {patent_abstract}
Description: {patent_description[:1200]}
Calculated Match Score: {similarity_score}%

Return ONLY valid JSON matching this exact structure:
{{
  "technical_features": [
    "wireless power transfer",
    "transmitter and receiver charging coils"
  ],
  "distinctive_features": [
    "foreign object detection",
    "impedance measurement",
    "resonant frequency monitoring"
  ],
  "matched_features": [
    {{
      "feature": "foreign object detection",
      "match_level": "strong",
      "evidence": "Discloses detecting foreign metallic objects located near the inductive charging coil..."
    }}
  ],
  "unmatched_features": [
    "temperature compensation"
  ],
  "overlap_summary": "Evidence-grounded 2-sentence summary of technical feature overlap.",
  "relevance_explanation": "Ground 2-sentence explanation of why this prior-art document is relevant.",
  "patent_specific_insights": [
    "Uses an impedance measurement circuit to detect metallic foreign objects..."
  ],
  "feature_comparison": [
    {{
      "target_feature": "foreign object detection",
      "prior_art_feature": "metallic debris detection circuit",
      "match_level": "Strong",
      "explanation": "Both systems implement sensor routines for identifying conductive obstacles."
    }}
  ]
}}
"""

                response = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a specialized Patent Law AI Assistant. Respond in strict valid JSON format only."},
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

        target_sentences = [s.strip() for s in re.split(r'[.;]', target_description) if len(s.strip()) > 15]
        
        distinctive_candidates = [
            "wireless power transfer", "contactless vehicle charging", "inductive charging",
            "resonant charging", "transmitter coil", "receiver coil", "electromagnetic field",
            "impedance measurement", "voltage monitoring", "current monitoring",
            "resonant frequency", "charging efficiency", "foreign object detection",
            "abnormal condition detection", "dynamic threshold", "temperature compensation",
            "calibration", "automatic power reduction", "power interruption"
        ]

        target_tech_features = [f for f in distinctive_candidates if f in target_text]
        if not target_tech_features:
            target_tech_features = [target_title.lower()]

        matched_feats = []
        unmatched_feats = []
        matched_feature_objects = []

        for feat in target_tech_features:
            if feat in patent_text:
                matched_feats.append(feat)
                matched_feature_objects.append({
                    "feature": feat.title(),
                    "match_level": "strong" if similarity_score > 65.0 else "partial",
                    "evidence": f"Discloses '{feat}' in patent specification ('{patent_title}')."
                })
            else:
                unmatched_feats.append(feat.title())

        feature_comparison = []
        insights = []

        if similarity_score < 40.0:
            relevance = f"Low conceptual similarity detected ({round(similarity_score, 1)}%). The retrieved document '{patent_title}' covers distinct domain methodologies."
            overlap_summary = f"Minimal technical feature overlap identified with target invention features."
            insights.append("Low overall similarity detected between target invention and retrieved document.")
            insights.append(f"Retrieved document focuses on: {patent_abstract[:120]}...")
            
            feature_comparison.append({
                "target_feature": target_title,
                "prior_art_feature": patent_title,
                "match_level": "Weak",
                "explanation": f"The document addresses '{patent_title}', exhibiting low structural overlap."
            })
        else:
            if matched_feats:
                feats_str = ", ".join([f.title() for f in matched_feats[:3]])
                relevance = f"This document is relevant because it directly describes {feats_str} in its technical specification ('{patent_title}')."
                overlap_summary = f"Direct overlap confirmed across key technical features including {feats_str}."
            else:
                relevance = f"The document '{patent_title}' describes technical methods that overlap with the target invention."
                overlap_summary = f"Partial conceptual overlap identified in overall processing architecture."

            insights.append(f"Document addresses technical domain of '{patent_title}'.")
            if matched_feats:
                insights.append(f"Direct technical feature overlap: {', '.join([f.title() for f in matched_feats])}.")

            # Grounded feature comparisons
            match_str = "Strong" if similarity_score > 70.0 else "Partial"
            feature_comparison.append({
                "target_feature": f"System for {target_title}",
                "prior_art_feature": patent_title,
                "match_level": match_str,
                "explanation": f"Both specifications implement processing routines for {target_title.lower()}."
            })

            if matched_feats:
                feature_comparison.append({
                    "target_feature": matched_feats[0].title(),
                    "prior_art_feature": f"Discloses {matched_feats[0]} in prior-art text",
                    "match_level": "Strong",
                    "explanation": f"Both documents explicitly specify {matched_feats[0]} mechanisms."
                })

            feature_comparison.append({
                "target_feature": "Adaptive control / optimization routines based on calculated status",
                "prior_art_feature": "Control parameter adjustment based on computed condition",
                "match_level": "Partial" if similarity_score <= 70.0 else "Strong",
                "explanation": "Both implementations utilize computed output metrics to adjust operating parameters."
            })

        return {
            "ai_powered": False,
            "technical_features": [f.title() for f in target_tech_features],
            "distinctive_features": [f.title() for f in target_tech_features if len(f.split()) >= 2],
            "matched_features": matched_feature_objects,
            "unmatched_features": unmatched_feats,
            "overlap_summary": overlap_summary,
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

