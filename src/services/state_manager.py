"""Session state management for chat conversations."""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

import streamlit as st

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationState:
    """Conversation state data class."""
    
    session_id: str
    messages: List[Dict[str, Any]]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class ChatStateManager:
    """Manager for chat session state."""
    
    SESSION_KEY = "chat_messages"
    SESSION_ID_KEY = "session_id"
    PENDING_PROMPT_KEY = "pending_prompt"
    
    def __init__(self):
        """Initialize state manager."""
        self._ensure_session_state()
    
    def _ensure_session_state(self) -> None:
        """Ensure session state is initialized."""
        if self.SESSION_KEY not in st.session_state:
            st.session_state[self.SESSION_KEY] = []
        
        if self.SESSION_ID_KEY not in st.session_state:
            st.session_state[self.SESSION_ID_KEY] = str(uuid.uuid4())
        
        if self.PENDING_PROMPT_KEY not in st.session_state:
            st.session_state[self.PENDING_PROMPT_KEY] = None
    
    @property
    def session_id(self) -> str:
        """Get current session ID."""
        return st.session_state.get(self.SESSION_ID_KEY, str(uuid.uuid4()))
    
    @property
    def messages(self) -> List[Dict[str, Any]]:
        """Get conversation messages."""
        return st.session_state.get(self.SESSION_KEY, [])
    
    @messages.setter
    def messages(self, value: List[Dict[str, Any]]) -> None:
        """Set conversation messages."""
        st.session_state[self.SESSION_KEY] = value
    
    @property
    def has_messages(self) -> bool:
        """Check if there are any messages."""
        return len(self.messages) > 0
    
    @property
    def pending_prompt(self) -> Optional[str]:
        """Get pending prompt (from example buttons)."""
        return st.session_state.get(self.PENDING_PROMPT_KEY)
    
    @pending_prompt.setter
    def pending_prompt(self, value: Optional[str]) -> None:
        """Set pending prompt."""
        st.session_state[self.PENDING_PROMPT_KEY] = value
    
    def add_message(
        self,
        role: str,
        content: str,
        **metadata
    ) -> Dict[str, Any]:
        """Add message to conversation.
        
        Args:
            role: Message role (user/assistant)
            content: Message content
            **metadata: Additional metadata
            
        Returns:
            Added message dictionary
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            **metadata
        }
        
        self.messages.append(message)
        logger.debug(f"Added {role} message to conversation")
        
        return message
    
    def add_user_message(self, content: str) -> Dict[str, Any]:
        """Add user message.
        
        Args:
            content: Message content
            
        Returns:
            Added message dictionary
        """
        return self.add_message("user", content)
    
    def add_assistant_message(
        self,
        content: str,
        thinking: Optional[str] = None,
        reasoning_details: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Add assistant message.
        
        Args:
            content: Response content
            thinking: Optional thinking/reasoning content
            reasoning_details: Optional reasoning details
            
        Returns:
            Added message dictionary
        """
        metadata = {}
        if thinking:
            metadata["thinking"] = thinking
        if reasoning_details:
            metadata["reasoning_details"] = reasoning_details
        
        return self.add_message("assistant", content, **metadata)
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages = []
        logger.info("Cleared conversation history")
    
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """Get last message in conversation."""
        messages = self.messages
        if messages:
            return messages[-1]
        return None
    
    def get_messages_for_api(self) -> List[Dict[str, Any]]:
        """Get messages formatted for API (without metadata)."""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
            if msg.get("content")
        ]
    
    def export_conversation(self) -> Dict[str, Any]:
        """Export conversation to dictionary.
        
        Returns:
            Conversation data dictionary
        """
        return {
            "session_id": self.session_id,
            "created_at": datetime.utcnow().isoformat(),
            "messages": self.messages
        }
    
    def import_conversation(self, data: Dict[str, Any]) -> bool:
        """Import conversation from dictionary.
        
        Args:
            data: Conversation data dictionary
            
        Returns:
            True if successful
        """
        try:
            if "messages" in data:
                self.messages = data["messages"]
                logger.info(f"Imported {len(self.messages)} messages")
                return True
        except Exception as e:
            logger.error(f"Failed to import conversation: {e}")
        
        return False
    
    def export_to_json(self) -> str:
        """Export conversation to JSON string.
        
        Returns:
            JSON string
        """
        return json.dumps(self.export_conversation(), indent=2)
    
    def import_from_json(self, json_str: str) -> bool:
        """Import conversation from JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            True if successful
        """
        try:
            data = json.loads(json_str)
            return self.import_conversation(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics.
        
        Returns:
            Statistics dictionary
        """
        messages = self.messages
        
        user_count = sum(1 for m in messages if m.get("role") == "user")
        assistant_count = sum(1 for m in messages if m.get("role") == "assistant")
        total_chars = sum(len(m.get("content", "")) for m in messages)
        
        return {
            "total_messages": len(messages),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "total_characters": total_chars,
            "session_id": self.session_id
        }
