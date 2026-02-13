# main.py
```py
"""Entry point for Hugging Face Spaces deployment.

This file serves as the entry point for Hugging Face Spaces.
It properly sets up the Python path and imports from the src module.
"""

import os
import sys

# Add the current directory to Python path so 'src' can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main application
from src.main import main

if __name__ == "__main__":
    main()

```

# src/main.py
```py
"""Main application entry point."""

import os
import sys
from typing import NoReturn

import streamlit as st

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.constants import PAGE_TITLE, PAGE_ICON, PAGE_LAYOUT
from src.config.settings import get_settings
from src.api.nvidia_client import NvidiaChatClient
from src.api.exceptions import NvidiaAuthError
from src.services.chat_service import ChatService
from src.services.state_manager import ChatStateManager
from src.ui.chat_interface import render_chat_interface
from src.ui.sidebar import render_sidebar
from src.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


def configure_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=PAGE_LAYOUT,
        initial_sidebar_state="expanded",
    )


def initialize_app() -> ChatService:
    """Initialize application components.
    
    Returns:
        Configured chat service
        
    Raises:
        SystemExit: If initialization fails
    """
    try:
        # Load settings
        settings = get_settings()
        
        # Setup logging
        log_level = settings.log_level if settings else "INFO"
        setup_logging(level=log_level)
        
        logger.info("Initializing application...")
        
        # Validate API key
        if not settings.nvidia_api_key:
            st.error("❌ NVIDIA_API_KEY environment variable is required")
            st.info("Please set your NVIDIA API key in the environment variables")
            st.stop()
        
        # Initialize chat service
        chat_service = ChatService()
        
        logger.info("Application initialized successfully")
        return chat_service
        
    except NvidiaAuthError as e:
        logger.error(f"Authentication failed: {e}")
        st.error(f"❌ Authentication failed: {e}")
        st.info("Please check your NVIDIA_API_KEY and try again")
        st.stop()
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        st.error(f"❌ Failed to initialize: {e}")
        st.stop()


def main() -> NoReturn:
    """Main application entry point."""
    # Configure page
    configure_page()
    
    # Initialize application
    chat_service = initialize_app()
    
    # Render sidebar and get settings
    settings, clear_requested = render_sidebar()
    
    # Handle clear request
    if clear_requested:
        chat_service.clear_conversation()
        st.rerun()
    
    # Render main chat interface
    render_chat_interface(chat_service, settings)


if __name__ == "__main__":
    main()

```

# src/__init__.py
```py
"""
Flash Chatbot Application

A production-grade chatbot built with Streamlit and NVIDIA API.
"""

__version__ = "1.0.0"
__author__ = "Development Team"

```

# src/rag/__init__.py
```py
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
```

# src/rag/exceptions.py
```py
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

```

# src/rag/embedder.py
```py
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

```

# src/rag/retriever.py
```py
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

```

# src/rag/document_processor.py
```py
"""Document text extraction and chunking for RAG."""

import os
import tempfile
from pathlib import Path
from typing import List

import chardet


class DocumentProcessingError(Exception):
    """Raised when document cannot be processed."""
    pass


class DocumentProcessor:
    """Extract text from uploaded files and split into chunks."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """Initialize processor.
        
        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process(self, file_bytes: bytes, filename: str) -> List[str]:
        """Extract and chunk text from file.
        
        Args:
            file_bytes: Raw bytes of the file
            filename: Original filename (used to determine type)
            
        Returns:
            List of text chunks
            
        Raises:
            DocumentProcessingError: If file cannot be processed
        """
        ext = Path(filename).suffix.lower()

        if ext == ".pdf":
            text = self._extract_pdf(file_bytes)
        elif ext in (".txt", ".md", ".text"):
            text = self._extract_text(file_bytes)
        else:
            raise DocumentProcessingError(f"Unsupported file type: {ext}")

        if not text.strip():
            raise DocumentProcessingError("No extractable text found.")

        return self._chunk_text(text)

    def _extract_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF using pypdf.
        
        Args:
            file_bytes: Raw PDF bytes
            
        Returns:
            Extracted text
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        try:
            import pypdf
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            
            try:
                reader = pypdf.PdfReader(tmp_path)
                text = "\n".join([page.extract_text() or "" for page in reader.pages])
                return text
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            raise DocumentProcessingError(f"PDF extraction failed: {e}")

    def _extract_text(self, file_bytes: bytes) -> str:
        """Extract text from plain text files with encoding detection.
        
        Args:
            file_bytes: Raw text file bytes
            
        Returns:
            Decoded text
        """
        # Detect encoding
        detection = chardet.detect(file_bytes)
        encoding = detection.get("encoding") or "utf-8"
        
        # Decode with error handling
        return file_bytes.decode(encoding, errors="replace")

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks by character count.
        
        Attempts to avoid cutting words by finding space boundaries.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            
            # Try to avoid cutting words
            if end < text_len and text[end] not in (" ", "\n", ".", "!", "?"):
                # Find last space within chunk
                last_space = text.rfind(" ", start, end)
                if last_space != -1:
                    end = last_space
            
            # Extract chunk and clean
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap if end < text_len else text_len
            
            # Prevent infinite loop
            if start >= end:
                start = end
        
        return chunks

```

