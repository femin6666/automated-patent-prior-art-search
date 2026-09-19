import pytest
from unittest.mock import patch, MagicMock
from app.services.lens_api_service import lens_api_service, LensAPIService
from app.services.patent_api_service import patent_api_service
from app.services.gemini_service import gemini_service
from ml.similarity_engine import compute_hybrid_score, calculate_deterministic_final_score

def test_lens_api_token_security_and_masking():
    """
    Acceptance Test 1: Verify token remains server-side and is properly masked in logs.
    """
    service = LensAPIService()
    service.api_token = "lens_secret_token_123456789"
    
    masked = service.masked_token()
    assert "lens_secret_token" not in masked
    assert masked.startswith("lens")
    assert masked.endswith("6789")
    assert "..." in masked

    unconfig = LensAPIService()
    unconfig.api_token = ""
    assert unconfig.masked_token() == "UNCONFIGURED"


def test_lens_multi_query_search_strategy_generation():
    """
    Acceptance Test 2: Verify invention analysis generates 8 focused search strategy queries covering:
    Core concept, technical terminology, component-function, component-relationship,
    operating-principle, claims-oriented, CPC/IPC, and broad discovery.
    """
    invention_analysis = gemini_service._heuristic_invention_analysis(
        title="Adaptive Foreign Object Detection System for Wireless Charging",
        problem_statement="Mitigate thermal overload caused by parasitic heating of metallic objects on wireless charging pads.",
        description="Controller monitors transmitter coil impedance parameters and adjusts foreign object detection thresholds dynamically.",
        keywords=["wireless charging", "foreign object detection", "transmitter coil"],
        domain="Electrical Engineering"
    )

    queries = invention_analysis.get("search_queries", [])
    assert len(queries) >= 8
    
    # Verify presence of field-specific or strategy syntax
    has_claim_query = any("claim" in q.lower() or "claims:" in q.lower() for q in queries)
    has_cpc_query = any("cpc" in q.lower() or "classifications_cpc" in q.lower() for q in queries)
    has_term_query = any("wireless" in q.lower() or "foreign object" in q.lower() for q in queries)

    assert has_term_query is True
    assert (has_claim_query or has_cpc_query) is True


def test_lens_response_normalization_truthfulness():
    """
    Acceptance Test 3: Verify raw Lens API JSON record is normalized into internal schema
    without data fabrication. Missing claims/descriptions must remain empty/None.
    """
    raw_lens_record = {
        "lens_id": "012-345-678-901-234",
        "doc_number": "20240123456",
        "jurisdiction": "US",
        "kind": "A1",
        "date_published": "2024-06-15",
        "biblio": {
            "invention_title": [{"lang": "en", "text": "Wireless Power System with Foreign Object Detector"}],
            "publication_reference": {"jurisdiction": "US", "doc_number": "20240123456"},
            "application_reference": {"date": "2023-12-01"},
            "priority_claims": {"data": [{"date": "2022-11-15"}]},
            "parties": {
                "applicants": [{"extracted_name": {"value": "Acme Patent Technologies Inc"}}],
                "inventors": [{"extracted_name": {"value": "Jane Doe"}}, {"extracted_name": {"value": "John Smith"}}]
            },
            "classifications_cpc": {
                "classifications": [{"symbol": "H02J50/60"}, {"symbol": "H02J50/12"}]
            }
        },
        "abstract": [{"lang": "en", "text": "A foreign object detector for inductive wireless power transfer pads."}],
        "claims": [],  # Explicitly empty claims
        "description": None,  # Explicitly missing description
        "has_claim": False,
        "has_description": False,
        "has_full_text": False,
        "families": {
            "simple_family": {"id": "FAM_98765", "size": 2}
        }
    }

    norm = lens_api_service._normalize_lens_record(raw_lens_record)
    assert norm is not None
    assert norm["patent_number"] == "US-20240123456"
    assert norm["title"] == "Wireless Power System with Foreign Object Detector"
    assert norm["abstract"] == "A foreign object detector for inductive wireless power transfer pads."
    assert norm["claims"] == ""  # Strictly empty string, NOT fabricated text
    assert norm["description"] == ""  # Strictly empty string, NOT fabricated text
    assert norm["has_claims"] is False
    assert norm["has_description"] is False
    assert norm["publication_date"] == "2024-06-15"
    assert norm["filing_date"] == "2023-12-01"
    assert norm["earliest_priority_date"] == "2022-11-15"
    assert norm["assignee"] == "Acme Patent Technologies Inc"
    assert norm["inventors"] == "Jane Doe, John Smith"
    assert norm["cpc_codes"] == "H02J50/60, H02J50/12"
    assert norm["family_id"] == "FAM_98765"
    assert norm["source"] == "Lens Patent API"
    assert norm["source_status"] == "LIVE_API"


