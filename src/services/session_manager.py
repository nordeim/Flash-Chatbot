"""Multi-session management for chat conversations."""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional


@dataclass
class Session:
    """Chat session data class.

    Represents a single conversation session with metadata.
    """

    id: str
    name: str
    messages: List[Dict[str, Any]]
    system_prompt: str = "You are a helpful assistant."
    created_at: Optional[datetime] = None
    token_count: int = 0

    def __post_init__(self):
        """Initialize defaults after creation."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary.

        Returns:
            Dictionary representation of session
        """
        return {
            "id": self.id,
            "name": self.name,
            "messages": self.messages,
            "system_prompt": self.system_prompt,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else datetime.utcnow().isoformat(),
            "token_count": self.token_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create session from dictionary.

        Args:
            data: Dictionary with session data

        Returns:
            Session instance
        """
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if isinstance(data["created_at"], str)
            else data["created_at"]
        )

        return cls(
            id=data["id"],
            name=data["name"],
            messages=data["messages"],
            system_prompt=data.get("system_prompt", "You are a helpful assistant."),
            created_at=created_at,
            token_count=data.get("token_count", 0),
        )


class SessionManager:
    """Manager for multiple chat sessions.

    Handles creation, switching, deletion, and persistence of sessions.
    """

    def __init__(self):
        """Initialize session manager with default session."""
        self.sessions: List[Session] = []
        self.current_session_id: Optional[str] = None
        self._session_counter = 0

        # Create initial session
        self._create_initial_session()

    def _create_initial_session(self) -> None:
        """Create initial session on startup."""
        initial_session = self.create_session("Session 1")
        self.current_session_id = initial_session.id

    def create_session(self, name: Optional[str] = None) -> Session:
        """Create a new session.

        Args:
            name: Optional session name (auto-generated if not provided)

        Returns:
            New Session instance
        """
        self._session_counter += 1

        if name is None:
            name = f"Session {self._session_counter}"

        session = Session(id=str(uuid.uuid4()), name=name, messages=[])

        self.sessions.append(session)
        return session

    def switch_session(self, session_id: str) -> None:
        """Switch to a different session.

        Args:
            session_id: ID of session to switch to

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session with id '{session_id}' not found")

        self.current_session_id = session_id

    def delete_session(self, session_id: str) -> None:
        """Delete a session.

        If deleting current session, switches to another session
        or creates a new one if it's the last session.

        Args:
            session_id: ID of session to delete
        """
        session = self.get_session(session_id)
        if session is None:
            return

        is_current = self.current_session_id == session_id

        # Remove session
        self.sessions = [s for s in self.sessions if s.id != session_id]

        # If we deleted current session, switch to another
        if is_current:
            if self.sessions:
                self.current_session_id = self.sessions[0].id
            else:
                # Create new session if none left
                new_session = self.create_session()
                self.current_session_id = new_session.id

    def list_sessions(self) -> List[Session]:
        """List all sessions.

        Returns:
            List of all sessions
        """
        return self.sessions.copy()

    def rename_session(self, session_id: str, new_name: str) -> None:
        """Rename a session.

        Args:
            session_id: ID of session to rename
            new_name: New name for session

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session with id '{session_id}' not found")

        session.name = new_name

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session instance or None if not found
        """
        for session in self.sessions:
            if session.id == session_id:
                return session
        return None

    def get_current_session(self) -> Optional[Session]:
        """Get current active session.

        Returns:
            Current session or None
        """
        if self.current_session_id is None:
            return None
        return self.get_session(self.current_session_id)

    def export_session(self, session_id: str) -> str:
        """Export session to JSON string.

        Args:
            session_id: Session ID to export

        Returns:
            JSON string representation
        """
        session = self.get_session(session_id)
        if session is None:
            return "{}"

        return json.dumps(session.to_dict(), indent=2)

    def import_session(self, json_str: str) -> Optional[Session]:
        """Import session from JSON string.

        Args:
            json_str: JSON string with session data

        Returns:
            Imported Session instance or None if failed
        """
        try:
            data = json.loads(json_str)
            session = Session.from_dict(data)

            # Generate new ID to avoid conflicts
            session.id = str(uuid.uuid4())

            self.sessions.append(session)
            return session
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            return None

    def duplicate_session(self, session_id: str) -> Optional[Session]:
        """Duplicate a session.

        Creates a copy with new ID and " (Copy)" suffix.

        Args:
            session_id: Session ID to duplicate

        Returns:
            New duplicated Session instance
        """
        original = self.get_session(session_id)
        if original is None:
            return None

        # Create deep copy of messages
        messages_copy = [msg.copy() for msg in original.messages]

        duplicate = Session(
            id=str(uuid.uuid4()),
            name=f"{original.name} (Copy)",
            messages=messages_copy,
            system_prompt=original.system_prompt,
            token_count=original.token_count,
        )

        self.sessions.append(duplicate)
        return duplicate

    def get_session_count(self) -> int:
        """Get total number of sessions.

        Returns:
            Number of sessions
        """
        return len(self.sessions)
