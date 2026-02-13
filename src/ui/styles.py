"""Custom CSS styles for dark mode glassmorphism design."""

CUSTOM_CSS = """
<style>
/* Root variables for dark theme */
:root {
    --bg-primary: #0a0a0f;
    --bg-secondary: #12121a;
    --bg-card: rgba(30, 30, 40, 0.85);
    --bg-glass: rgba(255, 255, 255, 0.08);
    --text-primary: #ffffff;
    --text-secondary: #c0c0c0;
    --text-muted: #9090a0;
    --accent-primary: #00d4ff;
    --accent-secondary: #7c3aed;
    --border-glass: rgba(255, 255, 255, 0.1);
    --border-accent: rgba(0, 212, 255, 0.3);
    --success: #10b981;
    --error: #ef4444;
    --warning: #f59e0b;
}

/* Main background */
.stApp {
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
}

/* Ensure all text in app is bright */
.stApp, .stApp p, .stApp span, .stApp div {
    color: var(--text-primary);
}

/* Chat message specific bright text */
.stChatMessage {
    color: #ffffff !important;
}

.stChatMessageContent {
    color: #ffffff !important;
}

.stChatMessageContent p {
    color: #ffffff !important;
    font-size: 16px;
    line-height: 1.6;
}

.stMarkdown {
    color: #ffffff !important;
}

.stMarkdown p {
    color: #ffffff !important;
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Glass card style */
.glass-card {
    background: var(--bg-glass);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.glass-card:hover {
    border-color: var(--border-accent);
    box-shadow: 0 4px 30px rgba(0, 212, 255, 0.1);
}

/* Thinking panel */
.thinking-container {
    background: rgba(124, 58, 237, 0.1);
    border: 1px solid rgba(124, 58, 237, 0.3);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    max-height: 200px;
    overflow-y: auto;
}

.thinking-container::-webkit-scrollbar {
    width: 6px;
}

.thinking-container::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
}

.thinking-container::-webkit-scrollbar-thumb {
    background: rgba(124, 58, 237, 0.5);
    border-radius: 3px;
}

.thinking-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--accent-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.thinking-content {
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: var(--text-secondary);
    white-space: pre-wrap;
}

/* Message bubbles */
.message-bubble {
    padding: 16px 20px;
    border-radius: 16px;
    margin-bottom: 12px;
    animation: fadeIn 0.3s ease;
}

.message-user {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(0, 212, 255, 0.05));
    border: 1px solid rgba(0, 212, 255, 0.2);
    margin-left: auto;
    max-width: 85%;
}

.message-assistant {
    background: var(--bg-card);
    border: 1px solid var(--border-glass);
    margin-right: auto;
    max-width: 95%;
    color: var(--text-primary);
}

/* Streamlit chat message content - ensure bright text */
[data-testid="stChatMessage"] {
    color: var(--text-primary) !important;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
    color: var(--text-primary) !important;
}

/* Assistant specific styling */
[data-testid="stChatMessage"][data-role="assistant"] {
    color: #ffffff !important;
}

[data-testid="stChatMessage"][data-role="assistant"] p {
    color: #ffffff !important;
    font-weight: 400;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Input area */
.chat-input-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(180deg, transparent 0%, var(--bg-primary) 20%);
    padding: 20px;
    z-index: 100;
}

/* Sidebar styling - Streamlit sidebar elements */
.stSidebar {
    background-color: #1e1e28 !important;
}

/* Target sidebar content areas at multiple levels */
.stSidebar > div,
.stSidebar > div > div,
.stSidebar > div > div > div {
    background-color: #1e1e28 !important;
}

/* Streamlit's internal sidebar content container */
section[data-testid="stSidebar"] {
    background-color: #1e1e28 !important;
}

section[data-testid="stSidebar"] > div {
    background-color: #1e1e28 !important;
}

section[data-testid="stSidebar"] > div > div {
    background-color: #1e1e28 !important;
}

section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    background-color: #1e1e28 !important;
}

/* Ensure sidebar text is white and visible */
.stSidebar p,
.stSidebar span,
.stSidebar label,
.stSidebar .stSlider label,
.stSidebar .stMarkdown,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: #ffffff !important;
}

/* Sidebar headings */
.stSidebar h1,
.stSidebar h2,
.stSidebar h3,
.stSidebar h4,
.stSidebar h5,
.stSidebar h6,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] h5,
section[data-testid="stSidebar"] h6 {
    color: #ffffff !important;
}

/* Slider text in sidebar */
.stSidebar .stSlider label,
section[data-testid="stSidebar"] .stSlider label {
    color: #ffffff !important;
}

/* Text area in sidebar */
.stSidebar .stTextArea > div > div > textarea,
section[data-testid="stSidebar"] .stTextArea > div > div > textarea {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
}

/* Expander in sidebar */
.stSidebar .streamlit-expanderHeader,
section[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}

.stSidebar .streamlit-expanderContent,
section[data-testid="stSidebar"] .streamlit-expanderContent {
    background: rgba(0, 0, 0, 0.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 0 0 8px 8px !important;
}

/* Info text in sidebar */
.stSidebar .stAlert,
section[data-testid="stSidebar"] .stAlert {
    background: rgba(0, 212, 255, 0.1) !important;
    border: 1px solid rgba(0, 212, 255, 0.2) !important;
    color: #ffffff !important;
}

/* Sidebar glass card */
.sidebar-glass {
    background: rgba(18, 18, 26, 0.95);
    border-right: 1px solid var(--border-glass);
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    border: none;
    color: white;
    border-radius: 12px;
    padding: 12px 24px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
}

.stButton > button:active {
    transform: translateY(0);
}

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: var(--bg-glass);
    border: 1px solid var(--border-glass);
    box-shadow: none;
}

.stButton > button[kind="secondary"]:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: var(--border-accent);
}

/* Slider styling */
.stSlider > div > div {
    background: var(--bg-glass) !important;
}

.stSlider > div > div > div {
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)) !important;
}

/* Text area */
.stTextArea > div > div > textarea {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
}

.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
}

.streamlit-expanderContent {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-glass);
    border-radius: 0 0 12px 12px;
    border-top: none;
}

/* Error message */
.error-message {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 12px;
    padding: 16px;
    color: #fca5a5;
}

/* Loading spinner */
.loading-spinner {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(0, 212, 255, 0.1);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}

.empty-state-icon {
    font-size: 64px;
    margin-bottom: 16px;
    opacity: 0.5;
}

/* Code blocks */
.stCodeBlock {
    border-radius: 12px !important;
    background: rgba(0, 0, 0, 0.4) !important;
    border: 1px solid var(--border-glass) !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--border-glass);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--border-accent);
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .message-user,
    .message-assistant {
        max-width: 95%;
    }
    
    .thinking-container {
        max-height: 150px;
    }
}
</style>
"""


def get_custom_css() -> str:
    """Get custom CSS styles.
    
    Returns:
        CSS string
    """
    return CUSTOM_CSS
