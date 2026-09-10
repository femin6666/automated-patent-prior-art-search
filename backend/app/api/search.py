from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
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
except ImportError:
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
    
    # 1. Use Gemini to understand invention, extract essential/optional features & quadruplets, and generate 8 search queries
    from backend.app.services.gemini_service import gemini_service
    invention_analysis = gemini_service.analyze_invention(
        title=request.title,
        problem_statement=request.problem_statement,
        description=request.description,
        keywords=request.keywords,
        domain=request.domain
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

    # 2. Fetch live patent candidates via The Lens Patent API (including independent CPC search & arXiv feed)
    try:
        api_stats = patent_api_service.fetch_and_cache_external_patents(
            db=db,
            title=request.title,
            keywords=request.keywords,
            domain=request.domain,
            search_queries=gemini_queries,
            cpc_candidates=cpc_candidates,
            limit=100
        )
        logger.info(f"[DEBUG PIPELINE] Step 2 Lens/arXiv Search Stats: {api_stats}")
    except Exception as e:
        logger.warning(f"[PATENT API] External search note ({e}). Continuing with local dataset candidates.")
        api_stats = {"patents_retrieved": 0, "patents_searched": 0}

    from backend.app.core.database import IS_POSTGRES, HAS_PGVECTOR

    if IS_POSTGRES and HAS_PGVECTOR and user_embedding:
        try:
            all_patents = db.query(Patent).order_by(Patent.embedding.l2_distance(user_embedding)).limit(150).all()
        except Exception:
            all_patents = db.query(Patent).all()
    else:
        all_patents = db.query(Patent).all()

    if not all_patents:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patent database is empty. Please run seed script first."
        )

    scored_items = []
    for patent in all_patents:
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

    scored_items.sort(key=lambda x: x["scores"]["final_score"], reverse=True)
    top_candidates = scored_items[:30]
    top_10 = top_candidates[:10]

    # Iterative Search & Citation Expansion for top candidates
    iterative_retrieved = 0
    citation_retrieved = 0
    top_pat_nums = [item["patent"].patent_number for item in top_10]
    if top_pat_nums:
        try:
            citation_recs = patent_api_service.execute_citation_expansion(db=db, top_patent_numbers=top_pat_nums)
            citation_retrieved = len(citation_recs)
        except Exception as e:
            logger.warning(f"Citation expansion note: {e}")

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
    pat_shortlisted = len(top_candidates)
    pat_deeply_analyzed = len(top_10)

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
        if item["scores"].get("evidence_score", 0) > 0
        or len(item["scores"].get("strong_matches", [])) > 0
        or item["scores"].get("evidence_status") in ["VERIFIED", "PARTIAL"]
    )

    from backend.app.schemas.schemas import ScoreBreakdown, PipelineMetrics, PatentFamilyMember

    pipeline_metrics = PipelineMetrics(
        patents_searched=pat_searched,
        patents_retrieved=pat_retrieved,
        vector_shortlisted=pat_shortlisted,
        unique_families=len({item["patent"].patent_number.split("-")[0] if "-" in item["patent"].patent_number else item["patent"].patent_number for item in scored_items}),
        patents_with_claims=patents_with_claims,
        patents_with_full_text=patents_with_full_text,
        evidence_verified_matches=evidence_verified,
        iterative_wave_retrieved=iterative_retrieved,
        citation_expansions_found=citation_retrieved
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

    for idx, item in enumerate(top_10, start=1):
        pat = item["patent"]
        sc = item["scores"]

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

        # Generate grounded patent pair feature comparison and limitation analysis
        pair_analysis = llm_service.analyze_patent_pair(
            target_title=request.title,
            target_problem=request.problem_statement,
            target_description=request.description,
            patent_number=pat.patent_number,
            patent_title=pat.title,
            patent_abstract=pat.abstract,
            patent_description=pat.description,
            similarity_score=f_score
        )

        sb_dict = sc.get("score_breakdown", {})
        score_bd_obj = ScoreBreakdown(
            semantic_similarity=sb_dict.get("semantic_similarity", sc["semantic_score"]),
            technical_features=sb_dict.get("technical_features", sc["keyword_score"]),
            evidence_strength=sb_dict.get("evidence_strength", sc.get("evidence_score", 0.0)),
            distinctive_concepts=sb_dict.get("distinctive_concepts", sc.get("distinctive_score", 0.0)),
            domain_cpc_alignment=sb_dict.get("domain_cpc_alignment", sc["domain_score"]),
            final_score=sc["final_score"],
            confidence_score=sc.get("confidence_score", 85.0),
            is_gated=sb_dict.get("is_gated", False),
            formula_explanation=sb_dict.get("formula_explanation", "Final Score = (25% Semantic) + (40% Technical Features) + (15% Evidence) + (10% Distinctive Concepts) + (10% Domain/CPC)")
        )

        # Calculate Temporal Status
        pub_date_str = str(pat.publication_date or "").strip()
        ref_date_str = str(request.reference_date or "").strip() if request.reference_date else ""

        if not ref_date_str:
            temporal_status = "DATE_UNKNOWN"
            temporal_conclusion = "Reference date not specified by user. Document timeline recorded."
        elif pub_date_str and pub_date_str > ref_date_str:
            temporal_status = "AFTER_REFERENCE_DATE"
            temporal_conclusion = f"Published on {pub_date_str}, which is AFTER reference date ({ref_date_str})."
        elif pub_date_str and pub_date_str <= ref_date_str:
            temporal_status = "BEFORE_REFERENCE_DATE"
            temporal_conclusion = f"Published on {pub_date_str}, which is BEFORE reference date ({ref_date_str})."
        else:
            temporal_status = "DATE_UNKNOWN"
            temporal_conclusion = "Document publication date unknown."

        ev_status = sc.get("evidence_status", "VERIFIED")
        if temporal_status == "AFTER_REFERENCE_DATE":
            res_status = "TECHNICALLY_RELEVANT_PUBLISHED_LATER"
        elif f_score < 30.0:
            res_status = "LOW_TECHNICAL_RELEVANCE"
        elif ev_status in ["NOT_VERIFIED", "NOT_AVAILABLE"]:
            res_status = "EVIDENCE_NOT_VERIFIED"
        else:
            res_status = "TECHNICALLY_RELEVANT"

        tech_rel_conclusion = pair_analysis.get("technical_relevance_conclusion") or f"Technical feature overlap is {sc.get('raw_feature_coverage', 0.0)}% across {sc.get('matched_feature_count', 0)} matching limitations."
        ev_conf_conclusion = pair_analysis.get("evidence_confidence_conclusion") or f"Evidence confidence is {sc.get('confidence_score', 85.0)}% based on specification text verification."
        legal_disclaimer = pair_analysis.get("legal_assessment_disclaimer") or "Preliminary AI screening only. Legal patentability is not determined by AI and requires formal patent attorney examination."

        result_items_response.append(
            SearchResultItem(
                patent=PatentOut.model_validate(pat),
                semantic_score=sc["semantic_score"],
                keyword_score=sc["keyword_score"],
                domain_score=sc["domain_score"],
                final_score=sc["final_score"],
                confidence_score=sc.get("confidence_score", 85.0),
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
                evidence_status_label=sc.get("evidence_status_label", "Limited evidence"),
                overlap_summary=pair_analysis.get("overlap_summary"),
                claim_elements=pair_analysis.get("claim_elements", []),
                single_document_anticipation=pair_analysis.get("single_document_anticipation", "NO"),
                missing_elements=pair_analysis.get("missing_elements", []),
                technical_feature_coverage=sc["keyword_score"],
                evidence_confidence=sc.get("confidence_score", 85.0),
                overall_result=pair_analysis.get("overall_result", "NON_ANTICIPATED"),
                score_breakdown=score_bd_obj,
                family_members=[
                    PatentFamilyMember(
                        patent_number=pat.patent_number,
                        jurisdiction=pat.jurisdiction or "US",
                        kind="A1",
                        title=pat.title,
                        publication_date=pat.publication_date,
                        document_type=pat.document_type or "PATENT",
                        source_url=pat.source_url or ""
                    )
                ],
                family_size=1,
                is_family_representative=True,
                family_id=pat.patent_number,
                temporal_status=temporal_status,
                result_status=res_status,
                evidence_status=ev_status,
                raw_feature_coverage=round(((sc.get("matched_feature_count") or len(pair_analysis.get("matched_features", [])) or (len(sc.get("strong_matches", [])) + len(sc.get("partial_matches", [])))) / (sc.get("total_feature_count") or len(gemini_features) or 9)) * 100.0, 1) if (sc.get("total_feature_count") or len(gemini_features) or 9) > 0 else 0.0,
                weighted_technical_score=sc.get("weighted_technical_score", sc["keyword_score"]),
                matched_feature_count=sc.get("matched_feature_count") or len(pair_analysis.get("matched_features", [])) or (len(sc.get("strong_matches", [])) + len(sc.get("partial_matches", []))),
                total_feature_count=sc.get("total_feature_count") or len(gemini_features) or 9,
                claims_status=sc.get("claims_status", "AVAILABLE" if (pat.claims and len(pat.claims) > 20) else "NOT_AVAILABLE"),
                full_text_status=sc.get("full_text_status", "AVAILABLE" if (pat.description and len(pat.description) > 100) else "NOT_AVAILABLE"),
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
        unique_families_count=len(scored_items),
        pipeline_metrics=pipeline_metrics
    )

    try:
        ai_analysis = getattr(llm_service, "generate_novelty_analysis", lambda **k: None)(
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
    except Exception:
        ai_analysis = None

    from backend.app.services.lens_api_service import lens_api_service
    active_data_source = "The Lens Patent API & arXiv Feed" if (pat_retrieved > 0 or lens_api_service.is_configured) else "Cached Patent Repository"
    active_ai_model = getattr(llm_service, "model_name", "Gemini 2.5 Flash")

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
    """Retrieve search results by search_id with ownership check."""
    search = db.query(Search).filter(Search.id == search_id).first()
    if not search:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search record not found.")

    if search.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized: You do not own this search record."
        )

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
        if f_score > 85:
            vhigh_count += 1
        elif f_score > 70:
            high_count += 1
        elif f_score > 40:
            mod_count += 1
        else:
            low_count += 1

        pair_analysis = llm_service.analyze_patent_pair(
            target_title=search.invention_title,
            target_problem=search.problem_statement,
            target_description=search.description,
            patent_number=r.patent.patent_number,
            patent_title=r.patent.title,
            patent_abstract=r.patent.abstract,
            patent_description=r.patent.description,
            similarity_score=f_score
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
