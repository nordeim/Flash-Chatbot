"""Ethereal session tabs component for multi-session support."""

import streamlit as st
from typing import Optional
from src.services.session_manager import SessionManager


def _inject_session_tab_styles():
    """Inject ethereal CSS for session tabs."""
    st.markdown(
        """
    <style>
    /* Session tabs container */
    .session-tabs-container {
        display: flex;
        gap: 8px;
        padding: 12px 0;
        margin-bottom: 16px;
        overflow-x: auto;
        scrollbar-width: thin;
    }
    
    /* Individual session tab */
    .session-tab {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 8px 16px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 8px;
        white-space: nowrap;
        position: relative;
    }
    
    .session-tab:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(0, 212, 255, 0.3);
        transform: translateY(-2px);
    }
    
    /* Active session tab */
    .session-tab.active {
        background: rgba(0, 212, 255, 0.1);
        border-color: rgba(0, 212, 255, 0.5);
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
    }
    
    .session-tab.active::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 20%;
        right: 20%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00d4ff, transparent);
        border-radius: 1px;
    }
    
    /* Session name */
    .session-name {
        color: #e0e0e0;
        font-size: 14px;
        font-weight: 500;
    }
    
    .session-tab.active .session-name {
        color: #00d4ff;
        font-weight: 600;
    }
    
    /* Message count badge */
    .session-badge {
        background: rgba(124, 58, 237, 0.2);
        color: #c0c0c0;
        font-size: 11px;
        padding: 2px 6px;
        border-radius: 10px;
        min-width: 18px;
        text-align: center;
    }
    
    .session-tab.active .session-badge {
        background: rgba(0, 212, 255, 0.2);
        color: #00d4ff;
    }
    
    /* Delete button */
    .session-delete {
        color: rgba(255, 255, 255, 0.3);
        font-size: 14px;
        padding: 0 4px;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s;
    }
    
    .session-delete:hover {
        color: #ff6b6b;
        background: rgba(255, 107, 107, 0.1);
    }
    
    /* New session button */
    .new-session-btn {
        background: rgba(0, 212, 255, 0.05);
        border: 1px dashed rgba(0, 212, 255, 0.3);
        border-radius: 12px;
        padding: 8px 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
        color: #00d4ff;
        font-size: 14px;
        transition: all 0.3s;
    }
    
    .new-session-btn:hover {
        background: rgba(0, 212, 255, 0.1);
        border-style: solid;
    }
    
    /* Session controls */
    .session-controls {
        display: flex;
        gap: 8px;
        margin-bottom: 16px;
        align-items: center;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


class SessionTabs:
    """Ethereal session tabs component."""

    def __init__(self, session_manager: SessionManager):
        """Initialize component.

        Args:
            session_manager: SessionManager instance
        """
        self.session_manager = session_manager

    def render(self) -> None:
        """Render session tabs."""
        _inject_session_tab_styles()

        # Session tabs row
        st.markdown('<div class="session-tabs-container">', unsafe_allow_html=True)

        # Render each session tab
        sessions = self.session_manager.list_sessions()
        for session in sessions:
            self._render_session_tab(session)

        st.markdown("</div>", unsafe_allow_html=True)

        # Session controls (New Session button)
        self._render_session_controls()

    def _render_session_tab(self, session) -> None:
        """Render individual session tab.

        Args:
            session: Session instance
        """
        is_active = self.session_manager.current_session_id == session.id
        active_class = "active" if is_active else ""
        message_count = len(session.messages)

        # Create tab HTML
        tab_html = f'''
        <div class="session-tab {active_class}" 
             onclick="window.location.href='?session={session.id}'"
             title="{session.name} - {message_count} messages">
            <span class="session-name">{session.name}</span>
            {f'<span class="session-badge">{message_count}</span>' if message_count > 0 else ""}
            <span class="session-delete" 
                  onclick="event.stopPropagation(); deleteSession('{session.id}')">×</span>
        </div>
        '''

        st.markdown(tab_html, unsafe_allow_html=True)

    def _render_session_controls(self) -> None:
        """Render session control buttons."""
        cols = st.columns([0.15, 0.85])

        with cols[0]:
            # New session button
            if st.button("➕ New", key="new_session_btn", help="Create new session"):
                self._handle_new_session()

        with cols[1]:
            # Optional: Session management expander
            with st.expander("⚙️ Manage Sessions"):
                self._render_session_management()

    def _render_session_management(self) -> None:
        """Render session management controls."""
        st.markdown("**Session Management**")

        # List all sessions with delete buttons
        sessions = self.session_manager.list_sessions()
        for i, session in enumerate(sessions):
            col1, col2, col3 = st.columns([0.5, 0.3, 0.2])

            with col1:
                new_name = st.text_input(
                    f"Name_{i}",
                    value=session.name,
                    key=f"rename_{session.id}",
                    label_visibility="collapsed",
                )
                if new_name != session.name:
                    self._handle_rename_session(session.id, new_name)

            with col2:
                st.caption(f"{len(session.messages)} messages")

            with col3:
                if st.button(
                    "🗑️", key=f"delete_{session.id}", help=f"Delete {session.name}"
                ):
                    self._handle_delete_session(session.id)

    def _handle_new_session(self, name: Optional[str] = None) -> None:
        """Handle creating new session.

        Args:
            name: Optional session name
        """
        session = self.session_manager.create_session(name)
        self.session_manager.switch_session(session.id)
        st.success(f"Created session: {session.name}")
        st.rerun()

    def _handle_delete_session(self, session_id: str) -> None:
        """Handle deleting a session.

        Args:
            session_id: Session ID to delete
        """
        session = self.session_manager.get_session(session_id)
        if session:
            self.session_manager.delete_session(session_id)
            st.success(f"Deleted session: {session.name}")
            st.rerun()

    def _handle_rename_session(self, session_id: str, new_name: str) -> None:
        """Handle renaming a session.

        Args:
            session_id: Session ID to rename
            new_name: New name for session
        """
        try:
            self.session_manager.rename_session(session_id, new_name)
        except ValueError:
            pass  # Session not found

    def _switch_session(self, session_id: str) -> None:
        """Switch to a different session.

        Args:
            session_id: Session ID to switch to
        """
        try:
            self.session_manager.switch_session(session_id)
            st.rerun()
        except ValueError:
            st.error("Session not found")


def render_session_tabs(session_manager: Optional[SessionManager] = None) -> None:
    """Convenience function to render session tabs.

    Args:
        session_manager: Optional SessionManager (creates new if None)
    """
    if session_manager is None:
        from src.services.session_manager import SessionManager

        session_manager = SessionManager()

    tabs = SessionTabs(session_manager)
    tabs.render()
