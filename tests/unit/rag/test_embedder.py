"""Tests for Embedder - RAG text embeddings."""

import pytest
import numpy as np
from unittest.mock import Mock, patch

# Check if sentence-transformers is available
try:
    import sentence_transformers

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    pytest.skip("sentence-transformers not installed", allow_module_level=True)

from src.rag.embedder import Embedder, get_embedder


@pytest.fixture
def mock_model_qwen():
    """Create mock SentenceTransformer model with Qwen dimensions."""
    mock = Mock()
    mock._model_name = Embedder.PRIMARY_MODEL

    def mock_encode(texts, **kwargs):
        if isinstance(texts, str):
            return np.random.randn(1024)
        return np.random.randn(len(texts), 1024)

    mock.encode = mock_encode
    return mock


@pytest.fixture
def mock_model_minilm():
    """Create mock SentenceTransformer model with MiniLM dimensions."""
    mock = Mock()
    mock._model_name = Embedder.FALLBACK_MODEL

    def mock_encode(texts, **kwargs):
        if isinstance(texts, str):
            return np.random.randn(384)
        return np.random.randn(len(texts), 384)

    mock.encode = mock_encode
    return mock


def create_fallback_mock(mock_model_minilm):
    """Create a side_effect function that simulates Qwen failing and falling back to MiniLM."""
    call_count = [0]

    def side_effect(model_name):
        call_count[0] += 1
        if call_count[0] == 1 and "Qwen" in model_name:
            # First call with Qwen should fail
            raise Exception("Qwen not available")
        # Fallback to MiniLM
        return mock_model_minilm

    return side_effect


