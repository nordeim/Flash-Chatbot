"""Pytest fixtures and configuration."""

import json
import pytest
from unittest.mock import MagicMock, patch
from typing import Generator, List, Dict, Any

from src.config.settings import Settings
from src.api.models import Message, ChatResponse, StreamChunk, Choice


@pytest.fixture
def mock_settings():
    """Mock settings with test values."""
    return Settings(
        nvidia_api_key="nvapi-test-key",
        nvidia_base_url="https://test.api.nvidia.com/v1",
        default_model="test-model",
        default_max_tokens=1000,
        default_temperature=0.7,
        default_top_p=0.9,
        log_level="DEBUG"
    )


@pytest.fixture
def sample_messages() -> List[Message]:
    """Sample messages for testing."""
    return [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello!"),
        Message(role="assistant", content="Hello! How can I help you today?")
    ]


@pytest.fixture
def mock_chat_response() -> ChatResponse:
    """Mock chat response."""
    return ChatResponse(
        id="test-response-id",
        object="chat.completion",
        created=1234567890,
        model="test-model",
        choices=[
            Choice(
                index=0,
                message=Message(role="assistant", content="Test response"),
                finish_reason="stop"
            )
        ]
    )


@pytest.fixture
def mock_stream_chunks() -> List[StreamChunk]:
    """Mock streaming chunks."""
    return [
        StreamChunk(
            id="chunk-1",
            object="chat.completion.chunk",
            created=1234567890,
            model="test-model",
            choices=[
                Choice(
                    index=0,
                    delta={"content": "Hello"}
                )
            ]
        ),
        StreamChunk(
            id="chunk-2",
            object="chat.completion.chunk",
            created=1234567890,
            model="test-model",
            choices=[
                Choice(
                    index=0,
                    delta={"content": " World"}
                )
            ]
        ),
        StreamChunk(
            id="chunk-3",
            object="chat.completion.chunk",
            created=1234567890,
            model="test-model",
            choices=[
                Choice(
                    index=0,
                    delta={"content": "!"},
                    finish_reason="stop"
                )
            ]
        )
    ]


@pytest.fixture
def mock_nvidia_api_response():
    """Mock NVIDIA API response."""
    return {
        "id": "test-response",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response."
                },
                "finish_reason": "stop"
            }
        ]
    }


@pytest.fixture
def mock_nvidia_stream_response():
    """Mock NVIDIA streaming response."""
    chunks = [
        'data: {"id":"1","object":"chat.completion.chunk","created":1,"model":"test","choices":[{"index":0,"delta":{"content":"Hello"}}]}',
        'data: {"id":"2","object":"chat.completion.chunk","created":1,"model":"test","choices":[{"index":0,"delta":{"content":" "}}]}',
        'data: {"id":"3","object":"chat.completion.chunk","created":1,"model":"test","choices":[{"index":0,"delta":{"content":"World"}}]}',
        'data: [DONE]'
    ]
    return chunks


@pytest.fixture
def mock_session_state(monkeypatch):
    """Mock Streamlit session state."""
    session_state = {}
    
    class MockSessionState:
        def __init__(self):
            self._state = session_state
        
        def __getitem__(self, key):
            return self._state.get(key)
        
        def __setitem__(self, key, value):
            self._state[key] = value
        
        def __contains__(self, key):
            return key in self._state
        
        def get(self, key, default=None):
            return self._state.get(key, default)
    
    import streamlit as st
    monkeypatch.setattr(st, "session_state", MockSessionState())
    return session_state


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit functions."""
    with patch("streamlit.session_state", {}) as mock_state:
        with patch("streamlit.set_page_config"):
            with patch("streamlit.title"):
                with patch("streamlit.markdown"):
                    with patch("streamlit.chat_message"):
                        with patch("streamlit.chat_input"):
                            with patch("streamlit.sidebar"):
                                yield mock_state