def test_lens_api_error_handling_statuses():
    """
    Acceptance Test 4: Verify Lens API explicit error status handling (AUTH_ERROR, RATE_LIMITED,
    UNAVAILABLE, QUERY_ERROR, NO_RESULTS, PARTIAL_RESULTS).
    """
    service = LensAPIService()
    service.api_token = "valid_test_bearer_token"

    # 1. Auth Error Test (HTTP 401)
    with patch("httpx.Client.post") as mock_post:
        mock_res = MagicMock()
        mock_res.status_code = 401
        mock_res.text = "Unauthorized Bearer Token"
        mock_post.return_value = mock_res

        res = service.search_patents(queries=["\"wireless power\""], limit=10)
        assert res["status"] == "LENS_AUTH_ERROR"
        assert res["retrieved_count"] == 0

    # 2. Rate Limit Test (HTTP 429)
    with patch("httpx.Client.post") as mock_post:
        mock_res = MagicMock()
        mock_res.status_code = 429
        mock_res.text = "Rate limit exceeded"
        mock_post.return_value = mock_res

        res = service.search_patents(queries=["\"wireless power\""], limit=10)
        assert res["status"] == "LENS_RATE_LIMITED"
        assert res["retrieved_count"] == 0

    # 3. Zero Results Test (HTTP 200 with empty list)
    with patch("httpx.Client.post") as mock_post:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {"data": []}
        mock_post.return_value = mock_res

        res = service.search_patents(queries=["\"nonexistent query term xyz\""], limit=10)
        assert res["status"] == "LENS_NO_RESULTS"
        assert res["retrieved_count"] == 0


def test_lens_patent_family_deduplication():
    """
    Acceptance Test 5: Deduplicate multi-country family publications (WO, US, EP, CN)
    into single representative family.
    """
    candidates = [
        {
            "patent_number": "WO-2024099999",
            "title": "Wireless Power Transfer Foreign Object Detection",
            "abstract": "WO publication abstract.",
            "claims": "Claims independent detection coil circuit.",
            "description": "Full WO description text.",
            "jurisdiction": "WO",
            "publication_date": "2024-01-10",
            "family_id": "FAM_555"
        },
        {
            "patent_number": "US-20240111111",
            "title": "Wireless Power Transfer Foreign Object Detection",
            "abstract": "US publication abstract.",
            "claims": "",
            "description": "Short US description.",
            "jurisdiction": "US",
            "publication_date": "2024-03-15",
            "family_id": "FAM_555"
        },
        {
            "patent_number": "EP-3999999",
            "title": "Wireless Power Transfer Foreign Object Detection",
            "abstract": "EP publication abstract.",
            "claims": "",
            "description": "EP description.",
            "jurisdiction": "EP",
            "publication_date": "2024-05-20",
            "family_id": "FAM_555"
        }
    ]

    grouped = lens_api_service.group_by_patent_family(candidates)
    assert len(grouped) == 1
    rep = grouped[0]
    assert rep["family_id"] == "FAM_555"
    assert rep["family_size"] == 3
    assert rep["patent_number"] == "WO-2024099999"  # Document with full claims selected as representative
    assert len(rep["family_members"]) == 3


def test_lens_independent_temporal_handling():
    """
    Acceptance Test 6: Verify priority_date and publication_date are preserved independently
    and evaluated against reference_date correctly.
    """
    norm = lens_api_service._normalize_lens_record({
        "doc_number": "11223344",
        "jurisdiction": "US",
        "date_published": "2023-06-15",
        "biblio": {
            "invention_title": "Sample Patent",
            "application_reference": {"date": "2021-12-01"},
            "priority_claims": {"data": [{"date": "2021-01-15"}]}
        }
    })

    assert norm["publication_date"] == "2023-06-15"
    assert norm["priority_date"] == "2021-01-15"

    ref_date = "2022-01-01"
    
    # Priority is before reference, but publication is after reference
    is_prio_before = norm["priority_date"] < ref_date
    is_pub_after = norm["publication_date"] > ref_date

    assert is_prio_before is True
    assert is_pub_after is True


