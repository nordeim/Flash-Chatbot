"""Message formatting utilities."""

import re
from typing import List, Optional, Dict, Any

from src.api.models import Message


class MessageFormatter:
    """Formatter for chat messages."""
    
    @staticmethod
    def format_messages_for_api(
        history: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> List[Message]:
        """Format conversation history for API.
        
        Args:
            history: List of message dictionaries with role and content
            system_prompt: Optional system prompt
            
        Returns:
            List of Message objects
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt and system_prompt.strip():
            messages.append(Message(role="system", content=system_prompt.strip()))
        
        # Add conversation history
        for msg in history:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if not content:
                continue
            
            if role == "user":
                messages.append(Message(role="user", content=content))
            elif role == "assistant":
                assistant_msg = Message(role="assistant", content=content)
                
                # Preserve reasoning details if present
                if msg.get("reasoning_details"):
                    assistant_msg.reasoning_details = msg["reasoning_details"]
                
                messages.append(assistant_msg)
        
        return messages
    
    @staticmethod
    def add_user_message(
        messages: List[Message],
        content: str
    ) -> List[Message]:
        """Add user message to message list.
        
        Args:
            messages: Existing messages
            content: User message content
            
        Returns:
            Updated message list
        """
        messages.append(Message(role="user", content=content))
        return messages
    
    @staticmethod
    def add_assistant_message(
        messages: List[Message],
        content: str,
        reasoning_details: Optional[str] = None
    ) -> List[Message]:
        """Add assistant message to message list.
        
        Args:
            messages: Existing messages
            content: Assistant response content
            reasoning_details: Optional reasoning/thinking content
            
        Returns:
            Updated message list
        """
        msg = Message(role="assistant", content=content)
        if reasoning_details:
            msg.reasoning_details = reasoning_details
        messages.append(msg)
        return messages
    
    @staticmethod
    def clean_thinking_content(text: str) -> str:
        """Clean thinking content by removing <think> tags.
        
        Args:
            text: Raw thinking text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove <think> tags
        cleaned = re.sub(r'</?think>', '', text)
        
        # Remove extra whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
    
    @staticmethod
    def extract_code_blocks(text: str) -> List[Dict[str, str]]:
        """Extract code blocks from markdown text.
        
        Args:
            text: Markdown text
            
        Returns:
            List of code block dictionaries with language and code
        """
        code_blocks = []
        
        # Match code blocks with optional language
        pattern = r'```(\w*)\n(.*?)```'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            language = match.group(1) or "text"
            code = match.group(2)
            code_blocks.append({
                "language": language,
                "code": code
            })
        
        return code_blocks
    
    @staticmethod
    def format_for_display(content: str) -> str:
        """Format content for display.
        
        Args:
            content: Raw content
            
        Returns:
            Formatted content
        """
        if not content:
            return ""
        
        # Convert newlines to markdown breaks
        formatted = content.replace('\n', '  \n')
        
        return formatted
    
    @staticmethod
    def truncate_content(content: str, max_length: int = 1000) -> str:
        """Truncate content to max length.
        
        Args:
            content: Content to truncate
            max_length: Maximum length
            
        Returns:
            Truncated content
        """
        if len(content) <= max_length:
            return content
        
        return content[:max_length] + "..."
    
    @staticmethod
    def format_conversation_stats(
        messages: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate conversation statistics.
        
        Args:
            messages: Conversation messages
            
        Returns:
            Dictionary with statistics
        """
        user_count = sum(1 for m in messages if m.get("role") == "user")
        assistant_count = sum(1 for m in messages if m.get("role") == "assistant")
        total_chars = sum(len(m.get("content", "")) for m in messages)
        
        return {
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "total_messages": len(messages),
            "total_characters": total_chars
        }
