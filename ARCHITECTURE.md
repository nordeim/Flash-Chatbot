# Architecture Documentation

## Overview

Step-3.5-Flash is a production-grade chatbot application built with **Clean Architecture** principles. The application uses a modular design with clear separation of concerns, making it maintainable, testable, and scalable.

## Architecture Principles

### Clean Architecture

The application follows Clean Architecture with the following layers:

```
┌─────────────────────────────────────────┐
│           UI Layer (Streamlit)          │
├─────────────────────────────────────────┤
│        Service Layer (Business)         │
├─────────────────────────────────────────┤
│           API Layer (External)          │
├─────────────────────────────────────────┤
│       Config Layer (Settings)           │
├─────────────────────────────────────────┤
│        Utils Layer (Shared)             │
└─────────────────────────────────────────┘
```

### Dependency Rule

Dependencies always point inward:
- UI Layer depends on Service Layer
- Service Layer depends on API Layer
- API Layer depends on Config Layer
- All layers depend on Utils Layer

## Project Structure

```
Step-3.5-Flash/
├── src/
│   ├── main.py                    # Application entry point
│   ├── __init__.py
│   │
│   ├── config/                    # Configuration Layer
│   │   ├── __init__.py
│   │   ├── constants.py            # Application constants
│   │   └── settings.py             # Pydantic settings management
│   │
│   ├── api/                       # API Layer
│   │   ├── __init__.py
│   │   ├── nvidia_client.py        # NVIDIA API client
│   │   ├── models.py               # Pydantic data models
│   │   └── exceptions.py           # Custom exceptions
│   │
│   ├── services/                  # Service Layer
│   │   ├── __init__.py
│   │   ├── chat_service.py         # Main chat business logic
│   │   ├── state_manager.py        # Session state management
│   │   └── message_formatter.py    # Message formatting utilities
│   │
│   ├── ui/                        # UI Layer
│   │   ├── __init__.py
│   │   ├── chat_interface.py       # Main chat interface
│   │   ├── sidebar.py              # Settings sidebar
│   │   ├── components.py           # Reusable UI components
│   │   └── styles.py               # CSS styling
│   │
│   └── utils/                     # Utils Layer
│       ├── __init__.py
│       └── logger.py               # Logging utilities
│
├── tests/                         # Test Suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── conftest.py                # Pytest fixtures
│
├── requirements.txt               # Dependencies
├── Dockerfile                     # Container definition
├── docker-compose.yml             # Local development
└── README.md                      # Documentation
```

## Layer Details

### 1. Config Layer

**Purpose**: Manage application configuration and settings

**Key Components**:
- `settings.py`: Pydantic-based configuration with validation
- `constants.py`: Application-wide constants

**Features**:
- Environment variable loading
- Type-safe settings with validation
- Singleton pattern for settings instance
- Support for `.env` files

**Design Patterns**:
- **Singleton**: Settings instance
- **Validation**: Pydantic validators

### 2. API Layer

**Purpose**: Handle external API communication

**Key Components**:
- `nvidia_client.py`: NVIDIA Chat Completions API client
- `models.py`: Pydantic models for requests/responses
- `exceptions.py`: Custom API exceptions

**Features**:
- Streaming support via SSE
- Retry logic with exponential backoff
- Custom exception handling
- Session management

**API Integration**:
```
User Input → ChatService → NvidiaChatClient → NVIDIA API
    ↑                                              ↓
    └──────── Stream Response ←────────────────────┘
```

**Design Patterns**:
- **Repository**: API client abstracts external service
- **Factory**: Response model creation
- **Context Manager**: Resource cleanup

### 3. Service Layer

**Purpose**: Business logic and state management

**Key Components**:
- `chat_service.py`: Main chat orchestration
- `state_manager.py`: Streamlit session state management
- `message_formatter.py`: Message formatting

**Features**:
- Conversation management
- Message formatting
- State persistence
- Statistics tracking

**Data Flow**:
```
User Input
    ↓
ChatService.send_message() / stream_message()
    ↓
MessageFormatter.format_messages_for_api()
    ↓
NvidiaChatClient.chat_complete() / chat_complete_stream()
    ↓
ChatStateManager.add_assistant_message()
    ↓
UI Update
```

**Design Patterns**:
- **Service**: Business logic encapsulation
- **State**: Session management
- **Strategy**: Message formatting

