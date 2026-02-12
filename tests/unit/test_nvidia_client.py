"""Tests for NVIDIA API client."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from src.api.nvidia_client import NvidiaChatClient
from src.api.exceptions import (
    NvidiaAPIError,
    NvidiaAuthError,
    NvidiaRateLimitError,
    NvidiaTimeoutError
)
from src.api.models import Message


class TestNvidiaChatClient:
    """Tests for NvidiaChatClient."""
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = NvidiaChatClient(api_key="nvapi-test-key")
        assert client.api_key == "nvapi-test-key"
        assert client.base_url == "https://integrate.api.nvidia.com/v1"
        client.close()
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        with pytest.raises(NvidiaAuthError):
            NvidiaChatClient(api_key="")
    
    @patch('src.api.nvidia_client.requests.Session')
    def test_get_headers(self, mock_session):
        """Test header generation."""
        client = NvidiaChatClient(api_key="nvapi-test")
        
        # Non-streaming headers
        headers = client._get_headers(stream=False)
        assert headers["Authorization"] == "Bearer nvapi-test"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        
        # Streaming headers
        headers = client._get_headers(stream=True)
        assert headers["Accept"] == "text/event-stream"
        
        client.close()
    
    @patch('src.api.nvidia_client.requests.Session')
    @patch('src.api.nvidia_client.get_settings')
    def test_chat_complete(self, mock_get_settings, mock_session_class):
        """Test chat completion."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "test",
            "object": "chat.completion",
            "created": 123,
            "model": "test-model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Test response"
                    },
                    "finish_reason": "stop"
                }
            ]
        }
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        mock_settings = Mock()
        mock_settings.nvidia_api_key = "nvapi-test"
        mock_settings.nvidia_base_url = "https://test.api.com"
        mock_get_settings.return_value = mock_settings
        
        client = NvidiaChatClient(api_key="nvapi-test")
        client.session = mock_session
        
        messages = [Message(role="user", content="Hello")]
        response = client.chat_complete(messages=messages)
        
        assert response.choices[0].message.content == "Test response"
        client.close()
    
    @patch('src.api.nvidia_client.requests.Session')
    def test_chat_complete_auth_error(self, mock_session_class):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = NvidiaChatClient(api_key="nvapi-test")
        client.session = mock_session
        
        messages = [Message(role="user", content="Hello")]
        
        with pytest.raises(NvidiaAuthError):
            client.chat_complete(messages=messages)
        
        client.close()
    
    @patch('src.api.nvidia_client.requests.Session')
    def test_chat_complete_rate_limit(self, mock_session_class):
        """Test rate limit error handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = NvidiaChatClient(api_key="nvapi-test")
        client.session = mock_session
        
        messages = [Message(role="user", content="Hello")]
        
        with pytest.raises(NvidiaRateLimitError):
            client.chat_complete(messages=messages)
        
        client.close()
    
    @patch('src.api.nvidia_client.requests.Session')
    def test_chat_complete_stream(self, mock_session_class):
        """Test streaming chat completion."""
        # Create mock streaming response
        def iter_lines():
            lines = [
                b'data: {"id":"1","object":"chat.completion.chunk","created":1,"model":"test","choices":[{"index":0,"delta":{"content":"Hello"}}]}',
                b'data: {"id":"2","object":"chat.completion.chunk","created":1,"model":"test","choices":[{"index":0,"delta":{"content":" World"}}]}',
                b'data: [DONE]'
            ]
            for line in lines:
                yield line
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter_lines()
        
        mock_session = Mock()
        mock_session.post.return_value.__enter__ = Mock(return_value=mock_response)
        mock_session.post.return_value.__exit__ = Mock(return_value=False)
        mock_session_class.return_value = mock_session
        
        client = NvidiaChatClient(api_key="nvapi-test")
        client.session = mock_session
        
        messages = [Message(role="user", content="Hello")]
        chunks = list(client.chat_complete_stream(messages=messages))
        
        assert len(chunks) > 0
        client.close()
    
    def test_context_manager(self):
        """Test context manager."""
        with NvidiaChatClient(api_key="nvapi-test") as client:
            assert client.api_key == "nvapi-test"
    
    def test_close(self):
        """Test close method."""
        client = NvidiaChatClient(api_key="nvapi-test")
        client.close()
        # Should not raise any errors
