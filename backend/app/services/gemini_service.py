import logging
import json
import re
import httpx
from typing import Dict, Any, List, Optional
try:
    from backend.app.core.config import settings
except ImportError:
    from ..core.config import settings

logger = logging.getLogger("patentlens.gemini")

class GeminiService:
    """Service for generating evidence-based patent claim examination using Google's official google-genai SDK (gemini-2.5-flash)."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL or "gemini-2.0-flash"
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        api_key = settings.GEMINI_API_KEY
        if api_key and len(api_key.strip()) > 10 and not api_key.startswith("your_"):
            self.api_key = api_key.strip()
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Google GenAI official SDK client initialized for model '{self.model_name}'.")
            except Exception as e:
                logger.warning(f"Could not load google-genai SDK client: {e}. Falling back to REST API.")
                self.client = None
        else:
            logger.info("Gemini API key not configured or placeholder used. Heuristic NLP analysis will be used.")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10 and not self.api_key.startswith("your_"))

    def analyze_invention(
        self,
        title: str,
        problem_statement: str,
        description: str,
        keywords: Optional[List[str]] = None,
        domain: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze user invention using Gemini 2.5 Flash to extract structured technical features,
        distinctive concepts, alternative terminology, targeted search queries, and candidate CPC classes.
        Filters out generic noise terms ('system', 'device', 'technology', 'signal', 'AI', 'electronics').
        """
        title = title or ""
        problem_statement = problem_statement or ""
        description = description or ""
        keywords = keywords or []
        domain = domain or "Technology"

        GENERIC_NOISE = {
            "system", "device", "technology", "signal", "ai", "electronics",
            "method", "apparatus", "process", "mechanism", "unit", "module",
            "component", "feature", "data", "information"
        }

        if self.is_configured:
            system_prompt = "You are a Senior Patent Examiner and IP Analyst. Return strict valid JSON only."
            user_prompt = f"""
Analyze the target invention disclosure and decompose it into structured technical concepts for prior-art retrieval.

RULES:
1. Extract "technical_features": Specific engineering components, structural elements, circuits, algorithms, or physical arrangements. Avoid single generic words like "system", "device", "technology", "signal", "AI", "electronics".
2. Extract "distinctive_concepts": Highly novel/unusual technical limitations or combinations.
3. Extract "alternative_terms": Synonyms or technical equivalents used in older or international patent literature.
4. Construct 3-5 "search_queries": Targeted multi-word technical search phrases combining distinctive concepts (e.g. "three-terminal semiconductor junction", "emitter collector base current control"). DO NOT create single broad queries like "semiconductor device".
5. Suggest 2-4 "cpc_candidates": Relevant CPC classification codes (e.g. "H01L29/66", "G06F18/20").
6. Identify the primary technical "domain".

INVENTION DISCLOSURE:
Title: {title}
Domain: {domain}
Problem: {problem_statement}
Description: {description}
Keywords: {', '.join(keywords)}

Return ONLY valid JSON matching this exact structure:
{{
  "technical_features": ["three-terminal semiconductor", "pn junction barrier"],
  "distinctive_concepts": ["current control via base bias voltage"],
  "alternative_terms": ["bipolar transistor", "triode semiconductor"],
  "search_queries": [
    "three-terminal semiconductor junction",
    "emitter collector base current control"
  ],
  "domain": "Electronics",
  "cpc_candidates": ["H01L29/66", "H01L29/73"]
}}
"""
            try:
                if self.client is not None:
                    from google.genai import types
                    logger.info("Extracting invention technical features via Gemini SDK...")
                    res = self.client.models.generate_content(
                        model=self.model_name,
                        contents=f"{system_prompt}\n\n{user_prompt}",
                        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1)
                    )
                    if res and res.text:
                        parsed = json.loads(res.text)
                        return self._clean_invention_analysis(parsed, title, keywords, domain)

                # REST API Fallback
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                    "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
                }
                with httpx.Client(timeout=15.0) as http_client:
                    response = http_client.post(url, json=payload)
                    if response.status_code == 200:
                        text_content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(text_content)
                        return self._clean_invention_analysis(parsed, title, keywords, domain)
            except Exception as e:
                logger.error(f"[GEMINI] Error in analyze_invention: {e}")

        # Heuristic NLP Fallback
        return self._heuristic_invention_analysis(title, problem_statement, description, keywords, domain)

    def _clean_invention_analysis(
        self,
        parsed: Dict[str, Any],
        title: str,
        keywords: List[str],
        domain: str
    ) -> Dict[str, Any]:
        GENERIC_NOISE = {
            "system", "device", "technology", "signal", "ai", "electronics",
            "method", "apparatus", "process", "mechanism", "unit", "module"
        }
        
        raw_feats = parsed.get("technical_features", [])
        clean_feats = [f for f in raw_feats if str(f).strip().lower() not in GENERIC_NOISE]

        raw_queries = parsed.get("search_queries", [])
        clean_queries = []
        for q in raw_queries:
            q_str = str(q).strip()
            if q_str and q_str.lower() not in GENERIC_NOISE and len(q_str.split()) >= 2:
                clean_queries.append(q_str)

        if not clean_queries:
            clean_queries = [f"{title} {k}" for k in (keywords[:3] or [domain])]

        return {
            "technical_features": clean_feats or [title],
            "distinctive_concepts": parsed.get("distinctive_concepts", []),
            "alternative_terms": parsed.get("alternative_terms", []),
            "search_queries": clean_queries,
            "domain": parsed.get("domain") or domain,
            "cpc_candidates": parsed.get("cpc_candidates", [])
        }

    def _heuristic_invention_analysis(
        self,
        title: str,
        problem_statement: str,
        description: str,
        keywords: List[str],
        domain: str
    ) -> Dict[str, Any]:
        from backend.ml.keyword_extractor import extract_atomic_technical_features
        full_text = f"{title} {problem_statement} {description}"
        atomic_feats = extract_atomic_technical_features(full_text, top_n=8)
        
        search_queries = []
        if len(atomic_feats) >= 2:
            search_queries.append(f"{atomic_feats[0]} {atomic_feats[1]}")
        if len(atomic_feats) >= 4:
            search_queries.append(f"{atomic_feats[2]} {atomic_feats[3]}")
        if title:
            search_queries.append(title)

        return {
            "technical_features": atomic_feats or [title],
            "distinctive_concepts": [f for f in atomic_feats if len(f.split()) >= 2],
            "alternative_terms": keywords or [],
            "search_queries": search_queries,
            "domain": domain or "Technology",
            "cpc_candidates": []
        }

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
        Decompose invention claims into atomic technical limitations and perform rigorous 
        feature-by-feature prior-art comparison using Gemini 2.5 Flash SDK.
        """
        target_title = target_title or ""
        target_problem = target_problem or ""
        target_description = target_description or ""
        patent_number = patent_number or ""
        patent_title = patent_title or ""
        patent_abstract = patent_abstract or ""
        patent_description = patent_description or ""

        if self.is_configured:
            system_prompt = "You are a Senior Patent Examiner conducting strict prior-art claim analysis. Output strict valid JSON only."
            user_prompt = f"""
