import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

logger = logging.getLogger("patentlens.database")

Base = declarative_base()

IS_POSTGRES = settings.DATABASE_URL.startswith("postgresql")

if IS_POSTGRES:
    try:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        # Test connection & attempt vector extension creation
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("Connected to PostgreSQL and verified pgvector extension.")
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

def get_db():
    """Dependency for obtaining database sessions in FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
