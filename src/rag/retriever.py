"""FAISS vector store for in-memory retrieval per session."""

from typing import List, Tuple, Optional
from dataclasses import dataclass, field
import numpy as np

from src.rag.embedder import Embedder


@dataclass
class Document:
    """Document with text and metadata."""

    text: str
    metadata: dict = field(default_factory=dict)


def create_retriever(embedder: Embedder) -> "BaseRetriever":
    """Factory function to create appropriate retriever based on FAISS availability.

    Args:
        embedder: Embedder instance for creating embeddings

    Returns:
        FAISSRetriever if FAISS is available, otherwise SimpleRetriever
    """
    try:
        import faiss

        return FAISSRetriever(embedder)
    except ImportError:
        return SimpleRetriever(embedder)


class BaseRetriever:
    """Abstract base class for retrievers."""

    def __init__(self, embedder: Embedder):
        """Initialize base retriever.

        Args:
            embedder: Embedder instance for creating embeddings
        """
        self.embedder = embedder
        self.documents: List[Document] = []

    def add_documents(self, texts: List[str], metadata: Optional[List[dict]] = None):
        """Add documents to the index.

        Args:
            texts: List of document texts
            metadata: Optional list of metadata dicts
        """
        raise NotImplementedError

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[Document, float]]:
        """Retrieve top-k documents with similarity scores.

        Args:
            query: Query text
            k: Number of results to return

        Returns:
            List of (Document, score) tuples
        """
        raise NotImplementedError

    def clear(self):
        """Remove all documents and reset index."""
        raise NotImplementedError


class FAISSRetriever(BaseRetriever):
    """Per-session FAISS index with document store."""

    def __init__(self, embedder: Embedder):
        """Initialize FAISS retriever.

        Args:
            embedder: Embedder instance for creating embeddings
        """
        super().__init__(embedder)
        self.index = None
        # Dimension is now dynamic based on embedder model (768 for Qwen, 384 for MiniLM)

    def _init_index(self):
        """Initialize FAISS index if not already done."""
        if self.index is None:
            import faiss

            # Get dimension from embedder (dynamic: 768 for Qwen, 384 for MiniLM)
            dimension = self.embedder.dimension
            self.index = faiss.IndexFlatIP(dimension)

    def add_documents(self, texts: List[str], metadata: Optional[List[dict]] = None):
        """Add documents to the index.

        Args:
            texts: List of document texts
            metadata: Optional list of metadata dicts
        """
        if not texts:
            return

        # Create embeddings
        embeddings = self.embedder.embed_documents(texts)

        # Initialize index if needed
        self._init_index()

        # Add to FAISS
        if self.index is not None:
            self.index.add(embeddings.astype(np.float32))

        # Store documents
        for i, text in enumerate(texts):
            meta = metadata[i] if metadata and i < len(metadata) else {}
            self.documents.append(Document(text=text, metadata=meta))

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[Document, float]]:
        """Retrieve top-k documents with similarity scores.

        Args:
            query: Query text
            k: Number of results to return

        Returns:
            List of (Document, score) tuples, sorted by score descending
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        # Create query embedding
        query_emb = self.embedder.embed_query(query).reshape(1, -1).astype(np.float32)

        # Search FAISS
        scores, indices = self.index.search(query_emb, min(k, self.index.ntotal))

        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(self.documents):
                results.append((self.documents[idx], float(score)))

        return results

    def clear(self):
        """Remove all documents and reset index."""
        self.index = None
        self.documents = []


class SimpleMockIndex:
    """Mock index object for SimpleRetriever to match FAISS API."""

    def __init__(self):
        self.ntotal = 0

    def add(self, count):
        self.ntotal += count


class SimpleRetriever(BaseRetriever):
    """Fallback retriever without FAISS using simple cosine similarity."""

    def __init__(self, embedder: Embedder):
        """Initialize simple retriever."""
        super().__init__(embedder)
        self._mock_index = SimpleMockIndex()
        self.index = self._mock_index  # Expose for API compatibility
        self._embeddings: Optional[np.ndarray] = None
        # Dimension is dynamic based on embedder (768 for Qwen, 384 for MiniLM)

    def _init_index(self):
        """No-op for simple retriever."""
        pass

    def add_documents(self, texts: List[str], metadata: Optional[List[dict]] = None):
        """Add documents with simple storage.

        Args:
            texts: List of document texts
            metadata: Optional list of metadata dicts
        """
        if not texts:
            return

        # Create embeddings
        embeddings = self.embedder.embed_documents(texts)

        # Store embeddings
        if self._embeddings is None:
            self._embeddings = embeddings
        else:
            self._embeddings = np.vstack([self._embeddings, embeddings])

        # Store documents
        for i, text in enumerate(texts):
            meta = metadata[i] if metadata and i < len(metadata) else {}
            self.documents.append(Document(text=text, metadata=meta))

        # Update mock index count
        self._mock_index.ntotal = len(self.documents)

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[Document, float]]:
        """Retrieve using cosine similarity.

        Args:
            query: Query text
            k: Number of results

        Returns:
            List of (Document, score) tuples
        """
        if self._embeddings is None or len(self.documents) == 0:
            return []

        # Create query embedding - already normalized by embedder
        query_emb = self.embedder.embed_query(query)

        # Compute cosine similarity without redundant normalization
        # (embedder already normalizes with normalize_embeddings=True)
        similarities = np.dot(self._embeddings, query_emb)

        # Get top-k
        k = min(k, len(self.documents))
        top_indices = np.argsort(similarities)[-k:][::-1]

        results = []
        for idx in top_indices:
            results.append((self.documents[idx], float(similarities[idx])))

        return results

    def clear(self):
        """Clear all data."""
        self._mock_index.ntotal = 0
        self.documents = []
        self._embeddings = None


# Backward compatibility alias
Retriever = FAISSRetriever
