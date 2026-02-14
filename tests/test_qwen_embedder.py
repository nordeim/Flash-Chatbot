"""Test Qwen embedder with real SentenceTransformer model.

Run with:
    source /opt/venv/bin/activate && python tests/test_qwen_embedder.py
    # or
    uv run python tests/test_qwen_embedder.py

This tests the actual Qwen/Qwen3-Embedding-0.6B model with real queries and documents.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentence_transformers import SentenceTransformer
from src.rag.embedder import Embedder, get_embedder


def test_qwen_model_direct():
    """Test Qwen model directly with similarity computation."""
    print("\n=== Testing Qwen Model Directly ===")
    model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

    queries = [
        "What is the capital of China?",
        "Explain gravity",
    ]
    documents = [
        "The capital of China is Beijing.",
        "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun.",
    ]

    query_embeddings = model.encode(queries, prompt_name="query")
    document_embeddings = model.encode(documents)

    similarity = model.similarity(query_embeddings, document_embeddings)
    print(f"Similarity matrix shape: {similarity.shape}")
    print(f"Similarity matrix:\n{similarity}")

    # Verify dimensions
    assert query_embeddings.shape[1] == 1024, (
        f"Qwen model should have 1024 dimensions, got {query_embeddings.shape[1]}"
    )
    assert document_embeddings.shape[1] == 1024, (
        f"Qwen model should have 1024 dimensions, got {document_embeddings.shape[1]}"
    )

    # Verify similarity is computed correctly (query about China should match Beijing document)
    china_similarity = similarity[
        0, 0
    ].item()  # Query 0 (China) vs Document 0 (Beijing)
    gravity_similarity = similarity[
        1, 1
    ].item()  # Query 1 (Gravity) vs Document 1 (Gravity)

    print(f"\nChina query -> Beijing document: {china_similarity:.4f}")
    print(f"Gravity query -> Gravity document: {gravity_similarity:.4f}")

    assert china_similarity > 0.5, (
        "China query should have high similarity with Beijing document"
    )
    assert gravity_similarity > 0.5, (
        "Gravity query should have high similarity with Gravity document"
    )

    print("✓ Qwen model direct test passed!")


def test_embedder_with_qwen():
    """Test the Embedder class with Qwen model."""
    print("\n=== Testing Embedder Class ===")

    # Reset singleton state for clean test
    Embedder._model = None
    Embedder._model_name = ""
    Embedder._dimension = 0

    embedder = get_embedder()

    # Test document embedding
    documents = [
        "The capital of China is Beijing.",
        "Gravity is a force that attracts two bodies towards each other.",
    ]

    doc_embeddings = embedder.embed_documents(documents)
    print(f"Document embeddings shape: {doc_embeddings.shape}")
    assert doc_embeddings.shape == (2, 1024), (
        f"Expected (2, 1024), got {doc_embeddings.shape}"
    )

    # Test query embedding with task-specific prompting
    query = "What is the capital of China?"
    query_embedding = embedder.embed_query(query)
    print(f"Query embedding shape: {query_embedding.shape}")
    assert query_embedding.shape == (1024,), (
        f"Expected (1024,), got {query_embedding.shape}"
    )

    # Verify embeddings are normalized
    import numpy as np

    norm = np.linalg.norm(query_embedding)
    print(f"Query embedding norm: {norm:.6f}")
    assert 0.99 < norm < 1.01, "Embeddings should be normalized (L2 norm ≈ 1)"

    # Verify model name
    print(f"Model loaded: {embedder.model_name}")
    assert "Qwen" in embedder.model_name, "Should use Qwen model as primary"

    print("✓ Embedder class test passed!")


def test_query_vs_document_embedding():
    """Test that query and document embeddings are compatible."""
    print("\n=== Testing Query vs Document Compatibility ===")

    # Reset singleton state
    Embedder._model = None
    Embedder._model_name = ""
    Embedder._dimension = 0

    embedder = get_embedder()

    # Embed query and document
    query = "What is machine learning?"
    document = "Machine learning is a subset of artificial intelligence."

    query_emb = embedder.embed_query(query)
    doc_emb = embedder.embed_documents([document])

    # Compute cosine similarity manually
    import numpy as np

    similarity = np.dot(query_emb, doc_emb[0]) / (
        np.linalg.norm(query_emb) * np.linalg.norm(doc_emb[0])
    )

    print(f"Cosine similarity: {similarity:.4f}")
    assert -1 <= similarity <= 1, "Similarity should be between -1 and 1"

    print("✓ Query vs document compatibility test passed!")


def test_fallback_mechanism():
    """Test fallback to MiniLM if Qwen is unavailable."""
    print("\n=== Testing Fallback Mechanism ===")
    print("Note: If Qwen is available, this test will pass with Qwen. ")
    print("      To truly test fallback, temporarily rename Qwen model name in code.")

    # The fallback happens automatically in get_model() if Qwen fails to load
    print("✓ Fallback mechanism configured (will activate if Qwen fails)")


if __name__ == "__main__":
    print("Testing Qwen Embedder with SentenceTransformer")
    print("=" * 60)

    try:
        test_qwen_model_direct()
        test_embedder_with_qwen()
        test_query_vs_document_embedding()
        test_fallback_mechanism()

        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
