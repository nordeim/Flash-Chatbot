"""Tests for message formatter."""

import pytest

from src.api.models import Message
from src.services.message_formatter import MessageFormatter


class TestMessageFormatter:
    """Tests for MessageFormatter."""
    
    def test_format_messages_for_api(self):
        """Test formatting messages for API."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!", "reasoning_details": "I should greet them"}
        ]
        
        messages = MessageFormatter.format_messages_for_api(
            history,
            system_prompt="You are helpful."
        )
        
        assert len(messages) == 3
        assert messages[0].role == "system"
        assert messages[0].content == "You are helpful."
        assert messages[1].role == "user"
        assert messages[2].reasoning_details == "I should greet them"
    
    def test_format_messages_without_system(self):
        """Test formatting without system prompt."""
        history = [{"role": "user", "content": "Hello"}]
        
        messages = MessageFormatter.format_messages_for_api(history)
        
        assert len(messages) == 1
        assert messages[0].role == "user"
    
    def test_add_user_message(self):
        """Test adding user message."""
        messages = []
        result = MessageFormatter.add_user_message(messages, "Hello")
        
        assert len(result) == 1
        assert result[0].role == "user"
        assert result[0].content == "Hello"
    
    def test_add_assistant_message(self):
        """Test adding assistant message."""
        messages = []
        result = MessageFormatter.add_assistant_message(
            messages,
            "Response",
            reasoning_details="Thinking"
        )
        
        assert len(result) == 1
        assert result[0].role == "assistant"
        assert result[0].reasoning_details == "Thinking"
    
    def test_clean_thinking_content(self):
        """Test cleaning thinking content."""
        # With tags
        cleaned = MessageFormatter.clean_thinking_content(
            "<think>This is thinking</think>"
        )
        assert "<think>" not in cleaned
        assert "</think>" not in cleaned
        assert "This is thinking" in cleaned
        
        # Empty content
        assert MessageFormatter.clean_thinking_content("") == ""
        
        # None content
        assert MessageFormatter.clean_thinking_content(None) == ""
    
    def test_extract_code_blocks(self):
        """Test extracting code blocks."""
        text = """
Here's some code:
```python
def hello():
    print("Hello")
```
And more:
```javascript
console.log("Hi");
```
"""
        blocks = MessageFormatter.extract_code_blocks(text)
        
        assert len(blocks) == 2
        assert blocks[0]["language"] == "python"
        assert "def hello()" in blocks[0]["code"]
        assert blocks[1]["language"] == "javascript"
    
    def test_format_for_display(self):
        """Test formatting for display."""
        content = "Line 1\nLine 2"
        formatted = MessageFormatter.format_for_display(content)
        
        assert "  \n" in formatted  # Double space before newline
    
    def test_truncate_content(self):
        """Test content truncation."""
        content = "a" * 2000
        truncated = MessageFormatter.truncate_content(content, max_length=1000)
        
        assert len(truncated) <= 1003  # 1000 + "..."
        assert truncated.endswith("...")
    
    def test_format_conversation_stats(self):
        """Test conversation statistics."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        stats = MessageFormatter.format_conversation_stats(messages)
        
        assert stats["user_messages"] == 2
        assert stats["assistant_messages"] == 1
        assert stats["total_messages"] == 3
        assert stats["total_characters"] > 0