You are a Senior Patent Examiner conducting a rigorous prior-art anticipation and feature disclosure comparison.

EXAMINATION RULES:
1. Break the target invention claim/description into atomic technical limitations/elements.
2. Compare EVERY limitation against the supplied prior-art document ({patent_number}: '{patent_title}').
3. Classify EVERY limitation as exactly ONE of:
   - EXPLICIT: Explicitly disclosed in prior-art text.
   - INHERENT: Inherent technical feature necessarily present in the disclosed prior-art structure.
   - PARTIAL: Partially disclosed or broadly suggested, missing structural details.
   - NOT_DISCLOSED: Completely absent from the prior-art document.
4. Provide explicit supporting quotes/evidence directly from the prior-art text for every classification. If evidence is insufficient, set evidence to "INSUFFICIENT_EVIDENCE".
5. Identify all missing technical features in "missing_elements".
6. Determine whether THIS SINGLE PRIOR-ART DOCUMENT discloses ALL essential limitations ("single_document_anticipation": {{"found": true/false, "reason": "string"}}).
7. NEVER combine multiple documents when determining single-document anticipation.
8. Similar terminology MUST NOT automatically be treated as identical unless structural identity is shown in prior-art text.
9. Calculate "technical_feature_coverage" as the percentage (0-100%) of target claim limitations classified as EXPLICIT, INHERENT, or PARTIAL.
10. Calculate "confidence" as an integer (0-100) representing your confidence in the evidence analysis.
11. Do NOT invent claims, dates, inventors, or prior-art disclosure. Do not make final legal conclusions of patentability.

