"""Sidebar component with settings."""

from typing import Dict, Any, Tuple

import streamlit as st

from src.config.constants import (
    SIDEBAR_TITLE,
    MAX_TOKENS_MIN,
    MAX_TOKENS_MAX,
    MAX_TOKENS_STEP,
    TEMPERATURE_MIN,
    TEMPERATURE_MAX,
    TEMPERATURE_STEP,
    TOP_P_MIN,
    TOP_P_MAX,
    TOP_P_STEP,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_SYSTEM_PROMPT,
)


def render_sidebar() -> Tuple[Dict[str, Any], bool]:
    """Render settings sidebar.
    
    Returns:
        Tuple of (settings dict, clear_requested bool)
    """
    with st.sidebar:
        st.header(SIDEBAR_TITLE)
        
        # System prompt
        system_prompt = st.text_area(
            "System Prompt",
            value=DEFAULT_SYSTEM_PROMPT,
            height=100,
            help="Instructions for the AI assistant"
        )
        
        st.divider()
        
        # Generation parameters
        st.subheader("Generation Parameters")
        
        max_tokens = st.slider(
            "Max Tokens",
            min_value=MAX_TOKENS_MIN,
            max_value=MAX_TOKENS_MAX,
            value=DEFAULT_MAX_TOKENS,
            step=MAX_TOKENS_STEP,
            help="Maximum number of tokens to generate"
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=TEMPERATURE_MIN,
            max_value=TEMPERATURE_MAX,
            value=DEFAULT_TEMPERATURE,
            step=TEMPERATURE_STEP,
            help="Controls randomness (0 = deterministic, 2 = very random)"
        )
        
        top_p = st.slider(
            "Top P",
            min_value=TOP_P_MIN,
            max_value=TOP_P_MAX,
            value=DEFAULT_TOP_P,
            step=TOP_P_STEP,
            help="Nucleus sampling parameter"
        )
        
        st.divider()
        
        # Clear conversation button
        clear_requested = st.button(
            "Clear Conversation",
            use_container_width=True,
            type="secondary"
        )
        
        # Model info
        st.divider()
        with st.expander("Model Info"):
            st.info("""
                **Model**: moonshotai/kimi-k2.5
                
                **Provider**: NVIDIA API
                
                **Features**:
                - Streaming responses
                - Thinking/reasoning display
                - Up to 128k tokens
                - Multi-turn conversation
            """)
    
    settings = {
        "system_prompt": system_prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }
    
    return settings, clear_requested
