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

        Raises:
            ValueError: If chunk_overlap >= chunk_size
        """
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be < chunk_size ({chunk_size})"
            )
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
        if end < text_len:
            start = end - self.chunk_overlap
            # Ensure forward progress - always advance at least 1 character
            if start >= end:
                start = end
            # Additional safety: if we're stuck, force progress
            if start >= end:
                start = min(end + 1, text_len)
        else:
            start = text_len

        return chunks