TARGET INVENTION:
Title: {target_title}
Problem: {target_problem}
Description: {target_description}

RETRIEVED PRIOR-ART PATENT:
Patent Number: {patent_number}
Title: {patent_title}
Abstract: {patent_abstract}
Description: {patent_description[:1500]}
SBERT Vector Retrieval Score: {similarity_score}%

Return ONLY valid JSON matching this exact structure:
{{
  "overall_result": "ANTICIPATED | PARTIALLY_DISCLOSED | NOT_ANTICIPATED | INSUFFICIENT_EVIDENCE",
  "confidence": 87,
  "technical_feature_coverage": 25.0,
  "claim_elements": [
    {{
      "element": "Atomic technical limitation name",
      "status": "EXPLICIT | INHERENT | PARTIAL | NOT_DISCLOSED",
      "evidence": "Direct quote or explicit evidence from prior-art text",
      "source_document": "{patent_number}"
    }}
  ],
  "single_document_anticipation": {{
    "found": false,
    "reason": "Detailed explanation of single-document disclosure assessment."
  }},
  "missing_elements": [
    "Specific missing technical element name"
  ],
  "reasoning": "Comprehensive examination explanation.",
  "relevance_explanation": "2-sentence relevance summary.",
  "overlap_summary": "2-sentence feature disclosure summary.",
  "patent_specific_insights": [
    "Key technical insight regarding prior-art specification."
  ],
  "technical_features": [
    "wireless power transfer",
    "impedance measurement"
  ],
  "distinctive_features": [
    "foreign object detection"
  ],
  "matched_features": [
    {{
      "feature": "impedance measurement",
      "match_level": "strong",
      "evidence": "Discloses impedance measurement circuit."
    }}
  ],
  "unmatched_features": [
    "temperature compensation"
  ],
  "feature_comparison": [
    {{
      "target_feature": "foreign object detection",
      "prior_art_feature": "metallic debris detection circuit",
      "match_level": "Strong",
      "explanation": "Both systems disclose sensor routines for detecting obstacles."
    }}
  ]
}}
"""

            try:
                # 1. Try Official google-genai SDK if available
                if self.client is not None:
                    from google.genai import types
                    logger.info("Executing Gemini 2.5 Flash analysis via official google-genai SDK...")
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=f"{system_prompt}\n\n{user_prompt}",
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )
                    if response and response.text:
                        parsed = json.loads(response.text)
                        parsed["ai_powered"] = True
                        parsed["model_used"] = self.model_name
                        parsed["provider"] = "gemini"
                        return self._normalize_parsed_response(parsed)

                # 2. Fallback to direct HTTP REST API call if SDK client is uninitialized
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                    "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
                }
                with httpx.Client(timeout=15.0) as http_client:
                    res = http_client.post(url, json=payload)
                    if res.status_code == 200:
                        text_content = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(text_content)
                        parsed["ai_powered"] = True
                        parsed["model_used"] = self.model_name
                        parsed["provider"] = "gemini"
                        return self._normalize_parsed_response(parsed)

            except Exception as e:
                logger.error(f"Error in Gemini patent pair analysis: {e}")

        # Heuristic NLP Fallback when API key is offline or unconfigured
        return self._normalize_parsed_response(self._generate_heuristic_pair_analysis(
            target_title=target_title,
            target_description=target_description,
            patent_number=patent_number,
            patent_title=patent_title,
            patent_abstract=patent_abstract,
            similarity_score=similarity_score
        ))

    def _generate_heuristic_pair_analysis(
        self,
        target_title: str,
        target_description: str,
        patent_number: str,
        patent_title: str,
        patent_abstract: str,
        similarity_score: float,
        patent_description: str = ""
    ) -> Dict[str, Any]:
        """Grounded NLP claim decomposition fallback when LLM API is unavailable."""
        from backend.ml.keyword_extractor import extract_atomic_technical_features

        target_text = f"{target_title} {target_description}".lower()
        patent_text = f"{patent_title} {patent_abstract} {patent_description}".lower()

        target_tech_features = extract_atomic_technical_features(target_text, top_n=9)
        if not target_tech_features:
            target_tech_features = [target_title.title()]

        claim_elements = []
        matched_feats = []
        unmatched_feats = []
        matched_feature_objects = []
        feature_comparison = []

        for feat in target_tech_features:
            feat_lower = feat.lower()
            pattern = r'\b' + re.escape(feat_lower) + r'\b' if len(feat_lower.split()) == 1 else re.escape(feat_lower)
            if re.search(pattern, patent_text):
                matched_feats.append(feat)
                matched_feature_objects.append({
                    "feature": feat,
                    "match_level": "strong" if similarity_score > 60.0 else "partial",
                    "evidence": f"Discloses '{feat}' in patent specification ('{patent_title}')."
                })
                claim_elements.append({
                    "element": feat,
                    "status": "EXPLICIT" if similarity_score > 60.0 else "PARTIAL",
                    "evidence": f"Explicitly discloses {feat} in patent '{patent_title}'.",
                    "source_document": patent_number or patent_title
                })
                feature_comparison.append({
                    "target_feature": feat,
                    "prior_art_feature": f"Discloses {feat} in specification",
                    "match_level": "Strong" if similarity_score > 60.0 else "Partial",
                    "explanation": f"Both specifications disclose {feat} structures.",
                    "evidence_quote": f"Explicit disclosure of {feat} in patent document text.",
                    "confidence": 92.0 if similarity_score > 60.0 else 78.0
                })
            else:
                unmatched_feats.append(feat)
                claim_elements.append({
                    "element": feat,
                    "status": "NOT_DISCLOSED",
                    "evidence": f"Feature '{feat}' is not disclosed in '{patent_title}'.",
                    "source_document": patent_number or patent_title
                })

        total_elems = len(target_tech_features)
        matched_count = len(matched_feats)
        coverage_pct = round((matched_count / total_elems) * 100.0, 1) if total_elems > 0 else 0.0

        single_doc_anticipation = {
            "found": coverage_pct == 100.0 and total_elems > 1,
            "reason": (
                f"Single document '{patent_title}' discloses {matched_count} out of {total_elems} essential claim limitations. "
                + ("All essential limitations are disclosed." if coverage_pct == 100.0 else "Missing essential limitations prevents single-document anticipation.")
            )
        }

        if coverage_pct >= 80.0:
            overall_result = "ANTICIPATED"
        elif coverage_pct >= 35.0:
            overall_result = "PARTIALLY_DISCLOSED"
        else:
            overall_result = "NOT_ANTICIPATED"

        if matched_feats:
            relevance = f"This prior art is relevant because it explicitly discloses {matched_count}/{total_elems} key technical features of '{target_title}': {', '.join(matched_feats[:4])}."
            overlap_summary = f"Direct technical feature match identified across {', '.join(matched_feats[:3])}."
        else:
            relevance = f"Document '{patent_title}' has low technical relevance. Zero matching technical features were detected in prior art text."
            overlap_summary = "Zero direct technical feature overlap detected between target invention and prior art document."

        return {
            "ai_powered": False,
            "model_used": "Heuristic-NLP",
            "provider": "heuristic",
            "overall_result": overall_result,
            "confidence": 85 if matched_feats else 40,
            "technical_feature_coverage": coverage_pct,
            "claim_elements": claim_elements,
            "single_document_anticipation": single_doc_anticipation,
            "missing_elements": unmatched_feats,
            "reasoning": f"Grounded analysis evaluated {total_elems} claim limitations against prior-art document.",
            "technical_features": target_tech_features,
            "distinctive_features": [f for f in target_tech_features if len(f.split()) >= 2],
            "matched_features": matched_feature_objects,
            "unmatched_features": unmatched_feats,
            "overlap_summary": overlap_summary,
            "relevance_explanation": relevance,
            "patent_specific_insights": [f"Prior-art document addresses '{patent_title}'.", f"Feature disclosure coverage: {coverage_pct}% ({matched_count}/{total_elems} matched)."],
            "feature_comparison": feature_comparison or [{
                "target_feature": target_title,
                "prior_art_feature": patent_title,
                "match_level": "Not Found",
                "explanation": f"Zero matching technical features found in '{patent_title}'."
            }]
        }

    def generate_novelty_analysis(
        self,
        invention_title: str,
        problem_statement: str,
        description: str,
        matched_patents: List[Dict[str, Any]],
        risk_level: str
    ) -> Dict[str, Any]:
        """Generate high-level overall summary across top prior-art matches using Gemini 2.5 Flash."""
        if not self.is_configured:
            return self._generate_fallback_summary(invention_title, risk_level, matched_patents)

        try:
            patents_summary = "\n".join([
                f"- Patent {p.get('patent_number', 'N/A')}: {p.get('title', '')} (SBERT Sim: {p.get('final_score', 0)}%)\n"
                f"  Abstract: {p.get('abstract', '')[:200]}..."
                for p in matched_patents[:3]
            ])

            user_prompt = f"""