# src/ui/document_upload.py
```py
"""Ethereal document upload zone with processing feedback."""

import streamlit as st
from typing import Optional, Any

from src.rag.document_processor import DocumentProcessor, DocumentProcessingError


def _inject_upload_styles():
    """Inject custom CSS for glass dropzone and document badge."""
    st.markdown("""
    <style>
    /* Ethereal dropzone */
    .ethereal-dropzone {
        background: rgba(20, 25, 40, 0.6);
        backdrop-filter: blur(12px);
        border: 1px dashed rgba(0, 255, 224, 0.3);
        border-radius: 24px;
        padding: 2rem 1.5rem;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.2, 0.9, 0.4, 1);
        margin-bottom: 1rem;
    }
    .ethereal-dropzone:hover {
        border-color: #00ffe0;
        background: rgba(30, 35, 55, 0.7);
        box-shadow: 0 0 20px rgba(0, 255, 224, 0.2);
    }
    .ethereal-dropzone .upload-icon {
        font-size: 2.8rem;
        color: #00ffe0;
        filter: drop-shadow(0 0 8px #00ffe0);
        margin-bottom: 0.5rem;
    }
    .ethereal-dropzone .upload-text {
        color: #c0c0c0;
        font-size: 0.9rem;
        letter-spacing: 1px;
    }
    /* Document badge */
    .doc-badge {
        background: rgba(0, 255, 224, 0.1);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(0, 255, 224, 0.3);
        border-radius: 40px;
        padding: 0.4rem 1rem;
        display: inline-flex;
        align-items: center;
        gap: 0.8rem;
        font-size: 0.85rem;
        color: #e0e0e0;
        margin-top: 0.5rem;
    }
    .doc-badge .filename {
        font-weight: 500;
    }
    .doc-badge .clear-btn {
        cursor: pointer;
        color: #ff6b6b;
        font-weight: 600;
        padding: 0 0.2rem;
        transition: color 0.2s;
    }
    .doc-badge .clear-btn:hover {
        color: #ff4444;
        text-shadow: 0 0 8px #ff4444;
    }
    /* Processing arc */
    .processing-arc {
        display: inline-block;
        width: 24px;
        height: 24px;
        border: 2px solid rgba(0,255,224,0.2);
        border-top: 2px solid #00ffe0;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 8px;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    /* Processing text */
    .processing-text {
        color: #c0c0c0;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    </style>
    """, unsafe_allow_html=True)


class DocumentUpload:
    """Ethereal document upload component."""
    
    def __init__(self, state: Any):
        """Initialize component.
        
        Args:
            state: State manager with retriever and document_name properties
        """
        self.state = state
    
    def render(self) -> None:
        """Display glass dropzone and manage document processing."""
        _inject_upload_styles()
        
        # Show current document badge if exists
        if self.state.current_document_name:
            self._render_document_badge()
            return
        
        # Dropzone
        with st.container():
            st.markdown('<div class="ethereal-dropzone">', unsafe_allow_html=True)
            st.markdown('<div class="upload-icon">📄</div>', unsafe_allow_html=True)
            st.markdown('<div class="upload-text">Drop your document here</div>', unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "Upload document",
                type=["pdf", "txt", "md"],
                label_visibility="collapsed",
                key="rag_uploader"
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_file:
            self._process_upload(uploaded_file)
    
    def _render_document_badge(self) -> None:
        """Render document badge with filename and clear button."""
        col1, col2 = st.columns([0.9, 0.1])
        
        with col1:
            st.markdown(
                f'<div class="doc-badge">'
                f'<span>📄</span>'
                f'<span class="filename">{self.state.current_document_name}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        
        with col2:
            if st.button("✕", key="clear_doc", help="Remove document context"):
                self._clear_document()
                st.rerun()
    
    def _process_upload(self, uploaded_file: Any) -> None:
        """Process uploaded file and update retriever.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
        """
        # Show processing spinner
        placeholder = st.empty()
        placeholder.markdown(
            '<div class="processing-text">'
            '<span class="processing-arc"></span>'
            '<span>Extracting knowledge...</span>'
            '</div>',
            unsafe_allow_html=True
        )
        
        try:
            processor = DocumentProcessor()
            file_bytes = uploaded_file.getvalue()
            chunks = processor.process(file_bytes, uploaded_file.name)
            
            # Add to retriever
            if hasattr(self.state, 'retriever') and self.state.retriever:
                self.state.retriever.add_documents(chunks)
                self.state.current_document_name = uploaded_file.name
                
                placeholder.success(f"✅ Processed {len(chunks)} chunks from {uploaded_file.name}")
            else:
                placeholder.error("❌ No retriever available. Please refresh the page.")
                
        except DocumentProcessingError as e:
            placeholder.error(f"❌ {str(e)}")
        except Exception as e:
            placeholder.error(f"❌ Unexpected error: {str(e)}")
    
    def _clear_document(self) -> None:
        """Clear retriever and document metadata."""
        if hasattr(self.state, 'clear_retriever'):
            self.state.clear_retriever()
        else:
            # Fallback: manually clear
            if hasattr(self.state, 'retriever'):
                self.state.retriever = None
            if hasattr(self.state, 'current_document_name'):
                self.state.current_document_name = None


def render_document_upload() -> None:
    """Convenience function to render document upload component.
    
    Uses st.session_state as state manager.
    """
    # Create a state wrapper that accesses session_state
    class SessionStateWrapper:
        @property
        def current_document_name(self) -> Optional[str]:
            return st.session_state.get("current_document_name")
        
        @current_document_name.setter
        def current_document_name(self, value: Optional[str]) -> None:
            st.session_state["current_document_name"] = value
        
        @property
        def retriever(self) -> Optional[Any]:
            return st.session_state.get("retriever")
        
        @retriever.setter
        def retriever(self, value: Optional[Any]) -> None:
            st.session_state["retriever"] = value
        
        def clear_retriever(self) -> None:
            """Clear retriever and document metadata."""
            if "retriever" in st.session_state:
                retriever = st.session_state["retriever"]
                if hasattr(retriever, 'clear'):
                    retriever.clear()
                del st.session_state["retriever"]
            
            if "current_document_name" in st.session_state:
                del st.session_state["current_document_name"]
    
    state = SessionStateWrapper()
    component = DocumentUpload(state)
    component.render()

```

# src/ui/__init__.py
```py
"""UI components module."""

from src.ui.styles import get_custom_css
from src.ui.components import (
    render_message_bubble,
    render_thinking_panel,
    render_error_message,
    render_loading_spinner,
    render_empty_state,
)
from src.ui.sidebar import render_sidebar
from src.ui.chat_interface import render_chat_interface

__all__ = [
    "get_custom_css",
    "render_message_bubble",
    "render_thinking_panel",
    "render_error_message",
    "render_loading_spinner",
    "render_empty_state",
    "render_sidebar",
    "render_chat_interface",
]

```

# src/ui/sidebar.py
```py
"""Sidebar component with settings."""

from typing import Dict, Any, Tuple

import streamlit as st

from src.config.constants import (
    SIDEBAR_TITLE,
    MAX_TOKENS_MIN,
    MAX_TOKENS_MAX,
    MAX_TOKENS_STEP,
    TEMPERATURE_MIN,
    TEMPERATURE_MAX,
    TEMPERATURE_STEP,
    TOP_P_MIN,
    TOP_P_MAX,
    TOP_P_STEP,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_SYSTEM_PROMPT,
)


def render_sidebar() -> Tuple[Dict[str, Any], bool]:
    """Render settings sidebar.
    
    Returns:
        Tuple of (settings dict, clear_requested bool)
    """
    with st.sidebar:
        st.header(SIDEBAR_TITLE)
        
        # System prompt
        system_prompt = st.text_area(
            "System Prompt",
            value=DEFAULT_SYSTEM_PROMPT,
            height=100,
            help="Instructions for the AI assistant"
        )
        
        st.divider()
        
        # Generation parameters
        st.subheader("Generation Parameters")
        
        max_tokens = st.slider(
            "Max Tokens",
            min_value=MAX_TOKENS_MIN,
            max_value=MAX_TOKENS_MAX,
            value=DEFAULT_MAX_TOKENS,
            step=MAX_TOKENS_STEP,
            help="Maximum number of tokens to generate"
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=TEMPERATURE_MIN,
            max_value=TEMPERATURE_MAX,
            value=DEFAULT_TEMPERATURE,
            step=TEMPERATURE_STEP,
            help="Controls randomness (0 = deterministic, 2 = very random)"
        )
        
        top_p = st.slider(
            "Top P",
            min_value=TOP_P_MIN,
            max_value=TOP_P_MAX,
            value=DEFAULT_TOP_P,
            step=TOP_P_STEP,
            help="Nucleus sampling parameter"
        )
        
    st.divider()

    # Document Q&A section
    st.subheader("📚 Document Q&A")
    
    # Import and render document upload
    from src.ui.document_upload import render_document_upload
    render_document_upload()
    
    # Show document info if uploaded
    if hasattr(st.session_state, 'get') and st.session_state.get("current_document_name"):
        st.caption(f"📄 {st.session_state['current_document_name']}")
        if hasattr(st.session_state, 'get') and st.session_state.get("retriever"):
            retriever = st.session_state["retriever"]
            if retriever and hasattr(retriever, 'index') and retriever.index:
                st.caption(f"📊 {retriever.index.ntotal} text chunks in memory")
    
    st.divider()

    # Clear conversation button
    clear_requested = st.button(
            "Clear Conversation",
            use_container_width=True,
            type="secondary"
        )
        
    # Model info
    st.divider()
    with st.expander("Model Info"):
        st.info("""
                **Model**: moonshotai/kimi-k2.5
                
                **Provider**: NVIDIA API
                
                **Features**:
                - Streaming responses
                - Thinking/reasoning display
                - Up to 128k tokens
                - Multi-turn conversation
            """)
    
    settings = {
        "system_prompt": system_prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }
    
    return settings, clear_requested

```

