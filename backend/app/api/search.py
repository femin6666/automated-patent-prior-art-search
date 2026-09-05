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
    from backend.ml.risk_classifier import classify_prior_art_risk
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
    from ...ml.risk_classifier import classify_prior_art_risk

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
    val_res = validate_invention_input(request.title, request.description)
    if not val_res["valid"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=val_res["error"])

    user_concepts = extract_technical_concepts(f"{request.title} {request.problem_statement} {request.description}")
    
    combined_text = prepare_combined_text(
        title=request.title,
        problem_statement=request.problem_statement,
        description=request.description,
        keywords=request.keywords
    )
    user_embedding = embedding_service.generate_embedding(combined_text)

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
            "domain": patent.domain
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
            patent=patent_dict
        )

        scored_items.append({
            "patent": patent,
            "scores": scores
        })

    scored_items.sort(key=lambda x: x["scores"]["final_score"], reverse=True)
    top_10 = scored_items[:10]

    highest_similarity = top_10[0]["scores"]["final_score"] if top_10 else 0.0
    risk_info = classify_prior_art_risk(highest_similarity)

    search_record = Search(
        user_id=current_user.id,
        invention_title=request.title,
        domain=request.domain,
        problem_statement=request.problem_statement,
        description=request.description,
        keywords=request.keywords,
        risk_level=risk_info["risk_level"],
        highest_similarity=highest_similarity
    )
    db.add(search_record)
    db.commit()
    db.refresh(search_record)

    result_items_response = []
    high_count = 0
    mod_count = 0
    low_count = 0
    vhigh_count = 0

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
        if f_score > 80:
            vhigh_count += 1
        elif f_score > 65:
            high_count += 1
        elif f_score > 40:
            mod_count += 1
        else:
            low_count += 1

        result_items_response.append(
            SearchResultItem(
                patent=PatentOut.model_validate(pat),
                semantic_score=sc["semantic_score"],
                keyword_score=sc["keyword_score"],
                domain_score=sc["domain_score"],
                final_score=sc["final_score"],
                matched_concepts=sc["matched_concepts"],
                rank=idx
            )
        )

    db.commit()

    summary = SearchSummary(
        total_results=len(result_items_response),
        high_similarity=high_count,
        moderate_similarity=mod_count,
        low_similarity=low_count,
        very_high_similarity=vhigh_count
    )

    return PriorArtSearchResponse(
        search_id=search_record.id,
        invention_title=search_record.invention_title,
        domain=search_record.domain,
        created_at=search_record.created_at,
        risk_level=risk_info["risk_level"],
        risk_label=risk_info["label"],
        highest_similarity=highest_similarity,
        summary=summary,
        results=result_items_response,
        is_demo_dataset=True
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

    result_items = []
    high_count = 0
    mod_count = 0
    low_count = 0
    vhigh_count = 0

    for r in results_db:
        f_score = r.final_score
        if f_score > 80:
            vhigh_count += 1
        elif f_score > 65:
            high_count += 1
        elif f_score > 40:
            mod_count += 1
        else:
            low_count += 1

        result_items.append(
            SearchResultItem(
                patent=PatentOut.model_validate(r.patent),
                semantic_score=r.semantic_score,
                keyword_score=r.keyword_score,
                domain_score=r.domain_score,
                final_score=r.final_score,
                matched_concepts=r.matched_concepts or [],
                rank=r.rank
            )
        )

    risk_info = classify_prior_art_risk(search.highest_similarity)

    summary = SearchSummary(
        total_results=len(result_items),
        high_similarity=high_count,
        moderate_similarity=mod_count,
        low_similarity=low_count,
        very_high_similarity=vhigh_count
    )

    return PriorArtSearchResponse(
        search_id=search.id,
        invention_title=search.invention_title,
        domain=search.domain,
        created_at=search.created_at,
        risk_level=risk_info["risk_level"],
        risk_label=risk_info["label"],
        highest_similarity=search.highest_similarity,
        summary=summary,
        results=result_items,
        is_demo_dataset=True
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
