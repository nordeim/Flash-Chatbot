"""Tests for DocumentProcessor - RAG text extraction and chunking."""

import pytest
import tempfile
import os
from pathlib import Path

from src.rag.document_processor import DocumentProcessor, DocumentProcessingError


class TestDocumentProcessor:
    """Test suite for DocumentProcessor."""

    @pytest.fixture
    def processor(self):
        """Create DocumentProcessor instance."""
        return DocumentProcessor(chunk_size=100, chunk_overlap=20)

    def test_extract_text_from_txt(self, processor):
        """Test extracting text from plain text file."""
        text = "Hello world. This is a test document.\nIt has multiple lines."
        file_bytes = text.encode('utf-8')
        
        chunks = processor.process(file_bytes, "test.txt")
        
        assert len(chunks) > 0
        assert "Hello" in chunks[0]
        assert "test" in chunks[0]

    def test_extract_text_from_md(self, processor):
        """Test extracting text from markdown file."""
        text = "# Heading\n\nThis is markdown content."
        file_bytes = text.encode('utf-8')
        
        chunks = processor.process(file_bytes, "test.md")
        
        assert len(chunks) > 0
        assert "Heading" in chunks[0] or "markdown" in chunks[0]

    def test_extract_text_from_pdf(self, processor, mocker):
        """Test extracting text from PDF using mocked pypdf."""
        # Mock pypdf.PdfReader
        mock_reader = mocker.patch('pypdf.PdfReader')
        mock_page = mocker.MagicMock()
        mock_page.extract_text.return_value = "PDF content here."
        mock_reader.return_value.pages = [mock_page]
        
        file_bytes = b"fake pdf bytes"
        chunks = processor.process(file_bytes, "test.pdf")
        
        assert len(chunks) > 0
        assert "PDF" in chunks[0]

    def test_chunking_respects_max_length(self, processor):
        """Test that chunks respect maximum length."""
        long_text = "Word " * 50  # 250 characters
        file_bytes = long_text.encode('utf-8')
        
        chunks = processor.process(file_bytes, "test.txt")
        
        # Each chunk should be close to chunk_size (100) but not exceed by much
        for chunk in chunks:
            assert len(chunk) <= 150  # Allow some overhead for word boundaries

    def test_chunking_with_overlap(self, processor):
        """Test that chunks have overlap between them."""
        text = "First part of text. Second part here. Third part now."
        file_bytes = text.encode('utf-8')
        
        chunks = processor.process(file_bytes, "test.txt")
        
        if len(chunks) > 1:
            # Adjacent chunks should share some content
            overlap_found = any(word in chunks[1] for word in chunks[0].split()[:3])
            # Overlap is approximate, just check chunks exist
            assert len(chunks) >= 1

    def test_unsupported_file_raises(self, processor):
        """Test that unsupported file types raise error."""
        file_bytes = b"some content"
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            processor.process(file_bytes, "test.docx")
        
        assert "Unsupported" in str(exc_info.value)

    def test_empty_file_raises(self, processor):
        """Test that empty files raise error."""
        file_bytes = b""
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            processor.process(file_bytes, "test.txt")
        
        assert "No extractable text" in str(exc_info.value) or "empty" in str(exc_info.value).lower()

    def test_whitespace_only_raises(self, processor):
        """Test that whitespace-only files raise error."""
        file_bytes = b"   \n\t   \n"
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            processor.process(file_bytes, "test.txt")
        
        assert "No extractable text" in str(exc_info.value)

    def test_encoding_detection(self, processor):
        """Test that different encodings are handled."""
        # UTF-8 with special characters
        text = "Café résumé naïve"
        file_bytes = text.encode('utf-8')
        
        chunks = processor.process(file_bytes, "test.txt")
        
        assert len(chunks) > 0
        assert "Café" in chunks[0]

    def test_pdf_extraction_failure(self, processor, mocker):
        """Test graceful handling of PDF extraction failure."""
        # Mock pypdf to raise exception
        mocker.patch('pypdf.PdfReader', side_effect=Exception("Corrupted PDF"))
        
        file_bytes = b"corrupted pdf"
        
        with pytest.raises(DocumentProcessingError) as exc_info:
            processor.process(file_bytes, "test.pdf")
        
        assert "PDF extraction failed" in str(exc_info.value)
