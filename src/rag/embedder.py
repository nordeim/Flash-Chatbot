"""Lightweight local embeddings using sentence-transformers.

Primary model: Qwen/Qwen3-Embedding-0.6B (high-quality, task-aware embeddings)
Fallback model: all-MiniLM-L6-v2 (lightweight, widely compatible)
"""

import numpy as np
from typing import List, cast


class Embedder:
    """Wrapper for SentenceTransformer with lazy loading and model fallback."""

    _model = None
    _model_name: str = ""
    _dimension: int = 0

    # Model configurations
    PRIMARY_MODEL = "Qwen/Qwen3-Embedding-0.6B"
    FALLBACK_MODEL = "all-MiniLM-L6-v2"

    @classmethod
    def get_model(cls):
        """Load model once and cache (lazy loading), with fallback support."""
        if cls._model is None:
            from sentence_transformers import SentenceTransformer

            # Try primary model first
            try:
                cls._model = SentenceTransformer(cls.PRIMARY_MODEL)
                cls._model_name = cls.PRIMARY_MODEL
                cls._dimension = 1024  # Qwen3-Embedding-0.6B dimension
            except Exception:
                # Fallback to lightweight model
                cls._model = SentenceTransformer(cls.FALLBACK_MODEL)
                cls._model_name = cls.FALLBACK_MODEL
                cls._dimension = 384  # all-MiniLM-L6-v2 dimension

        return cls._model

    @property
    def dimension(self) -> int:
        """Get the dimension of embeddings based on loaded model."""
        if self._dimension == 0:
            self.get_model()  # Trigger model loading
        return self._dimension

    @property
    def model_name(self) -> str:
        """Get the name of the loaded model."""
        if self._model_name == "":
            self.get_model()  # Trigger model loading
        return self._model_name

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for a list of documents.

        Args:
            texts: List of document texts

        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([]).reshape(0, self.dimension)

        model = self.get_model()
        embeddings = model.encode(texts, normalize_embeddings=True)

        # Ensure we return a numpy array
        return cast(np.ndarray, embeddings)

    def embed_query(self, text: str) -> np.ndarray:
        """Create embedding for a single query.

        Args:
            text: Query text

        Returns:
            Numpy array
        """
        model = self.get_model()

        # Qwen model supports query-specific prompting for better retrieval
        if self._model_name == self.PRIMARY_MODEL:
            embedding = model.encode(
                text, prompt_name="query", normalize_embeddings=True
            )
        else:
            embedding = model.encode(text, normalize_embeddings=True)

        # Ensure we return a numpy array
        return cast(np.ndarray, embedding)


# Singleton instance
_embedder_instance = None


def get_embedder() -> Embedder:
    """Get or create singleton Embedder instance.

    Returns:
        Embedder singleton
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = Embedder()
    return _embedder_instance
