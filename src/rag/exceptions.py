"""RAG-specific exceptions."""


class RAGError(Exception):
    """Base exception for RAG errors."""
    pass


class RetrievalError(RAGError):
    """Raised when document retrieval fails."""
    pass


class EmbeddingError(RAGError):
    """Raised when embedding creation fails."""
    pass