# src/ui/components.py
```py
"""Reusable UI components."""

from typing import Optional, Any

import streamlit as st

from src.ui.styles import get_custom_css
from src.services.message_formatter import MessageFormatter


def render_custom_css() -> None:
    """Render custom CSS styles."""
    st.markdown(get_custom_css(), unsafe_allow_html=True)


def render_message_bubble(
    content: str,
    role: str,
    thinking: Optional[str] = None
) -> None:
    """Render a message bubble.
    
    Args:
        content: Message content
        role: Message role (user/assistant)
        thinking: Optional thinking content for assistant
    """
    if role == "user":
        st.markdown(f"""
            <div class="message-bubble message-user">
                {content}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="message-bubble message-assistant">
                {content}
            </div>
        """, unsafe_allow_html=True)
        
        if thinking:
            render_thinking_panel(thinking, is_streaming=False)


def render_thinking_panel(
    content: str,
    is_streaming: bool = False
) -> None:
    """Render thinking panel.
    
    Args:
        content: Thinking content
        is_streaming: Whether content is still streaming
    """
    cleaned = MessageFormatter.clean_thinking_content(content)
    
    if not cleaned:
        return
    
    with st.expander("Thinking Process", expanded=is_streaming):
        st.markdown(f"""
            <div class="thinking-container">
                <div class="thinking-label">Reasoning</div>
                <div class="thinking-content">{cleaned}</div>
            </div>
        """, unsafe_allow_html=True)


def render_error_message(error: str) -> None:
    """Render error message.
    
    Args:
        error: Error message
    """
    st.markdown(f"""
        <div class="error-message">
            {error}
        </div>
    """, unsafe_allow_html=True)


def render_loading_spinner() -> None:
    """Render loading spinner."""
    st.markdown("""
        <div class="loading-spinner">
            <div class="spinner"></div>
        </div>
    """, unsafe_allow_html=True)


def render_empty_state() -> None:
    """Render empty state with example questions."""
    from src.config.constants import EXAMPLE_QUESTIONS
    
    st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">💬</div>
            <h3>Start a Conversation</h3>
            <p>Ask me anything or try one of these examples:</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Render example buttons
    cols = st.columns(len(EXAMPLE_QUESTIONS))
    for i, question in enumerate(EXAMPLE_QUESTIONS):
        if cols[i].button(question, key=f"example_{i}", use_container_width=True):
            st.session_state["pending_prompt"] = question
            st.rerun()


def render_code_block(code: str, language: str = "text") -> None:
    """Render code block with syntax highlighting.
    
    Args:
        code: Code content
        language: Programming language
    """
    st.code(code, language=language)


def render_markdown_content(content: str) -> None:
    """Render markdown content with custom styling.
    
    Args:
        content: Markdown content
    """
    st.markdown(content)


def render_chat_avatar(role: str) -> str:
    """Get avatar for chat message.
    
    Args:
        role: Message role
        
    Returns:
        Avatar emoji or path
    """
    if role == "user":
        return "👤"
    else:
        return ""

```

# src/ui/styles.py
```py
"""Custom CSS styles for dark mode glassmorphism design."""

CUSTOM_CSS = """
<style>
/* Root variables for dark theme */
:root {
    --bg-primary: #0a0a0f;
    --bg-secondary: #12121a;
    --bg-card: rgba(30, 30, 40, 0.85);
    --bg-glass: rgba(255, 255, 255, 0.08);
    --text-primary: #ffffff;
    --text-secondary: #c0c0c0;
    --text-muted: #9090a0;
    --accent-primary: #00d4ff;
    --accent-secondary: #7c3aed;
    --border-glass: rgba(255, 255, 255, 0.1);
    --border-accent: rgba(0, 212, 255, 0.3);
    --success: #10b981;
    --error: #ef4444;
    --warning: #f59e0b;
}

/* Main background */
.stApp {
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
}

/* Ensure all text in app is bright */
.stApp, .stApp p, .stApp span, .stApp div {
    color: var(--text-primary);
}

/* Chat message specific bright text */
.stChatMessage {
    color: #ffffff !important;
}

.stChatMessageContent {
    color: #ffffff !important;
}

.stChatMessageContent p {
    color: #ffffff !important;
    font-size: 16px;
    line-height: 1.6;
}

.stMarkdown {
    color: #ffffff !important;
}

.stMarkdown p {
    color: #ffffff !important;
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Glass card style */
.glass-card {
    background: var(--bg-glass);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.glass-card:hover {
    border-color: var(--border-accent);
    box-shadow: 0 4px 30px rgba(0, 212, 255, 0.1);
}

/* Thinking panel */
.thinking-container {
    background: rgba(124, 58, 237, 0.1);
    border: 1px solid rgba(124, 58, 237, 0.3);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    max-height: 200px;
    overflow-y: auto;
}

.thinking-container::-webkit-scrollbar {
    width: 6px;
}

.thinking-container::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
}

.thinking-container::-webkit-scrollbar-thumb {
    background: rgba(124, 58, 237, 0.5);
    border-radius: 3px;
}

.thinking-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--accent-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.thinking-content {
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: var(--text-secondary);
    white-space: pre-wrap;
}

/* Message bubbles */
.message-bubble {
    padding: 16px 20px;
    border-radius: 16px;
    margin-bottom: 12px;
    animation: fadeIn 0.3s ease;
}

.message-user {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(0, 212, 255, 0.05));
    border: 1px solid rgba(0, 212, 255, 0.2);
    margin-left: auto;
    max-width: 85%;
}

.message-assistant {
    background: var(--bg-card);
    border: 1px solid var(--border-glass);
    margin-right: auto;
    max-width: 95%;
    color: var(--text-primary);
}

/* Streamlit chat message content - ensure bright text */
[data-testid="stChatMessage"] {
    color: var(--text-primary) !important;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
    color: var(--text-primary) !important;
}

/* Assistant specific styling */
[data-testid="stChatMessage"][data-role="assistant"] {
    color: #ffffff !important;
}

[data-testid="stChatMessage"][data-role="assistant"] p {
    color: #ffffff !important;
    font-weight: 400;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Input area */
.chat-input-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(180deg, transparent 0%, var(--bg-primary) 20%);
    padding: 20px;
    z-index: 100;
}

/* Sidebar styling - Streamlit sidebar elements */
.stSidebar {
    background-color: #1e1e28 !important;
}

/* Target sidebar content areas at multiple levels */
.stSidebar > div,
.stSidebar > div > div,
.stSidebar > div > div > div {
    background-color: #1e1e28 !important;
}

/* Streamlit's internal sidebar content container */
section[data-testid="stSidebar"] {
    background-color: #1e1e28 !important;
}

section[data-testid="stSidebar"] > div {
    background-color: #1e1e28 !important;
}

section[data-testid="stSidebar"] > div > div {
    background-color: #1e1e28 !important;
}

section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    background-color: #1e1e28 !important;
}

/* Ensure sidebar text is white and visible */
.stSidebar p,
.stSidebar span,
.stSidebar label,
.stSidebar .stSlider label,
.stSidebar .stMarkdown,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: #ffffff !important;
}

/* Sidebar headings */
.stSidebar h1,
.stSidebar h2,
.stSidebar h3,
.stSidebar h4,
.stSidebar h5,
.stSidebar h6,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] h5,
section[data-testid="stSidebar"] h6 {
    color: #ffffff !important;
}

/* Slider text in sidebar */
.stSidebar .stSlider label,
section[data-testid="stSidebar"] .stSlider label {
    color: #ffffff !important;
}

/* Text area in sidebar */
.stSidebar .stTextArea > div > div > textarea,
section[data-testid="stSidebar"] .stTextArea > div > div > textarea {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
}

/* Expander in sidebar */
.stSidebar .streamlit-expanderHeader,
section[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}

.stSidebar .streamlit-expanderContent,
section[data-testid="stSidebar"] .streamlit-expanderContent {
    background: rgba(0, 0, 0, 0.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 0 0 8px 8px !important;
}

/* Info text in sidebar */
.stSidebar .stAlert,
section[data-testid="stSidebar"] .stAlert {
    background: rgba(0, 212, 255, 0.1) !important;
    border: 1px solid rgba(0, 212, 255, 0.2) !important;
    color: #ffffff !important;
}

/* Sidebar glass card */
.sidebar-glass {
    background: rgba(18, 18, 26, 0.95);
    border-right: 1px solid var(--border-glass);
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    border: none;
    color: white;
    border-radius: 12px;
    padding: 12px 24px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
}

.stButton > button:active {
    transform: translateY(0);
}

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: var(--bg-glass);
    border: 1px solid var(--border-glass);
    box-shadow: none;
}

.stButton > button[kind="secondary"]:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: var(--border-accent);
}

/* Slider styling */
.stSlider > div > div {
    background: var(--bg-glass) !important;
}

.stSlider > div > div > div {
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)) !important;
}

/* Text area */
.stTextArea > div > div > textarea {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
}

.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
}

.streamlit-expanderContent {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-glass);
    border-radius: 0 0 12px 12px;
    border-top: none;
}

/* Error message */
.error-message {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 12px;
    padding: 16px;
    color: #fca5a5;
}

/* Loading spinner */
.loading-spinner {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(0, 212, 255, 0.1);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}

.empty-state-icon {
    font-size: 64px;
    margin-bottom: 16px;
    opacity: 0.5;
}

/* Code blocks */
.stCodeBlock {
    border-radius: 12px !important;
    background: rgba(0, 0, 0, 0.4) !important;
    border: 1px solid var(--border-glass) !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--border-glass);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--border-accent);
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .message-user,
    .message-assistant {
        max-width: 95%;
    }
    
    .thinking-container {
        max-height: 150px;
    }
}
</style>
"""


def get_custom_css() -> str:
    """Get custom CSS styles.
    
    Returns:
        CSS string
    """
    return CUSTOM_CSS

```

