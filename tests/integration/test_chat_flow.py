"""Integration tests for chat flow."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from src.services.chat_service import ChatService
from src.services.state_manager import ChatStateManager
from src.api.models import Message


@pytest.mark.integration
class TestChatFlow:
    """Integration tests for end-to-end chat flow."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock NVIDIA client."""
        client = Mock()
        
        # Mock chat_complete
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Mocked response", role="assistant"))
        ]
        client.chat_complete.return_value = mock_response
        
        # Mock chat_complete_stream
        def mock_stream(*args, **kwargs):
            chunks = [
                Mock(
                    delta_content="Hello",
                    delta_reasoning=None,
                    reasoning_details=None
                ),
                Mock(
                    delta_content=" World",
                    delta_reasoning="Let me think",
                    reasoning_details=None
                ),
                Mock(
                    delta_content="!",
                    delta_reasoning=None,
                    reasoning_details={"type": "final"}
                )
            ]
            for chunk in chunks:
                yield chunk
        
        client.chat_complete_stream = mock_stream
        
        return client
    
    def test_send_message(self, mock_client):
        """Test sending a message."""
        service = ChatService(client=mock_client)
        
        response = service.send_message("Hello")
        
        assert response.content is not None
        assert response.finished is True
        
        # Verify message was saved
        assert service.state_manager.has_messages
        messages = service.state_manager.messages
        assert len(messages) == 2  # user + assistant
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
    
    def test_stream_message(self, mock_client):
        """Test streaming a message."""
        service = ChatService(client=mock_client)
        
        results = []
        for thinking, content, details in service.stream_message("Hello"):
            results.append((thinking, content, details))
        
        assert len(results) > 0
        last_thinking, last_content, last_details = results[-1]
        assert "World" in last_content
        assert last_details is not None
    
    def test_conversation_history(self, mock_client):
        """Test conversation history."""
        service = ChatService(client=mock_client)
        
        # Send multiple messages
        service.send_message("First message")
        service.send_message("Second message")
        
        # Verify history
        messages = service.state_manager.messages
        assert len(messages) == 4  # 2 user + 2 assistant
        
        # Verify order
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "First message"
        assert messages[2]["role"] == "user"
        assert messages[2]["content"] == "Second message"
    
    def test_clear_conversation(self, mock_client):
        """Test clearing conversation."""
        service = ChatService(client=mock_client)
        
        service.send_message("Hello")
        assert service.state_manager.has_messages
        
        service.clear_conversation()
        assert not service.state_manager.has_messages
    
    def test_conversation_stats(self, mock_client):
        """Test conversation statistics."""
        service = ChatService(client=mock_client)
        
        service.send_message("Hello")
        
        stats = service.get_conversation_stats()
        
        assert stats["total_messages"] == 2
        assert stats["user_messages"] == 1
        assert stats["assistant_messages"] == 1
        assert stats["total_characters"] > 0
    
    def test_export_import_conversation(self, mock_client, tmp_path):
        """Test exporting and importing conversation."""
        service = ChatService(client=mock_client)
        
        service.send_message("Test message")
        
        # Export
        json_str = service.export_conversation()
        
        # Clear
        service.clear_conversation()
        assert not service.state_manager.has_messages
        
        # Import
        result = service.import_conversation(json_str)
        assert result is True
        assert service.state_manager.has_messages


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling."""
    
    def test_error_handling_in_stream(self):
        """Test error handling in stream."""
        mock_client = Mock()
        
        def error_stream(*args, **kwargs):
            raise Exception("API Error")
        
        mock_client.chat_complete_stream = error_stream
        
        service = ChatService(client=mock_client)
        
        results = list(service.stream_message("Hello"))
        
        # Should still yield results with error message
        assert len(results) == 1
        _, content, _ = results[0]
        assert "Error" in content
    
    def test_error_handling_in_send(self):
        """Test error handling in send."""
        mock_client = Mock()
        mock_client.chat_complete.side_effect = Exception("API Error")
        
        service = ChatService(client=mock_client)
        
        response = service.send_message("Hello")
        
        assert "Error" in response.content


@pytest.mark.integration
class TestContextManager:
    """Integration tests for context manager."""
    
    def test_context_manager(self, mock_client):
        """Test using service as context manager."""
        with ChatService(client=mock_client) as service:
            service.send_message("Hello")
            assert service.state_manager.has_messages
        
        # Client should be closed
        mock_client.close.assert_called_once()