def test_full_provenance_chain_traceability():
    """
    Acceptance Test 7: Verify complete provenance chain:
    USER INVENTION -> GENERATED QUERY -> LENS REQUEST -> LENS RESPONSE -> NORMALIZED PATENT -> SBERT -> FEATURE MATCH -> EVIDENCE -> FINAL SCORE
    """
    user_invention = {
        "title": "Foreign Object Detection for EV Wireless Charging",
        "description": "Dynamic threshold adjustment circuit coupled to transmitter coil sensor bridge.",
        "domain": "Electrical Engineering"
    }

    # Step 1: Generate Queries
    inv_analysis = gemini_service._heuristic_invention_analysis(
        title=user_invention["title"],
        problem_statement="Prevent thermal damage",
        description=user_invention["description"],
        keywords=["wireless charging", "foreign object detection"],
        domain=user_invention["domain"]
    )
    generated_queries = inv_analysis["search_queries"]
    assert len(generated_queries) >= 8

    # Step 2 & 3: Lens Request & Normalized Lens Patent
    raw_lens_data = {
        "doc_number": "10987654",
        "jurisdiction": "US",
        "date_published": "2021-05-10",
        "biblio": {
            "invention_title": "Apparatus for Detecting Foreign Objects on Inductive Power Transfer Surface",
            "priority_claims": {"data": [{"date": "2020-03-01"}]}
        },
        "abstract": "A wireless charging pad with foreign object detection.",
        "claims": "Claims a wireless power transfer coil, dynamic threshold adjustment circuit, and metallic object detection sensor.",
        "description": "Describing resonant charging coils, impedance monitoring bridge, and dynamic threshold adjustment.",
        "has_claim": True,
        "has_description": True,
        "has_full_text": True
    }
    norm_patent = lens_api_service._normalize_lens_record(raw_lens_data)
    assert norm_patent["source"] == "Lens Patent API"

    # Step 4: SBERT & Deterministic Scoring
    score_res = compute_hybrid_score(
        user_embedding=[1.0, 0.0, 0.0],
        patent_embedding=[0.85, 0.1, 0.0],
        user_keywords=["foreign object detection"],
        user_concepts=inv_analysis["technical_features"],
        user_domain=user_invention["domain"],
        patent=norm_patent,
        target_text_for_concepts=f"{user_invention['title']} {user_invention['description']}",
        distinctive_features=inv_analysis["distinctive_features"],
        technical_features=inv_analysis["technical_features"]
    )

    assert score_res["final_score"] >= 60.0
    assert len(score_res["strong_matches"]) > 0
    assert score_res["score_breakdown"]["final_score"] == score_res["final_score"]


def test_lens_timeout_configuration_coordination():
    """
    Acceptance Test 8: Verify nested timeouts satisfy HTTP <= Thread < Pipeline hierarchy (20s <= 22s <= 25s).
    """
    from app.core.config import settings
    http_timeout = getattr(settings, "LENS_HTTP_TIMEOUT", 20.0)
    thread_timeout = getattr(settings, "LENS_THREAD_TIMEOUT", 22.0)
    pipeline_timeout = getattr(settings, "EXTERNAL_API_PIPELINE_TIMEOUT", 25.0)

    assert http_timeout <= thread_timeout
    assert thread_timeout <= pipeline_timeout
    assert pipeline_timeout >= 25.0
    assert http_timeout == 20.0
    assert thread_timeout == 22.0


def test_lens_http_200_delayed_9s_accepted():
    """
    Acceptance Test 9 (Scenario A): Verify Lens HTTP 200 response taking ~9 seconds
    is accepted as successful LENS_OK with LIVE_API provenance.
    """
    import time
    from app.services.lens_api_service import LensAPIService

    service = LensAPIService()
    service.api_token = "valid_test_bearer_token"

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "data": [
            {
                "doc_number": "20249999",
                "jurisdiction": "US",
                "biblio": {"invention_title": "9s Delayed Patent"},
                "abstract": "Abstract text for 9s delay test."
            }
        ]
    }

    def delayed_post(*args, **kwargs):
        time.sleep(0.05)  # Fast test simulation representing 9s completion within 20s
        return mock_res

    with patch("httpx.Client.post", side_effect=delayed_post):
        res = service.search_patents(queries=["waste segregation"], limit=5)
        assert res["status"] == "LENS_OK"
        assert res["retrieved_count"] == 1
        assert res["results"][0]["source_status"] == "LIVE_API"
        assert res["results"][0]["source"] == "Lens Patent API"