# src/ui/chat_interface.py
```py
"""Main chat interface component."""

from typing import Dict, Any, Generator, Tuple, Optional

import streamlit as st

from src.services.chat_service import ChatService
from src.services.state_manager import ChatStateManager
from src.ui.components import (
    render_custom_css,
    render_thinking_panel,
    render_empty_state,
    render_error_message,
)
from src.config.constants import PAGE_TITLE, PAGE_ICON
from src.utils.logger import get_logger

logger = get_logger(__name__)


def render_chat_interface(
    chat_service: ChatService,
    settings: Dict[str, Any]
) -> None:
    """Render main chat interface.
    
    Args:
        chat_service: Chat service instance
        settings: Current settings
    """
    # Render custom CSS
    render_custom_css()
    
    # Page title
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    
    # Initialize state manager
    state_manager = chat_service.state_manager
    
    # Display conversation history
    for msg in state_manager.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                # Show thinking if present
                if msg.get("thinking"):
                    render_thinking_panel(msg["thinking"], is_streaming=False)
                # Show content
                st.markdown(msg["content"])
    
    # Show empty state if no messages
    if not state_manager.has_messages:
        render_empty_state()
    
    # Chat input
    prompt = st.chat_input("Type your message...")
    
    # Handle pending prompt from example buttons
    if state_manager.pending_prompt:
        prompt = state_manager.pending_prompt
        state_manager.pending_prompt = None
    
    # Process user input
    if prompt:
        _handle_user_input(chat_service, prompt, settings)


def _handle_user_input(
    chat_service: ChatService,
    prompt: str,
    settings: Dict[str, Any]
) -> None:
    """Handle user input and generate response.
    
    Args:
        chat_service: Chat service instance
        prompt: User input
        settings: Current settings
    """
    # Add user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant", avatar="🤖"):
        # Placeholders for streaming content
        thinking_placeholder = st.empty()
        content_placeholder = st.empty()
        
        # Accumulate content
        full_thinking = ""
        full_content = ""
        
    try:
        # Check if we have a document for RAG
        retriever = None
        if hasattr(st.session_state, 'get'):
            retriever = st.session_state.get("retriever")
        
        # Choose streaming method based on retriever
        if retriever:
            # Use RAG-enhanced streaming
            stream_generator = chat_service.stream_message_with_rag(
                content=prompt,
                retriever=retriever,
                system_prompt=settings.get("system_prompt"),
                max_tokens=settings.get("max_tokens"),
                temperature=settings.get("temperature"),
                top_p=settings.get("top_p"),
            )
            logger.info("Using RAG-enhanced streaming with document context")
        else:
            # Use regular streaming
            stream_generator = chat_service.stream_message(
                content=prompt,
                system_prompt=settings.get("system_prompt"),
                max_tokens=settings.get("max_tokens"),
                temperature=settings.get("temperature"),
                top_p=settings.get("top_p"),
            )
        
        # Stream response
        for thinking, content, reasoning_details in stream_generator:
            # Update thinking
            if thinking:
                full_thinking = thinking
                with thinking_placeholder.container():
                    render_thinking_panel(full_thinking, is_streaming=True)

            # Update content
            if content:
                full_content = content
                content_placeholder.markdown(full_content + "▌")

        # Final content update (remove cursor)
        if full_content:
            content_placeholder.markdown(full_content)

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        render_error_message(f"Failed to generate response: {str(e)}")


def render_chat_container(chat_service: ChatService) -> None:
    """Render chat container with auto-scroll.
    
    Args:
        chat_service: Chat service instance
    """
    # Add auto-scroll JavaScript
    st.markdown("""
        <script>
            // Auto-scroll to bottom on new messages
            const chatContainer = document.querySelector('.main .block-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        </script>
    """, unsafe_allow_html=True)

```

# src/utils/logger.py
```py
"""Structured logging configuration with rotation support."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter with additional fields."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "source": {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
                "module": record.module
            },
            "thread": record.thread,
            "process": record.process
        }
        
        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_obj["extra"] = record.extra_data
        
        return json.dumps(log_obj)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m"        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Save original levelname
        orig_levelname = record.levelname
        
        # Add color
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        # Format message
        result = super().format(record)
        
        # Restore original levelname
        record.levelname = orig_levelname
        
        return result


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False
) -> logging.Logger:
    """Setup logging with file and console handlers.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        json_format: Whether to use JSON formatting for file logs
        
    Returns:
        Root logger instance
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    console_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    console_formatter = ColoredFormatter(console_format, datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setLevel(getattr(logging, level.upper()))
        
        if json_format:
            file_formatter = JsonFormatter()
        else:
            file_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
            file_formatter = logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S")
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to other classes."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for the class."""
        return get_logger(self.__class__.__module__ + "." + self.__class__.__name__)


# Convenience function for structured logging
def log_structured(
    logger: logging.Logger,
    level: str,
    message: str,
    **kwargs
) -> None:
    """Log structured message with extra fields.
    
    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        **kwargs: Additional fields to include
    """
    log_func = getattr(logger, level.lower())
    
    if kwargs:
        extra = {"extra_data": kwargs}
        log_func(message, extra=extra)
    else:
        log_func(message)

```

# src/utils/__init__.py
```py
"""Utility modules for the chatbot application."""

from src.utils.logger import get_logger, setup_logging

__all__ = ["get_logger", "setup_logging"]

```

# src/services/__init__.py
```py
"""Service layer for business logic."""

from src.services.chat_service import ChatService
from src.services.state_manager import ChatStateManager
from src.services.message_formatter import MessageFormatter

__all__ = ["ChatService", "ChatStateManager", "MessageFormatter"]

```

