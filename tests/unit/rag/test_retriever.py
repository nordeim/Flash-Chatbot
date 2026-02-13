"""Tests for Retriever - RAG vector store and retrieval."""

import pytest
import numpy as np
from unittest.mock import Mock

from src.rag.retriever import Retriever, Document


class TestRetriever:
    """Test suite for Retriever."""

    @pytest.fixture
    def mock_embedder(self):
        """Create mock embedder that returns fixed embeddings."""
        embedder = Mock()
        # Return normalized embeddings for consistent testing
        def mock_embed_docs(texts):
            embeddings = []
            for i, text in enumerate(texts):
                # Create deterministic embedding based on text
                emb = np.zeros(384)
                emb[i % 384] = 1.0  # One-hot encoding
                emb = emb / np.linalg.norm(emb)  # Normalize
                embeddings.append(emb)
            return np.array(embeddings)
        
        def mock_embed_query(text):
            # Return same pattern as documents for matching
            emb = np.zeros(384)
            emb[hash(text) % 384] = 1.0
            emb = emb / np.linalg.norm(emb)
            return emb
        
        embedder.embed_documents = mock_embed_docs
        embedder.embed_query = mock_embed_query
        return embedder

    @pytest.fixture
    def retriever(self, mock_embedder):
        """Create Retriever instance with mock embedder."""
        return Retriever(mock_embedder)

    def test_add_documents_updates_index(self, retriever):
        """Test that adding documents updates the FAISS index."""
        texts = ["First document", "Second document", "Third document"]
        retriever.add_documents(texts)
        
        assert retriever.index is not None
        assert retriever.index.ntotal == 3

    def test_retrieve_returns_correct_k(self, retriever):
        """Test that retrieval returns correct number of results."""
        texts = [
            "The cat sat on the mat",
            "The dog ran in the park",
            "The bird flew in the sky",
            "The fish swam in the pond"
        ]
        retriever.add_documents(texts)
        
        results = retriever.retrieve("cat mat", k=2)
        
        assert len(results) == 2
        assert isinstance(results[0], tuple)
        assert isinstance(results[0][0], Document)
        assert isinstance(results[0][1], float)  # Score

    def test_empty_index_returns_empty_list(self, retriever):
        """Test that empty index returns empty results."""
        results = retriever.retrieve("query", k=3)
        
        assert results == []
        assert isinstance(results, list)

    def test_clear_removes_all_documents(self, retriever):
        """Test that clear removes all documents and resets index."""
        texts = ["First", "Second", "Third"]
        retriever.add_documents(texts)
        
        retriever.clear()
        
        assert retriever.index.ntotal == 0
        assert len(retriever.documents) == 0

    def test_retrieve_with_metadata(self, retriever):
        """Test that metadata is preserved in documents."""
        texts = ["Document one", "Document two"]
        metadata = [{"source": "file1.txt"}, {"source": "file2.txt"}]
        retriever.add_documents(texts, metadata=metadata)
        
        results = retriever.retrieve("document", k=2)
        
        assert len(results) == 2
        # Check metadata is preserved
        for doc, _ in results:
            assert doc.metadata is not None
            assert "source" in doc.metadata

    def test_retrieve_k_larger_than_index(self, retriever):
        """Test retrieving more results than available documents."""
        texts = ["Only one document"]
        retriever.add_documents(texts)
        
        results = retriever.retrieve("query", k=10)
        
        assert len(results) == 1  # Should return all available

    def test_add_documents_in_batches(self, retriever):
        """Test adding documents in multiple batches."""
        retriever.add_documents(["First batch"])
        retriever.add_documents(["Second batch"])
        retriever.add_documents(["Third batch"])
        
        assert retriever.index.ntotal == 3

    def test_document_text_stored_correctly(self, retriever):
        """Test that document text is stored and returned correctly."""
        text = "This is the exact text that should be stored"
        retriever.add_documents([text])
        
        results = retriever.retrieve("exact text", k=1)
        
        assert len(results) == 1
        assert results[0][0].text == text

    def test_similarity_scores_in_range(self, retriever):
        """Test that similarity scores are between 0 and 1."""
        texts = ["Document A", "Document B", "Document C"]
        retriever.add_documents(texts)
        
        results = retriever.retrieve("document", k=3)
        
        for doc, score in results:
            assert 0 <= score <= 1.0

    def test_retrieve_relevance_ordering(self, retriever):
        """Test that results are ordered by relevance (highest score first)."""
        # Add documents with different content
        texts = [
            "Machine learning is fascinating",
            "Python is a programming language",
            "Deep learning uses neural networks",
            "I like pizza"
        ]
        retriever.add_documents(texts)
        
        # Query about machine learning
        results = retriever.retrieve("machine learning neural networks", k=3)
        
        # Scores should be in descending order
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_empty_text_list_adds_nothing(self, retriever):
        """Test that adding empty list doesn't change index."""
        retriever.add_documents([])
        
        assert retriever.index.ntotal == 0
        assert len(retriever.documents) == 0
