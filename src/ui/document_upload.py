"""Ethereal document upload zone with processing feedback."""

import html
from typing import Optional, Any

import streamlit as st

from src.config.constants import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB
from src.rag.document_processor import DocumentProcessor, DocumentProcessingError


def _inject_upload_styles():
    """Inject custom CSS for glass dropzone and document badge with deduplication."""
    if "upload_css_injected" in st.session_state:
        return

    st.markdown(
        """
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
    """,
        unsafe_allow_html=True,
    )
    st.session_state["upload_css_injected"] = True


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

        # Dropzone - Use single HTML block for visual styling
        st.markdown(
            '<div class="ethereal-dropzone">'
            '<div class="upload-icon">📄</div>'
            '<div class="upload-text">Drop your document here</div>'
            "</div>",
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Upload document",
            type=["pdf", "txt", "md"],
            label_visibility="collapsed",
            key="rag_uploader",
        )

        if uploaded_file:
            self._process_upload(uploaded_file)

    def _render_document_badge(self) -> None:
        """Render document badge with filename and clear button."""
        col1, col2 = st.columns([0.9, 0.1])

        with col1:
            escaped_filename = html.escape(self.state.current_document_name)
            st.markdown(
                f'<div class="doc-badge">'
                f"<span>📄</span>"
                f'<span class="filename">{escaped_filename}</span>'
                f"</div>",
                unsafe_allow_html=True,
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
            "<span>Extracting knowledge...</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        try:
            processor = DocumentProcessor()
            file_bytes = uploaded_file.getvalue()

            # Check file size
            if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
                placeholder.error(
                    f"❌ File too large. Maximum size: {MAX_UPLOAD_SIZE_MB}MB"
                )
                return

            chunks = processor.process(file_bytes, uploaded_file.name)

            # Add to retriever
            if hasattr(self.state, "retriever") and self.state.retriever:
                self.state.retriever.add_documents(chunks)
                self.state.current_document_name = uploaded_file.name

                placeholder.success(
                    f"✅ Processed {len(chunks)} chunks from {uploaded_file.name}"
                )
            else:
                placeholder.error("❌ No retriever available. Please refresh the page.")

        except DocumentProcessingError as e:
            placeholder.error(f"❌ {str(e)}")
        except Exception as e:
            placeholder.error(f"❌ Unexpected error: {str(e)}")

    def _clear_document(self) -> None:
        """Clear retriever and document metadata."""
        if hasattr(self.state, "clear_retriever"):
            self.state.clear_retriever()
        else:
            # Fallback: manually clear
            if hasattr(self.state, "retriever"):
                self.state.retriever = None
            if hasattr(self.state, "current_document_name"):
                self.state.current_document_name = None


def render_document_upload() -> None:
    """Convenience function to render document upload component.

    Uses st.session_state as state manager.
    Uses consistent key 'rag_retriever' to match ChatStateManager.
    """

    # Create a state wrapper that accesses session_state
    class SessionStateWrapper:
        RETRIEVER_KEY = "rag_retriever"
        DOCUMENT_NAME_KEY = "rag_document_name"

        @property
        def current_document_name(self) -> Optional[str]:
            return st.session_state.get(self.DOCUMENT_NAME_KEY)

        @current_document_name.setter
        def current_document_name(self, value: Optional[str]) -> None:
            st.session_state[self.DOCUMENT_NAME_KEY] = value

        @property
        def retriever(self) -> Optional[Any]:
            return st.session_state.get(self.RETRIEVER_KEY)

        @retriever.setter
        def retriever(self, value: Optional[Any]) -> None:
            st.session_state[self.RETRIEVER_KEY] = value

        def clear_retriever(self) -> None:
            """Clear retriever and document metadata."""
            if self.RETRIEVER_KEY in st.session_state:
                retriever = st.session_state[self.RETRIEVER_KEY]
                if hasattr(retriever, "clear"):
                    retriever.clear()
                del st.session_state[self.RETRIEVER_KEY]

            if self.DOCUMENT_NAME_KEY in st.session_state:
                del st.session_state[self.DOCUMENT_NAME_KEY]

    state = SessionStateWrapper()
    component = DocumentUpload(state)
    component.render()