You are a Senior AI Patent Examiner. Provide a high-level preliminary prior-art assessment for the target invention using Gemini 2.5 Flash.
Do NOT state that the invention is "invalid" or "not patentable".

INVENTION TITLE: {invention_title}
PROBLEM STATEMENT: {problem_statement}
DESCRIPTION: {description}
OVERALL RELEVANCE PROFILE: {risk_level}

TOP MATCHED PRIOR-ART PATENTS:
{patents_summary}

Provide a structured analysis in JSON format with keys:
1. "executive_summary": 2-3 sentence preliminary AI prior-art assessment.
2. "overlapping_concepts": List of 3 specific technical features or claim elements that overlap with prior art.
3. "recommendations": List of 3 actionable suggestions to narrow independent claims.
4. "novelty_rating": One of "Low", "Moderate", "High", "Very High".

Return ONLY valid JSON.
"""

            if self.client is not None:
                from google.genai import types
                res = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2)
                )
                if res and res.text:
                    parsed = json.loads(res.text)
                    parsed["ai_powered"] = True
                    parsed["model_used"] = self.model_name
                    parsed["provider"] = "gemini"
                    return parsed

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
            }
            with httpx.Client(timeout=15.0) as http_client:
                response = http_client.post(url, json=payload)
                if response.status_code == 200:
                    text_content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(text_content)
                    parsed["ai_powered"] = True
                    parsed["model_used"] = self.model_name
                    parsed["provider"] = "gemini"
                    return parsed

        except Exception as e:
            logger.error(f"Error in Gemini novelty analysis: {e}")

        return self._generate_fallback_summary(invention_title, risk_level, matched_patents)

    def _generate_fallback_summary(
        self,
        invention_title: str,
        risk_level: str,
        matched_patents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Rule-based overall summary when LLM API is unavailable."""
        top_patent = matched_patents[0] if matched_patents else {}
        top_title = top_patent.get("title", "existing prior art")
        
        return {
            "ai_powered": False,
            "model_used": "Heuristic-NLP",
            "provider": "heuristic",
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

    def _normalize_parsed_response(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parsed JSON schema so single_document_anticipation is 'YES'/'NO' and claim_elements has standard keys."""
        sda = parsed.get("single_document_anticipation")
        if isinstance(sda, dict):
            parsed["single_document_anticipation"] = "YES" if sda.get("found") else "NO"
        elif isinstance(sda, str):
            parsed["single_document_anticipation"] = "YES" if "YES" in sda.upper() or "TRUE" in sda.upper() else "NO"
        elif isinstance(sda, bool):
            parsed["single_document_anticipation"] = "YES" if sda else "NO"
        else:
            parsed["single_document_anticipation"] = "NO"

        raw_claims = parsed.get("claim_elements", [])
        norm_claims = []
        for idx, c in enumerate(raw_claims, start=1):
            if isinstance(c, dict):
                lim_num = c.get("limitation_number") or idx
                elem_text = c.get("element_text") or c.get("element") or c.get("limitation") or ""
                status = c.get("status") or "PARTIAL"
                status_str = str(status).upper()
                if "EXPLICIT" in status_str:
                    status = "EXPLICIT"
                elif "INHERENT" in status_str:
                    status = "INHERENT"
                elif "NOT" in status_str or "MISSING" in status_str:
                    status = "NOT_DISCLOSED"
                else:
                    status = "PARTIAL"
                quote = c.get("evidence_quote") or c.get("evidence") or ""
                expl = c.get("explanation") or c.get("reasoning") or ""
                norm_claims.append({
                    "limitation_number": lim_num,
                    "element_text": elem_text,
                    "status": status,
                    "evidence_quote": quote,
                    "explanation": expl
                })
        parsed["claim_elements"] = norm_claims
        return parsed


gemini_service = GeminiService()
