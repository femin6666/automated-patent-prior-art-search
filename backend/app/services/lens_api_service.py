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

            # Build Lens API POST Payload (omit include to allow full standard biblio & abstract fields)
            payload = {
                "query": cleaned_query,
                "size": min(25, limit - len(all_results)),
                "from": 0
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
        1. Claims / Abstract
        2. Description / Biblio metadata
        3. Assignees & Inventors
        """
        try:
            lens_id = raw.get("lens_id") or raw.get("id") or ""
            biblio = raw.get("biblio", {})
            pub_ref = biblio.get("publication_reference", {})

            doc_num = raw.get("doc_number") or pub_ref.get("doc_number") or raw.get("publication_number") or lens_id
            if not doc_num:
                return None

            jurisdiction = (raw.get("jurisdiction") or pub_ref.get("jurisdiction") or "").upper()
            if jurisdiction and not str(doc_num).startswith(jurisdiction):
                formatted_pat_num = f"{jurisdiction}-{doc_num}"
            else:
                formatted_pat_num = str(doc_num)

            # Extract Title from biblio.invention_title or raw.title
            t_str = ""
            inv_titles = biblio.get("invention_title") or raw.get("title")
            if isinstance(inv_titles, list):
                en_title = next((t.get("text") for t in inv_titles if isinstance(t, dict) and t.get("lang") == "en"), None)
                if en_title:
                    t_str = en_title.strip()
                else:
                    t_str = " ".join([t.get("text", "") if isinstance(t, dict) else str(t) for t in inv_titles]).strip()
            elif isinstance(inv_titles, dict):
                t_str = inv_titles.get("text", "").strip()
            elif inv_titles:
                t_str = str(inv_titles).strip()

            if not t_str:
                t_str = f"Patent Document {formatted_pat_num}"

            # Extract Abstract
            abs_field = raw.get("abstract") or biblio.get("abstract")
            abs_str = ""
            if isinstance(abs_field, list):
                en_abs = next((a.get("text") for a in abs_field if isinstance(a, dict) and a.get("lang") == "en"), None)
                if en_abs:
                    abs_str = en_abs.strip()
                else:
                    abs_str = " ".join([a.get("text", "") if isinstance(a, dict) else str(a) for a in abs_field]).strip()
            elif isinstance(abs_field, dict):
                abs_str = abs_field.get("text", "").strip()
            elif abs_field:
                abs_str = str(abs_field).strip()

            # Extract Claims
            claims_field = raw.get("claims") or raw.get("claim") or biblio.get("claims")
            claims_str = ""
            if isinstance(claims_field, list):
                en_claim = next((c.get("text") for c in claims_field if isinstance(c, dict) and c.get("lang") == "en"), None)
                if en_claim:
                    claims_str = en_claim.strip()
                else:
                    claims_str = " ".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in claims_field]).strip()
            elif isinstance(claims_field, dict):
                claims_str = claims_field.get("text", "").strip()
            elif claims_field:
                claims_str = str(claims_field).strip()

            # Extract Description
            desc_field = raw.get("description")
            desc_str = ""
            if isinstance(desc_field, list):
                en_desc = next((d.get("text") for d in desc_field if isinstance(d, dict) and d.get("lang") == "en"), None)
                if en_desc:
                    desc_str = en_desc.strip()
                else:
                    desc_str = " ".join([d.get("text", "") if isinstance(d, dict) else str(d) for d in desc_field]).strip()
            elif isinstance(desc_field, dict):
                desc_str = desc_field.get("text", "").strip()
            elif desc_field:
                desc_str = str(desc_field).strip()

            # Extract Assignees / Applicants from biblio.parties or raw
            parties = biblio.get("parties", {})
            applicants = parties.get("applicants") or raw.get("owner") or raw.get("assignee")
            owners = ""
            if isinstance(applicants, list):
                names = []
                for app in applicants:
                    if isinstance(app, dict):
                        ex_name = app.get("extracted_name", {}).get("value") or app.get("name")
                        if ex_name:
                            names.append(ex_name)
                    elif isinstance(app, str):
                        names.append(app)
                owners = ", ".join(names)
            elif isinstance(applicants, dict):
                owners = applicants.get("extracted_name", {}).get("value") or applicants.get("name", "")

            # Extract Inventors
            inventors_list = parties.get("inventors") or raw.get("inventor") or raw.get("author")
            inventors = ""
            if isinstance(inventors_list, list):
                inv_names = []
                for inv in inventors_list:
                    if isinstance(inv, dict):
                        ex_name = inv.get("extracted_name", {}).get("value") or inv.get("name")
                        if ex_name:
                            inv_names.append(ex_name)
                    elif isinstance(inv, str):
                        inv_names.append(inv)
                inventors = ", ".join(inv_names)
            elif isinstance(inventors_list, dict):
                inventors = inventors_list.get("extracted_name", {}).get("value") or inventors_list.get("name", "")

            # Publication Date
            pub_date = (
                raw.get("date_published") or
                pub_ref.get("date") or
                raw.get("publication_date") or
                raw.get("priority_date") or
                "2024-01-01"
            )

            # CPC & IPC codes
            cpc_data = biblio.get("classifications_cpc", {}).get("classifications") or raw.get("classifications_cpc", [])
            cpc_codes = []
            if isinstance(cpc_data, list):
                for c in cpc_data:
                    if isinstance(c, dict) and c.get("symbol"):
                        cpc_codes.append(c["symbol"])
                    elif isinstance(c, str):
                        cpc_codes.append(c)

            ipc_data = biblio.get("classifications_ipcr", {}).get("classifications") or raw.get("classifications_ipc", [])
            ipc_codes = []
            if isinstance(ipc_data, list):
                for i in ipc_data:
                    if isinstance(i, dict) and i.get("symbol"):
                        ipc_codes.append(i["symbol"])
                    elif isinstance(i, str):
                        ipc_codes.append(i)

            # Family Information
            families_info = raw.get("families") or {}
            simple_fam = families_info.get("simple_family") or raw.get("simple_family") or {}
            ext_fam = families_info.get("extended_family") or raw.get("extended_family") or {}
            
            family_id = (
                simple_fam.get("id") or
                ext_fam.get("id") or
                str(doc_num).replace("-", "").replace(" ", "").upper()[:12]
            )

            kind_code = raw.get("kind") or pub_ref.get("kind") or "A1"
            url = raw.get("url") or f"https://www.lens.org/lens/patent/{lens_id or formatted_pat_num}"

            # Fallbacks for missing text
            if not abs_str and claims_str:
                abs_str = f"Main Patent Claim: {claims_str[:500]}..."
            elif not abs_str and desc_str:
                abs_str = f"Patent summary: {desc_str[:500]}..."
            elif not abs_str:
                abs_str = f"Patent publication {formatted_pat_num} ({t_str}) retrieved live from The Lens Patent API."

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
                "jurisdiction": jurisdiction or "US",
                "family_id": str(family_id),
                "kind": kind_code
            }
        except Exception as e:
            logger.warning(f"[LENS API] Failed normalizing Lens record: {e}")
            return None

    def search_by_cpc_classification(
        self,
        cpc_codes: List[str],
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Execute independent CPC/IPC classification retrieval path.
        USPTO guidance notes text search alone misses prior art when different terminology is used.
        """
        if not self.is_configured or not cpc_codes:
            return []

        cpc_queries = [f"cpc:{code.strip()}" for code in cpc_codes if code.strip()]
        if not cpc_queries:
            return []

        logger.info(f"[LENS API] Executing independent CPC classification search for codes: {cpc_codes}")
        return self.search_patents(queries=cpc_queries, limit=limit)

    def fetch_citations_and_family(
        self,
        patent_numbers: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Execute citation expansion (backward/forward citations and related family members)
        for strong prior-art candidates to create a search feedback loop.
        """
        if not self.is_configured or not patent_numbers:
            return []

        citation_queries = [f"citation:\"{p_num}\"" for p_num in patent_numbers[:5] if p_num]
        if not citation_queries:
            return []

        logger.info(f"[LENS API] Executing citation expansion search for candidates: {patent_numbers[:5]}")
        return self.search_patents(queries=citation_queries, limit=20)

    def group_by_patent_family(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group retrieved patent candidates by patent family (simple/extended family) to deduplicate
        publications representing the same invention across jurisdictions (WO, US, EP, CN, etc.).
        Selects 1 best representative document per family based on claims richness, text completeness,
        jurisdiction, and publication date.
        """
        if not candidates:
            return []

        family_groups: Dict[str, List[Dict[str, Any]]] = {}

        for item in candidates:
            fam_id = item.get("family_id")
            if not fam_id:
                # Deduplicate by core document number without jurisdiction/kind
                clean_num = str(item.get("patent_number", "")).split("-")[-1]
                fam_id = clean_num[:10] if clean_num else "UNKNOWN_FAMILY"

            if fam_id not in family_groups:
                family_groups[fam_id] = []
            family_groups[fam_id].append(item)

        deduplicated_representatives = []

        for fam_id, members in family_groups.items():
            # Rank members within family
            def rank_key(m):
                has_claims = 1 if m.get("claims") and len(m["claims"]) > 20 else 0
                text_len = len(m.get("abstract", "")) + len(m.get("claims", "")) + len(m.get("description", ""))
                jurisdiction_bonus = 2 if m.get("jurisdiction") in ["US", "WO", "EP"] else 0
                return (has_claims, jurisdiction_bonus, text_len, m.get("publication_date", ""))

            sorted_members = sorted(members, key=rank_key, reverse=True)
            rep = dict(sorted_members[0])

            family_member_list = [
                {
                    "patent_number": mem.get("patent_number"),
                    "jurisdiction": mem.get("jurisdiction", "US"),
                    "kind": mem.get("kind", "A1"),
                    "title": mem.get("title", ""),
                    "publication_date": mem.get("publication_date", "2024-01-01"),
                    "document_type": mem.get("document_type", "PATENT"),
                    "source_url": mem.get("source_url", "")
                }
                for mem in sorted_members
            ]

            rep["family_members"] = family_member_list
            rep["family_size"] = len(sorted_members)
            rep["is_family_representative"] = True
            rep["family_id"] = fam_id

            deduplicated_representatives.append(rep)

        logger.info(f"[PATENT DEDUPLICATION] Grouped {len(candidates)} raw documents into {len(deduplicated_representatives)} distinct patent families.")
        return deduplicated_representatives


lens_api_service = LensAPIService()

