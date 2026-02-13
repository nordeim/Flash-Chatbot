"""RAG-Lite module for document Q&A."""

from src.rag.document_processor import DocumentProcessor, DocumentProcessingError
from src.rag.embedder import Embedder, get_embedder
from src.rag.retriever import Retriever, SimpleRetriever, Document
from src.rag.exceptions import RAGError

__all__ = [
    "DocumentProcessor",
    "DocumentProcessingError",
    "Embedder",
    "get_embedder",
    "Retriever",
    "SimpleRetriever",
    "Document",
    "RAGError",
]