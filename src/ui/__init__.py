"""UI components module."""

from src.ui.styles import get_custom_css
from src.ui.components import (
    render_message_bubble,
    render_thinking_panel,
    render_error_message,
    render_loading_spinner,
    render_empty_state,
    ThreeOrbIndicator,
)
from src.ui.sidebar import render_sidebar
from src.ui.chat_interface import render_chat_interface

# Accessibility utilities (import directly to avoid circular deps)
try:
    from src.ui.accessibility import (
        aria_labels,
        get_accessibility_css,
        SkipLink,
        LiveRegion,
        KeyboardHandler,
        FocusScope,
    )

    accessibility_available = True
except ImportError:
    accessibility_available = False

__all__ = [
    "get_custom_css",
    "render_message_bubble",
    "render_thinking_panel",
    "render_error_message",
    "render_loading_spinner",
    "render_empty_state",
    "render_sidebar",
    "render_chat_interface",
    "ThreeOrbIndicator",
]

if accessibility_available:
    __all__.extend(
        [
            "aria_labels",
            "get_accessibility_css",
            "SkipLink",
            "LiveRegion",
            "KeyboardHandler",
            "FocusScope",
        ]
    )
