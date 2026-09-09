import logging
from typing import Union
try:
    from backend.app.core.config import settings
    from backend.app.services.gemini_service import GeminiService
    from backend.app.services.groq_service import GroqService
except ImportError:
    from ..core.config import settings
    from .gemini_service import GeminiService
    from .groq_service import GroqService

logger = logging.getLogger("patentlens.llm_factory")

def get_llm_service(provider_override: str = None) -> Union[GeminiService, GroqService]:
    """
    Factory function returning the configured LLM service (GeminiService or GroqService).
    Checks provider_override first, then settings.LLM_PROVIDER (defaults to 'gemini').
    """
    provider = (provider_override or getattr(settings, "LLM_PROVIDER", "gemini")).strip().lower()
    
    if provider == "groq":
        logger.info("Initializing Groq LLM Service provider.")
        return GroqService()
    else:
        logger.info("Initializing Gemini LLM Service provider (gemini-2.0-flash).")
        return GeminiService()
