"""Tests for DocumentUpload UI component."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import io

from src.ui.document_upload import DocumentUpload
from src.rag.document_processor import DocumentProcessingError


class MockState:
    """Mock state manager for testing."""
    
    def __init__(self):
        self.current_document_name = None
        self._retriever = None
        self.clear_called = False
    
    @property
    def retriever(self):
        return self._retriever
    
    @retriever.setter
    def retriever(self, value):
        self._retriever = value
    
    def clear_retriever(self):
        self.clear_called = True
        self._retriever = None
        self.current_document_name = None


class TestDocumentUpload:
    """Test suite for DocumentUpload component."""

    @pytest.fixture
    def mock_state(self):
        """Create mock state manager."""
        return MockState()

    @pytest.fixture
    def mock_processor(self):
        """Create mock document processor."""
        processor = Mock()
        processor.process.return_value = ["Chunk 1", "Chunk 2", "Chunk 3"]
        return processor

    @pytest.fixture
    def mock_retriever(self):
        """Create mock retriever."""
        retriever = Mock()
        retriever.add_documents = Mock()
        return retriever

    def test_process_document_updates_state(self, mock_state, mock_processor, mock_retriever):
        """Test that processing document updates state correctly."""
        # Setup
        mock_state.retriever = mock_retriever
        
        # Create mock file
        mock_file = Mock()
        mock_file.name = "test.pdf"
        mock_file.getvalue.return_value = b"PDF content"
        
        # Process
        with patch('src.ui.document_upload.DocumentProcessor', return_value=mock_processor):
            component = DocumentUpload(mock_state)
            
            # Call _process_upload directly
            with patch('streamlit.empty') as mock_empty:
                with patch('streamlit.markdown'):
                    mock_placeholder = Mock()
                    mock_empty.return_value = mock_placeholder
                    component._process_upload(mock_file)
            
            # Verify state updated
            assert mock_state.current_document_name == "test.pdf"
            assert mock_retriever.add_documents.called
            
            # Verify chunks added
            call_args = mock_retriever.add_documents.call_args
            chunks = call_args[0][0]
            assert len(chunks) == 3
            assert "Chunk 1" in chunks

    def test_clear_document_clears_state(self, mock_state):
        """Test that clearing document clears state."""
        mock_state.current_document_name = "test.pdf"
        
        component = DocumentUpload(mock_state)
        component._clear_document()
        
        # Should clear state
        assert mock_state.clear_called

    def test_unsupported_file_error_handled(self, mock_state, mock_processor):
        """Test that unsupported file type errors are handled."""
        mock_processor.process.side_effect = DocumentProcessingError("Unsupported file type: .docx")
        
        mock_file = Mock()
        mock_file.name = "test.docx"
        mock_file.getvalue.return_value = b"content"
        
        with patch('src.ui.document_upload.DocumentProcessor', return_value=mock_processor):
            with patch('streamlit.empty') as mock_empty:
                with patch('streamlit.markdown'):
                    mock_placeholder = Mock()
                    mock_empty.return_value = mock_placeholder
                    
                    component = DocumentUpload(mock_state)
                    component._process_upload(mock_file)
                    
                    # Should call error on placeholder
                    assert mock_placeholder.error.called

    def test_empty_file_error_handled(self, mock_state, mock_processor):
        """Test that empty file errors are handled."""
        mock_processor.process.side_effect = DocumentProcessingError("No extractable text found.")
        
        mock_file = Mock()
        mock_file.name = "empty.txt"
        mock_file.getvalue.return_value = b""
        
        with patch('src.ui.document_upload.DocumentProcessor', return_value=mock_processor):
            with patch('streamlit.empty') as mock_empty:
                with patch('streamlit.markdown'):
                    mock_placeholder = Mock()
                    mock_empty.return_value = mock_placeholder
                    
                    component = DocumentUpload(mock_state)
                    component._process_upload(mock_file)
                    
                    # Should call error on placeholder
                    assert mock_placeholder.error.called

    def test_successful_processing_shows_success(self, mock_state, mock_processor, mock_retriever):
        """Test that successful processing shows success message."""
        mock_state.retriever = mock_retriever
        
        mock_file = Mock()
        mock_file.name = "test.pdf"
        mock_file.getvalue.return_value = b"PDF content"
        
        with patch('src.ui.document_upload.DocumentProcessor', return_value=mock_processor):
            with patch('streamlit.empty') as mock_empty:
                with patch('streamlit.markdown'):
                    mock_placeholder = Mock()
                    mock_empty.return_value = mock_placeholder
                    
                    component = DocumentUpload(mock_state)
                    component._process_upload(mock_file)
                    
                    # Should call success on placeholder
                    assert mock_placeholder.success.called
                    
                    # Verify message contains chunk count
                    success_msg = str(mock_placeholder.success.call_args)
                    assert "3 chunks" in success_msg or "processed" in success_msg.lower()

    def test_pdf_extraction_error_handled(self, mock_state, mock_processor):
        """Test that PDF extraction errors are handled gracefully."""
        mock_processor.process.side_effect = DocumentProcessingError("PDF extraction failed: corrupted")
        
        mock_file = Mock()
        mock_file.name = "corrupted.pdf"
        mock_file.getvalue.return_value = b"corrupted pdf bytes"
        
        with patch('src.ui.document_upload.DocumentProcessor', return_value=mock_processor):
            with patch('streamlit.empty') as mock_empty:
                with patch('streamlit.markdown'):
                    mock_placeholder = Mock()
                    mock_empty.return_value = mock_placeholder
                    
                    component = DocumentUpload(mock_state)
                    component._process_upload(mock_file)
                    
                    # Should show error, not raise exception
                    assert mock_placeholder.error.called

    def test_no_retriever_shows_error(self, mock_state, mock_processor):
        """Test that missing retriever shows error."""
        mock_state.retriever = None  # No retriever
        
        mock_file = Mock()
        mock_file.name = "test.pdf"
        mock_file.getvalue.return_value = b"PDF content"
        
        with patch('src.ui.document_upload.DocumentProcessor', return_value=mock_processor):
            with patch('streamlit.empty') as mock_empty:
                with patch('streamlit.markdown'):
                    mock_placeholder = Mock()
                    mock_empty.return_value = mock_placeholder
                    
                    component = DocumentUpload(mock_state)
                    component._process_upload(mock_file)
                    
                    # Should show error about missing retriever
                    assert mock_placeholder.error.called
                    error_msg = str(mock_placeholder.error.call_args)
                    assert "retriever" in error_msg.lower()

    def test_document_upload_init(self, mock_state):
        """Test that DocumentUpload initializes correctly."""
        component = DocumentUpload(mock_state)
        
        assert component.state is mock_state

    def test_clear_document_fallback(self, mock_state):
        """Test clear_document fallback when clear_retriever not available."""
        # Remove clear_retriever method
        delattr(type(mock_state), 'clear_retriever')
        
        mock_state.current_document_name = "test.pdf"
        mock_state.retriever = Mock()
        
        component = DocumentUpload(mock_state)
        component._clear_document()
        
        # Should clear properties via fallback
        assert mock_state.current_document_name is None
        assert mock_state.retriever is None
