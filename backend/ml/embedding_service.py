import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger("patentlens.embedding_service")

class SentenceTransformerEmbeddingService:
    _instance = None
    _model = None
    _load_attempted = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SentenceTransformerEmbeddingService, cls).__new__(cls)
        return cls._instance

    def load_model(self, model_name: str = "all-MiniLM-L6-v2", force: bool = False):
        """Load SBERT model into memory ONCE during application startup with dynamic GPU/MPS/CPU hardware detection."""
        if self._model is not None and not force:
            return

        if self._load_attempted and self._model is None and not force:
            return

        self._load_attempted = True
        logger.info(f"Loading Sentence Transformer model '{model_name}'...")
        try:
            import torch
            from sentence_transformers import SentenceTransformer
            
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
            
            logger.info(f"Initializing Sentence Transformer '{model_name}' on device: {device}")
            self._model = SentenceTransformer(model_name, device=device)
            logger.info(f"Successfully loaded Sentence Transformer model '{model_name}' on {device}.")
        except Exception as e:
            logger.error(f"Failed to load sentence_transformers model '{model_name}': {e}")
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

        if self._model is None and not self._load_attempted:
            try:
                self.load_model()
            except Exception as le:
                logger.warning(f"Could not load SBERT model: {le}")

        if self._model is not None:
            try:
                # show_progress_bar=False prevents Windows stdout/tqdm [Errno 22] Invalid argument in uvicorn
                embedding = self._model.encode(
                    text,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Error generating model embedding: {e}")

        return self._generate_fallback_vector(text)

    def _generate_fallback_vector(self, text: str) -> List[float]:
        import hashlib
        words = text.lower().split()
        vec = np.zeros(384, dtype=np.float32)
        for idx, word in enumerate(words):
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            dim = h % 384
            val = ((h >> 8) % 1000) / 1000.0
            vec[dim] += val
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

embedding_service = SentenceTransformerEmbeddingService()