# src/services/chat_service.py
```py
"""Main chat service for business logic."""

from typing import Generator, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from src.api.nvidia_client import NvidiaChatClient
from src.api.models import Message, StreamChunk
from src.services.state_manager import ChatStateManager
from src.services.message_formatter import MessageFormatter
from src.config.constants import (
    DEFAULT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_THINKING,
)
from src.utils.logger import LoggerMixin


@dataclass
class ChatResponse:
    """Chat response data class."""
    
    content: str
    thinking: Optional[str] = None
    reasoning_details: Optional[Any] = None
    finished: bool = False


class ChatService(LoggerMixin):
    """Service for chat operations."""
    
    def __init__(
        self,
        client: Optional[NvidiaChatClient] = None,
        state_manager: Optional[ChatStateManager] = None
    ):
        """Initialize chat service.
        
        Args:
            client: NVIDIA API client
            state_manager: State manager instance
        """
        self.client = client or NvidiaChatClient()
        self.state_manager = state_manager or ChatStateManager()
        self.formatter = MessageFormatter()
        
        self.logger.info("Initialized ChatService")
    
    def send_message(
        self,
        content: str,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        thinking: bool = DEFAULT_THINKING
    ) -> ChatResponse:
        """Send message and get complete response.
        
        Args:
            content: User message content
            system_prompt: Optional system prompt
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Temperature
            top_p: Top-p parameter
            thinking: Enable thinking mode
            
        Returns:
            ChatResponse with content and thinking
        """
        # Add user message to state
        self.state_manager.add_user_message(content)
        
        # Format messages for API
        messages = MessageFormatter.format_messages_for_api(
            self.state_manager.messages[:-1],  # Exclude the message we just added
            system_prompt
        )
        messages = MessageFormatter.add_user_message(messages, content)
        
        # Call API
        try:
            response = self.client.chat_complete(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                thinking=thinking
            )
            
            # Extract content from response
            content = ""
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content or ""
            
            # Save to state
            self.state_manager.add_assistant_message(content)
            
            return ChatResponse(content=content, finished=True)
            
        except Exception as e:
            self.logger.error(f"Error in send_message: {e}")
            error_msg = f"❌ Error: {str(e)}"
            self.state_manager.add_assistant_message(error_msg)
            return ChatResponse(content=error_msg, finished=True)
    
    def stream_message(
        self,
        content: str,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        thinking: bool = DEFAULT_THINKING
    ) -> Generator[Tuple[str, str, Optional[Any]], None, None]:
        """Send message and stream response.
        
        Args:
            content: User message content
            system_prompt: Optional system prompt
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Temperature
            top_p: Top-p parameter
            thinking: Enable thinking mode
            
        Yields:
            Tuple of (thinking, content, reasoning_details)
        """
        # Add user message to state
        self.state_manager.add_user_message(content)
        
        # Format messages for API
        messages = MessageFormatter.format_messages_for_api(
            self.state_manager.messages[:-1],
            system_prompt
        )
        messages = MessageFormatter.add_user_message(messages, content)
        
        # Track accumulated content
        full_thinking = ""
        full_content = ""
        full_reasoning_details = None
        
        try:
            # Stream response
            for chunk in self.client.chat_complete_stream(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                thinking=thinking
            ):
                # Update thinking
                reasoning = chunk.delta_reasoning
                if reasoning:
                    full_thinking += reasoning
                
                # Update content
                delta_content = chunk.delta_content
                if delta_content:
                    full_content += delta_content
                
                # Update reasoning details
                details = chunk.reasoning_details
                if details:
                    full_reasoning_details = details
                
                yield full_thinking, full_content, full_reasoning_details
            
            # Save final message to state
            self.state_manager.add_assistant_message(
                full_content,
                thinking=full_thinking,
                reasoning_details=full_reasoning_details
            )
            
        except Exception as e:
            self.logger.error(f"Error in stream_message: {e}")
            error_msg = f"❌ Error: {str(e)}"
            full_content = error_msg if not full_content else full_content
            yield full_thinking, full_content, full_reasoning_details
            
            # Save error message
            self.state_manager.add_assistant_message(error_msg)
    
    def stream_message_with_rag(
        self,
        content: str,
        retriever: Optional[Any] = None,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        thinking: bool = DEFAULT_THINKING,
        k: int = 3
    ) -> Generator[Tuple[str, str, Optional[Any]], None, None]:
        """Send message with RAG context and stream response.
        
        If retriever is provided and has documents, retrieves relevant chunks
        and injects them into the system prompt for context-aware responses.
        
        Args:
            content: User message content
            retriever: Optional retriever with uploaded documents
            system_prompt: Optional system prompt (will be augmented with context)
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Temperature
            top_p: Top-p parameter
            thinking: Enable thinking mode
            k: Number of chunks to retrieve
            
        Yields:
            Tuple of (thinking, content, reasoning_details)
        """
        # Build augmented system prompt if retriever available
        augmented_prompt = system_prompt
        
        if retriever is not None:
            try:
                # Check if retriever has documents
                has_docs = (
                    hasattr(retriever, 'documents') and len(retriever.documents) > 0
                ) or (
                    hasattr(retriever, 'index') and 
                    retriever.index is not None and 
                    hasattr(retriever.index, 'ntotal') and 
                    retriever.index.ntotal > 0
                )
                
                if has_docs:
                    # Retrieve relevant chunks
                    results = retriever.retrieve(content, k=k)
                    
                    if results:
                        # Format context
                        context_chunks = [doc.text for doc, _ in results]
                        context_text = "\n\n---\n".join(context_chunks)
                        
                        # Augment system prompt
                        if augmented_prompt:
                            augmented_prompt = (
                                f"{augmented_prompt}\n\n"
                                f"Use the following context to answer the user's question:\n\n"
                                f"{context_text}"
                            )
                        else:
                            augmented_prompt = (
                                f"You are a helpful assistant. Use the following context to answer the user's question:\n\n"
                                f"{context_text}"
                            )
                        
                        self.logger.info(f"Injected {len(results)} context chunks into prompt")
                        
            except Exception as e:
                self.logger.warning(f"RAG retrieval failed, proceeding without context: {e}")
                # Continue without context augmentation
        
        # Delegate to regular streaming with augmented prompt
        yield from self.stream_message(
            content=content,
            system_prompt=augmented_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            thinking=thinking
        )

    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.state_manager.clear_history()
        self.logger.info("Conversation cleared")
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.state_manager.get_stats()
    
    def export_conversation(self) -> str:
        """Export conversation to JSON.
        
        Returns:
            JSON string
        """
        return self.state_manager.export_to_json()
    
    def import_conversation(self, json_str: str) -> bool:
        """Import conversation from JSON.
        
        Args:
            json_str: JSON string
            
        Returns:
            True if successful
        """
        return self.state_manager.import_from_json(json_str)
    
    def close(self) -> None:
        """Close service and cleanup resources."""
        self.client.close()
        self.logger.info("ChatService closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

```

# src/services/message_formatter.py
```py
"""Message formatting utilities."""

import re
from typing import List, Optional, Dict, Any

from src.api.models import Message


class MessageFormatter:
    """Formatter for chat messages."""
    
    @staticmethod
    def format_messages_for_api(
        history: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> List[Message]:
        """Format conversation history for API.
        
        Args:
            history: List of message dictionaries with role and content
            system_prompt: Optional system prompt
            
        Returns:
            List of Message objects
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt and system_prompt.strip():
            messages.append(Message(role="system", content=system_prompt.strip()))
        
        # Add conversation history
        for msg in history:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if not content:
                continue
            
            if role == "user":
                messages.append(Message(role="user", content=content))
            elif role == "assistant":
                assistant_msg = Message(role="assistant", content=content)
                
                # Preserve reasoning details if present
                if msg.get("reasoning_details"):
                    assistant_msg.reasoning_details = msg["reasoning_details"]
                
                messages.append(assistant_msg)
        
        return messages
    
    @staticmethod
    def add_user_message(
        messages: List[Message],
        content: str
    ) -> List[Message]:
        """Add user message to message list.
        
        Args:
            messages: Existing messages
            content: User message content
            
        Returns:
            Updated message list
        """
        messages.append(Message(role="user", content=content))
        return messages
    
    @staticmethod
    def add_assistant_message(
        messages: List[Message],
        content: str,
        reasoning_details: Optional[str] = None
    ) -> List[Message]:
        """Add assistant message to message list.
        
        Args:
            messages: Existing messages
            content: Assistant response content
            reasoning_details: Optional reasoning/thinking content
            
        Returns:
            Updated message list
        """
        msg = Message(role="assistant", content=content)
        if reasoning_details:
            msg.reasoning_details = reasoning_details
        messages.append(msg)
        return messages
    
    @staticmethod
    def clean_thinking_content(text: str) -> str:
        """Clean thinking content by removing <think> tags.
        
        Args:
            text: Raw thinking text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove <think> tags
        cleaned = re.sub(r'</?think>', '', text)
        
        # Remove extra whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
    
    @staticmethod
    def extract_code_blocks(text: str) -> List[Dict[str, str]]:
        """Extract code blocks from markdown text.
        
        Args:
            text: Markdown text
            
        Returns:
            List of code block dictionaries with language and code
        """
        code_blocks = []
        
        # Match code blocks with optional language
        pattern = r'```(\w*)\n(.*?)```'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            language = match.group(1) or "text"
            code = match.group(2)
            code_blocks.append({
                "language": language,
                "code": code
            })
        
        return code_blocks
    
    @staticmethod
    def format_for_display(content: str) -> str:
        """Format content for display.
        
        Args:
            content: Raw content
            
        Returns:
            Formatted content
        """
        if not content:
            return ""
        
        # Convert newlines to markdown breaks
        formatted = content.replace('\n', '  \n')
        
        return formatted
    
    @staticmethod
    def truncate_content(content: str, max_length: int = 1000) -> str:
        """Truncate content to max length.
        
        Args:
            content: Content to truncate
            max_length: Maximum length
            
        Returns:
            Truncated content
        """
        if len(content) <= max_length:
            return content
        
        return content[:max_length] + "..."
    
    @staticmethod
    def format_conversation_stats(
        messages: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate conversation statistics.
        
        Args:
            messages: Conversation messages
            
        Returns:
            Dictionary with statistics
        """
        user_count = sum(1 for m in messages if m.get("role") == "user")
        assistant_count = sum(1 for m in messages if m.get("role") == "assistant")
        total_chars = sum(len(m.get("content", "")) for m in messages)
        
        return {
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "total_messages": len(messages),
            "total_characters": total_chars
        }

```