class TestEmbedder:
    """Test suite for Embedder."""

    def test_model_loads_lazily(self):
        """Test that model is not loaded until first use."""
        # Reset state
        Embedder._model = None
        Embedder._model_name = ""
        Embedder._dimension = 0

        # Create embedder but don't use it yet
        embedder = Embedder()

        # Model should be None before first use
        assert Embedder._model is None

    def test_embed_dimension_minilm(self, mock_model_minilm):
        """Test that embeddings have correct dimension with MiniLM."""
        # Create side_effect that simulates Qwen failing and falling back to MiniLM
        side_effect = create_fallback_mock(mock_model_minilm)

        with patch(
            "sentence_transformers.SentenceTransformer", side_effect=side_effect
        ):
            # Clear any cached model and create new embedder inside patch
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            embedding = embedder.embed_query("test query")

            assert isinstance(embedding, np.ndarray)
            assert embedding.shape == (384,)
            assert embedder.model_name == Embedder.FALLBACK_MODEL

    def test_embed_dimension_qwen(self, mock_model_qwen):
        """Test that embeddings have correct dimension with Qwen."""
        with patch(
            "sentence_transformers.SentenceTransformer", return_value=mock_model_qwen
        ):
            # Clear any cached model and create new embedder inside patch
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            embedding = embedder.embed_query("test query")

            assert isinstance(embedding, np.ndarray)
            assert embedding.shape == (1024,)
            assert embedder.model_name == Embedder.PRIMARY_MODEL

    def test_embed_documents_batch_minilm(self, mock_model_minilm):
        """Test embedding multiple documents with MiniLM."""
        side_effect = create_fallback_mock(mock_model_minilm)

        with patch(
            "sentence_transformers.SentenceTransformer", side_effect=side_effect
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            texts = ["First document", "Second document", "Third document"]
            embeddings = embedder.embed_documents(texts)

            assert isinstance(embeddings, np.ndarray)
            assert embeddings.shape == (3, 384)

    def test_embed_documents_batch_qwen(self, mock_model_qwen):
        """Test embedding multiple documents with Qwen."""
        with patch(
            "sentence_transformers.SentenceTransformer", return_value=mock_model_qwen
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            texts = ["First document", "Second document", "Third document"]
            embeddings = embedder.embed_documents(texts)

            assert isinstance(embeddings, np.ndarray)
            assert embeddings.shape == (3, 1024)

    def test_embed_query_and_docs_consistent(self, mock_model_qwen):
        """Test that query and document embeddings are compatible."""
        with patch(
            "sentence_transformers.SentenceTransformer", return_value=mock_model_qwen
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            query_emb = embedder.embed_query("test")
            doc_emb = embedder.embed_documents(["test"])

            # Should be able to compute similarity
            similarity = np.dot(query_emb, doc_emb[0])
            assert isinstance(similarity, (float, np.floating))

    def test_singleton_pattern(self, mock_model_qwen):
        """Test that get_embedder returns singleton."""
        with patch(
            "sentence_transformers.SentenceTransformer", return_value=mock_model_qwen
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0

            embedder1 = get_embedder()
            embedder2 = get_embedder()

            # Should be same instance
            assert embedder1 is embedder2

    def test_empty_text_list(self, mock_model_minilm):
        """Test handling of empty text list."""
        side_effect = create_fallback_mock(mock_model_minilm)

        with patch(
            "sentence_transformers.SentenceTransformer", side_effect=side_effect
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            embeddings = embedder.embed_documents([])

            assert isinstance(embeddings, np.ndarray)
            assert embeddings.shape[0] == 0
            assert embeddings.shape[1] == 384  # Should match model dimension

    def test_single_document_as_list(self, mock_model_minilm):
        """Test embedding single document in list."""
        side_effect = create_fallback_mock(mock_model_minilm)

        with patch(
            "sentence_transformers.SentenceTransformer", side_effect=side_effect
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            embeddings = embedder.embed_documents(["single document"])

            assert embeddings.shape == (1, 384)

    def test_normalize_embeddings(self, mock_model_qwen):
        """Test that embeddings are valid numpy arrays."""
        with patch(
            "sentence_transformers.SentenceTransformer", return_value=mock_model_qwen
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            embedding = embedder.embed_query("test")

            # Check it's a valid numpy array with finite values
            assert np.isfinite(embedding).all()
            assert embedding.shape == (1024,)

    def test_special_characters(self, mock_model_minilm):
        """Test embedding text with special characters."""
        side_effect = create_fallback_mock(mock_model_minilm)

        with patch(
            "sentence_transformers.SentenceTransformer", side_effect=side_effect
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            text = "Café résumé naïve 🎉 <script>alert('test')</script>"
            embedding = embedder.embed_query(text)

            assert embedding.shape == (384,)
            assert np.isfinite(embedding).all()

    def test_long_text(self, mock_model_minilm):
        """Test embedding very long text."""
        side_effect = create_fallback_mock(mock_model_minilm)

        with patch(
            "sentence_transformers.SentenceTransformer", side_effect=side_effect
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            long_text = "word " * 1000
            embedding = embedder.embed_query(long_text)

            assert embedding.shape == (384,)
            assert np.isfinite(embedding).all()

    def test_qwen_query_prompts(self, mock_model_qwen):
        """Test that Qwen model uses query-specific prompts."""
        with patch(
            "sentence_transformers.SentenceTransformer", return_value=mock_model_qwen
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            # Mock encode to capture the kwargs
            encode_calls = []

            def tracking_encode(texts, **kwargs):
                encode_calls.append((texts, kwargs))
                if isinstance(texts, str):
                    return np.random.randn(1024)
                return np.random.randn(len(texts), 1024)

            Embedder._model = Mock()
            Embedder._model.encode = tracking_encode
            Embedder._model_name = Embedder.PRIMARY_MODEL
            Embedder._dimension = 1024

            # Query embedding should include prompt_name
            embedder.embed_query("What is AI?")
            assert len(encode_calls) == 1
            assert encode_calls[0][1].get("prompt_name") == "query"

            # Document embedding should not include prompt_name
            encode_calls.clear()
            embedder.embed_documents(["AI is artificial intelligence"])
            assert len(encode_calls) == 1
            assert "prompt_name" not in encode_calls[0][1]

    def test_model_dimension_property(self, mock_model_qwen):
        """Test that dimension property works correctly."""
        with patch(
            "sentence_transformers.SentenceTransformer", return_value=mock_model_qwen
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            # Should trigger model load
            assert embedder.dimension == 1024

    def test_model_name_property(self, mock_model_qwen):
        """Test that model_name property works correctly."""
        with patch(
            "sentence_transformers.SentenceTransformer", return_value=mock_model_qwen
        ):
            Embedder._model = None
            Embedder._model_name = ""
            Embedder._dimension = 0
            embedder = Embedder()

            # Should trigger model load
            assert embedder.model_name == Embedder.PRIMARY_MODEL
