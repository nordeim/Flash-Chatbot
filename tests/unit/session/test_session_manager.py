"""Tests for Session and SessionManager - Multi-session support."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Mock streamlit before importing session_manager
sys.modules["streamlit"] = MagicMock()
sys.modules["streamlit.session_state"] = MagicMock()

from src.services.session_manager import Session, SessionManager


class TestSession:
    """Test suite for Session dataclass."""

    def test_session_creation(self):
        """Test that Session can be created with required fields."""
        session = Session(
            id="sess_123",
            name="Test Session",
            messages=[{"role": "user", "content": "Hello"}],
            system_prompt="You are helpful.",
            created_at=datetime.utcnow(),
            token_count=100,
        )

        assert session.id == "sess_123"
        assert session.name == "Test Session"
        assert len(session.messages) == 1
        assert session.system_prompt == "You are helpful."
        assert session.token_count == 100

    def test_session_default_values(self):
        """Test that Session has correct default values."""
        session = Session(id="sess_456", name="Another Session", messages=[])

        assert session.system_prompt == "You are a helpful assistant."
        assert session.token_count == 0
        assert isinstance(session.created_at, datetime)

    def test_session_to_dict(self):
        """Test that Session can be converted to dictionary."""
        created = datetime.utcnow()
        session = Session(
            id="sess_789",
            name="Export Test",
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="Test prompt",
            created_at=created,
            token_count=50,
        )

        data = session.to_dict()

        assert data["id"] == "sess_789"
        assert data["name"] == "Export Test"
        assert data["messages"] == [{"role": "user", "content": "Hi"}]
        assert data["system_prompt"] == "Test prompt"
        assert data["token_count"] == 50
        assert "created_at" in data

    def test_session_from_dict(self):
        """Test that Session can be created from dictionary."""
        data = {
            "id": "sess_abc",
            "name": "Imported Session",
            "messages": [{"role": "assistant", "content": "Hello!"}],
            "system_prompt": "Custom prompt",
            "created_at": datetime.utcnow().isoformat(),
            "token_count": 200,
        }

        session = Session.from_dict(data)

        assert session.id == "sess_abc"
        assert session.name == "Imported Session"
        assert len(session.messages) == 1
        assert session.system_prompt == "Custom prompt"
        assert session.token_count == 200


class TestSessionManager:
    """Test suite for SessionManager."""

    @pytest.fixture
    def session_manager(self):
        """Create SessionManager instance."""
        return SessionManager()

    def test_create_session(self, session_manager):
        """Test creating a new session."""
        session = session_manager.create_session("My Session")

        assert session.id is not None
        assert session.name == "My Session"
        assert session.messages == []
        assert session in session_manager.sessions

    def test_create_session_auto_name(self, session_manager):
        """Test creating session with auto-generated name."""
        session = session_manager.create_session()

        assert session.name.startswith("Session ")
        assert session.id is not None

    def test_create_session_unique_ids(self, session_manager):
        """Test that created sessions have unique IDs."""
        session1 = session_manager.create_session("First")
        session2 = session_manager.create_session("Second")

        assert session1.id != session2.id

    def test_switch_session(self, session_manager):
        """Test switching to a different session."""
        session1 = session_manager.create_session("Session 1")
        session2 = session_manager.create_session("Session 2")

        # Add message to session1
        session1.messages.append({"role": "user", "content": "Hello"})

        # Switch to session2
        session_manager.switch_session(session2.id)

        # Current session should be session2
        assert session_manager.current_session_id == session2.id

        # Session1 should still have its message
        assert len(session1.messages) == 1
        assert session2.messages == []

    def test_switch_session_invalid_id(self, session_manager):
        """Test switching to non-existent session raises error."""
        with pytest.raises(ValueError) as exc_info:
            session_manager.switch_session("invalid_id")

        assert "not found" in str(exc_info.value).lower()

    def test_delete_session(self, session_manager):
        """Test deleting a session."""
        # Note: session_manager already has 1 initial session
        initial_count = session_manager.get_session_count()
        session1 = session_manager.create_session("To Delete")
        session2 = session_manager.create_session("Keep")

        assert session_manager.get_session_count() == initial_count + 2

        session_manager.delete_session(session1.id)

        assert session1 not in session_manager.sessions
        assert session2 in session_manager.sessions
        assert session_manager.get_session_count() == initial_count + 1

    def test_delete_current_session_switches_to_another(self, session_manager):
        """Test deleting current session switches to another session."""
        session1 = session_manager.create_session("First")
        session2 = session_manager.create_session("Second")
        session_manager.switch_session(session1.id)

        assert session_manager.current_session_id == session1.id

        # Delete current session
        session_manager.delete_session(session1.id)

        # Should switch to another session (could be session2 or initial)
        assert session_manager.current_session_id is not None
        assert session_manager.current_session_id != session1.id

    def test_list_sessions(self, session_manager):
        """Test listing all sessions."""
        initial_count = session_manager.get_session_count()
        session1 = session_manager.create_session("Alpha")
        session2 = session_manager.create_session("Beta")
        session3 = session_manager.create_session("Gamma")

        sessions = session_manager.list_sessions()

        assert len(sessions) == initial_count + 3
        assert session1 in sessions
        assert session2 in sessions
        assert session3 in sessions

    def test_rename_session(self, session_manager):
        """Test renaming a session."""
        session = session_manager.create_session("Old Name")

        session_manager.rename_session(session.id, "New Name")

        assert session.name == "New Name"

    def test_rename_session_invalid_id(self, session_manager):
        """Test renaming non-existent session raises error."""
        with pytest.raises(ValueError) as exc_info:
            session_manager.rename_session("invalid_id", "New Name")

        assert "not found" in str(exc_info.value).lower()

    def test_get_session(self, session_manager):
        """Test getting a session by ID."""
        session = session_manager.create_session("Test")

        retrieved = session_manager.get_session(session.id)

        assert retrieved is session

    def test_get_session_not_found(self, session_manager):
        """Test getting non-existent session returns None."""
        retrieved = session_manager.get_session("non_existent")

        assert retrieved is None

    def test_export_session(self, session_manager):
        """Test exporting session to JSON."""
        session = session_manager.create_session("Export Me")
        session.messages.append({"role": "user", "content": "Hello"})

        json_str = session_manager.export_session(session.id)

        assert "Export Me" in json_str
        assert "Hello" in json_str
        assert "id" in json_str

    def test_import_session(self, session_manager):
        """Test importing session from JSON."""
        json_str = """{"id": "imported_123", "name": "Imported", "messages": [{"role": "user", "content": "Hi"}], "system_prompt": "Test", "created_at": "2024-01-01T00:00:00", "token_count": 0}"""

        session = session_manager.import_session(json_str)

        assert session.name == "Imported"
        assert len(session.messages) == 1
        assert session in session_manager.sessions

    def test_duplicate_session(self, session_manager):
        """Test duplicating a session."""
        original = session_manager.create_session("Original")
        original.messages.append({"role": "user", "content": "Message"})
        original.system_prompt = "Custom prompt"

        duplicate = session_manager.duplicate_session(original.id)

        assert duplicate.name == "Original (Copy)"
        assert len(duplicate.messages) == 1
        assert duplicate.messages[0]["content"] == "Message"
        assert duplicate.system_prompt == "Custom prompt"
        assert duplicate.id != original.id
        assert duplicate in session_manager.sessions

    def test_get_session_count(self, session_manager):
        """Test getting total session count."""
        assert session_manager.get_session_count() == 1  # Initial session

        session_manager.create_session("One")
        session_manager.create_session("Two")

        assert session_manager.get_session_count() == 3

    def test_get_current_session(self, session_manager):
        """Test getting current session object."""
        current = session_manager.get_current_session()

        assert current is not None
        assert current.name == "Session 1"

    def test_initial_session_created(self):
        """Test that SessionManager creates initial session on init."""
        manager = SessionManager()

        assert len(manager.sessions) == 1
        assert manager.current_session_id is not None
        assert manager.get_current_session().name == "Session 1"

    def test_session_isolation(self, session_manager):
        """Test that sessions are isolated from each other."""
        session1 = session_manager.create_session("Session 1")
        session2 = session_manager.create_session("Session 2")

        # Add different messages to each
        session1.messages.append({"role": "user", "content": "Message 1"})
        session2.messages.append({"role": "user", "content": "Message 2"})

        # Verify isolation
        assert len(session1.messages) == 1
        assert len(session2.messages) == 1
        assert session1.messages[0]["content"] == "Message 1"
        assert session2.messages[0]["content"] == "Message 2"