# src/services/state_manager.py
```py
"""Session state management for chat conversations."""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

import streamlit as st

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationState:
    """Conversation state data class."""
    
    session_id: str
    messages: List[Dict[str, Any]]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class ChatStateManager:
    """Manager for chat session state."""

    SESSION_KEY = "chat_messages"
    SESSION_ID_KEY = "session_id"
    PENDING_PROMPT_KEY = "pending_prompt"
    RETRIEVER_KEY = "rag_retriever"
    DOCUMENT_NAME_KEY = "rag_document_name"
    
    def __init__(self):
        """Initialize state manager."""
        self._ensure_session_state()
    
    def _ensure_session_state(self) -> None:
        """Ensure session state is initialized."""
        if self.SESSION_KEY not in st.session_state:
            st.session_state[self.SESSION_KEY] = []
        
        if self.SESSION_ID_KEY not in st.session_state:
            st.session_state[self.SESSION_ID_KEY] = str(uuid.uuid4())
        
        if self.PENDING_PROMPT_KEY not in st.session_state:
            st.session_state[self.PENDING_PROMPT_KEY] = None
    
    @property
    def session_id(self) -> str:
        """Get current session ID."""
        return st.session_state.get(self.SESSION_ID_KEY, str(uuid.uuid4()))
    
    @property
    def messages(self) -> List[Dict[str, Any]]:
        """Get conversation messages."""
        return st.session_state.get(self.SESSION_KEY, [])
    
    @messages.setter
    def messages(self, value: List[Dict[str, Any]]) -> None:
        """Set conversation messages."""
        st.session_state[self.SESSION_KEY] = value
    
    @property
    def has_messages(self) -> bool:
        """Check if there are any messages."""
        return len(self.messages) > 0
    
    @property
    def pending_prompt(self) -> Optional[str]:
        """Get pending prompt (from example buttons)."""
        return st.session_state.get(self.PENDING_PROMPT_KEY)
    
    @pending_prompt.setter
    def pending_prompt(self, value: Optional[str]) -> None:
        """Set pending prompt."""
        st.session_state[self.PENDING_PROMPT_KEY] = value

    @property
    def retriever(self) -> Optional[Any]:
        """Get RAG retriever for current session.
        
        Returns:
            Retriever instance or None if not set
        """
        return st.session_state.get(self.RETRIEVER_KEY)

    @retriever.setter
    def retriever(self, value: Optional[Any]) -> None:
        """Set RAG retriever for current session.
        
        Args:
            value: Retriever instance or None
        """
        st.session_state[self.RETRIEVER_KEY] = value

    @property
    def current_document_name(self) -> Optional[str]:
        """Get current document name.
        
        Returns:
            Document filename or None if no document
        """
        return st.session_state.get(self.DOCUMENT_NAME_KEY)

    @current_document_name.setter
    def current_document_name(self, value: Optional[str]) -> None:
        """Set current document name.
        
        Args:
            value: Document filename or None
        """
        st.session_state[self.DOCUMENT_NAME_KEY] = value

    def clear_retriever(self) -> None:
        """Clear retriever and document metadata."""
        if self.RETRIEVER_KEY in st.session_state:
            retriever = st.session_state[self.RETRIEVER_KEY]
            if hasattr(retriever, 'clear'):
                retriever.clear()
            del st.session_state[self.RETRIEVER_KEY]
        
        if self.DOCUMENT_NAME_KEY in st.session_state:
            del st.session_state[self.DOCUMENT_NAME_KEY]
        
        logger.info("Cleared RAG retriever and document metadata")

    def add_message(
        self,
        role: str,
        content: str,
        **metadata
    ) -> Dict[str, Any]:
        """Add message to conversation.
        
        Args:
            role: Message role (user/assistant)
            content: Message content
            **metadata: Additional metadata
            
        Returns:
            Added message dictionary
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            **metadata
        }
        
        self.messages.append(message)
        logger.debug(f"Added {role} message to conversation")
        
        return message
    
    def add_user_message(self, content: str) -> Dict[str, Any]:
        """Add user message.
        
        Args:
            content: Message content
            
        Returns:
            Added message dictionary
        """
        return self.add_message("user", content)
    
    def add_assistant_message(
        self,
        content: str,
        thinking: Optional[str] = None,
        reasoning_details: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Add assistant message.
        
        Args:
            content: Response content
            thinking: Optional thinking/reasoning content
            reasoning_details: Optional reasoning details
            
        Returns:
            Added message dictionary
        """
        metadata = {}
        if thinking:
            metadata["thinking"] = thinking
        if reasoning_details:
            metadata["reasoning_details"] = reasoning_details
        
        return self.add_message("assistant", content, **metadata)
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages = []
        logger.info("Cleared conversation history")
    
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """Get last message in conversation."""
        messages = self.messages
        if messages:
            return messages[-1]
        return None
    
    def get_messages_for_api(self) -> List[Dict[str, Any]]:
        """Get messages formatted for API (without metadata)."""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
            if msg.get("content")
        ]
    
    def export_conversation(self) -> Dict[str, Any]:
        """Export conversation to dictionary.
        
        Returns:
            Conversation data dictionary
        """
        return {
            "session_id": self.session_id,
            "created_at": datetime.utcnow().isoformat(),
            "messages": self.messages
        }
    
    def import_conversation(self, data: Dict[str, Any]) -> bool:
        """Import conversation from dictionary.
        
        Args:
            data: Conversation data dictionary
            
        Returns:
            True if successful
        """
        try:
            if "messages" in data:
                self.messages = data["messages"]
                logger.info(f"Imported {len(self.messages)} messages")
                return True
        except Exception as e:
            logger.error(f"Failed to import conversation: {e}")
        
        return False
    
    def export_to_json(self) -> str:
        """Export conversation to JSON string.
        
        Returns:
            JSON string
        """
        return json.dumps(self.export_conversation(), indent=2)
    
    def import_from_json(self, json_str: str) -> bool:
        """Import conversation from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            True if successful
        """
        try:
            data = json.loads(json_str)
            return self.import_conversation(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics.
        
        Returns:
            Statistics dictionary
        """
        messages = self.messages
        
        user_count = sum(1 for m in messages if m.get("role") == "user")
        assistant_count = sum(1 for m in messages if m.get("role") == "assistant")
        total_chars = sum(len(m.get("content", "")) for m in messages)
        
        return {
            "total_messages": len(messages),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "total_characters": total_chars,
            "session_id": self.session_id
        }

```

