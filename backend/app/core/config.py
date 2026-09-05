import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # pyrefly: ignore [unexpected-keyword]
    model_config = ConfigDict(case_sensitive=True, env_file=".env")

    PROJECT_NAME: str = "PatentLens AI"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/patentlens_db"
    )
    
    # JWT Security
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", "patentlens_super_secret_jwt_key_2026_change_in_production"
    )
    JWT_REFRESH_SECRET: str = os.getenv(
        "JWT_REFRESH_SECRET", "patentlens_super_secret_refresh_key_2026_change_in_production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS & Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Machine Learning
    MODEL_NAME: str = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")

settings = Settings()
