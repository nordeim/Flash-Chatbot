"""Tests for state manager."""

import pytest
from unittest.mock import MagicMock, patch

from src.services.state_manager import ChatStateManager


class TestChatStateManager:
    """Tests for ChatStateManager."""
    
    @pytest.fixture
    def state_manager(self, mock_session_state):
        """Create state manager with mocked session state."""
        return ChatStateManager()
    
    def test_initialization(self, state_manager):
        """Test state manager initialization."""
        assert state_manager.session_key == "chat_messages"
        assert state_manager.session_id_key == "session_id"
    
    def test_has_messages(self, state_manager):
        """Test has_messages property."""
        assert state_manager.has_messages is False
        
        state_manager.add_user_message("Hello")
        assert state_manager.has_messages is True
    
    def test_add_user_message(self, state_manager):
        """Test adding user message."""
        msg = state_manager.add_user_message("Hello")
        
        assert msg["role"] == "user"
        assert msg["content"] == "Hello"
        assert "timestamp" in msg
    
    def test_add_assistant_message(self, state_manager):
        """Test adding assistant message."""
        msg = state_manager.add_assistant_message(
            "Response",
            thinking="Thinking...",
            reasoning_details={"details": "test"}
        )
        
        assert msg["role"] == "assistant"
        assert msg["content"] == "Response"
        assert msg["thinking"] == "Thinking..."
        assert msg["reasoning_details"] == {"details": "test"}
    
    def test_clear_history(self, state_manager):
        """Test clearing history."""
        state_manager.add_user_message("Hello")
        assert state_manager.has_messages is True
        
        state_manager.clear_history()
        assert state_manager.has_messages is False
    
    def test_get_last_message(self, state_manager):
        """Test getting last message."""
        assert state_manager.get_last_message() is None
        
        state_manager.add_user_message("First")
        state_manager.add_user_message("Second")
        
        last = state_manager.get_last_message()
        assert last["content"] == "Second"
    
    def test_export_conversation(self, state_manager):
        """Test exporting conversation."""
        state_manager.add_user_message("Hello")
        
        exported = state_manager.export_conversation()
        
        assert "session_id" in exported
        assert "messages" in exported
        assert len(exported["messages"]) == 1
    
    def test_import_conversation(self, state_manager):
        """Test importing conversation."""
        data = {
            "session_id": "test-id",
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }
        
        result = state_manager.import_conversation(data)
        
        assert result is True
        assert state_manager.has_messages is True
        assert len(state_manager.messages) == 1
    
    def test_export_to_json(self, state_manager):
        """Test export to JSON."""
        state_manager.add_user_message("Hello")
        
        json_str = state_manager.export_to_json()
        
        assert isinstance(json_str, str)
        assert "Hello" in json_str
    
    def test_import_from_json(self, state_manager):
        """Test import from JSON."""
        json_str = '{"session_id": "test", "messages": [{"role": "user", "content": "Hi"}]}'
        
        result = state_manager.import_from_json(json_str)
        
        assert result is True
        assert state_manager.has_messages is True
    
    def test_get_stats(self, state_manager):
        """Test getting stats."""
        state_manager.add_user_message("Hello")
        state_manager.add_assistant_message("Hi!")
        
        stats = state_manager.get_stats()
        
        assert stats["total_messages"] == 2
        assert stats["user_messages"] == 1
        assert stats["assistant_messages"] == 1
        assert stats["total_characters"] > 0
    
    def test_pending_prompt(self, state_manager):
        """Test pending prompt."""
        assert state_manager.pending_prompt is None
        
        state_manager.pending_prompt = "Example question"
        assert state_manager.pending_prompt == "Example question"
