"""Main application entry point."""

import os
import sys
from typing import NoReturn

import streamlit as st

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.constants import PAGE_TITLE, PAGE_ICON, PAGE_LAYOUT
from src.config.settings import get_settings
from src.api.nvidia_client import NvidiaChatClient
from src.api.exceptions import NvidiaAuthError
from src.services.chat_service import ChatService
from src.services.state_manager import ChatStateManager
from src.ui.chat_interface import render_chat_interface
from src.ui.sidebar import render_sidebar
from src.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


def configure_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=PAGE_LAYOUT,
        initial_sidebar_state="expanded",
    )


def initialize_app() -> ChatService:
    """Initialize application components.

    Returns:
        Configured chat service

    Raises:
        SystemExit: If initialization fails
    """
    try:
        # Load settings
        settings = get_settings()

        # Setup logging
        log_level = settings.log_level if settings else "INFO"
        setup_logging(level=log_level)

        logger.info("Initializing application...")

        # Validate API key
        if not settings.nvidia_api_key:
            st.error("❌ NVIDIA_API_KEY environment variable is required")
            st.info("Please set your NVIDIA API key in the environment variables")
            st.stop()

        # Initialize chat service
        chat_service = ChatService()

        logger.info("Application initialized successfully")
        return chat_service

    except NvidiaAuthError as e:
        logger.error(f"Authentication failed: {e}")
        st.error(f"❌ Authentication failed: {e}")
        st.info("Please check your NVIDIA_API_KEY and try again")
        st.stop()
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        st.error(f"❌ Failed to initialize: {e}")
        st.stop()


def main() -> None:
    """Main application entry point."""
    # Configure page
    configure_page()

    # Initialize application
    chat_service = initialize_app()

    # Render sidebar and get settings
    settings, clear_requested = render_sidebar()

    # Handle clear request
    if clear_requested:
        chat_service.clear_conversation()
        st.rerun()

    # Render main chat interface
    render_chat_interface(chat_service, settings)


if __name__ == "__main__":
    main()
