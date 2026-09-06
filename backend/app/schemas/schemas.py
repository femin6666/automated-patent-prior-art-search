from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

# --- Auth Schemas ---

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str

    @field_validator("confirm_password")
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match.")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class OTPResendRequest(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    is_verified: bool = False
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    require_otp: bool = False
    otp_sent_to: Optional[str] = None
    demo_otp: Optional[str] = None
    user: Optional[UserOut] = None


class UserUpdateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


# --- Patent Schemas ---

class PatentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patent_number: str
    title: str
    abstract: str
    description: str
    inventors: str
    assignee: str
    publication_date: str
    domain: str
    source_url: Optional[str] = None


class CreateCustomPatentRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    abstract: str = Field(..., min_length=10, max_length=2000)
    description: str = Field(..., min_length=20, max_length=10000)
    domain: str = Field(..., min_length=2, max_length=100)
    inventors: Optional[str] = "User Inventor"
    assignee: Optional[str] = "Independent Assignee"


# --- Prior-Art Search Schemas ---

class PriorArtSearchRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    domain: str = Field(..., min_length=2, max_length=100)
    problem_statement: str = Field(..., min_length=10, max_length=2000)
    description: str = Field(..., min_length=20, max_length=10000)
    keywords: List[str] = Field(default_factory=list, max_length=20)


class FeatureComparisonItem(BaseModel):
    target_feature: str
    prior_art_feature: str
    match_level: str  # Strong, Partial, Weak, Not Found
    explanation: str


class MatchedFeatureItem(BaseModel):
    feature: str
    match_level: str  # strong, partial, weak, none
    evidence: str


class SearchResultItem(BaseModel):
    patent: PatentOut
    semantic_score: float
    keyword_score: float
    domain_score: float
    final_score: float
    matched_concepts: List[str]
    rank: int
    semantic_similarity_label: Optional[str] = "Moderate"
    relevance_explanation: Optional[str] = None
    feature_comparison: List[FeatureComparisonItem] = Field(default_factory=list)
    patent_specific_insights: List[str] = Field(default_factory=list)
    technical_features: List[str] = Field(default_factory=list)
    distinctive_features: List[str] = Field(default_factory=list)
    matched_features: List[MatchedFeatureItem] = Field(default_factory=list)
    unmatched_features: List[str] = Field(default_factory=list)
    overlap_summary: Optional[str] = None


class SearchSummary(BaseModel):
    total_results: int
    high_similarity: int
    moderate_similarity: int
    low_similarity: int
    very_high_similarity: int


class PriorArtSearchResponse(BaseModel):
    search_id: str
    invention_title: str
    domain: str
    created_at: datetime
    risk_level: str
    risk_label: str
    highest_similarity: float
    summary: SearchSummary
    results: List[SearchResultItem]
    ai_analysis: Optional[Dict[str, Any]] = None
    is_demo_dataset: bool = True
    disclaimer: str = (
        "PatentLens AI provides AI-assisted preliminary prior-art search results "
        "for informational and research purposes only. The results do not constitute "
        "legal advice, a patentability determination, or a professional patent opinion."
    )


class SearchHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invention_title: str
    domain: str
    created_at: datetime
    highest_similarity: float
    risk_level: str
    total_results: int = 1110


# --- Saved Patents Schemas ---

class SavePatentRequest(BaseModel):
    notes: Optional[str] = None


class SavedPatentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patent_id: str
    notes: Optional[str] = None
    created_at: datetime
    patent: PatentOut


# --- Report Schemas ---

class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    search_id: str
    report_path: str
    created_at: datetime
