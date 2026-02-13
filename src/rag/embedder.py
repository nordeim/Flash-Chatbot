"""Lightweight local embeddings using sentence-transformers."""

import numpy as np
from typing import List


class Embedder:
    """Wrapper for SentenceTransformer with lazy loading."""
    
    _model = None
    _dimension = 384  # all-MiniLM-L6-v2 dimension
    
    @classmethod
    def get_model(cls):
        """Load model once and cache (lazy loading)."""
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model
    
    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for a list of documents.
        
        Args:
            texts: List of document texts
            
        Returns:
            Numpy array of embeddings with shape (len(texts), 384)
        """
        if not texts:
            return np.array([]).reshape(0, self._dimension)
        
        model = self.get_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings
    
    def embed_query(self, text: str) -> np.ndarray:
        """Create embedding for a single query.
        
        Args:
            text: Query text
            
        Returns:
            Numpy array of shape (384,)
        """
        model = self.get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding


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
