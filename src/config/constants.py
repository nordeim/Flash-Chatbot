"""Application constants and default values."""

# API Configuration
NVIDIA_API_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_CHAT_ENDPOINT = "/chat/completions"

# Model Configuration
DEFAULT_MODEL = "moonshotai/kimi-k2.5"
DEFAULT_MAX_TOKENS = 65536
DEFAULT_TEMPERATURE = 1.00
DEFAULT_TOP_P = 0.95
DEFAULT_STREAMING = True
DEFAULT_THINKING = True

# Request Configuration
DEFAULT_TIMEOUT = 120.0  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
RETRY_BACKOFF = 2.0  # exponential backoff multiplier

# UI Configuration
PAGE_TITLE = "Step-3.5-Flash"
PAGE_ICON = ""
PAGE_LAYOUT = "centered"

# Sidebar Configuration
SIDEBAR_TITLE = "⚙️ Settings"
MAX_TOKENS_MIN = 256
MAX_TOKENS_MAX = 131072
MAX_TOKENS_STEP = 256
TEMPERATURE_MIN = 0.0
TEMPERATURE_MAX = 2.0
TEMPERATURE_STEP = 0.1
TOP_P_MIN = 0.1
TOP_P_MAX = 1.0
TOP_P_STEP = 0.05

# Default System Prompt
DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."

# Thinking/Reasoning Configuration
THINKING_LABEL = "Thinking Process"
CONTENT_LABEL = "Response"

# Error Messages
ERROR_API_KEY_MISSING = "NVIDIA API key is not configured. Please set NVIDIA_API_KEY environment variable."
ERROR_API_CONNECTION = "Failed to connect to NVIDIA API. Please check your network connection."
ERROR_API_RATE_LIMIT = "Rate limit exceeded. Please wait a moment before sending another message."
ERROR_API_AUTH = "Authentication failed. Please check your API key."
ERROR_GENERIC = "An error occurred. Please try again."

# Example Questions
EXAMPLE_QUESTIONS = [
    "Please explain what machine learning is.",
    "Help me write a Python quicksort algorithm.",
    "How many prime numbers are there under 1000?",
]

# Log Messages
LOG_API_REQUEST = "Sending request to NVIDIA API"
LOG_API_RESPONSE = "Received response from NVIDIA API"
LOG_STREAM_CHUNK = "Processing stream chunk"
LOG_SESSION_START = "Session started"
LOG_SESSION_END = "Session ended"
