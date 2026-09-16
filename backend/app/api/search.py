from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from backend.app.core.config import settings
    from backend.app.core.database import get_db, IS_POSTGRES
    from backend.app.core.security import get_current_user
    from backend.app.models.models import User, Patent, Search, SearchResult
    from backend.app.schemas.schemas import (
        PriorArtSearchRequest, PriorArtSearchResponse, SearchResultItem,
        SearchSummary, SearchHistoryItem, PatentOut
    )
    from backend.ml.preprocessing import validate_invention_input, prepare_combined_text
    from backend.ml.keyword_extractor import extract_technical_concepts
    from backend.ml.embedding_service import embedding_service
    from backend.ml.similarity_engine import compute_hybrid_score, calculate_cosine_similarity
    from backend.ml.risk_classifier import classify_prior_art_risk, get_similarity_level_label
    from backend.app.services.llm_factory import get_llm_service
    from backend.app.services.patent_api_service import patent_api_service
    from backend.app.services.lens_api_service import lens_api_service
except ImportError:
    from ..core.config import settings
    from ..core.database import get_db, IS_POSTGRES
    from ..core.security import get_current_user
    from ..models.models import User, Patent, Search, SearchResult
    from ..schemas.schemas import (
        PriorArtSearchRequest, PriorArtSearchResponse, SearchResultItem,
        SearchSummary, SearchHistoryItem, PatentOut
    )
    from ...ml.preprocessing import validate_invention_input, prepare_combined_text
    from ...ml.keyword_extractor import extract_technical_concepts
    from ...ml.embedding_service import embedding_service
    from ...ml.similarity_engine import compute_hybrid_score, calculate_cosine_similarity
    from ...ml.risk_classifier import classify_prior_art_risk, get_similarity_level_label
    from ..services.llm_factory import get_llm_service
    from ..services.patent_api_service import patent_api_service
    from ..services.lens_api_service import lens_api_service

router = APIRouter(prefix="/search", tags=["Prior-Art Search"])