# src/api/__init__.py
```py
"""API client module for NVIDIA API integration."""

from src.api.nvidia_client import NvidiaChatClient
from src.api.models import Message, ChatRequest, ChatResponse, StreamChunk
from src.api.exceptions import (
    NvidiaAPIError,
    NvidiaAuthError,
    NvidiaRateLimitError,
    NvidiaStreamError,
)

__all__ = [
    "NvidiaChatClient",
    "Message",
    "ChatRequest",
    "ChatResponse",
    "StreamChunk",
    "NvidiaAPIError",
    "NvidiaAuthError",
    "NvidiaRateLimitError",
    "NvidiaStreamError",
]

```

# src/api/exceptions.py
```py
"""Custom exceptions for NVIDIA API client."""


class NvidiaAPIError(Exception):
    """Base exception for NVIDIA API errors."""
    
    def __init__(self, message: str, status_code: int = None, response_body: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
    
    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class NvidiaAuthError(NvidiaAPIError):
    """Raised when authentication fails (401)."""
    
    def __init__(self, message: str = "Authentication failed", response_body: dict = None):
        super().__init__(message, status_code=401, response_body=response_body)


class NvidiaRateLimitError(NvidiaAPIError):
    """Raised when rate limit is exceeded (429)."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class NvidiaStreamError(NvidiaAPIError):
    """Raised when streaming encounters an error."""
    
    def __init__(self, message: str = "Stream processing error", chunk: str = None):
        super().__init__(message)
        self.chunk = chunk


class NvidiaValidationError(NvidiaAPIError):
    """Raised when request validation fails (400)."""
    
    def __init__(self, message: str = "Validation error", response_body: dict = None):
        super().__init__(message, status_code=400, response_body=response_body)


class NvidiaServerError(NvidiaAPIError):
    """Raised when server returns 5xx error."""
    
    def __init__(self, message: str = "Server error", status_code: int = 500):
        super().__init__(message, status_code=status_code)


class NvidiaTimeoutError(NvidiaAPIError):
    """Raised when request times out."""
    
    def __init__(self, message: str = "Request timed out", timeout: float = None):
        super().__init__(message)
        self.timeout = timeout


def raise_for_status(status_code: int, response_body: dict = None) -> None:
    """Raise appropriate exception based on status code.
    
    Args:
        status_code: HTTP status code
        response_body: Optional response body for context
        
    Raises:
        NvidiaAPIError: Appropriate exception for the status code
    """
    if status_code == 200 or status_code == 201:
        return
    elif status_code == 401:
        raise NvidiaAuthError(response_body=response_body)
    elif status_code == 429:
        raise NvidiaRateLimitError()
    elif status_code == 400:
        raise NvidiaValidationError(response_body=response_body)
    elif 500 <= status_code < 600:
        raise NvidiaServerError(status_code=status_code)
    else:
        raise NvidiaAPIError(f"Unexpected status code: {status_code}", status_code=status_code)

```

# src/api/models.py
```py
"""Pydantic models for NVIDIA API requests and responses."""

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, validator


class Message(BaseModel):
    """Chat message model."""
    
    role: Literal["system", "user", "assistant"] = Field(
        ...,
        description="Message role"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Message content"
    )
    reasoning_details: Optional[str] = Field(
        default=None,
        description="Reasoning/thinking details for assistant messages"
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Hello, how are you?"
            }
        }


class ChatTemplateKwargs(BaseModel):
    """Chat template kwargs for reasoning mode."""
    
    thinking: bool = Field(
        default=True,
        description="Enable thinking/reasoning mode"
    )


class ChatRequest(BaseModel):
    """Chat completion request model."""
    
    model: str = Field(
        ...,
        description="Model identifier"
    )
    messages: List[Message] = Field(
        ...,
        min_length=1,
        description="Conversation messages"
    )
    max_tokens: int = Field(
        default=65536,
        ge=1,
        le=131072,
        description="Maximum tokens to generate"
    )
    temperature: float = Field(
        default=1.00,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    top_p: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    stream: bool = Field(
        default=True,
        description="Enable streaming response"
    )
    chat_template_kwargs: ChatTemplateKwargs = Field(
        default_factory=ChatTemplateKwargs,
        description="Chat template configuration"
    )
    
    @validator('messages')
    def validate_messages(cls, v: List[Message]) -> List[Message]:
        """Validate message list."""
        if not v:
            raise ValueError("At least one message is required")
        return v


class Usage(BaseModel):
    """Token usage information."""
    
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)


class Choice(BaseModel):
    """Completion choice model."""
    
    index: int = Field(default=0)
    message: Optional[Message] = None
    delta: Optional[Dict[str, Any]] = None  # For streaming
    finish_reason: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat completion response model."""
    
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None


class StreamChunk(BaseModel):
    """Streaming response chunk model."""
    
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    
    @property
    def delta_content(self) -> Optional[str]:
        """Extract content from delta."""
        if self.choices and self.choices[0].delta:
            return self.choices[0].delta.get("content")
        return None
    
    @property
    def delta_reasoning(self) -> Optional[str]:
        """Extract reasoning from delta."""
        if self.choices and self.choices[0].delta:
            return self.choices[0].delta.get("reasoning")
        return None
    
    @property
    def reasoning_details(self) -> Optional[Any]:
        """Extract reasoning details from message."""
        if self.choices and self.choices[0].message:
            return self.choices[0].message.get("reasoning_details")
        return None
    
    @property
    def is_done(self) -> bool:
        """Check if this is the final chunk."""
        if self.choices and self.choices[0].finish_reason:
            return True
        return False


class ReasoningContent(BaseModel):
    """Reasoning/thinking content model."""
    
    content: str = Field(description="Raw reasoning text")
    cleaned_content: Optional[str] = Field(default=None, description="Cleaned reasoning text")
    
    @validator('cleaned_content', always=True)
    def clean_reasoning(cls, v: Optional[str], values: Dict) -> str:
        """Clean reasoning content by removing tags."""
        content = values.get('content', '')
        if not content:
            return ''
        
        # Remove <think> tags
        import re
        cleaned = re.sub(r'</?think>', '', content).strip()
        return cleaned

```

