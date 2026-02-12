"""Reusable UI components."""

from typing import Optional, Any

import streamlit as st

from src.ui.styles import get_custom_css
from src.services.message_formatter import MessageFormatter


def render_custom_css() -> None:
    """Render custom CSS styles."""
    st.markdown(get_custom_css(), unsafe_allow_html=True)


def render_message_bubble(
    content: str,
    role: str,
    thinking: Optional[str] = None
) -> None:
    """Render a message bubble.
    
    Args:
        content: Message content
        role: Message role (user/assistant)
        thinking: Optional thinking content for assistant
    """
    if role == "user":
        st.markdown(f"""
            <div class="message-bubble message-user">
                {content}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="message-bubble message-assistant">
                {content}
            </div>
        """, unsafe_allow_html=True)
        
        if thinking:
            render_thinking_panel(thinking, is_streaming=False)


def render_thinking_panel(
    content: str,
    is_streaming: bool = False
) -> None:
    """Render thinking panel.
    
    Args:
        content: Thinking content
        is_streaming: Whether content is still streaming
    """
    cleaned = MessageFormatter.clean_thinking_content(content)
    
    if not cleaned:
        return
    
    with st.expander("Thinking Process", expanded=is_streaming):
        st.markdown(f"""
            <div class="thinking-container">
                <div class="thinking-label">Reasoning</div>
                <div class="thinking-content">{cleaned}</div>
            </div>
        """, unsafe_allow_html=True)


def render_error_message(error: str) -> None:
    """Render error message.
    
    Args:
        error: Error message
    """
    st.markdown(f"""
        <div class="error-message">
            {error}
        </div>
    """, unsafe_allow_html=True)


def render_loading_spinner() -> None:
    """Render loading spinner."""
    st.markdown("""
        <div class="loading-spinner">
            <div class="spinner"></div>
        </div>
    """, unsafe_allow_html=True)


def render_empty_state() -> None:
    """Render empty state with example questions."""
    from src.config.constants import EXAMPLE_QUESTIONS
    
    st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">💬</div>
            <h3>Start a Conversation</h3>
            <p>Ask me anything or try one of these examples:</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Render example buttons
    cols = st.columns(len(EXAMPLE_QUESTIONS))
    for i, question in enumerate(EXAMPLE_QUESTIONS):
        if cols[i].button(question, key=f"example_{i}", use_container_width=True):
            st.session_state["pending_prompt"] = question
            st.rerun()


def render_code_block(code: str, language: str = "text") -> None:
    """Render code block with syntax highlighting.
    
    Args:
        code: Code content
        language: Programming language
    """
    st.code(code, language=language)


def render_markdown_content(content: str) -> None:
    """Render markdown content with custom styling.
    
    Args:
        content: Markdown content
    """
    st.markdown(content)


def render_chat_avatar(role: str) -> str:
    """Get avatar for chat message.
    
    Args:
        role: Message role
        
    Returns:
        Avatar emoji or path
    """
    if role == "user":
        return "👤"
    else:
        return ""
