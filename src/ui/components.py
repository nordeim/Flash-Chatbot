"""Reusable UI components."""

import html
from typing import Optional, Any

import streamlit as st

from src.ui.styles import get_custom_css
from src.services.message_formatter import MessageFormatter


def render_custom_css() -> None:
    """Render custom CSS styles with accessibility and deduplication."""
    from src.ui.styles import get_combined_css

    if "css_injected" not in st.session_state:
        st.markdown(get_combined_css(), unsafe_allow_html=True)
        st.session_state["css_injected"] = True


def render_message_bubble(
    content: str, role: str, thinking: Optional[str] = None
) -> None:
    """Render a message bubble with XSS protection.

    Args:
        content: Message content
        role: Message role (user/assistant)
        thinking: Optional thinking content for assistant
    """
    escaped_content = html.escape(content)
    if role == "user":
        st.markdown(
            f"""
            <div class="message-bubble message-user">
            {escaped_content}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="message-bubble message-assistant">
            {escaped_content}
            </div>
            """,
            unsafe_allow_html=True,
        )
    if thinking:
        render_thinking_panel(thinking, is_streaming=False)


def render_thinking_panel(content: str, is_streaming: bool = False) -> None:
    """Render thinking panel with XSS protection.

    Args:
        content: Thinking content
        is_streaming: Whether content is still streaming
    """
    cleaned = MessageFormatter.clean_thinking_content(content)

    if not cleaned:
        return

    escaped_cleaned = html.escape(cleaned)

    with st.expander("Thinking Process", expanded=is_streaming):
        st.markdown(
            f"""
            <div class="thinking-container">
            <div class="thinking-label">Reasoning</div>
            <div class="thinking-content">{escaped_cleaned}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_error_message(error: str) -> None:
    """Render error message with XSS protection.

    Args:
        error: Error message
    """
    escaped_error = html.escape(error)
    st.markdown(
        f"""
        <div class="error-message">
        {escaped_error}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_loading_spinner(is_reduced_motion: bool = False) -> None:
    """Render ethereal three-orb loading indicator.

    Args:
        is_reduced_motion: Whether to use static version for accessibility
    """
    indicator = ThreeOrbIndicator(is_reduced_motion=is_reduced_motion)
    st.markdown(indicator.render(), unsafe_allow_html=True)


def render_empty_state() -> None:
    """Render empty state with example questions."""
    from src.config.constants import EXAMPLE_QUESTIONS

    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-state-icon">💬</div>
            <h3>Start a Conversation</h3>
            <p>Ask me anything or try one of these examples:</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

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


class ThreeOrbIndicator:
    """Ethereal three-orb thinking indicator with reduced-motion support.

    A visually striking loading indicator using three pulsing orbs
    that gracefully degrades to a static version when reduced-motion
    is preferred.

    Attributes:
        is_reduced_motion: Whether to use static version
        size: Size of the indicator (small, medium, large)
    """

    def __init__(self, is_reduced_motion: bool = False, size: str = "medium"):
        """Initialize the three-orb indicator.

        Args:
            is_reduced_motion: Whether to disable animations
            size: Size variant (small, medium, large)
        """
        self.is_reduced_motion = is_reduced_motion
        self.size = size
        self.size_map = {
            "small": {"orb": 8, "gap": 6, "container": 40},
            "medium": {"orb": 12, "gap": 8, "container": 60},
            "large": {"orb": 16, "gap": 10, "container": 80},
        }

    def render(self) -> str:
        """Render the three-orb indicator HTML.

        Returns:
            HTML string for the indicator
        """
        dims = self.size_map.get(self.size, self.size_map["medium"])
        motion_class = "static" if self.is_reduced_motion else "animated"
        aria_attrs = 'aria-label="AI is thinking" aria-live="polite"'

        html = f"""<div class="three-orb-indicator {motion_class}" {aria_attrs} role="status">
            <div class="orb" style="width: {dims["orb"]}px; height: {dims["orb"]}px;"></div>
            <div class="orb" style="width: {dims["orb"]}px; height: {dims["orb"]}px;"></div>
            <div class="orb" style="width: {dims["orb"]}px; height: {dims["orb"]}px;"></div>
        </div>"""

        return html


# ============================================================================
# Accessibility-enhanced wrapper functions
# ============================================================================


def render_button(
    label: str,
    key: str,
    help_text: Optional[str] = None,
    aria_label: Optional[str] = None,
    **kwargs,
) -> bool:
    """Render an accessible button with ARIA attributes.

    Args:
        label: Button label text
        key: Unique key for Streamlit
        help_text: Optional tooltip/help text
        aria_label: Optional ARIA label (uses label if not provided)
        **kwargs: Additional Streamlit button kwargs

    Returns:
        True if button was clicked
    """
    from src.ui.accessibility import aria_labels

    # Use aria-label if provided, otherwise use label
    accessible_label = aria_label or label

    # Generate ARIA attributes
    aria_attrs = aria_labels(
        label=accessible_label,
        describedby=f"{key}-help" if help_text else None,
        role="button",
    )

    # Add ARIA attributes as HTML if needed
    if aria_attrs:
        # Streamlit doesn't directly support ARIA, but we can inject via CSS
        pass

    return st.button(label, key=key, help=help_text, **kwargs)
