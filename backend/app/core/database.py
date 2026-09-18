import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

logger = logging.getLogger("patentlens.database")

Base = declarative_base()

def _get_masked_db_url(url: str) -> str:
    """Safely mask database credentials for startup logs."""
    if not url:
        return "not configured"
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname or "unknown"
        port = f":{parsed.port}" if parsed.port else ""
        db_name = parsed.path or ""
        return f"{parsed.scheme}://***:***@{hostname}{port}{db_name}"
    except Exception:
        return "postgresql://***:***@<masked-host>"

IS_POSTGRES = settings.DATABASE_URL.startswith("postgresql")
HAS_PGVECTOR = False

is_production = (getattr(settings, "ENVIRONMENT", "development").lower() == "production" or os.getenv("ENVIRONMENT", "").lower() == "production")

if IS_POSTGRES:
    logger.info("Database backend: PostgreSQL")
    logger.info(f"Database host: {_get_masked_db_url(settings.DATABASE_URL)}")
    try:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 10}
        )
        # Test connection & attempt vector extension creation
        with engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                HAS_PGVECTOR = True
                logger.info("Connected to PostgreSQL and verified pgvector extension.")
            except Exception as ve:
                logger.info(f"Connected to PostgreSQL successfully! (pgvector extension note: {ve})")
    except Exception as e:
        if is_production:
            logger.error(f"CRITICAL: Production PostgreSQL database connection failed ({_get_masked_db_url(settings.DATABASE_URL)}): {e}")
            raise RuntimeError(f"Production PostgreSQL connection failed: {e}")
        else:
            logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to SQLite for local development.")
            IS_POSTGRES = False
            SQLITE_URL = "sqlite:///./patentlens.db"
            engine = create_engine(
                SQLITE_URL,
                connect_args={"check_same_thread": False}
            )
else:
    if is_production:
        raise RuntimeError("Production environment requires PostgreSQL DATABASE_URL (postgresql://...). SQLite is disabled in production.")
    logger.info("Database backend: SQLite (Development/Testing)")
    SQLITE_URL = "sqlite:///./patentlens.db"
    engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def ensure_columns_exist(engine_instance):
    """Ensure newly added columns exist in searches, users, and patents tables across PostgreSQL and SQLite."""
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
    cols_users = [
        ("is_verified", "BOOLEAN DEFAULT FALSE"),
        ("otp_code", "VARCHAR(6)"),
        ("otp_expires_at", "TIMESTAMP"),
    ]
    cols_patents = [
        ("claims", "TEXT"),
        ("source_type", "VARCHAR(50) DEFAULT 'THE LENS'"),
        ("source_status", "VARCHAR(50) DEFAULT 'LIVE_API'"),
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
    try:
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

            for col_name, col_type in cols_users:
                try:
                    if IS_POSTGRES:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                    else:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"))
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
        logger.info("Successfully executed database column migration check.")
    except Exception as e:
        logger.warning(f"Database column migration note: {e}")

# Run schema column checks upon engine initialization
try:
    ensure_columns_exist(engine)
except Exception as e:
    logger.warning(f"Initial schema migration note: {e}")

def get_db():
    """Dependency for obtaining database sessions in FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

