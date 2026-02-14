"""Accessibility utilities and components for WCAG AAA compliance.

This module provides:
- ARIA label utilities for semantic HTML attributes
- Focus management for keyboard navigation
- Reduced-motion support for animations
- Screen reader helper components
- Skip links and live regions
"""

from typing import Optional, List, Callable, Dict, Any
from dataclasses import dataclass


# ============================================================================
# ARIA Label Utilities
# ============================================================================


def aria_labels(
    label: Optional[str] = None,
    describedby: Optional[str] = None,
    labelledby: Optional[str] = None,
    expanded: Optional[bool] = None,
    hidden: Optional[bool] = None,
    role: Optional[str] = None,
    live: Optional[str] = None,
    atomic: Optional[bool] = None,
    controls: Optional[str] = None,
    owns: Optional[str] = None,
    haspopup: Optional[str] = None,
    pressed: Optional[bool] = None,
    selected: Optional[bool] = None,
    disabled: Optional[bool] = None,
    required: Optional[bool] = None,
    invalid: Optional[bool] = None,
    multiselectable: Optional[bool] = None,
    autocomplete: Optional[str] = None,
) -> str:
    """Generate ARIA attribute string for HTML elements.

    Args:
        label: aria-label - Accessible label for element
        describedby: aria-describedby - ID of element that describes this one
        labelledby: aria-labelledby - ID of element that labels this one
        expanded: aria-expanded - Whether control is expanded
        hidden: aria-hidden - Whether element is hidden from assistive tech
        role: ARIA role (button, region, complementary, etc.)
        live: aria-live (polite, assertive, off) - Live region politeness
        atomic: aria-atomic - Whether to announce entire region on change
        controls: aria-controls - ID of controlled element
        owns: aria-owns - ID of owned element
        haspopup: aria-haspopup - Type of popup (menu, listbox, etc.)
        pressed: aria-pressed - Whether button is pressed (toggle buttons)
        selected: aria-selected - Whether option is selected
        disabled: aria-disabled - Whether element is disabled
        required: aria-required - Whether input is required
        invalid: aria-invalid - Whether input has invalid value
        multiselectable: aria-multiselectable - Whether multiple items selectable
        autocomplete: aria-autocomplete - Autocomplete behavior

    Returns:
        Space-separated ARIA attribute string

    Example:
        >>> aria_labels(label="Send message", describedby="help-text")
        'aria-label="Send message" aria-describedby="help-text"'
    """
    attrs = []

    if label is not None:
        attrs.append(f'aria-label="{label}"')
    if describedby is not None:
        attrs.append(f'aria-describedby="{describedby}"')
    if labelledby is not None:
        attrs.append(f'aria-labelledby="{labelledby}"')
    if expanded is not None:
        attrs.append(f'aria-expanded="{"true" if expanded else "false"}"')
    if hidden is not None:
        attrs.append(f'aria-hidden="{"true" if hidden else "false"}"')
    if role is not None:
        attrs.append(f'role="{role}"')
    if live is not None:
        attrs.append(f'aria-live="{live}"')
    if atomic is not None:
        attrs.append(f'aria-atomic="{"true" if atomic else "false"}"')
    if controls is not None:
        attrs.append(f'aria-controls="{controls}"')
    if owns is not None:
        attrs.append(f'aria-owns="{owns}"')
    if haspopup is not None:
        attrs.append(f'aria-haspopup="{haspopup}"')
    if pressed is not None:
        attrs.append(f'aria-pressed="{"true" if pressed else "false"}"')
    if selected is not None:
        attrs.append(f'aria-selected="{"true" if selected else "false"}"')
    if disabled is not None:
        attrs.append(f'aria-disabled="{"true" if disabled else "false"}"')
    if required is not None:
        attrs.append(f'aria-required="{"true" if required else "false"}"')
    if invalid is not None:
        attrs.append(f'aria-invalid="{"true" if invalid else "false"}"')
    if multiselectable is not None:
        attrs.append(f'aria-multiselectable="{"true" if multiselectable else "false"}"')
    if autocomplete is not None:
        attrs.append(f'aria-autocomplete="{autocomplete}"')

    return " ".join(attrs)


