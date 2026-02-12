"""Tests for API models."""

import pytest
from pydantic import ValidationError

from src.api.models import (
    Message,
    ChatTemplateKwargs,
    ChatRequest,
    Usage,
    Choice,
    ChatResponse,
    StreamChunk,
    ReasoningContent
)


class TestMessage:
    """Tests for Message model."""
    
    def test_valid_message(self):
        """Test creating valid message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.reasoning_details is None
    
    def test_message_with_reasoning(self):
        """Test message with reasoning details."""
        msg = Message(
            role="assistant",
            content="Response",
            reasoning_details="Thinking..."
        )
        assert msg.reasoning_details == "Thinking..."
    
    def test_invalid_role(self):
        """Test invalid role."""
        with pytest.raises(ValidationError):
            Message(role="invalid", content="Hello")
    
    def test_empty_content(self):
        """Test empty content validation."""
        with pytest.raises(ValidationError):
            Message(role="user", content="")
    
    def test_system_message(self):
        """Test system message."""
        msg = Message(role="system", content="System prompt")
        assert msg.role == "system"


class TestChatTemplateKwargs:
    """Tests for ChatTemplateKwargs."""
    
    def test_default_thinking(self):
        """Test default thinking value."""
        kwargs = ChatTemplateKwargs()
        assert kwargs.thinking is True
    
    def test_disabled_thinking(self):
        """Test disabled thinking."""
        kwargs = ChatTemplateKwargs(thinking=False)
        assert kwargs.thinking is False


class TestChatRequest:
    """Tests for ChatRequest."""
    
    def test_valid_request(self):
        """Test valid request."""
        request = ChatRequest(
            model="test-model",
            messages=[
                Message(role="user", content="Hello")
            ],
            max_tokens=100,
            temperature=0.7,
            top_p=0.9
        )
        assert request.model == "test-model"
        assert len(request.messages) == 1
    
    def test_default_values(self):
        """Test default values."""
        request = ChatRequest(
            model="test-model",
            messages=[Message(role="user", content="Hi")]
        )
        assert request.max_tokens == 65536
        assert request.temperature == 1.00
        assert request.top_p == 0.95
        assert request.stream is True
        assert request.chat_template_kwargs.thinking is True
    
    def test_invalid_max_tokens(self):
        """Test invalid max_tokens."""
        with pytest.raises(ValidationError):
            ChatRequest(
                model="test",
                messages=[Message(role="user", content="Hi")],
                max_tokens=0
            )
        
        with pytest.raises(ValidationError):
            ChatRequest(
                model="test",
                messages=[Message(role="user", content="Hi")],
                max_tokens=200000
            )
    
    def test_invalid_temperature(self):
        """Test invalid temperature."""
        with pytest.raises(ValidationError):
            ChatRequest(
                model="test",
                messages=[Message(role="user", content="Hi")],
                temperature=-0.1
            )
    
    def test_invalid_top_p(self):
        """Test invalid top_p."""
        with pytest.raises(ValidationError):
            ChatRequest(
                model="test",
                messages=[Message(role="user", content="Hi")],
                top_p=1.1
            )
    
    def test_empty_messages(self):
        """Test empty messages."""
        with pytest.raises(ValidationError):
            ChatRequest(model="test", messages=[])


class TestStreamChunk:
    """Tests for StreamChunk."""
    
    def test_stream_chunk_creation(self):
        """Test creating stream chunk."""
        chunk = StreamChunk(
            id="chunk-1",
            object="chat.completion.chunk",
            created=1234567890,
            model="test-model",
            choices=[
                Choice(index=0, delta={"content": "Hello"})
            ]
        )
        assert chunk.id == "chunk-1"
        assert chunk.delta_content == "Hello"
    
    def test_delta_content_extraction(self):
        """Test extracting content from delta."""
        chunk = StreamChunk(
            id="1",
            object="chunk",
            created=1,
            model="test",
            choices=[Choice(index=0, delta={"content": "Test"})]
        )
        assert chunk.delta_content == "Test"
    
    def test_delta_reasoning_extraction(self):
        """Test extracting reasoning from delta."""
        chunk = StreamChunk(
            id="1",
            object="chunk",
            created=1,
            model="test",
            choices=[Choice(index=0, delta={"reasoning": "Thinking"})]
        )
        assert chunk.delta_reasoning == "Thinking"
    
    def test_is_done_detection(self):
        """Test detecting end of stream."""
        chunk = StreamChunk(
            id="1",
            object="chunk",
            created=1,
            model="test",
            choices=[Choice(index=0, finish_reason="stop")]
        )
        assert chunk.is_done is True


class TestReasoningContent:
    """Tests for ReasoningContent."""
    
    def test_thinking_tag_removal(self):
        """Test removal of  <think>  tags."""
        content = ReasoningContent(
            content="<think>This is thinking</think>"
        )
        assert "<think>" not in content.cleaned_content
        assert "</think>" not in content.cleaned_content
    
    def test_empty_content(self):
        """Test empty content handling."""
        content = ReasoningContent(content="")
        assert content.cleaned_content == ""
    
    def test_content_without_tags(self):
        """Test content without tags."""
        content = ReasoningContent(content="Plain thinking")
        assert content.cleaned_content == "Plain thinking"


class TestChatResponse:
    """Tests for ChatResponse."""
    
    def test_response_creation(self):
        """Test creating response."""
        response = ChatResponse(
            id="response-1",
            object="chat.completion",
            created=1234567890,
            model="test-model",
            choices=[
                Choice(
                    index=0,
                    message=Message(role="assistant", content="Response"),
                    finish_reason="stop"
                )
            ]
        )
        assert response.id == "response-1"
        assert len(response.choices) == 1
