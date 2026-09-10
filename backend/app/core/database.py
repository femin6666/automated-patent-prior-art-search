import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

logger = logging.getLogger("patentlens.database")

Base = declarative_base()

IS_POSTGRES = settings.DATABASE_URL.startswith("postgresql")
HAS_PGVECTOR = False

if IS_POSTGRES:
    try:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 2}
        )
        # Test connection & attempt vector extension creation
        with engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                HAS_PGVECTOR = True
                logger.info("Connected to PostgreSQL and verified pgvector extension.")
            except Exception as ve:
                logger.info(f"Connected to PostgreSQL successfully! (pgvector extension not installed in Postgres: {ve})")
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to SQLite local database.")
        IS_POSTGRES = False
        SQLITE_URL = "sqlite:///./patentlens.db"
        engine = create_engine(
            SQLITE_URL,
            connect_args={"check_same_thread": False}
        )
else:
    SQLITE_URL = "sqlite:///./patentlens.db"
    engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def ensure_columns_exist(engine_instance):
    """Ensure newly added columns exist in searches and patents tables across PostgreSQL and SQLite."""
    cols_searches = [
        ("total_results", "INTEGER DEFAULT 0"),
        ("very_high_similarity", "INTEGER DEFAULT 0"),
        ("high_similarity", "INTEGER DEFAULT 0"),
        ("moderate_similarity", "INTEGER DEFAULT 0"),
        ("low_similarity", "INTEGER DEFAULT 0"),
        ("patents_searched", "INTEGER DEFAULT 0"),
        ("patents_retrieved", "INTEGER DEFAULT 0"),
        ("patents_shortlisted", "INTEGER DEFAULT 0"),
        ("patents_deeply_analyzed", "INTEGER DEFAULT 0"),
    ]
    cols_patents = [
        ("claims", "TEXT"),
        ("source_type", "VARCHAR(50) DEFAULT 'THE LENS'"),
        ("document_type", "VARCHAR(50) DEFAULT 'PATENT'"),
        ("lens_id", "VARCHAR(100)"),
        ("filing_date", "VARCHAR(50)"),
        ("earliest_priority_date", "VARCHAR(50)"),
        ("simple_family_id", "VARCHAR(100)"),
        ("simple_family_size", "INTEGER DEFAULT 1"),
        ("extended_family_size", "INTEGER DEFAULT 1"),
        ("data_quality_status", "VARCHAR(50) DEFAULT 'LIMITED'"),
        ("cpc_codes", "TEXT"),
        ("ipc_codes", "TEXT"),
        ("jurisdiction", "VARCHAR(20)"),
    ]
    with engine_instance.connect() as conn:
        for col_name, col_type in cols_searches:
            try:
                if IS_POSTGRES:
                    conn.execute(text(f"ALTER TABLE searches ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                else:
                    conn.execute(text(f"ALTER TABLE searches ADD COLUMN {col_name} {col_type};"))
                conn.commit()
            except Exception:
                pass

        for col_name, col_type in cols_patents:
            try:
                if IS_POSTGRES:
                    conn.execute(text(f"ALTER TABLE patents ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                else:
                    conn.execute(text(f"ALTER TABLE patents ADD COLUMN {col_name} {col_type};"))
                conn.commit()
            except Exception:
                pass

# Note: ensure_columns_exist is called inside startup lifespan in main.py to avoid module import side-effects


def get_db():
    """Dependency for obtaining database sessions in FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
