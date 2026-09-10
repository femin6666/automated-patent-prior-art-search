import sys
import os
import logging
from contextlib import asynccontextmanager

# Add parent directory to sys.path so imports work regardless of execution CWD
# Server reloaded with instant rate-limit circuit breaker and fast GET search details
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.app.core.config import settings
    from backend.app.core.database import engine, Base, ensure_columns_exist
    from backend.ml.embedding_service import embedding_service
    from backend.scripts.seed_database import seed_patents_if_needed

    from backend.app.api.auth import router as auth_router
    from backend.app.api.search import router as search_router
    from backend.app.api.patents import router as patents_router
    from backend.app.api.reports import router as reports_router
    from backend.app.api.users import router as users_router
except ImportError:
    from app.core.config import settings
    from app.core.database import engine, Base, ensure_columns_exist
    from ml.embedding_service import embedding_service
    from scripts.seed_database import seed_patents_if_needed

    from app.api.auth import router as auth_router
    from app.api.search import router as search_router
    from app.api.patents import router as patents_router
    from app.api.reports import router as reports_router
    from app.api.users import router as users_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("patentlens.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to load ML model & seed database once at startup."""
    print("\n[PATENTLENS AI] Initializing backend services...", flush=True)
    logger.info("Initializing PatentLens AI Backend...")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"Database table check note: {e}")
    
    try:
        embedding_service.load_model(settings.MODEL_NAME)
        print(f"[PATENTLENS AI] SBERT embedding model '{settings.MODEL_NAME}' ready.", flush=True)
        logger.info(f"SBERT model '{settings.MODEL_NAME}' successfully loaded into memory.")
    except Exception as e:
        logger.warning(f"Could not preload SBERT model: {e}")

    try:
        seed_patents_if_needed()
    except Exception as e:
        logger.error(f"Error during startup seed: {e}")

    print("[PATENTLENS AI] Backend ready! Listening on http://localhost:8000\n", flush=True)
    logger.info("================ AI MODEL CONFIGURATION DIAGNOSTICS ================")
    logger.info(f"Gemini Model:    {settings.GEMINI_MODEL}")
    logger.info(f"Groq Model:      {settings.GROQ_MODEL}")
    logger.info(f"Embedding Model: {settings.MODEL_NAME}")
    logger.info("====================================================================")

    yield
    logger.info("Shutting down PatentLens AI Backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"http://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url}: {exc}")
    origin = request.headers.get("origin") or "*"
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": str(exc) or "Internal server error occurred.",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(search_router, prefix=settings.API_PREFIX)
app.include_router(patents_router, prefix=settings.API_PREFIX)
app.include_router(reports_router, prefix=settings.API_PREFIX)
app.include_router(users_router, prefix=settings.API_PREFIX)

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "model_loaded": embedding_service.is_loaded
    }

if __name__ == "__main__":
    import uvicorn
    print("\n==================================================", flush=True)
    print("  Starting PatentLens AI Server on http://localhost:8000", flush=True)
    print("==================================================\n", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