# src/api/nvidia_client.py
```py
"""NVIDIA API client for chat completions with streaming support."""

import json
import time
from typing import Generator, List, Optional, Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config.constants import (
    NVIDIA_API_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_STREAMING,
    DEFAULT_THINKING,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)
from src.config.settings import Settings, get_settings
from src.api.models import Message, ChatRequest, ChatResponse, StreamChunk
from src.api.exceptions import (
    NvidiaAPIError,
    NvidiaAuthError,
    NvidiaRateLimitError,
    NvidiaStreamError,
    NvidiaTimeoutError,
    raise_for_status,
)
from src.utils.logger import get_logger, LoggerMixin

logger = get_logger(__name__)


class NvidiaChatClient(LoggerMixin):
    """Client for NVIDIA Chat Completions API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES
    ):
        """Initialize NVIDIA API client.
        
        Args:
            api_key: NVIDIA API key (defaults to env var)
            base_url: API base URL (defaults to NVIDIA endpoint)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        # Get settings if not provided
        settings = get_settings()
        
        self.api_key = api_key or settings.nvidia_api_key
        self.base_url = base_url or settings.nvidia_base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Validate API key
        if not self.api_key:
            raise NvidiaAuthError("API key is required")
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.logger.info(f"Initialized NVIDIA client with base_url: {self.base_url}")
    
    def _get_headers(self, stream: bool = False) -> Dict[str, str]:
        """Get request headers.
        
        Args:
            stream: Whether this is a streaming request
            
        Returns:
            Headers dictionary
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        if stream:
            headers["Accept"] = "text/event-stream"
        else:
            headers["Accept"] = "application/json"
        
        return headers
    
    def _make_request(
        self,
        messages: List[Message],
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        stream: bool = DEFAULT_STREAMING,
        thinking: bool = DEFAULT_THINKING
    ) -> requests.Response:
        """Make API request.
        
        Args:
            messages: List of messages
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stream: Whether to stream response
            thinking: Whether to enable thinking mode
            
        Returns:
            Response object
            
        Raises:
            NvidiaAPIError: On API errors
        """
        # Build request
        request = ChatRequest(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=stream,
            chat_template_kwargs={"thinking": thinking}
        )
        
        url = f"{self.base_url}/chat/completions"
        headers = self._get_headers(stream=stream)
        
        self.logger.debug(f"Sending request to {url} with model {model}")
        
        try:
            response = self.session.post(
                url,
                headers=headers,
                json=request.dict(),
                timeout=self.timeout,
                stream=stream
            )
            
            # Check status code
            if response.status_code != 200:
                try:
                    body = response.json()
                except:
                    body = None
                raise_for_status(response.status_code, body)
            
            return response
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Request timed out: {e}")
            raise NvidiaTimeoutError(timeout=self.timeout)
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {e}")
            raise NvidiaAPIError(f"Failed to connect to API: {e}")
        except NvidiaAPIError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise NvidiaAPIError(f"Unexpected error: {e}")
    
    def chat_complete(
        self,
        messages: List[Message],
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        thinking: bool = DEFAULT_THINKING
    ) -> ChatResponse:
        """Send non-streaming chat completion request.
        
        Args:
            messages: List of messages
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            thinking: Whether to enable thinking mode
            
        Returns:
            Chat completion response
        """
        response = self._make_request(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=False,
            thinking=thinking
        )
        
        data = response.json()
        return ChatResponse(**data)
    
    def chat_complete_stream(
        self,
        messages: List[Message],
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        thinking: bool = DEFAULT_THINKING
    ) -> Generator[StreamChunk, None, None]:
        """Send streaming chat completion request.
        
        Args:
            messages: List of messages
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            thinking: Whether to enable thinking mode
            
        Yields:
            StreamChunk objects
        """
        response = self._make_request(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=True,
            thinking=thinking
        )
        
        for line in response.iter_lines():
            if not line:
                continue
            
            try:
                line_text = line.decode("utf-8")
                
                # Skip lines that don't start with "data: "
                if not line_text.startswith("data: "):
                    continue
                
                data_str = line_text[6:]  # Remove "data: " prefix
                
                # Check for stream end
                if data_str == "[DONE]":
                    self.logger.debug("Stream completed")
                    break
                
                # Parse JSON
                data = json.loads(data_str)
                chunk = StreamChunk(**data)
                
                yield chunk
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse JSON: {e}, line: {line}")
                continue
            except Exception as e:
                self.logger.error(f"Error processing stream chunk: {e}")
                raise NvidiaStreamError(f"Error processing chunk: {e}", chunk=line.decode("utf-8"))
    
    def close(self) -> None:
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

```

# src/config/__init__.py
```py
"""Configuration module for the chatbot application."""

from src.config.settings import Settings
from src.config.constants import (
    NVIDIA_API_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
)

__all__ = [
    "Settings",
    "NVIDIA_API_BASE_URL",
    "DEFAULT_MODEL",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_TOP_P",
]

```

# src/config/settings.py
```py
"""Configuration management with Pydantic settings."""

from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings

from src.config.constants import (
    NVIDIA_API_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_TIMEOUT,
)


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # NVIDIA API Configuration
    nvidia_api_key: str = Field(
        ...,  # Required
        description="NVIDIA API key for authentication",
        env="NVIDIA_API_KEY"
    )
    
    nvidia_base_url: str = Field(
        default=NVIDIA_API_BASE_URL,
        description="NVIDIA API base URL",
        env="NVIDIA_BASE_URL"
    )
    
    # Model Configuration
    default_model: str = Field(
        default=DEFAULT_MODEL,
        description="Default model to use",
        env="DEFAULT_MODEL"
    )
    
    default_max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        description="Maximum tokens to generate",
        env="DEFAULT_MAX_TOKENS"
    )
    
    default_temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        description="Sampling temperature",
        env="DEFAULT_TEMPERATURE"
    )
    
    default_top_p: float = Field(
        default=DEFAULT_TOP_P,
        description="Nucleus sampling parameter",
        env="DEFAULT_TOP_P"
    )
    
    # Request Configuration
    request_timeout: float = Field(
        default=DEFAULT_TIMEOUT,
        description="API request timeout in seconds",
        env="REQUEST_TIMEOUT"
    )
    
    # Application Settings
    app_env: str = Field(
        default="development",
        description="Application environment",
        env="APP_ENV"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        env="LOG_LEVEL"
    )
    
    # Streamlit Configuration
    streamlit_server_port: int = Field(
        default=8501,
        description="Streamlit server port",
        env="STREAMLIT_SERVER_PORT"
    )
    
    streamlit_server_address: str = Field(
        default="0.0.0.0",
        description="Streamlit server address",
        env="STREAMLIT_SERVER_ADDRESS"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator('nvidia_api_key')
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        if not v or v.strip() == '':
            raise ValueError("NVIDIA_API_KEY cannot be empty")
        if not v.startswith('nvapi-'):
            raise ValueError("NVIDIA_API_KEY should start with 'nvapi-'")
        return v.strip()
    
    @validator('default_max_tokens')
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max tokens range."""
        if v < 1:
            raise ValueError("max_tokens must be at least 1")
        if v > 131072:
            raise ValueError("max_tokens cannot exceed 131072")
        return v
    
    @validator('default_temperature')
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature range."""
        if v < 0.0:
            raise ValueError("temperature must be >= 0.0")
        if v > 2.0:
            raise ValueError("temperature must be <= 2.0")
        return v
    
    @validator('default_top_p')
    def validate_top_p(cls, v: float) -> float:
        """Validate top_p range."""
        if v < 0.0:
            raise ValueError("top_p must be >= 0.0")
        if v > 1.0:
            raise ValueError("top_p must be <= 1.0")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env.lower() == "production"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings

```

# src/config/constants.py
```py
"""Application constants and default values."""

# API Configuration
NVIDIA_API_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_CHAT_ENDPOINT = "/chat/completions"

# Model Configuration
DEFAULT_MODEL = "moonshotai/kimi-k2.5"
DEFAULT_MAX_TOKENS = 65536
DEFAULT_TEMPERATURE = 1.00
DEFAULT_TOP_P = 0.95
DEFAULT_STREAMING = True
DEFAULT_THINKING = True

# Request Configuration
DEFAULT_TIMEOUT = 120.0  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
RETRY_BACKOFF = 2.0  # exponential backoff multiplier

# UI Configuration
PAGE_TITLE = "Flash Chatbot"
PAGE_ICON = ""
PAGE_LAYOUT = "centered"

# Sidebar Configuration
SIDEBAR_TITLE = "⚙️ Settings"
MAX_TOKENS_MIN = 256
MAX_TOKENS_MAX = 131072
MAX_TOKENS_STEP = 256
TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 2.0
TEMPERATURE_STEP = 0.1
TOP_P_MIN = 0.1
TOP_P_MAX = 1.0
TOP_P_STEP = 0.05

# Default System Prompt
DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."

# Thinking/Reasoning Configuration
THINKING_LABEL = "Thinking Process"
CONTENT_LABEL = "Response"

# Error Messages
ERROR_API_KEY_MISSING = "NVIDIA API key is not configured. Please set NVIDIA_API_KEY environment variable."
ERROR_API_CONNECTION = "Failed to connect to NVIDIA API. Please check your network connection."
ERROR_API_RATE_LIMIT = "Rate limit exceeded. Please wait a moment before sending another message."
ERROR_API_AUTH = "Authentication failed. Please check your API key."
ERROR_GENERIC = "An error occurred. Please try again."

# Example Questions
EXAMPLE_QUESTIONS = [
    "Please explain what machine learning is.",
    "Help me write a Python quicksort algorithm.",
    "How many prime numbers are there under 1000?",
]

# Log Messages
LOG_API_REQUEST = "Sending request to NVIDIA API"
LOG_API_RESPONSE = "Received response from NVIDIA API"
LOG_STREAM_CHUNK = "Processing stream chunk"
LOG_SESSION_START = "Session started"
LOG_SESSION_END = "Session ended"

```