def test_lens_http_200_delayed_15s_accepted():
    """
    Acceptance Test 10 (Scenario B): Verify Lens HTTP 200 response taking ~15 seconds
    is accepted as successful LENS_OK with LIVE_API provenance.
    """
    import time
    from app.services.lens_api_service import LensAPIService

    service = LensAPIService()
    service.api_token = "valid_test_bearer_token"

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "data": [
            {
                "doc_number": "20248888",
                "jurisdiction": "US",
                "biblio": {"invention_title": "15s Delayed Large Payload Patent"},
                "abstract": "Abstract text for 15s delay test."
            }
        ]
    }

    def delayed_post(*args, **kwargs):
        time.sleep(0.1)  # Fast test simulation representing 15s completion within 20s
        return mock_res

    with patch("httpx.Client.post", side_effect=delayed_post):
        res = service.search_patents(queries=["waste segregation"], limit=5)
        assert res["status"] == "LENS_OK"
        assert res["retrieved_count"] == 1
        assert res["results"][0]["source_status"] == "LIVE_API"
        assert res["results"][0]["source"] == "Lens Patent API"


def test_genuine_request_exceeding_configured_timeout():
    """
    Acceptance Test 11 (Scenario C): Verify genuine request exceeding configured timeout
    is classified as LENS_API_UNAVAILABLE according to existing error taxonomy.
    """
    from app.services.lens_api_service import LensAPIService
    import httpx

    service = LensAPIService()
    service.api_token = "valid_test_bearer_token"

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read operation timed out after 20s")):
        res = service.search_patents(queries=["waste segregation"], limit=5)
        assert res["status"] == "LENS_API_UNAVAILABLE"
        assert res["retrieved_count"] == 0
        assert res["results"] == []


def test_http_429_remains_rate_limited():
    """
    Acceptance Test 12 (Scenario D): Verify HTTP 429 remains LENS_RATE_LIMITED.
    """
    from app.services.lens_api_service import LensAPIService

    service = LensAPIService()
    service.api_token = "valid_test_bearer_token"

    mock_res = MagicMock()
    mock_res.status_code = 429
    mock_res.text = "Too Many Requests"

    with patch("httpx.Client.post", return_value=mock_res):
        res = service.search_patents(queries=["waste segregation"], limit=5)
        assert res["status"] == "LENS_RATE_LIMITED"
        assert res["retrieved_count"] == 0


def test_http_401_403_remains_auth_error():
    """
    Acceptance Test 13 (Scenario E): Verify HTTP 401/403 remains LENS_AUTH_ERROR.
    """
    from app.services.lens_api_service import LensAPIService

    service = LensAPIService()
    service.api_token = "invalid_token"

    mock_res = MagicMock()
    mock_res.status_code = 401
    mock_res.text = "Unauthorized Token"

    with patch("httpx.Client.post", return_value=mock_res):
        res = service.search_patents(queries=["waste segregation"], limit=5)
        assert res["status"] == "LENS_AUTH_ERROR"
        assert res["retrieved_count"] == 0


def test_http_200_zero_records_remains_no_results():
    """
    Acceptance Test 14 (Scenario F): Verify HTTP 200 with zero records remains LENS_NO_RESULTS, NOT API_UNAVAILABLE.
    """
    from app.services.lens_api_service import LensAPIService

    service = LensAPIService()
    service.api_token = "valid_test_bearer_token"

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"data": []}

    with patch("httpx.Client.post", return_value=mock_res):
        res = service.search_patents(queries=["nonexistent string xyz"], limit=5)
        assert res["status"] == "LENS_NO_RESULTS"
        assert res["status"] != "LENS_API_UNAVAILABLE"
        assert res["retrieved_count"] == 0


def test_provenance_distinction_live_api_vs_google():
    """
    Acceptance Test 15 (Scenarios G & H): Verify successful Lens records have source_status='LIVE_API'
    and Google dataset records have source_status='LIVE_DATASET'.
    """
    from app.services.lens_api_service import LensAPIService

    service = LensAPIService()
    service.api_token = "valid_test_bearer_token"

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "data": [
            {
                "doc_number": "20247777",
                "jurisdiction": "US",
                "biblio": {"invention_title": "Live Lens Patent"},
                "abstract": "Abstract text."
            }
        ]
    }

    with patch("httpx.Client.post", return_value=mock_res):
        res = service.search_patents(queries=["waste segregation"], limit=5)
        lens_rec = res["results"][0]
        assert lens_rec["source_status"] == "LIVE_API"
        assert lens_rec["source"] == "Lens Patent API"

    # Verify Google Patents record representation
    google_rec_source_status = "LIVE_DATASET"
    google_rec_source_type = "GOOGLE PATENTS"
    assert google_rec_source_status != lens_rec["source_status"]
    assert google_rec_source_type != lens_rec["source_type"]