# ============================================================================
# Focus Management
# ============================================================================


@dataclass
class FocusScope:
    """Focus scope for trapping focus within a container (e.g., modal dialogs).

    Attributes:
        container_id: ID of the container element
        focusable_selectors: CSS selectors for focusable elements
    """

    container_id: str
    focusable_selectors: str = (
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )

    def get_container(self) -> str:
        """Get container ID."""
        return self.container_id

    def set_focusables(self, elements: List[str]) -> None:
        """Set list of focusable element IDs.

        Args:
            elements: List of focusable element IDs
        """
        self._focusables = elements

    def get_current_focus(self) -> Optional[str]:
        """Get currently focused element ID.

        Returns:
            Current focus element ID or None
        """
        return getattr(self, "_current_focus", None)


class KeyboardHandler:
    """Keyboard event handler for accessible navigation.

    Manages keyboard bindings and focus movement between elements.
    """

    def __init__(self):
        """Initialize keyboard handler."""
        self._bindings: Dict[str, Callable] = {}
        self._focusables: List[str] = []
        self._current_index: int = -1

    def bind_key(self, key: str, callback: Callable) -> None:
        """Bind a key to a callback function.

        Args:
            key: Key name (e.g., "Enter", "Escape", "Tab")
            callback: Function to call when key is pressed
        """
        self._bindings[key] = callback

    def simulate_keydown(self, key: str) -> None:
        """Simulate a keydown event.

        Args:
            key: Key that was pressed
        """
        if key in self._bindings:
            self._bindings[key]()

    def set_focusables(self, elements: List[str]) -> None:
        """Set the list of focusable elements.

        Args:
            elements: List of focusable element IDs
        """
        self._focusables = elements

    def get_current_focus(self) -> Optional[str]:
        """Get the currently focused element.

        Returns:
            Current focus element ID or None
        """
        if 0 <= self._current_index < len(self._focusables):
            return self._focusables[self._current_index]
        return None

    def focus_next(self) -> Optional[str]:
        """Move focus to the next element.

        Returns:
            New focus element ID or None
        """
        if not self._focusables:
            return None
        self._current_index = (self._current_index + 1) % len(self._focusables)
        return self._focusables[self._current_index]

    def focus_previous(self) -> Optional[str]:
        """Move focus to the previous element.

        Returns:
            New focus element ID or None
        """
        if not self._focusables:
            return None
        self._current_index = (self._current_index - 1) % len(self._focusables)
        return self._focusables[self._current_index]


def get_focus_order() -> Optional[List[str]]:
    """Get the logical tab order of focusable elements.

    Returns:
        List of element IDs in tab order, or None if not defined
    """
    # This would be populated based on the actual DOM structure
    return None


# ============================================================================
# Skip Link Component
# ============================================================================


@dataclass
class SkipLink:
    """Skip to content link for screen reader and keyboard users.

    Allows users to skip repetitive navigation and jump to main content.

    Attributes:
        target_id: ID of the main content element to skip to
        label: Text label for the skip link
    """

    target_id: str
    label: str = "Skip to main content"

    def render(self) -> str:
        """Render skip link HTML.

        Returns:
            HTML string for skip link
        """
        return f"""<a href="#{self.target_id}" class="skip-link">{self.label}</a>"""


# ============================================================================
# Live Region Component
# ============================================================================


@dataclass
class LiveRegion:
    """ARIA live region for announcing dynamic content changes.

    Used to announce messages to screen readers without moving focus.

    Attributes:
        region_id: Unique ID for the live region
        politeness: How aggressively to announce (polite, assertive, off)
        atomic: Whether to announce entire region on change
    """

    region_id: str
    politeness: str = "polite"  # polite, assertive, off
    atomic: bool = True

    def render(self) -> str:
        """Render live region HTML.

        Returns:
            HTML string for live region
        """
        return (
            f'<div id="{self.region_id}" '
            f'aria-live="{self.politeness}" '
            f'aria-atomic="{"true" if self.atomic else "false"}" '
            f'class="sr-only"></div>'
        )