@router.post("", response_model=PriorArtSearchResponse, status_code=status.HTTP_201_CREATED)
def perform_prior_art_search(
    request: PriorArtSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform AI-assisted preliminary prior-art search:
    1. Preprocess input text
    2. Extract technical concepts
    3. Generate SBERT 384-d embedding
    4. Perform vector similarity search against patent database
    5. Compute hybrid similarity score (Semantic 70%, Keyword 20%, Domain 10%)
    6. Classify risk level (LOW, MODERATE, HIGH, VERY HIGH)
    7. Persist search and search results in database
    """
    import logging
    logger = logging.getLogger("patentlens.search")

    val_res = validate_invention_input(request.title, request.description)
    if not val_res["valid"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=val_res["error"])

    target_full_text = f"{request.title} {request.problem_statement} {request.description}"
    user_concepts = extract_technical_concepts(target_full_text)
    
    # 1. Use LLM service (Groq / Gemini) to understand invention, extract features & search queries
    llm_service = get_llm_service()
    import concurrent.futures

    try:
        def _do_inv_analysis():
            return llm_service.analyze_invention(
                title=request.title,
                problem_statement=request.problem_statement,
                description=request.description,
                keywords=request.keywords,
                domain=request.domain
            )
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as inv_pool:
            inv_fut = inv_pool.submit(_do_inv_analysis)
            invention_analysis = inv_fut.result(timeout=2.5)
    except Exception as e_inv:
        logger.warning(f"[SEARCH ROUTE] Invention analysis timeout/note ({e_inv}). Falling back to instant heuristic NLP analysis.")
        from backend.app.services.gemini_service import gemini_service
        invention_analysis = gemini_service._heuristic_invention_analysis(
            request.title, request.problem_statement, request.description, request.keywords, request.domain
        )

    gemini_features = invention_analysis.get("technical_features", [])
    gemini_essential = invention_analysis.get("essential_features", [])
    gemini_optional = invention_analysis.get("optional_features", [])
    gemini_quads = invention_analysis.get("structured_quadruplets", [])
    gemini_queries = invention_analysis.get("search_queries", [])
    cpc_candidates = invention_analysis.get("cpc_candidates", [])

    logger.info("[DEBUG PIPELINE] ==================== INVENTIVE STEP 1: GEMINI ====================")
    logger.info(f"[DEBUG PIPELINE] Target Invention: '{request.title}' | Domain: '{request.domain}'")
    logger.info(f"[DEBUG PIPELINE] Technical Problem: {invention_analysis.get('technical_problem', '')}")
    logger.info(f"[DEBUG PIPELINE] Essential Features: {gemini_essential}")
    logger.info(f"[DEBUG PIPELINE] Gemini Search Queries (8 Strategies): {gemini_queries}")
    logger.info(f"[DEBUG PIPELINE] Gemini CPC Candidates: {cpc_candidates}")

    combined_text = prepare_combined_text(
        title=request.title,
        problem_statement=request.problem_statement,
        description=request.description,
        keywords=request.keywords
    )
    user_embedding = embedding_service.generate_embedding(combined_text)

    # 2. Fetch live patent candidates via The Lens Patent API with configurable pipeline timeout
    import concurrent.futures
    try:
        def _do_external_fetch():
            return patent_api_service.fetch_and_cache_external_patents(
                db=db,
                title=request.title,
                keywords=request.keywords,
                domain=request.domain,
                search_queries=gemini_queries,
                cpc_candidates=cpc_candidates,
                limit=50
            )
        pipeline_timeout = getattr(settings, "EXTERNAL_API_PIPELINE_TIMEOUT", 25.0)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ext_pool:
            ext_fut = ext_pool.submit(_do_external_fetch)
            api_stats = ext_fut.result(timeout=pipeline_timeout)
        logger.info(f"[DEBUG PIPELINE] Step 2 Lens/arXiv Search Stats: {api_stats}")
    except Exception as e:
        logger.warning(f"[PATENT API] External search timeout/note ({e}). Proceeding immediately with local dataset candidates.")
        fallback_lens_status = "LENS_API_UNAVAILABLE" if lens_api_service.is_configured else "LENS_UNCONFIGURED"
        api_stats = {"patents_retrieved": 0, "patents_searched": 0, "lens_api_status": fallback_lens_status}


    from backend.app.core.database import IS_POSTGRES, HAS_PGVECTOR
    import numpy as np

    if IS_POSTGRES and HAS_PGVECTOR and user_embedding:
        try:
            all_patents = db.query(Patent).order_by(Patent.embedding.l2_distance(user_embedding)).limit(150).all()
        except Exception:
            all_patents = db.query(Patent).limit(200).all()
    else:
        all_patents = db.query(Patent).limit(200).all()


    if not all_patents:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patent database is empty. Please run seed script first."
        )

    # Ultra-fast NumPy vector cosine pre-filtering
    candidate_patents = all_patents
    if len(all_patents) > 100 and user_embedding:
        try:
            valid_patents = []
            emb_vectors = []
            u_arr = np.array(user_embedding, dtype=np.float32)
            u_norm = np.linalg.norm(u_arr)

            for p in all_patents:
                p_emb = p.embedding
                if isinstance(p_emb, str):
                    try:
                        p_emb = json.loads(p_emb)
                    except Exception:
                        p_emb = None
                if p_emb and len(p_emb) == 384:
                    valid_patents.append(p)
                    emb_vectors.append(p_emb)

            if emb_vectors and u_norm > 0:
                mat = np.array(emb_vectors, dtype=np.float32)
                norms = np.linalg.norm(mat, axis=1)
                norms[norms == 0] = 1e-9
                sims = np.dot(mat, u_arr) / (norms * u_norm)
                
                # Pair patents with similarities and pick top 100
                sorted_patents = [p for p, s in sorted(zip(valid_patents, sims), key=lambda x: x[1], reverse=True)]
                candidate_patents = sorted_patents[:100]
        except Exception as e_pref:
            logger.warning(f"Vector pre-filtering fallback: {e_pref}")
            candidate_patents = all_patents[:100]

    from backend.ml.similarity_engine import is_technical_mismatch

    scored_items = []
    for patent in candidate_patents:
        # Stage 3 Funnel Gate: Technical Mismatch Filter (Kill false positives)
        if is_technical_mismatch(
            user_domain=request.domain,
            user_text=target_full_text,
            patent_title=patent.title,
            patent_abstract=patent.abstract,
            patent_domain=patent.domain
        ):
            logger.info(f"[STAGE 3 FUNNEL] Disqualified technical mismatch candidate: '{patent.title}'")
            continue

        patent_dict = {
            "title": patent.title,
            "abstract": patent.abstract,
            "description": patent.description,
            "claims": patent.claims,
            "domain": patent.domain,
            "cpc_codes": patent.cpc_codes,
            "cpc_candidates": cpc_candidates
        }
        
        patent_emb = patent.embedding
        if isinstance(patent_emb, str):
            import json
            patent_emb = json.loads(patent_emb)

        scores = compute_hybrid_score(
            user_embedding=user_embedding,
            patent_embedding=patent_emb,
            user_keywords=request.keywords,
            user_concepts=user_concepts,
            user_domain=request.domain,
            patent=patent_dict,
            target_text_for_concepts=target_full_text,
            distinctive_features=invention_analysis.get("distinctive_features"),
            technical_features=gemini_features,
            essential_features=gemini_essential
        )

        scored_items.append({
            "patent": patent,
            "scores": scores
        })

    # Robust patent family deduplication & metric tracking
    import re
    def _get_fam_key(pat_obj: Any) -> str:
        fam_id = getattr(pat_obj, "simple_family_id", None) or getattr(pat_obj, "family_id", None)
        if fam_id and str(fam_id).strip() and str(fam_id).strip() != "None":
            return str(fam_id).strip().upper()
        p_num = (pat_obj.patent_number or "").strip().upper()
        clean = p_num.split("-")[-1] if "-" in p_num else p_num
        clean = re.sub(r'[A-Z]\d?$', '', clean)
        return clean if clean else p_num

    candidates_with_family_ids_cnt = sum(
        1 for item in scored_items
        if (getattr(item["patent"], "simple_family_id", None) or getattr(item["patent"], "family_id", None))
    )

    family_grouped: Dict[str, Any] = {}
    for item in scored_items:
        fam_key = _get_fam_key(item["patent"])

        if fam_key not in family_grouped:
            family_grouped[fam_key] = item
        else:
            prev = family_grouped[fam_key]
            prev_claims_len = len(prev["patent"].claims or "")
            curr_claims_len = len(item["patent"].claims or "")
            if item["scores"]["final_score"] > prev["scores"]["final_score"] or (item["scores"]["final_score"] == prev["scores"]["final_score"] and curr_claims_len > prev_claims_len):
                family_grouped[fam_key] = item

    # Stage 4 Technical Relevance Gate (Non-forced Top N): Reject candidates with score < 30% and 0 feature matches
    deduped_scored_items = list(family_grouped.values())
    deduped_scored_items.sort(key=lambda x: x["scores"]["final_score"], reverse=True)

    gated_candidates = []
    rejected_count = 0
    for item in deduped_scored_items:
        sc = item["scores"]
        has_matched_feat = sc.get("matched_feature_count", 0) > 0 or len(sc.get("strong_matches", [])) > 0 or len(sc.get("partial_matches", [])) > 0
        has_dist_match = sc.get("distinctive_score", 0.0) > 0.0
        
        # Only retain candidates passing technical relevance gate (Score >= 30% or matching features)
        if sc["final_score"] < 30.0 and not has_matched_feat and not has_dist_match:
            rejected_count += 1
            logger.info(f"[STAGE 4 REJECTION] Rejected candidate '{item['patent'].title}' (Score: {sc['final_score']}%) Reason: IRRELEVANT_NO_TECHNICAL_OVERLAP")
        else:
            gated_candidates.append(item)

    top_candidates = [item for item in gated_candidates if item["scores"]["final_score"] >= 30.0 or item["scores"]["matched_feature_count"] > 0]
    top_10 = top_candidates[:10]

    # Iterative Search & Citation Expansion for top candidates
    iterative_retrieved = 0
    citation_retrieved = 0
    top_pat_nums = [item["patent"].patent_number for item in top_10]
    if top_pat_nums:
        try:
            def _do_citation():
                return patent_api_service.execute_citation_expansion(db=db, top_patent_numbers=top_pat_nums)
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as cit_pool:
                cit_fut = cit_pool.submit(_do_citation)
                citation_recs = cit_fut.result(timeout=1.5)
                citation_retrieved = len(citation_recs)
        except Exception as e:
            logger.warning(f"Citation expansion note/timeout: {e}")

    highest_similarity = top_10[0]["scores"]["final_score"] if top_10 else 0.0
    highest_semantic_similarity = max((item["scores"]["semantic_score"] for item in top_10), default=0.0)
    risk_info = classify_prior_art_risk(highest_similarity)

    vhigh_count = 0
    high_count = 0
    mod_count = 0
    low_count = 0

    for item in top_10:
        f_score = item["scores"]["final_score"]
        r_level = classify_prior_art_risk(f_score)["risk_level"]
        if r_level == "VERY HIGH":
            vhigh_count += 1
        elif r_level == "HIGH":
            high_count += 1
        elif r_level == "MODERATE":
            mod_count += 1
        else:
            low_count += 1

    total_matches_count = len(top_10)

    pat_searched = api_stats.get("patents_searched") or (len(all_patents) + api_stats.get("patents_retrieved", 0))
    pat_retrieved = api_stats.get("patents_retrieved", 0)
    pat_shortlisted = len(top_10)
    pat_deeply_analyzed = len(top_10)

    lens_status = api_stats.get("lens_api_status", "LENS_OK")

    # Structured Stage-by-Stage Retrieval Quality Logging & Single Search Trace
    logger.info("==================================================")
    logger.info(f"[END-TO-END SEARCH TRACE] User Invention: '{request.title}' | Domain: '{request.domain}'")
    logger.info(f"[END-TO-END SEARCH TRACE] Extracted Essential Features: {gemini_essential}")
    logger.info(f"[END-TO-END SEARCH TRACE] Generated Queries: {gemini_queries}")
    logger.info(f"[END-TO-END SEARCH TRACE] Lens API Endpoint: https://api.lens.org/patent/search | Method: POST")
    logger.info(f"[END-TO-END SEARCH TRACE] Lens API Status: {lens_status} | Live Records Returned: {pat_retrieved}")
    logger.info(f"[END-TO-END SEARCH TRACE] DB Candidates Evaluated: {len(candidate_patents)} | Deduplicated Families: {len(family_grouped)}")
    logger.info(f"[END-TO-END SEARCH TRACE] Stage 4 Rejected Irrelevant Candidates: {rejected_count}")
    logger.info(f"[END-TO-END SEARCH TRACE] Final Shortlisted Technically Relevant Candidates: {len(top_10)}")
    logger.info(f"[END-TO-END SEARCH TRACE] Highest Similarity Score: {highest_similarity}% | Risk: {risk_info['risk_level']}")
    logger.info("==================================================")

    patents_with_claims = sum(
        1 for item in scored_items
        if (item["patent"].claims and len(item["patent"].claims.strip()) > 10)
        or (item["patent"].abstract and len(item["patent"].abstract.strip()) > 20)
        or (item["patent"].description and len(item["patent"].description.strip()) > 30)
    )
    patents_with_full_text = sum(
        1 for item in scored_items
        if (item["patent"].description and len(item["patent"].description.strip()) > 30)
        or (item["patent"].abstract and len(item["patent"].abstract.strip()) > 30)
    )
    evidence_verified = sum(
        1 for item in top_10
        if any(e.get("verified") for e in item["scores"].get("evidence_items", []))
    )

    from backend.app.schemas.schemas import ScoreBreakdown, PipelineMetrics, PatentFamilyMember

    pipeline_metrics = PipelineMetrics(
        patents_searched=pat_searched,
        patents_retrieved=pat_retrieved,
        lens_records_retrieved=pat_retrieved,
        database_fallback_candidates=len(candidate_patents) if pat_retrieved == 0 else 0,
        final_shortlisted=len(top_10),
        total_candidates_evaluated=len(candidate_patents) + pat_retrieved,
        raw_candidates=len(candidate_patents),
        candidates_with_family_ids=candidates_with_family_ids_cnt,
        post_dedup_candidates=len(deduped_scored_items),
        vector_shortlisted=pat_shortlisted,
        unique_families=len(family_grouped),
        semantic_candidates=len(candidate_patents),
        technical_candidates=len(top_10),
        patents_with_claims=patents_with_claims,
        patents_with_full_text=patents_with_full_text,
        evidence_verified_matches=evidence_verified,
        iterative_wave_retrieved=iterative_retrieved,
        citation_expansions_found=citation_retrieved,
        lens_api_status=lens_status
    )

    search_record = Search(
        user_id=current_user.id,
        invention_title=request.title,
        domain=request.domain,
        problem_statement=request.problem_statement,
        description=request.description,
        keywords=request.keywords,
        risk_level=risk_info["risk_level"],
        highest_similarity=highest_similarity,
        total_results=total_matches_count,
        very_high_similarity=vhigh_count,
        high_similarity=high_count,
        moderate_similarity=mod_count,
        low_similarity=low_count,
        patents_searched=pat_searched,
        patents_retrieved=pat_retrieved,
        patents_shortlisted=pat_shortlisted,
        patents_deeply_analyzed=pat_deeply_analyzed
    )
    db.add(search_record)
    db.commit()
    db.refresh(search_record)

    llm_service = get_llm_service()
    result_items_response = []

    # Parallelize patent pair feature analysis across top candidates
    from concurrent.futures import ThreadPoolExecutor

    def _execute_pair_analysis(indexed_tuple):
        i_idx, item_obj = indexed_tuple
        p_obj = item_obj["patent"]
        s_obj = item_obj["scores"]
        try:
            res_analysis = llm_service.analyze_patent_pair(
                target_title=request.title,
                target_problem=request.problem_statement,
                target_description=request.description,
                patent_number=p_obj.patent_number,
                patent_title=p_obj.title,
                patent_abstract=p_obj.abstract,
                patent_description=p_obj.description,
                similarity_score=s_obj["final_score"]
            )
        except Exception as e_pair:
            logger.warning(f"Pair analysis thread fallback for {p_obj.patent_number}: {e_pair}")
            res_analysis = llm_service._normalize_parsed_response(
                llm_service._generate_heuristic_pair_analysis(
                    target_title=request.title,
                    target_description=request.description,
                    patent_number=p_obj.patent_number,
                    patent_title=p_obj.title,
                    patent_abstract=p_obj.abstract,
                    similarity_score=s_obj["final_score"],
                    patent_description=p_obj.description
                )
            )
        return i_idx, res_analysis

    pair_analysis_map = {}
    if top_10:
        pair_timeout = 1.0 if (not llm_service.is_configured or lens_status == "LENS_RATE_LIMITED") else 4.0
        with ThreadPoolExecutor(max_workers=min(10, len(top_10))) as pool:
            futures = [pool.submit(_execute_pair_analysis, item_tuple) for item_tuple in enumerate(top_10, start=1)]
            for fut in futures:
                try:
                    i_idx, res_analysis = fut.result(timeout=pair_timeout)
                    pair_analysis_map[i_idx] = res_analysis
                except Exception as e_fut:
                    logger.warning(f"Thread pool task timeout/error: {e_fut}")

    for idx, item in enumerate(top_10, start=1):
        pat = item["patent"]
        sc = item["scores"]
        res_status = "TECHNICALLY_RELEVANT"

        sr = SearchResult(
            search_id=search_record.id,
            patent_id=pat.id,
            semantic_score=sc["semantic_score"],
            keyword_score=sc["keyword_score"],
            domain_score=sc["domain_score"],
            final_score=sc["final_score"],
            matched_concepts=sc["matched_concepts"],
            rank=idx
        )
        db.add(sr)

        f_score = sc["final_score"]

        # Retrieve grounded patent pair feature comparison and limitation analysis
        raw_pair = pair_analysis_map.get(idx) or llm_service._generate_heuristic_pair_analysis(
            target_title=request.title,
            target_description=request.description,
            patent_number=pat.patent_number,
            patent_title=pat.title,
            patent_abstract=pat.abstract,
            similarity_score=f_score,
            patent_description=pat.description
        )
        pair_analysis = llm_service._normalize_parsed_response(raw_pair)

        sb_dict = sc.get("score_breakdown", {})
        conf_score = sc.get("confidence_score") if sc.get("confidence_score") is not None else 45.0
        score_bd_obj = ScoreBreakdown(
            semantic_similarity=sb_dict.get("semantic_similarity", sc["semantic_score"]),
            technical_features=sb_dict.get("technical_features", sc["keyword_score"]),
            evidence_strength=sb_dict.get("evidence_strength", sc.get("evidence_score", 0.0)),
            distinctive_concepts=sb_dict.get("distinctive_concepts", sc.get("distinctive_score", 0.0)),
            domain_cpc_alignment=sb_dict.get("domain_cpc_alignment", sc["domain_score"]),
            final_score=sc["final_score"],
            confidence_score=conf_score,
            is_gated=sb_dict.get("is_gated", False),
            formula_explanation=sb_dict.get("formula_explanation", "Final Score = (25% Semantic) + (35% Technical Features) + (20% Evidence) + (10% Distinctive Concepts) + (10% Domain/CPC)")
        )

        # Calculate Temporal Status according to Phase 16
        p_date = str(pat.publication_date or "").strip()[:10]
        prio_date = str(getattr(pat, "earliest_priority_date", "") or p_date).strip()[:10]
        r_date = str(request.reference_date or "").strip()[:10] if request.reference_date else ""

        if not r_date:
            temporal_status = "DATE_UNAVAILABLE"
            temporal_conclusion = f"Reference date not specified by user. Document publication date is {p_date}."
        elif p_date and p_date == r_date:
            temporal_status = "SAME_DATE"
            temporal_conclusion = f"Published on {p_date}, which is the SAME date as reference date ({r_date})."
        elif prio_date and p_date and prio_date < r_date and p_date > r_date:
            temporal_status = "EARLIER_PRIORITY_BUT_PUBLISHED_AFTER"
            temporal_conclusion = f"Earlier Priority ({prio_date}) — Published After Reference Date ({p_date} > {r_date})."
        elif p_date and p_date > r_date:
            temporal_status = "PUBLISHED_AFTER_REFERENCE"
            temporal_conclusion = f"Published on {p_date}, which is AFTER reference date ({r_date})."
        elif p_date and p_date < r_date:
            temporal_status = "PUBLISHED_BEFORE_REFERENCE"
            temporal_conclusion = f"Published on {p_date}, which is BEFORE reference date ({r_date})."
        else:
            temporal_status = "TEMPORAL_STATUS_UNCERTAIN"
            temporal_conclusion = f"Publication timeline uncertain (Pub Date: {p_date})."

        ev_status = sc.get("evidence_status", "VERIFIED")
        rel_info = classify_prior_art_risk(f_score)
        relevance_level = rel_info["label"]

        if f_score < 30.0:
            res_status = "TECHNICALLY_DISTINCT"
            overall_res = "NON_ANTICIPATED"
        elif f_score < 50.0:
            res_status = "PARTIALLY_RELEVANT"
            overall_res = "PARTIALLY_DISCLOSED"
        elif f_score < 70.0:
            res_status = "TECHNICALLY_RELEVANT"
            overall_res = "HIGH_SIMILARITY"
        else:
            res_status = "TECHNICALLY_RELEVANT"
            overall_res = "ANTICIPATED"

        if temporal_status in ["PUBLISHED_AFTER_REFERENCE", "EARLIER_PRIORITY_BUT_PUBLISHED_AFTER"]:
            res_status = f"{res_status}_PUBLISHED_LATER"

        has_verified_ev = sc.get("evidence_score", 0.0) > 0.0 and any(item.get("verified") for item in sc.get("evidence_items", []))
        if not has_verified_ev:
            ev_conf_conclusion = "NOT VERIFIED — Specification text unavailable or 0 evidence quotes verified."
            ev_status_lbl = "Limited evidence (0% verified)"
            # Clamp unverified evidence confidence between 10.0 and 25.0 so a valid non-zero float is sent to the frontend
            ev_conf_val = round(max(10.0, min(25.0, sc.get("confidence_score", 20.0))), 1)
        else:
            ev_conf_conclusion = pair_analysis.get("evidence_confidence_conclusion") or f"Evidence confidence is {conf_score}% based on specification text verification."
            ev_status_lbl = sc.get("evidence_status_label", "Claim evidence verified")
            ev_conf_val = conf_score

        tech_rel_conclusion = pair_analysis.get("technical_relevance_conclusion") or f"Technical feature overlap is {sc.get('raw_feature_coverage', 0.0)}% across {sc.get('matched_feature_count', 0)} matching limitations."
        legal_disclaimer = pair_analysis.get("legal_assessment_disclaimer") or "Preliminary AI screening only. Legal patentability is not determined by AI and requires formal patent attorney examination."

        if pat_retrieved > 0:
            item_source_status = "LIVE_API"
            item_source_name = "The Lens Patent API"
            item_retrieval_status = "LIVE_API_SUCCESS"
            doc_type_val = pat.document_type or "PATENT"
        else:
            item_source_status = "DATABASE"
            item_source_name = "Database Repository"
            item_retrieval_status = "DATABASE_REPOSITORY_FALLBACK"
            doc_type_val = "DATABASE RECORD"

        pat_out_obj = PatentOut.model_validate(pat)
        pat_out_obj.source_status = item_source_status
        pat_out_obj.source_name = item_source_name
        pat_out_obj.retrieval_status = item_retrieval_status
        pat_out_obj.source_type = item_source_name.upper()
        pat_out_obj.document_type = doc_type_val

        result_items_response.append(
            SearchResultItem(
                patent=pat_out_obj,
                semantic_score=sc["semantic_score"],
                keyword_score=sc["keyword_score"],
                domain_score=sc["domain_score"],
                final_score=sc["final_score"],
                confidence_score=ev_conf_val,
                matched_concepts=sc["matched_concepts"],
                rank=idx,
                semantic_similarity_label=get_similarity_level_label(sc["semantic_score"]),
                relevance_explanation=pair_analysis.get("relevance_explanation"),
                feature_comparison=pair_analysis.get("feature_comparison", []),
                patent_specific_insights=pair_analysis.get("patent_specific_insights", []),
                technical_features=pair_analysis.get("technical_features", gemini_features),
                essential_features=gemini_essential,
                optional_features=gemini_optional,
                structured_quadruplets=gemini_quads,
                distinctive_features=pair_analysis.get("distinctive_features", []),
                matched_features=pair_analysis.get("matched_features", []),
                strong_matches=sc.get("strong_matches", []),
                partial_matches=sc.get("partial_matches", []),
                weak_matches=sc.get("weak_matches", []),
                missing_features=sc.get("missing_features", []),
                unmatched_features=pair_analysis.get("unmatched_features", sc.get("missing_features", [])),
                unverifiable_features=sc.get("unverifiable_features", []),
                evidence_items=sc.get("evidence_items", []),
                evidence_status_label=ev_status_lbl,
                overlap_summary=pair_analysis.get("overlap_summary"),
                claim_elements=pair_analysis.get("claim_elements", []),
                single_document_anticipation=pair_analysis.get("single_document_anticipation", "NO"),
                missing_elements=pair_analysis.get("missing_elements", []),
                technical_feature_coverage=sc["keyword_score"],
                evidence_confidence=ev_conf_val,
                overall_result=overall_res,
                score_breakdown=score_bd_obj,
                family_members=[
                    PatentFamilyMember(
                        patent_number=pat.patent_number,
                        jurisdiction=pat.jurisdiction or "US",
                        kind="A1",
                        title=pat.title,
                        publication_date=pat.publication_date,
                        document_type=doc_type_val,
                        source_url=pat.source_url or ""
                    )
                ],
                family_size=getattr(pat, "simple_family_size", 1) or 1,
                is_family_representative=True,
                family_id=getattr(pat, "simple_family_id", pat.patent_number) or pat.patent_number,
                temporal_status=temporal_status,
                result_status=res_status,
                relevance_level=relevance_level,
                evidence_status=ev_status,
                evidence_availability_level=sc.get("evidence_availability_level", "NOT_VERIFIABLE"),
                source_status=item_source_status,
                source_name=item_source_name,
                retrieval_status=item_retrieval_status,
                feature_match_status=sc.get("feature_match_status", "PARTIAL"),
                feature_match_source=sc.get("feature_match_source", "ABSTRACT/TITLE"),
                raw_feature_coverage=round(((sc.get("matched_feature_count") or len(pair_analysis.get("matched_features", [])) or (len(sc.get("strong_matches", [])) + len(sc.get("partial_matches", [])))) / (sc.get("total_feature_count") or len(gemini_features) or 9)) * 100.0, 1) if (sc.get("total_feature_count") or len(gemini_features) or 9) > 0 else 0.0,
                weighted_technical_score=sc.get("weighted_technical_score", sc["keyword_score"]),
                matched_feature_count=sc.get("matched_feature_count") or len(pair_analysis.get("matched_features", [])) or (len(sc.get("strong_matches", [])) + len(sc.get("partial_matches", []))),
                total_feature_count=sc.get("total_feature_count") or len(gemini_features) or 9,
                claims_status=sc.get("claims_status", "AVAILABLE" if (pat.claims and len(pat.claims) > 20) else "NOT_AVAILABLE"),
                full_text_status=sc.get("full_text_status", "AVAILABLE" if (pat.description and len(pat.description) > 100) else "NOT_AVAILABLE"),
                has_abstract=bool(pat.abstract and len(pat.abstract) > 10),
                has_claims=bool(pat.claims and len(pat.claims) > 20),
                has_description=bool(pat.description and len(pat.description) > 50),
                has_full_text=bool(pat.description and len(pat.description) > 50 and pat.claims and len(pat.claims) > 20),
                score_cap=sb_dict.get("score_cap"),
                score_cap_reason=sb_dict.get("score_cap_reason"),
                verification_status="VERIFIED" if (ev_status == "VERIFIED" and has_verified_ev) else "NOT_VERIFIED",
                data_quality_status=getattr(pat, "data_quality_status", "LIMITED") or "LIMITED",
                technical_relevance_conclusion=tech_rel_conclusion,
                evidence_confidence_conclusion=ev_conf_conclusion,
                temporal_status_conclusion=temporal_conclusion,
                legal_assessment_disclaimer=legal_disclaimer
            )
        )

    db.commit()

    summary = SearchSummary(
        total_results=total_matches_count,
        high_similarity=high_count,
        moderate_similarity=mod_count,
        low_similarity=low_count,
        very_high_similarity=vhigh_count,
        patents_searched=pat_searched,
        patents_retrieved=pat_retrieved,
        patents_shortlisted=pat_shortlisted,
        patents_deeply_analyzed=pat_deeply_analyzed,
        highest_semantic_similarity=highest_semantic_similarity,
        unique_families_count=len(family_grouped),
        pipeline_metrics=pipeline_metrics
    )

    try:
        def _do_novelty():
            return getattr(llm_service, "generate_novelty_analysis", lambda **k: None)(
                invention_title=request.title,
                problem_statement=request.problem_statement,
                description=request.description,
                matched_patents=[
                    {
                        "patent_number": item["patent"].patent_number,
                        "title": item["patent"].title,
                        "abstract": item["patent"].abstract,
                        "final_score": item["scores"]["final_score"]
                    }
                    for item in top_10
                ],
                risk_level=risk_info["risk_level"]
            )
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as nov_pool:
            nov_fut = nov_pool.submit(_do_novelty)
            ai_analysis = nov_fut.result(timeout=1.5)
    except Exception as e_nov:
        logger.warning(f"[SEARCH ROUTE] Novelty analysis route timeout/note ({e_nov}). Using fallback summary.")
        ai_analysis = getattr(llm_service, "_generate_fallback_summary", lambda **k: None)(
            invention_title=request.title,
            risk_level=risk_info["risk_level"],
            matched_patents=[{"title": item["patent"].title} for item in top_10]
        )

    if pat_retrieved > 0:
        active_data_source = "The Lens Patent API (Live API)"
    elif lens_status == "LENS_RATE_LIMITED":
        active_data_source = "Database Repository (Lens API HTTP 429 Rate Limited / Monthly Quota Exceeded)"
    elif lens_status == "LENS_AUTH_ERROR":
        active_data_source = "Database Repository (Lens API HTTP Authorization Error)"
    elif lens_status == "LENS_API_UNAVAILABLE":
        active_data_source = "Database Repository (Lens API Unavailable / Network Timeout)"
    elif lens_api_service.is_configured:
        active_data_source = "Database Repository (Lens API 0 Live Records)"
    else:
        active_data_source = "Database Repository"
    active_ai_model = getattr(llm_service, "model_name", "Gemini 3.6 Flash")

    return PriorArtSearchResponse(
        search_id=search_record.id,
        invention_title=search_record.invention_title,
        domain=search_record.domain,
        created_at=search_record.created_at,
        risk_level=risk_info["risk_level"],
        risk_label=risk_info["label"],
        highest_similarity=highest_similarity,
        highest_semantic_similarity=highest_semantic_similarity,
        summary=summary,
        results=result_items_response,
        ai_analysis=ai_analysis,
        is_demo_dataset=True,
        data_source=active_data_source,
        ai_model_used=active_ai_model
    )

@router.get("/history", response_model=List[SearchHistoryItem])
def get_user_search_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve search history for the authenticated user."""
    searches = (
        db.query(Search)
        .filter(Search.user_id == current_user.id)
        .order_by(Search.created_at.desc())
        .all()
    )
    return [SearchHistoryItem.model_validate(s) for s in searches]

@router.get("/{search_id}", response_model=PriorArtSearchResponse)
def get_search_details(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve search results by search_id."""
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search record not found.")

    results_db = (
        db.query(SearchResult)
        .filter(SearchResult.search_id == search.id)
        .order_by(SearchResult.rank.asc())
        .all()
    )

    llm_service = get_llm_service()
    result_items = []
    high_count = 0
    mod_count = 0
    low_count = 0
    vhigh_count = 0

    for r in results_db:
        f_score = r.final_score
        r_level = classify_prior_art_risk(f_score)["risk_level"]
        if r_level == "VERY HIGH":
            vhigh_count += 1
        elif r_level == "HIGH":
            high_count += 1
        elif r_level == "MODERATE":
            mod_count += 1
        else:
            low_count += 1

        from backend.app.services.gemini_service import gemini_service
        pair_analysis = gemini_service._normalize_parsed_response(
            gemini_service._generate_heuristic_pair_analysis(
                target_title=search.invention_title,
                target_description=search.description,
                patent_number=r.patent.patent_number,
                patent_title=r.patent.title,
                patent_abstract=r.patent.abstract,
                similarity_score=f_score,
                patent_description=r.patent.description or ""
            )
        )

        result_items.append(
            SearchResultItem(
                patent=PatentOut.model_validate(r.patent),
                semantic_score=r.semantic_score,
                keyword_score=r.keyword_score,
                domain_score=r.domain_score,
                final_score=r.final_score,
                matched_concepts=r.matched_concepts or [],
                rank=r.rank,
                semantic_similarity_label=get_similarity_level_label(r.semantic_score),
                relevance_explanation=pair_analysis.get("relevance_explanation"),
                feature_comparison=pair_analysis.get("feature_comparison", []),
                patent_specific_insights=pair_analysis.get("patent_specific_insights", []),
                technical_features=pair_analysis.get("technical_features", []),
                distinctive_features=pair_analysis.get("distinctive_features", []),
                matched_features=pair_analysis.get("matched_features", []),
                unmatched_features=pair_analysis.get("unmatched_features", []),
                overlap_summary=pair_analysis.get("overlap_summary"),
                claim_elements=pair_analysis.get("claim_elements", []),
                single_document_anticipation=pair_analysis.get("single_document_anticipation", "NO"),
                missing_elements=pair_analysis.get("missing_elements", []),
                technical_feature_coverage=pair_analysis.get("technical_feature_coverage", 0.0),
                evidence_confidence=pair_analysis.get("evidence_confidence", 0.0),
                overall_result=pair_analysis.get("overall_result", "NON_ANTICIPATED")
            )
        )

    risk_info = classify_prior_art_risk(search.highest_similarity)
    highest_semantic = max((r.semantic_score for r in result_items), default=0.0)

    vhigh_val = vhigh_count
    high_val = high_count
    mod_val = mod_count
    low_val = low_count
    tot_val = vhigh_val + high_val + mod_val + low_val

    summary = SearchSummary(
        total_results=tot_val,
        high_similarity=high_val,
        moderate_similarity=mod_val,
        low_similarity=low_val,
        very_high_similarity=vhigh_val,
        patents_searched=search.patents_searched or tot_val,
        patents_retrieved=search.patents_retrieved or 0,
        patents_shortlisted=search.patents_shortlisted or tot_val,
        patents_deeply_analyzed=search.patents_deeply_analyzed or tot_val,
        highest_semantic_similarity=highest_semantic
    )

    active_data_source = "Live arXiv & CrossRef Feed" if (search.patents_retrieved or 0) > 0 else "Cached Patent Repository"
    active_ai_model = getattr(llm_service, "model_name", "Gemini 2.5 Flash")

    return PriorArtSearchResponse(
        search_id=search.id,
        invention_title=search.invention_title,
        domain=search.domain,
        created_at=search.created_at,
        risk_level=risk_info["risk_level"],
        risk_label=risk_info["label"],
        highest_similarity=search.highest_similarity,
        highest_semantic_similarity=highest_semantic,
        summary=summary,
        results=result_items,
        is_demo_dataset=True,
        data_source=active_data_source,
        ai_model_used=active_ai_model
    )

@router.delete("/{search_id}")
def delete_search_record(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a search record belonging to the authenticated user."""
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search record not found.")

    if search.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access.")

    db.delete(search)
    db.commit()
    return {"success": True, "message": "Search record successfully deleted."}
