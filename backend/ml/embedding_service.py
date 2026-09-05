import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger("patentlens.embedding_service")

class SentenceTransformerEmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SentenceTransformerEmbeddingService, cls).__new__(cls)
        return cls._instance

    def load_model(self, model_name: str = "all-MiniLM-L6-v2"):
        """Load SBERT model into memory ONCE during application startup."""
        if self._model is None:
            logger.info(f"Loading Sentence Transformer model '{model_name}'...")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(model_name)
                logger.info(f"Successfully loaded Sentence Transformer model '{model_name}'.")
            except Exception as e:
                logger.error(f"Failed to load sentence_transformers model '{model_name}': {e}")
                # Fallback flag handling if sentence_transformers isn't fully installed or offline
                self._model = None
                raise RuntimeError(f"Could not initialize SBERT embedding model: {e}")

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a normalized 384-dimensional vector embedding for the input text.
        """
        if not text:
            return [0.0] * 384
            
        if self._model is None:
            self.load_model()

        if self._model is not None:
            try:
                # encode returns ndarray, normalize for cosine similarity via dot product
                embedding = self._model.encode(text, normalize_embeddings=True)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                raise RuntimeError(f"Embedding generation failed: {e}")
        else:
            raise RuntimeError("Sentence Transformer model is not loaded.")

embedding_service = SentenceTransformerEmbeddingService()