### 4. UI Layer

**Purpose**: User interface rendering

**Key Components**:
- `chat_interface.py`: Main chat interface
- `sidebar.py`: Settings controls
- `components.py`: Reusable UI elements
- `styles.py`: Custom CSS

**Features**:
- Dark mode with glassmorphism
- Responsive design
- Real-time streaming display
- Error handling

**Design Patterns**:
- **Component**: Reusable UI elements
- **Template**: Style definitions

### 5. Utils Layer

**Purpose**: Shared utilities

**Key Components**:
- `logger.py`: Structured logging

**Features**:
- Colored console output
- JSON formatting
- Log level management

## Data Models

### Message Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   User      │────→│   Message    │────→│    API      │
│   Input     │     │   Formatter  │     │   Request   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ↓
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│    UI       │←────│   Message    │←────│    API      │
│   Display   │     │   Parser     │     │   Response  │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Key Models

**Message**:
```python
{
    "role": "user" | "assistant" | "system",
    "content": str,
    "reasoning_details": Optional[str]
}
```

**ChatRequest**:
```python
{
    "model": str,
    "messages": List[Message],
    "max_tokens": int,
    "temperature": float,
    "top_p": float,
    "stream": bool,
    "chat_template_kwargs": {"thinking": bool}
}
```

**ChatResponse**:
```python
{
    "id": str,
    "object": str,
    "created": int,
    "model": str,
    "choices": List[Choice],
    "usage": Optional[Usage]
}
```

## Error Handling

### Exception Hierarchy

```
NvidiaAPIError (base)
├── NvidiaAuthError (401)
├── NvidiaRateLimitError (429)
├── NvidiaValidationError (400)
├── NvidiaServerError (5xx)
├── NvidiaStreamError (streaming)
└── NvidiaTimeoutError (timeout)
```

### Error Flow

```
API Call
    ↓
HTTP Response
    ↓
Status Check
    ↓
Success → Parse Response
    ↓
Error → Raise Exception → Handle in Service → Display in UI
```

## State Management

### Session State

Using Streamlit's session state for persistence:

```python
{
    "chat_messages": List[Message],
    "session_id": str,
    "pending_prompt": Optional[str]
}
```

### State Persistence

- **In-memory**: Session-based persistence
- **Export/Import**: JSON-based conversation saving
- **No Database**: Stateless design

## Testing Strategy

### Test Pyramid

```
    /\
   /  \  E2E Tests (integration/)
  /____\
 /      \  Integration Tests (integration/)
/________\
/          \  Unit Tests (unit/)
/____________\
```

### Test Organization

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Fixtures**: Mock external dependencies

### Coverage Goals

- Config: 100%
- API Client: 95%
- Services: 90%
- UI: 80%
- Overall: 85%+

## Security Considerations

### API Key Management

- Store in environment variables
- Never commit to repository
- Use `.env.example` as template
- Validate format on startup

### Container Security

- Non-root user in Docker
- Minimal base image
- Health checks
- Read-only mounts where possible

### Input Validation

- Pydantic model validation
- Content sanitization
- Length limits
- Rate limiting support

## Performance

### Optimization Strategies

1. **Streaming**: Real-time response display
2. **Session Caching**: Avoid repeated API calls
3. **Lazy Loading**: On-demand content
4. **Connection Pooling**: Reuse HTTP connections

### Metrics

- Target startup: < 3 seconds
- Streaming latency: < 100ms
- Memory usage: < 512MB

## Deployment

### Docker

Multi-stage build:
1. Builder stage: Install dependencies
2. Production stage: Run application

### Environment Variables

Required:
- `NVIDIA_API_KEY`

Optional:
- `NVIDIA_BASE_URL`
- `DEFAULT_MODEL`
- `LOG_LEVEL`
- `APP_ENV`

### Health Checks

```bash
curl -f http://localhost:8501/_stcore/health
```

## Future Enhancements

### Potential Improvements

1. **Database**: Persistent storage with SQLite/PostgreSQL
2. **Caching**: Redis for response caching
3. **Auth**: User authentication system
4. **Analytics**: Usage tracking and metrics
5. **Multi-model**: Support for multiple models
6. **Plugins**: Extensible plugin system

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [NVIDIA API Reference](https://docs.nvidia.com/)