def announce_status(message: str, region_id: str = "status-region") -> str:
    """Announce a status message to screen readers.

    Returns HTML for a live region that announces the message to
    assistive technologies when rendered.

    Args:
        message: Message to announce
        region_id: ID of the live region to update

    Returns:
        HTML string for the live region
    """
    return f'<div id="{region_id}" aria-live="polite" class="sr-only">{message}</div>'


# ============================================================================
# Accessibility CSS
# ============================================================================

ACCESSIBILITY_CSS = """
<style>
/* ==========================================================================
   ACCESSIBILITY STYLES
   WCAG AAA Compliant Focus Indicators & Reduced Motion Support
   ========================================================================== */

/* --------------------------------------------------------------------------
   Skip Link
   -------------------------------------------------------------------------- */
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: #00d4ff;
    color: #0a0a0f;
    padding: 8px 16px;
    text-decoration: none;
    font-weight: 600;
    border-radius: 0 0 8px 0;
    z-index: 10000;
    transition: top 0.3s;
}

.skip-link:focus {
    top: 0;
    outline: 3px solid #7c3aed;
    outline-offset: 2px;
}

/* --------------------------------------------------------------------------
   Focus Indicators - Neon Cyan for Keyboard Navigation
   -------------------------------------------------------------------------- */
/* Visible focus only for keyboard navigation (:focus-visible) */
*:focus-visible {
    outline: 3px solid #00d4ff;
    outline-offset: 2px;
    box-shadow: 0 0 0 4px rgba(0, 212, 255, 0.2);
}

/* Remove default focus outline for mouse users */
*:focus:not(:focus-visible) {
    outline: none;
}

/* Focus indicator for buttons */
button:focus-visible,
.stButton > button:focus-visible {
    outline: 3px solid #00d4ff;
    outline-offset: 2px;
    box-shadow: 0 0 0 4px rgba(0, 212, 255, 0.3);
}

/* Focus indicator for form inputs */
input:focus-visible,
textarea:focus-visible,
select:focus-visible,
.stTextInput input:focus-visible,
.stTextArea textarea:focus-visible {
    outline: 3px solid #00d4ff;
    outline-offset: 2px;
    border-color: #00d4ff !important;
    box-shadow: 0 0 0 4px rgba(0, 212, 255, 0.2);
}

/* Focus indicator for interactive elements with tabindex */
[tabindex]:focus-visible {
    outline: 3px solid #00d4ff;
    outline-offset: 2px;
}

/* Focus indicator for links */
a:focus-visible {
    outline: 3px solid #00d4ff;
    outline-offset: 3px;
}

/* Focus indicator for session tabs */
.session-tab:focus-visible {
    outline: 3px solid #00d4ff;
    outline-offset: 2px;
    box-shadow: 0 0 0 4px rgba(0, 212, 255, 0.3);
}

/* --------------------------------------------------------------------------
   Screen Reader Only Content
   -------------------------------------------------------------------------- */
.sr-only,
.visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

/* --------------------------------------------------------------------------
   Reduced Motion Support
   -------------------------------------------------------------------------- */
@media (prefers-reduced-motion: reduce) {
    /* Disable animations */
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }

    /* Keep essential transitions for focus states */
    *:focus-visible {
        transition-duration: 0.15s !important;
    }

    /* Disable spinner animation */
    .spinner {
        animation: none !important;
        border-top-color: var(--accent-primary);
    }

    /* Disable message bubble animations */
    .message-bubble {
        animation: none !important;
    }

    /* Disable glass card hover transitions */
    .glass-card:hover {
        transform: none !important;
        transition: border-color 0.15s ease !important;
    }

    /* Disable session tab hover effects */
    .session-tab:hover {
        transform: none !important;
    }

    /* Disable three-orb animation (static fallback) */
    .orb {
        animation: none !important;
        opacity: 0.8;
    }

    /* Disable button hover transforms */
    .stButton > button:hover {
        transform: none !important;
    }

    /* Static underline for active tabs instead of animated */
    .session-tab.active::after {
        animation: none !important;
    }
}

/* --------------------------------------------------------------------------
   ARIA Role Styling Enhancements
   -------------------------------------------------------------------------- */
/* Complementary region (sidebar) */
[role="complementary"] {
    /* Sidebar already styled, this ensures accessibility */
}

/* Button role styling */
[role="button"] {
    cursor: pointer;
}

[role="button"]:focus-visible {
    outline: 3px solid #00d4ff;
    outline-offset: 2px;
}

/* Navigation role */
[role="navigation"] {
    /* Ensures navigation landmarks are properly styled */
}

/* Main content region */
[role="main"] {
    /* Main content area styling */
}

/* Log region for chat messages */
[role="log"] {
    /* Live region for chat updates */
}

/* Alert dialog role */
[role="alertdialog"] {
    /* Modal dialog styling */
}

/* --------------------------------------------------------------------------
   High Contrast Mode Support
   -------------------------------------------------------------------------- */
@media (prefers-contrast: high) {
    .focus-indicator {
        outline: 3px solid currentColor;
        outline-offset: 2px;
    }

    button:focus-visible,
    input:focus-visible,
    textarea:focus-visible {
        outline: 3px solid currentColor;
    }
}

/* --------------------------------------------------------------------------
   Focus Management Classes
   -------------------------------------------------------------------------- */
.focus-indicator {
    position: relative;
}

.focus-indicator::after {
    content: '';
    position: absolute;
    inset: -4px;
    border: 3px solid transparent;
    border-radius: inherit;
    pointer-events: none;
    transition: border-color 0.15s ease;
}

.focus-indicator:focus-visible::after {
    border-color: #00d4ff;
}

/* Focus trap indicator for modals */
.focus-trap {
    /* Marker class for focus trap containers */
}

/* Focus sentinel for focus trap boundaries */
.focus-sentinel {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
}

/* --------------------------------------------------------------------------
   Keyboard Navigation Enhancements
   -------------------------------------------------------------------------- */
/* Ensure all interactive elements are keyboard accessible */
button:not([disabled]),
[role="button"]:not([aria-disabled="true"]),
a[href],
input:not([disabled]),
textarea:not([disabled]),
select:not([disabled]),
[tabindex]:not([tabindex="-1"]):not([disabled]) {
    cursor: pointer;
}

/* Disabled state styling */
[disabled],
[aria-disabled="true"] {
    cursor: not-allowed;
    opacity: 0.6;
}

/* --------------------------------------------------------------------------
   Three-Orb Thinking Indicator - Reduced Motion Fallback
   -------------------------------------------------------------------------- */
/* Default animated state */
.three-orb-indicator .orb {
    animation: orb-pulse 1.4s ease-in-out infinite;
}

.three-orb-indicator .orb:nth-child(1) {
    animation-delay: 0s;
}

.three-orb-indicator .orb:nth-child(2) {
    animation-delay: 0.2s;
}

.three-orb-indicator .orb:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes orb-pulse {
    0%, 100% {
        transform: scale(0.6);
        opacity: 0.4;
    }
    50% {
        transform: scale(1);
        opacity: 1;
    }
}

/* Static version for reduced motion */
.three-orb-indicator.static .orb {
    animation: none !important;
    opacity: 0.8;
}

/* --------------------------------------------------------------------------
   Tooltip Accessibility
   -------------------------------------------------------------------------- */
[aria-describedby] {
    position: relative;
}

/* --------------------------------------------------------------------------
   Chat Message Accessibility
   -------------------------------------------------------------------------- */
/* Ensure chat messages are announced properly */
.chat-message-region {
    aria-live: polite;
    aria-atomic: false;
}

/* Status message for screen readers */
.status-announcement {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
}
</style>
"""


def get_accessibility_css() -> str:
    """Get accessibility CSS styles.

    Returns:
        CSS string with accessibility styles
    """
    return ACCESSIBILITY_CSS
