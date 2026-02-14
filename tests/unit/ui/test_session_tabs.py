"""Tests for SessionTabs UI component."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from unittest.mock import Mock, patch, MagicMock

# Mock streamlit before importing
sys.modules["streamlit"] = MagicMock()
sys.modules["streamlit.session_state"] = MagicMock()
sys.modules["streamlit.components"] = MagicMock()
sys.modules["streamlit.components.v1"] = MagicMock()

from src.services.session_manager import SessionManager
from src.ui.session_tabs import SessionTabs


class TestSessionTabs:
    """Test suite for SessionTabs UI component."""

    @pytest.fixture
    def session_manager(self):
        """Create SessionManager with test sessions."""
        sm = SessionManager()
        # Create additional sessions
        sm.create_session("Work Chat")
        sm.create_session("Personal")
        return sm

    def test_session_tabs_init(self, session_manager):
        """Test SessionTabs initialization."""
        tabs = SessionTabs(session_manager)

        assert tabs.session_manager is session_manager

    def test_new_session_button(self, session_manager):
        """Test new session button creates session."""
        initial_count = session_manager.get_session_count()

        tabs = SessionTabs(session_manager)
        tabs._handle_new_session("New Session")

        # Should create new session
        assert session_manager.get_session_count() == initial_count + 1
        assert "New Session" in [s.name for s in session_manager.list_sessions()]

    def test_delete_session_button(self, session_manager):
        """Test delete button removes session."""
        sessions = session_manager.list_sessions()
        session_to_delete = sessions[1]
        initial_count = session_manager.get_session_count()

        tabs = SessionTabs(session_manager)
        tabs._handle_delete_session(session_to_delete.id)

        # Session should be deleted
        assert session_manager.get_session_count() == initial_count - 1
        assert session_to_delete not in session_manager.list_sessions()

    def test_session_click_switches_session(self, session_manager):
        """Test clicking session tab switches to that session."""
        sessions = session_manager.list_sessions()
        target_session = sessions[2]

        tabs = SessionTabs(session_manager)

        # Mock st.rerun to avoid Streamlit error
        with patch("src.ui.session_tabs.st.rerun"):
            tabs._switch_session(target_session.id)

            assert session_manager.current_session_id == target_session.id

    def test_rename_session(self, session_manager):
        """Test renaming a session."""
        session = session_manager.list_sessions()[0]
        old_name = session.name

        tabs = SessionTabs(session_manager)
        tabs._handle_rename_session(session.id, "Renamed Session")

        # Session should be renamed
        assert session.name != old_name
        assert session.name == "Renamed Session"

    def test_rename_session_invalid_id(self, session_manager):
        """Test renaming non-existent session doesn't raise error."""
        tabs = SessionTabs(session_manager)

        # Should not raise exception
        tabs._handle_rename_session("invalid_id", "New Name")

    def test_delete_current_session_switches(self, session_manager):
        """Test deleting current session switches to another."""
        sessions = session_manager.list_sessions()
        session_to_delete = session_manager.get_current_session()

        tabs = SessionTabs(session_manager)

        with patch("src.ui.session_tabs.st.rerun"):
            tabs._handle_delete_session(session_to_delete.id)

            # Current session should be different
            assert session_manager.current_session_id != session_to_delete.id
            assert session_manager.current_session_id is not None

    def test_session_tabs_with_messages(self, session_manager):
        """Test session tabs with message counts."""
        # Add messages to a session
        session = session_manager.list_sessions()[0]
        session.messages.append({"role": "user", "content": "Hello"})
        session.messages.append({"role": "assistant", "content": "Hi"})

        tabs = SessionTabs(session_manager)

        # Just verify initialization works
        assert tabs.session_manager is session_manager
        assert len(session.messages) == 2

    def test_render_method_exists(self, session_manager):
        """Test that render method exists and is callable."""
        tabs = SessionTabs(session_manager)

        assert hasattr(tabs, "render")
        assert callable(tabs.render)

    def test_multiple_new_sessions(self, session_manager):
        """Test creating multiple new sessions."""
        initial_count = session_manager.get_session_count()

        tabs = SessionTabs(session_manager)
        tabs._handle_new_session("First")
        tabs._handle_new_session("Second")
        tabs._handle_new_session("Third")

        assert session_manager.get_session_count() == initial_count + 3
        session_names = [s.name for s in session_manager.list_sessions()]
        assert "First" in session_names
        assert "Second" in session_names
        assert "Third" in session_names

    def test_session_isolation_after_operations(self, session_manager):
        """Test that sessions remain isolated after operations."""
        # Create two sessions with different messages
        tabs = SessionTabs(session_manager)

        session1 = session_manager.list_sessions()[0]
        session2 = session_manager.list_sessions()[1]

        # Add messages to session 1
        session1.messages.append({"role": "user", "content": "Message 1"})

        # Add messages to session 2
        session2.messages.append({"role": "user", "content": "Message 2"})

        # Verify isolation
        assert len(session1.messages) == 1
        assert len(session2.messages) == 1
        assert session1.messages[0]["content"] == "Message 1"
        assert session2.messages[0]["content"] == "Message 2"
