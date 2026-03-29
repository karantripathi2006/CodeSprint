"""
Embedding Service
=================
Manages sentence-transformer model loading and text encoding.
Singleton pattern ensures the model is loaded only once.
"""

import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Singleton model instance
_model_instance = None
_model_name = None


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with a model name. Model is loaded lazily."""
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        """Load the sentence-transformer model (lazy loading)."""
        global _model_instance, _model_name
        if _model_instance is not None and _model_name == self.model_name:
            self._model = _model_instance
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            _model_instance = self._model
            _model_name = self.model_name
            logger.info(f"Model {self.model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self._model = None

    def encode(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        Encode a list of texts into embeddings.
        
        Args:
            texts: List of strings to encode
            
        Returns:
            NumPy array of shape (len(texts), embedding_dim) or None on failure
        """
        if self._model is None:
            self._load_model()

        if self._model is None:
            logger.warning("Model not available, cannot encode texts")
            return None

        try:
            embeddings = self._model.encode(texts, show_progress_bar=False)
            return embeddings
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return None

    def encode_single(self, text: str) -> Optional[np.ndarray]:
        """Encode a single text string."""
        result = self.encode([text])
        return result[0] if result is not None else None

    def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts."""
        embeddings = self.encode([text1, text2])
        if embeddings is None:
            return 0.0

        # Cosine similarity
        a, b = embeddings[0], embeddings[1]
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
