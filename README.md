# Step-3.5-Flash Chatbot

A production-grade intelligent conversational assistant built with Streamlit and the NVIDIA API, featuring a modern dark mode UI with glassmorphism design.

## Features

- **Dark Mode UI**: Modern glassmorphism design with dark theme
- **NVIDIA API Integration**: Uses `moonshotai/kimi-k2.5` model via NVIDIA API
- **Streaming Responses**: Real-time streaming with thinking process display
- **Multi-turn Conversations**: Persistent conversation history
- **Adjustable Parameters**: Temperature, top_p, and max_tokens controls
- **Export/Import**: Save and load conversations
- **Responsive Design**: Works on desktop and mobile

## Quick Start

### Prerequisites

- Python 3.11+
- NVIDIA API key (get one at [NVIDIA AI](https://www.nvidia.com/en-us/ai/))

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Step-3.5-Flash
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
```

4. Run the application:
```bash
streamlit run src/main.py
```

The application will be available at `http://localhost:8501`

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t step-3.5-flash .
docker run -p 8501:8501 -e NVIDIA_API_KEY=your-key step-3.5-flash
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NVIDIA_API_KEY` | Yes | - | Your NVIDIA API key |
| `NVIDIA_BASE_URL` | No | `https://integrate.api.nvidia.com/v1` | API base URL |
| `DEFAULT_MODEL` | No | `moonshotai/kimi-k2.5` | Model to use |
| `DEFAULT_MAX_TOKENS` | No | `65536` | Maximum tokens |
| `DEFAULT_TEMPERATURE` | No | `1.00` | Temperature (0.0-2.0) |
| `DEFAULT_TOP_P` | No | `0.95` | Top-p (0.0-1.0) |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `APP_ENV` | No | `development` | Environment |

## Project Structure

```
Step-3.5-Flash/
├── src/
│   ├── main.py              # Application entry point
│   ├── config/
│   │   ├── constants.py     # Application constants
│   │   └── settings.py      # Configuration management
│   ├── api/
│   │   ├── nvidia_client.py # NVIDIA API client
│   │   ├── models.py        # Pydantic models
│   │   └── exceptions.py    # Custom exceptions
│   ├── services/
│   │   ├── chat_service.py  # Business logic
│   │   ├── state_manager.py # Session management
│   │   └── message_formatter.py # Message formatting
│   ├── ui/
│   │   ├── chat_interface.py # Main UI
│   │   ├── sidebar.py       # Settings sidebar
│   │   ├── components.py    # UI components
│   │   └── styles.py        # Custom CSS
│   └── utils/
│       └── logger.py        # Logging utilities
├── requirements.txt         # Dependencies
├── requirements-dev.txt     # Development dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Docker compose config
├── .env.example            # Environment template
└── README.md               # This file
```

## Architecture

The application follows Clean Architecture principles:

1. **Config Layer**: Environment-based configuration with Pydantic validation
2. **API Layer**: NVIDIA API client with streaming and error handling
3. **Service Layer**: Business logic and state management
4. **UI Layer**: Streamlit components with dark mode styling

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/

# Check style
flake8 src/

# Type check
mypy src/
```

## API Reference

### NVIDIA API

The application uses the NVIDIA API for chat completions:

- **Endpoint**: `https://integrate.api.nvidia.com/v1/chat/completions`
- **Model**: `moonshotai/kimi-k2.5`
- **Features**: Streaming, thinking mode, up to 128k tokens

### ChatService

Main service for chat operations:

```python
from src.services.chat_service import ChatService

with ChatService() as chat:
    # Send message with streaming
    for thinking, content, details in chat.stream_message("Hello"):
        print(f"Thinking: {thinking}")
        print(f"Content: {content}")
```

## Troubleshooting

### API Key Issues

If you see authentication errors:
1. Verify your API key starts with `nvapi-`
2. Check the `.env` file is properly loaded
3. Ensure the API key has access to the model

### Streaming Issues

If streaming doesn't work:
1. Check network connectivity
2. Verify the API endpoint is accessible
3. Check logs for error details

### Memory Issues

For large conversations:
1. Clear conversation history periodically
2. Reduce max_tokens setting
3. Monitor application memory usage

## License

Apache-2.0

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [NVIDIA API](https://www.nvidia.com/en-us/ai/)
- Uses [moonshotai/kimi-k2.5](https://huggingface.co/moonshotai/kimi-k2.5) model
