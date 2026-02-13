"""Tests for ChatService RAG integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.services.chat_service import ChatService
from src.services.state_manager import ChatStateManager
from src.rag.retriever import SimpleRetriever, Document


class TestChatServiceRAG:
    """Test suite for ChatService RAG functionality."""

    @pytest.fixture
    def mock_embedder(self):
        """Create mock embedder."""
        embedder = Mock()
        embedder.embed_documents.return_value = np.array([
            [1.0, 0.0, 0.0] + [0.0] * 381,  # 384-dim
            [0.0, 1.0, 0.0] + [0.0] * 381,
        ])
        embedder.embed_query.return_value = np.array([1.0, 0.0, 0.0] + [0.0] * 381)
        return embedder

    @pytest.fixture
    def mock_retriever(self, mock_embedder):
        """Create mock retriever with documents."""
        retriever = SimpleRetriever(mock_embedder)
        # Add some documents
        retriever.add_documents(
            ["Python is a programming language", "JavaScript runs in browsers"],
            metadata=[{"source": "doc1"}, {"source": "doc2"}]
        )
        return retriever

    @pytest.fixture
    def chat_service(self):
        """Create ChatService with mocked NVIDIA client."""
        with patch('src.services.chat_service.NvidiaChatClient') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.chat_complete_stream.return_value = iter([
                Mock(delta_content="Response with context", delta_reasoning="", reasoning_details=None)
            ])
            mock_client.return_value = mock_client_instance
            
            service = ChatService()
            service.client = mock_client_instance
            yield service

    def test_stream_message_with_rag_context_injects_chunks(self, chat_service, mock_retriever):
        """Test that RAG context is injected into system prompt."""
        # Setup mock client to capture messages
        captured_messages = []
        
        def capture_stream(messages, **kwargs):
            captured_messages.append(messages)
            yield Mock(delta_content="Answer", delta_reasoning="", reasoning_details=None)
        
        chat_service.client.chat_complete_stream = capture_stream
        
        # Call with RAG context
        generator = chat_service.stream_message_with_rag(
            content="What is Python?",
            retriever=mock_retriever,
            system_prompt="You are a helpful assistant."
        )
        
        # Consume generator
        list(generator)
        
        # Verify messages were captured
        assert len(captured_messages) > 0
        messages = captured_messages[0]
        
        # Find system message
        system_msg = next((m for m in messages if m.role == "system"), None)
        assert system_msg is not None
        
        # Check that context was added
        assert "Python" in system_msg.content or "programming" in system_msg.content

    def test_no_context_if_no_document_uploaded(self, chat_service):
        """Test that no context is added when retriever is empty."""
        # Create empty retriever
        mock_embedder = Mock()
        empty_retriever = SimpleRetriever(mock_embedder)
        # No documents added
        
        captured_messages = []
        
        def capture_stream(messages, **kwargs):
            captured_messages.append(messages)
            yield Mock(delta_content="Answer", delta_reasoning="", reasoning_details=None)
        
        chat_service.client.chat_complete_stream = capture_stream
        
        # Call with empty retriever
        generator = chat_service.stream_message_with_rag(
            content="What is Python?",
            retriever=empty_retriever,
            system_prompt="You are a helpful assistant."
        )
        
        list(generator)
        
        # Verify messages were captured
        assert len(captured_messages) > 0
        messages = captured_messages[0]
        
        # Find system message
        system_msg = next((m for m in messages if m.role == "system"), None)
        assert system_msg is not None
        
        # Original system prompt should be unchanged
        assert system_msg.content == "You are a helpful assistant."

    def test_retrieval_failure_graceful_degradation(self, chat_service):
        """Test graceful handling of retrieval failures."""
        # Create retriever that will fail
        mock_embedder = Mock()
        mock_embedder.embed_query.side_effect = Exception("Embedding failed")
        failing_retriever = SimpleRetriever(mock_embedder)
        failing_retriever.add_documents(["Some text"])
        
        captured_messages = []
        
        def capture_stream(messages, **kwargs):
            captured_messages.append(messages)
            yield Mock(delta_content="Answer without context", delta_reasoning="", reasoning_details=None)
        
        chat_service.client.chat_complete_stream = capture_stream
        
        # Call with failing retriever
        generator = chat_service.stream_message_with_rag(
            content="What is Python?",
            retriever=failing_retriever,
            system_prompt="You are a helpful assistant."
        )
        
        # Should not raise exception
        list(generator)
        
        # Verify fallback behavior
        assert len(captured_messages) > 0
        messages = captured_messages[0]
        system_msg = next((m for m in messages if m.role == "system"), None)
        assert system_msg is not None
        # Should have original prompt without context
        assert system_msg.content == "You are a helpful assistant."

    def test_stream_message_without_rag_calls_original(self, chat_service):
        """Test that stream_message still works without RAG."""
        captured_messages = []
        
        def capture_stream(messages, **kwargs):
            captured_messages.append(messages)
            yield Mock(delta_content="Answer", delta_reasoning="", reasoning_details=None)
        
        chat_service.client.chat_complete_stream = capture_stream
        
        # Call without retriever
        generator = chat_service.stream_message(
            content="Hello",
            system_prompt="Be helpful"
        )
        
        list(generator)
        
        assert len(captured_messages) > 0
        messages = captured_messages[0]
        assert any(m.role == "user" and m.content == "Hello" for m in messages)

    def test_retriever_none_skips_context(self, chat_service):
        """Test that None retriever skips context injection."""
        captured_messages = []
        
        def capture_stream(messages, **kwargs):
            captured_messages.append(messages)
            yield Mock(delta_content="Answer", delta_reasoning="", reasoning_details=None)
        
        chat_service.client.chat_complete_stream = capture_stream
        
        # Call with None retriever
        generator = chat_service.stream_message_with_rag(
            content="Hello",
            retriever=None,
            system_prompt="Be helpful"
        )
        
        list(generator)
        
        assert len(captured_messages) > 0
        messages = captured_messages[0]
        system_msg = next((m for m in messages if m.role == "system"), None)
        assert system_msg.content == "Be helpful"

    def test_retrieved_context_formatted_correctly(self, chat_service, mock_retriever):
        """Test that retrieved context is formatted properly."""
        captured_messages = []
        
        def capture_stream(messages, **kwargs):
            captured_messages.append(messages)
            yield Mock(delta_content="Answer", delta_reasoning="", reasoning_details=None)
        
        chat_service.client.chat_complete_stream = capture_stream
        
        generator = chat_service.stream_message_with_rag(
            content="What is Python?",
            retriever=mock_retriever,
            system_prompt="You are helpful."
        )
        
        list(generator)
        
        messages = captured_messages[0]
        system_msg = next((m for m in messages if m.role == "system"), None)
        
        # Check context formatting
        assert "---" in system_msg.content or "context" in system_msg.content.lower()

    def test_user_message_added_before_rag_call(self, chat_service, mock_retriever):
        """Test that user message is added to conversation before API call."""
        chat_service.client.chat_complete_stream.return_value = iter([
            Mock(delta_content="Answer", delta_reasoning="", reasoning_details=None)
        ])
        
        generator = chat_service.stream_message_with_rag(
            content="What is Python?",
            retriever=mock_retriever
        )
        
        list(generator)
        
        # Check that message was added to state
        assert chat_service.state_manager.has_messages
        last_msg = chat_service.state_manager.get_last_message()
        assert last_msg["role"] == "assistant"

    def test_assistant_message_saved_with_rag(self, chat_service, mock_retriever):
        """Test that assistant response is saved after RAG call."""
        chat_service.client.chat_complete_stream.return_value = iter([
            Mock(delta_content="Python is a ", delta_reasoning="Thinking", reasoning_details=None),
            Mock(delta_content="Python is a programming language", delta_reasoning="", reasoning_details=None),
        ])
        
        generator = chat_service.stream_message_with_rag(
            content="What is Python?",
            retriever=mock_retriever
        )
        
        list(generator)
        
        # Check saved message
        messages = chat_service.state_manager.messages
        assistant_msgs = [m for m in messages if m["role"] == "assistant"]
        assert len(assistant_msgs) > 0
        assert "Python" in assistant_msgs[-1]["content"]
