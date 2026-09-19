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
        """Load SBERT model via FastEmbed ONNX runtime into memory ONCE during startup."""
        if self._model is not None and not force:
            return

        if self._load_attempted and self._model is None and not force:
            return

        self._load_attempted = True
        logger.info(f"Loading FastEmbed ONNX embedding model '{model_name}'...")
        try:
            # pyrefly: ignore [missing-import]
            from fastembed import TextEmbedding
            
            # Map standard model names to FastEmbed model identifiers
            model_id = f"sentence-transformers/{model_name}" if "all-MiniLM" in model_name and not model_name.startswith("sentence-transformers/") else model_name
            
            logger.info(f"Initializing FastEmbed TextEmbedding '{model_id}' on ONNX CPU runtime...")
            self._model = TextEmbedding(model_name=model_id)
            logger.info(f"Successfully loaded FastEmbed ONNX embedding model '{model_id}'.")
        except Exception as e:
            logger.error(f"Failed to load FastEmbed model '{model_name}': {e}")
            self._model = None
            raise RuntimeError(f"Could not initialize FastEmbed ONNX embedding model: {e}")

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def _normalize(self, vec: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vec)
        if norm > 0:
            return vec / norm
        return vec

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a normalized 384-dimensional vector embedding for the input text using FastEmbed ONNX.
        """
        if not text:
            return [0.0] * 384

        if self._model is None and not self._load_attempted:
            try:
                self.load_model()
            except Exception as le:
                logger.warning(f"Could not load FastEmbed model: {le}")

        if self._model is not None:
            try:
                embeddings = list(self._model.embed([text]))
                vec = self._normalize(embeddings[0])
                return vec.tolist()
            except Exception as e:
                logger.error(f"Error generating FastEmbed model embedding: {e}")

        return self._generate_fallback_vector(text)

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate normalized 384-dimensional vector embeddings for a list of input texts in batch using FastEmbed ONNX.
        """
        if not texts:
            return []

        if self._model is None and not self._load_attempted:
            try:
                self.load_model()
            except Exception as le:
                logger.warning(f"Could not load FastEmbed model: {le}")

        if self._model is not None:
            try:
                embeddings = list(self._model.embed(texts, batch_size=32))
                return [self._normalize(vec).tolist() for vec in embeddings]
            except Exception as e:
                logger.error(f"Error generating FastEmbed model embeddings: {e}")

        return [self.generate_embedding(text) for text in texts]

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
