"""Main chat interface component."""

from typing import Dict, Any, Generator, Tuple, Optional

import streamlit as st

from src.services.chat_service import ChatService
from src.services.state_manager import ChatStateManager
from src.ui.components import (
    render_custom_css,
    render_thinking_panel,
    render_empty_state,
    render_error_message,
)
from src.config.constants import PAGE_TITLE, PAGE_ICON
from src.utils.logger import get_logger

logger = get_logger(__name__)


def render_chat_interface(
    chat_service: ChatService,
    settings: Dict[str, Any]
) -> None:
    """Render main chat interface.
    
    Args:
        chat_service: Chat service instance
        settings: Current settings
    """
    # Render custom CSS
    render_custom_css()
    
    # Page title
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    
    # Initialize state manager
    state_manager = chat_service.state_manager
    
    # Display conversation history
    for msg in state_manager.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant", avatar=""):
                # Show thinking if present
                if msg.get("thinking"):
                    render_thinking_panel(msg["thinking"], is_streaming=False)
                # Show content
                st.markdown(msg["content"])
    
    # Show empty state if no messages
    if not state_manager.has_messages:
        render_empty_state()
    
    # Chat input
    prompt = st.chat_input("Type your message...")
    
    # Handle pending prompt from example buttons
    if state_manager.pending_prompt:
        prompt = state_manager.pending_prompt
        state_manager.pending_prompt = None
    
    # Process user input
    if prompt:
        _handle_user_input(chat_service, prompt, settings)


def _handle_user_input(
    chat_service: ChatService,
    prompt: str,
    settings: Dict[str, Any]
) -> None:
    """Handle user input and generate response.
    
    Args:
        chat_service: Chat service instance
        prompt: User input
        settings: Current settings
    """
    # Add user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant", avatar=""):
        # Placeholders for streaming content
        thinking_placeholder = st.empty()
        content_placeholder = st.empty()
        
        # Accumulate content
        full_thinking = ""
        full_content = ""
        
        try:
            # Stream response
            for thinking, content, reasoning_details in chat_service.stream_message(
                content=prompt,
                system_prompt=settings.get("system_prompt"),
                max_tokens=settings.get("max_tokens"),
                temperature=settings.get("temperature"),
                top_p=settings.get("top_p"),
            ):
                # Update thinking
                if thinking:
                    full_thinking = thinking
                    with thinking_placeholder.container():
                        render_thinking_panel(full_thinking, is_streaming=True)
                
                # Update content
                if content:
                    full_content = content
                    content_placeholder.markdown(full_content + "▌")
            
            # Final content update (remove cursor)
            if full_content:
                content_placeholder.markdown(full_content)
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            render_error_message(f"Failed to generate response: {str(e)}")


def render_chat_container(chat_service: ChatService) -> None:
    """Render chat container with auto-scroll.
    
    Args:
        chat_service: Chat service instance
    """
    # Add auto-scroll JavaScript
    st.markdown("""
        <script>
            // Auto-scroll to bottom on new messages
            const chatContainer = document.querySelector('.main .block-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        </script>
    """, unsafe_allow_html=True)
