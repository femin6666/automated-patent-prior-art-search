from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=ENV_FILE_PATH if ENV_FILE_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "PatentLens AI"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DEMO_MODE: bool = True

    # Database
    DATABASE_URL: str = "postgresql://postgres:femin12345@localhost:5432/Patentartpro"

    # JWT Security
    JWT_SECRET: str = "patentlens_super_secret_jwt_key_2026_change_in_production"
    JWT_REFRESH_SECRET: str = "patentlens_super_secret_refresh_key_2026_change_in_production"

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS & Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Machine Learning & AI Services
    LLM_PROVIDER: str = "gemini"
    MODEL_NAME: str = "all-MiniLM-L6-v2"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # External Patent APIs Configuration
    PATENTS_API_KEY: str = ""
    PATENTS_API_PROVIDER: str = "patentsview"
    MAX_EXTERNAL_API_RESULTS: int = 100
    LENS_API_TOKEN: str = ""
    LENS_API_URL: str = "https://api.lens.org/patent/search"

    # Configurable Similarity Thresholds (0-40% Low, 40-70% Moderate, 70-85% High, 85-100% Very High)
    SIMILARITY_THRESHOLD_LOW: float = 40.0
    SIMILARITY_THRESHOLD_MODERATE: float = 70.0
    SIMILARITY_THRESHOLD_HIGH: float = 85.0
    SIMILARITY_THRESHOLD_VERY_HIGH: float = 100.0


settings = Settings()