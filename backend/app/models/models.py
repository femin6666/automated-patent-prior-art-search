import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, IS_POSTGRES, HAS_PGVECTOR

# Optional pgvector Vector type import if available and running PostgreSQL with pgvector
try:
    if HAS_PGVECTOR:
        from pgvector.sqlalchemy import Vector
        VECTOR_TYPE = Vector(384)
    else:
        VECTOR_TYPE = JSON
except ImportError:
    VECTOR_TYPE = JSON


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    searches = relationship("Search", back_populates="user", cascade="all, delete-orphan")
    saved_patents = relationship("SavedPatent", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")


class Patent(Base):
    __tablename__ = "patents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patent_number = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    abstract = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    inventors = Column(String(500), nullable=False)
    assignee = Column(String(500), nullable=False)
    publication_date = Column(String(50), nullable=False)
    domain = Column(String(100), index=True, nullable=False)
    source_url = Column(String(500), nullable=True)
    embedding = Column(VECTOR_TYPE, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    search_results = relationship("SearchResult", back_populates="patent", cascade="all, delete-orphan")
    saved_by_users = relationship("SavedPatent", back_populates="patent", cascade="all, delete-orphan")


class Search(Base):
    __tablename__ = "searches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invention_title = Column(String(500), nullable=False)
    domain = Column(String(100), nullable=False)
    problem_statement = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    keywords = Column(JSON, default=list)
    risk_level = Column(String(50), nullable=False)  # LOW, MODERATE, HIGH, VERY HIGH
    highest_similarity = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="searches")
    results = relationship("SearchResult", back_populates="search", cascade="all, delete-orphan", order_by="SearchResult.rank")
    reports = relationship("Report", back_populates="search", cascade="all, delete-orphan")


class SearchResult(Base):
    __tablename__ = "search_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    search_id = Column(String(36), ForeignKey("searches.id", ondelete="CASCADE"), nullable=False, index=True)
    patent_id = Column(String(36), ForeignKey("patents.id", ondelete="CASCADE"), nullable=False, index=True)
    semantic_score = Column(Float, nullable=False)
    keyword_score = Column(Float, nullable=False)
    domain_score = Column(Float, nullable=False)
    final_score = Column(Float, nullable=False)
    matched_concepts = Column(JSON, default=list)
    rank = Column(Integer, nullable=False)

    # Relationships
    search = relationship("Search", back_populates="results")
    patent = relationship("Patent", back_populates="search_results")


class SavedPatent(Base):
    __tablename__ = "saved_patents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patent_id = Column(String(36), ForeignKey("patents.id", ondelete="CASCADE"), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="saved_patents")
    patent = relationship("Patent", back_populates="saved_by_users")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    search_id = Column(String(36), ForeignKey("searches.id", ondelete="CASCADE"), nullable=False, index=True)
    report_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reports")
    search = relationship("Search", back_populates="reports")
