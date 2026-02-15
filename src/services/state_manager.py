"""Session state management for chat conversations."""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

import streamlit as st

from src.utils.logger import get_logger
from src.services.session_manager import SessionManager, Session

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
    """Manager for chat session state with multi-session support."""

    SESSION_KEY = "chat_messages"
    SESSION_ID_KEY = "session_id"
    PENDING_PROMPT_KEY = "pending_prompt"
    RETRIEVER_KEY = "rag_retriever"
    DOCUMENT_NAME_KEY = "rag_document_name"
    SESSION_MANAGER_KEY = "session_manager"

    def __init__(self):
        """Initialize state manager with multi-session support."""
        self._ensure_session_state()
        self._init_session_manager()

    def _init_session_manager(self) -> None:
        """Initialize session manager for multi-session support."""
        if self.SESSION_MANAGER_KEY not in st.session_state:
            st.session_state[self.SESSION_MANAGER_KEY] = SessionManager()

    @property
    def session_manager(self) -> SessionManager:
        """Get session manager.

        Returns:
            SessionManager instance
        """
        return st.session_state.get(self.SESSION_MANAGER_KEY)

    @property
    def current_session(self) -> Optional[Session]:
        """Get current active session.

        Returns:
            Current session or None
        """
        sm = self.session_manager
        if sm:
            return sm.get_current_session()
        return None

    def create_new_session(self, name: Optional[str] = None) -> Optional[Session]:
        """Create a new chat session.

        Args:
            name: Optional session name

        Returns:
            New Session instance
        """
        sm = self.session_manager
        if sm:
            session = sm.create_session(name)
            sm.switch_session(session.id)
            logger.info(f"Created new session: {session.name} ({session.id})")
            return session
        return None

    def switch_to_session(self, session_id: str) -> None:
        """Switch to a different session.

        Args:
            session_id: Session ID to switch to
        """
        sm = self.session_manager
        if sm:
            sm.switch_session(session_id)
            logger.info(f"Switched to session: {session_id}")

    def delete_session(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: Session ID to delete
        """
        sm = self.session_manager
        if sm:
            sm.delete_session(session_id)
            logger.info(f"Deleted session: {session_id}")

    def rename_session(self, session_id: str, new_name: str) -> None:
        """Rename a session.

        Args:
            session_id: Session ID to rename
            new_name: New name for session
        """
        sm = self.session_manager
        if sm:
            sm.rename_session(session_id, new_name)
            logger.info(f"Renamed session {session_id} to: {new_name}")

    def list_sessions(self) -> List[Session]:
        """List all sessions.

        Returns:
            List of all sessions
        """
        sm = self.session_manager
        if sm:
            return sm.list_sessions()
        return []

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
        """Get conversation messages for current session."""
        session = self.current_session
        if session:
            return session.messages
        return st.session_state.get(self.SESSION_KEY, [])

    @messages.setter
    def messages(self, value: List[Dict[str, Any]]) -> None:
        """Set conversation messages for current session."""
        session = self.current_session
        if session:
            session.messages = value
        else:
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

    @property
    def retriever(self) -> Optional[Any]:
        """Get RAG retriever for current session.

        Returns:
            Retriever instance or None if not set
        """
        return st.session_state.get(self.RETRIEVER_KEY)

    @retriever.setter
    def retriever(self, value: Optional[Any]) -> None:
        """Set RAG retriever for current session.

        Args:
            value: Retriever instance or None
        """
        st.session_state[self.RETRIEVER_KEY] = value

    @property
    def current_document_name(self) -> Optional[str]:
        """Get current document name.

        Returns:
            Document filename or None if no document
        """
        return st.session_state.get(self.DOCUMENT_NAME_KEY)

    @current_document_name.setter
    def current_document_name(self, value: Optional[str]) -> None:
        """Set current document name.

        Args:
            value: Document filename or None
        """
        st.session_state[self.DOCUMENT_NAME_KEY] = value

    def clear_retriever(self) -> None:
        """Clear retriever and document metadata."""
        if self.RETRIEVER_KEY in st.session_state:
            retriever = st.session_state[self.RETRIEVER_KEY]
            if hasattr(retriever, "clear"):
                retriever.clear()
            del st.session_state[self.RETRIEVER_KEY]

        if self.DOCUMENT_NAME_KEY in st.session_state:
            del st.session_state[self.DOCUMENT_NAME_KEY]

        logger.info("Cleared RAG retriever and document metadata")

    def add_message(self, role: str, content: str, **metadata) -> Dict[str, Any]:
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
            **metadata,
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
        reasoning_details: Optional[Any] = None,
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
            "messages": self.messages,
        }

    def import_conversation(self, data: Dict[str, Any]) -> bool:
        """Import conversation from dictionary with validation.

        Args:
            data: Conversation data dictionary

        Returns:
            True if successful
        """
        try:
            if "messages" not in data:
                logger.error("Import failed: no 'messages' key in data")
                return False

            validated = []
            for i, msg in enumerate(data["messages"]):
                # Validate message structure
                if not isinstance(msg, dict):
                    logger.warning(f"Skipping invalid message at index {i}: not a dict")
                    continue

                role = msg.get("role")
                content = msg.get("content", "")

                # Validate role
                if role not in ("user", "assistant", "system"):
                    logger.warning(
                        f"Skipping message at index {i}: invalid role '{role}'"
                    )
                    continue

                # Validate content type and size
                if not isinstance(content, str):
                    logger.warning(
                        f"Skipping message at index {i}: content is not a string"
                    )
                    continue

                if len(content) > 100_000:  # 100KB limit per message
                    logger.warning(
                        f"Skipping message at index {i}: content exceeds 100KB"
                    )
                    continue

                # Validate timestamp if present
                timestamp = msg.get("timestamp")
                if timestamp and not isinstance(timestamp, str):
                    timestamp = datetime.utcnow().isoformat()

                validated.append(
                    {
                        "role": role,
                        "content": content,
                        "timestamp": timestamp or datetime.utcnow().isoformat(),
                    }
                )

            self.messages = validated
            logger.info(f"Imported {len(validated)} validated messages")
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
            "session_id": self.session_id,
        }
