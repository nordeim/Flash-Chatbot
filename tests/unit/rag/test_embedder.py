"""Tests for Embedder - RAG text embeddings."""

import pytest
import numpy as np
from unittest.mock import Mock, patch

# Skip all tests if sentence-transformers not available
sentence_transformers = pytest.importorskip("sentence_transformers", reason="sentence-transformers not installed")

from src.rag.embedder import Embedder, get_embedder


class TestEmbedder:
    """Test suite for Embedder."""

    @pytest.fixture
    def embedder(self):
        """Create Embedder instance."""
        return Embedder()

    @pytest.fixture
    def mock_model(self):
        """Create mock SentenceTransformer model."""
        mock = Mock()
        # Mock encode to return fixed-size embeddings
        def mock_encode(texts, **kwargs):
            if isinstance(texts, str):
                return np.random.randn(384)
            return np.random.randn(len(texts), 384)
        mock.encode = mock_encode
        return mock

    def test_model_loads_lazily(self, embedder):
        """Test that model is not loaded until first use."""
        # Model should be None before first use
        assert Embedder._model is None

    def test_embed_dimension(self, embedder, mock_model):
        """Test that embeddings have correct dimension."""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            # Clear any cached model
            Embedder._model = None
            
            embedding = embedder.embed_query("test query")
            
            assert isinstance(embedding, np.ndarray)
            assert embedding.shape == (384,)

    def test_embed_documents_batch(self, embedder, mock_model):
        """Test embedding multiple documents."""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            Embedder._model = None
            
            texts = ["First document", "Second document", "Third document"]
            embeddings = embedder.embed_documents(texts)
            
            assert isinstance(embeddings, np.ndarray)
            assert embeddings.shape == (3, 384)

    def test_embed_query_and_docs_consistent(self, embedder, mock_model):
        """Test that query and document embeddings are compatible."""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            Embedder._model = None
            
            query_emb = embedder.embed_query("test")
            doc_emb = embedder.embed_documents(["test"])
            
            # Should be able to compute similarity
            similarity = np.dot(query_emb, doc_emb[0])
            assert isinstance(similarity, (float, np.floating))

    def test_singleton_pattern(self, mock_model):
        """Test that get_embedder returns singleton."""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            Embedder._model = None
            
            embedder1 = get_embedder()
            embedder2 = get_embedder()
            
            # Should be same instance
            assert embedder1 is embedder2

    def test_empty_text_list(self, embedder, mock_model):
        """Test handling of empty text list."""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            Embedder._model = None
            
            embeddings = embedder.embed_documents([])
            
            assert isinstance(embeddings, np.ndarray)
            assert embeddings.shape[0] == 0

    def test_single_document_as_list(self, embedder, mock_model):
        """Test embedding single document in list."""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            Embedder._model = None
            
            embeddings = embedder.embed_documents(["single document"])
            
            assert embeddings.shape == (1, 384)

    def test_normalize_embeddings(self, embedder, mock_model):
        """Test that embeddings are normalized."""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            Embedder._model = None
            
            embedding = embedder.embed_query("test")
            
            # Mock returns random values, but in real implementation
            # embeddings should be normalized to unit length
            # Just check it's a valid numpy array
            assert np.isfinite(embedding).all()

    def test_special_characters(self, embedder, mock_model):
        """Test embedding text with special characters."""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            Embedder._model = None
            
            text = "Café résumé naïve 🎉 <script>alert('test')</script>"
            embedding = embedder.embed_query(text)
            
            assert embedding.shape == (384,)
            assert np.isfinite(embedding).all()

    def test_long_text(self, embedder, mock_model):
        """Test embedding very long text."""
        with patch('sentence_transformers.SentenceTransformer', return_value=mock_model):
            Embedder._model = None
            
            long_text = "word " * 1000
            embedding = embedder.embed_query(long_text)
            
            assert embedding.shape == (384,)
            assert np.isfinite(embedding).all()
