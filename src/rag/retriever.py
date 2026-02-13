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


class Retriever:
    """Per-session FAISS index with document store.
    
    Falls back to SimpleRetriever if FAISS is not available.
    """
    
    def __new__(cls, embedder: Embedder):
        """Create appropriate retriever based on FAISS availability."""
        if cls._check_faiss():
            instance = super().__new__(cls)
            instance._is_fallback = False
            return instance
        else:
            # Return SimpleRetriever instance instead
            instance = super().__new__(SimpleRetriever)
            instance._is_fallback = True
            return instance
    
    def __init__(self, embedder: Embedder):
        """Initialize retriever.
        
        Args:
            embedder: Embedder instance for creating embeddings
        """
        self.embedder = embedder
        self.index = None
        self.documents: List[Document] = []
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        self._faiss_available = True
    
    @staticmethod
    def _check_faiss() -> bool:
        """Check if FAISS is available."""
        try:
            import faiss
            return True
        except ImportError:
            return False
    
    def _init_index(self):
        """Initialize FAISS index if not already done."""
        if self.index is None and self._faiss_available:
            import faiss
            self.index = faiss.IndexFlatIP(self.dimension)
    
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


class SimpleRetriever(Retriever):
    """Fallback retriever without FAISS using simple cosine similarity."""
    
    def __init__(self, embedder: Embedder):
        """Initialize simple retriever."""
        self.embedder = embedder
        self._mock_index = SimpleMockIndex()
        self.index = self._mock_index  # Expose for API compatibility
        self.documents: List[Document] = []
        self._embeddings: Optional[np.ndarray] = None
        self.dimension = 384
    
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
        
        # Create query embedding
        query_emb = self.embedder.embed_query(query)
        query_emb = query_emb / np.linalg.norm(query_emb)
        
        # Compute cosine similarity
        embeddings_norm = self._embeddings / np.linalg.norm(self._embeddings, axis=1, keepdims=True)
        similarities = np.dot(embeddings_norm, query_emb)
        
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
