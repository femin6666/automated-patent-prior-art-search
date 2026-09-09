import logging
import json
import time
import httpx
from typing import List, Dict, Any, Optional

try:
    from backend.app.core.config import settings
except ImportError:
    from ..core.config import settings

logger = logging.getLogger("patentlens.lens_api")


class LensAPIService:
    """
    Dedicated service for querying The Lens Patent API (POST https://api.lens.org/patent/search)
    using Bearer-token authentication, exponential backoff, structured query execution,
    and robust error handling.
    """

    def __init__(self):
        self.api_token = getattr(settings, "LENS_API_TOKEN", "")
        self.api_url = getattr(settings, "LENS_API_URL", "https://api.lens.org/patent/search")
        self.max_results = getattr(settings, "MAX_EXTERNAL_API_RESULTS", 100)

    @property
    def is_configured(self) -> bool:
        token = (self.api_token or "").strip()
        return bool(token and len(token) > 8 and not token.startswith("your_"))

    def masked_token(self) -> str:
        token = (self.api_token or "").strip()
        if not token:
            return "UNCONFIGURED"
        if len(token) <= 8:
            return "****"
        return f"{token[:4]}...{token[-4:]}"

    def search_patents(
        self,
        queries: List[str],
        cpc_candidates: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Execute multi-query search against The Lens Patent API.
        
        Args:
            queries: List of technical search query strings generated from user invention.
            cpc_candidates: List of CPC classification codes to focus search.
            limit: Maximum records to retrieve.
            
        Returns:
            List of normalized patent records retrieved from The Lens.
        """
        if not self.is_configured:
            logger.warning("[LENS API] API token not configured. Skipping live Lens request.")
            return []

        logger.info(f"[LENS API] Initiating search on {self.api_url} with Token: {self.masked_token()}")
        logger.info(f"[LENS API] Generated input queries count: {len(queries)} | Queries: {queries}")

        headers = {
            "Authorization": f"Bearer {self.api_token.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PatentLens-AI/1.0"
        }

        all_results: List[Dict[str, Any]] = []
        seen_lens_ids = set()

        for q_idx, query_str in enumerate(queries):
            if len(all_results) >= limit:
                break

            cleaned_query = (query_str or "").strip()
            if not cleaned_query:
                continue

            # Build Lens API POST Payload
            payload = {
                "query": cleaned_query,
                "size": min(25, limit - len(all_results)),
                "from": 0,
                "include": [
                    "lens_id", "publication_number", "title", "abstract",
                    "claim", "description", "publication_date", "priority_date",
                    "filing_date", "owner", "author", "classifications_cpc",
                    "classifications_ipc", "jurisdiction", "url"
                ]
            }

            logger.info(f"[LENS API] Query [{q_idx + 1}/{len(queries)}]: '{cleaned_query}'")

            # Exponential backoff retry loop
            for attempt in range(3):
                try:
                    with httpx.Client(timeout=15.0, follow_redirects=True) as http_client:
                        res = http_client.post(self.api_url, json=payload, headers=headers)

                        if res.status_code == 200:
                            data = res.json()
                            results = data.get("data") or data.get("results") or []
                            logger.info(f"[LENS API] Query '{cleaned_query}' returned {len(results)} records.")

                            for item in results:
                                norm_item = self._normalize_lens_record(item)
                                if norm_item and norm_item["patent_number"] not in seen_lens_ids:
                                    seen_lens_ids.add(norm_item["patent_number"])
                                    all_results.append(norm_item)
                            break

                        elif res.status_code in [429, 503]:
                            logger.warning(f"[LENS API] Rate limited / Service unavailable (HTTP {res.status_code}). Backoff retry {attempt + 1}/3...")
                            time.sleep(2.0 * (attempt + 1))

                        elif res.status_code == 401:
                            logger.error("[LENS API] HTTP 401 Unauthorized — Invalid Lens API Token.")
                            return all_results

                        else:
                            logger.warning(f"[LENS API] HTTP {res.status_code} for query '{cleaned_query}': {res.text[:200]}")
                            break

                except Exception as e:
                    logger.warning(f"[LENS API] Attempt {attempt + 1} exception for query '{cleaned_query}': {e}")
                    time.sleep(1.0)

        logger.info(f"[LENS API] Completed search. Retrieved {len(all_results)} unique patent candidate records from The Lens.")
        return all_results[:limit]

    def _normalize_lens_record(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize Lens API JSON record into standardized internal format prioritizing:
        1. Claims
        2. Abstract
        3. Description
        4. Other available technical text.
        """
        try:
            lens_id = raw.get("lens_id") or raw.get("id") or ""
            pub_num = raw.get("publication_number") or raw.get("doc_number") or lens_id
            if not pub_num:
                return None

            # Format patent number nicely with jurisdiction if present
            jurisdiction = raw.get("jurisdiction", "").upper()
            if jurisdiction and not pub_num.startswith(jurisdiction):
                formatted_pat_num = f"{jurisdiction}-{pub_num}"
            else:
                formatted_pat_num = pub_num

            # Extract Title
            title_field = raw.get("title")
            if isinstance(title_field, list):
                t_str = " ".join([t.get("text", "") if isinstance(t, dict) else str(t) for t in title_field]).strip()
            elif isinstance(title_field, dict):
                t_str = title_field.get("text", "").strip()
            else:
                t_str = str(title_field or "Untitled Patent Document").strip()

            # Extract Abstract
            abs_field = raw.get("abstract")
            if isinstance(abs_field, list):
                abs_str = " ".join([a.get("text", "") if isinstance(a, dict) else str(a) for a in abs_field]).strip()
            elif isinstance(abs_field, dict):
                abs_str = abs_field.get("text", "").strip()
            else:
                abs_str = str(abs_field or "").strip()

            # Extract Claims
            claims_field = raw.get("claim") or raw.get("claims")
            if isinstance(claims_field, list):
                claims_str = " ".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in claims_field]).strip()
            elif isinstance(claims_field, dict):
                claims_str = claims_field.get("text", "").strip()
            else:
                claims_str = str(claims_field or "").strip()

            # Extract Description
            desc_field = raw.get("description")
            if isinstance(desc_field, list):
                desc_str = " ".join([d.get("text", "") if isinstance(d, dict) else str(d) for d in desc_field]).strip()
            elif isinstance(desc_field, dict):
                desc_str = desc_field.get("text", "").strip()
            else:
                desc_str = str(desc_field or "").strip()

            # Assignees / Owners
            owner_field = raw.get("owner") or raw.get("applicant") or raw.get("assignee")
            if isinstance(owner_field, list):
                owners = ", ".join([o.get("name", "") if isinstance(o, dict) else str(o) for o in owner_field]).strip()
            elif isinstance(owner_field, dict):
                owners = owner_field.get("name", "").strip()
            else:
                owners = str(owner_field or "Independent Assignee").strip()

            # Inventors / Authors
            author_field = raw.get("author") or raw.get("inventor")
            if isinstance(author_field, list):
                inventors = ", ".join([a.get("name", "") if isinstance(a, dict) else str(a) for a in author_field]).strip()
            elif isinstance(author_field, dict):
                inventors = author_field.get("name", "").strip()
            else:
                inventors = str(author_field or "Independent Inventor").strip()

            # Dates
            pub_date = raw.get("publication_date") or raw.get("priority_date") or raw.get("filing_date") or "2024-01-01"

            # CPC & IPC codes
            cpc_list = raw.get("classifications_cpc", [])
            cpc_codes = []
            if isinstance(cpc_list, list):
                for c in cpc_list:
                    if isinstance(c, dict) and c.get("symbol"):
                        cpc_codes.append(c["symbol"])
                    elif isinstance(c, str):
                        cpc_codes.append(c)

            ipc_list = raw.get("classifications_ipc", [])
            ipc_codes = []
            if isinstance(ipc_list, list):
                for i in ipc_list:
                    if isinstance(i, dict) and i.get("symbol"):
                        ipc_codes.append(i["symbol"])
                    elif isinstance(i, str):
                        ipc_codes.append(i)

            # URL
            url = raw.get("url") or f"https://www.lens.org/lens/patent/{lens_id or pub_num}"

            # Fallbacks for empty text fields
            if not abs_str and claims_str:
                abs_str = f"Main Patent Claim: {claims_str[:500]}..."
            elif not abs_str and desc_str:
                abs_str = f"Patent summary: {desc_str[:500]}..."
            elif not abs_str:
                abs_str = f"Patent publication {formatted_pat_num} retrieved from The Lens Patent API."

            if not desc_str:
                desc_str = f"Patent specification for {formatted_pat_num} ({t_str}). Abstract: {abs_str}"

            return {
                "patent_number": formatted_pat_num,
                "lens_id": lens_id,
                "title": t_str,
                "abstract": abs_str,
                "claims": claims_str,
                "description": desc_str,
                "inventors": inventors or "Lens Patent Inventor",
                "assignee": owners or "Lens Patent Assignee",
                "publication_date": str(pub_date)[:10],
                "source_url": url,
                "source_type": "THE LENS",
                "document_type": "PATENT",
                "cpc_codes": ", ".join(cpc_codes[:5]) if cpc_codes else "",
                "ipc_codes": ", ".join(ipc_codes[:5]) if ipc_codes else "",
                "jurisdiction": jurisdiction or "US"
            }
        except Exception as e:
            logger.warning(f"[LENS API] Failed normalizing Lens record: {e}")
            return None


lens_api_service = LensAPIService()
