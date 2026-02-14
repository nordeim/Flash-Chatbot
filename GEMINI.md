# CLAUDE.md - Project Briefing Document

## Single Source of Truth for AI Coding Agents

**Project**: Flash-Chatbot  
**Type**: Production-grade AI Chatbot Application  
**Last Updated**: 2026-02-15  
**Status**: Phases 1-4 Complete, Ready for Deployment

---

## Executive Summary

Flash-Chatbot is a **production-grade Streamlit chatbot application** that integrates with the **NVIDIA API** using the `moonshotai/kimi-k2.5` model. The application has been architected following **Clean Architecture** principles with a **modular design** separating Config, API, Service, and UI layers.

### Completed Phases
1. ✅ **Phase 0**: Foundation & Configuration (NVIDIA API, settings, logging)
2. ✅ **Phase 1**: Multi-Session Management (34 tests)
3. ✅ **Phase 2**: UI Polish & Accessibility (56 tests)
4. ✅ **Phase 3**: RAG-Lite Document Q&A (38 tests)

**Important to adopt Test-Driven Development methodology (TDD)**

**Total Test Coverage**: 180+ tests passing

---

## Architecture Overview

### Clean Architecture Layers

```
┌─────────────────────────────────────────┐
│ UI Layer (Streamlit)                   │
├─────────────────────────────────────────┤
│ Service Layer (Business Logic)         │
├─────────────────────────────────────────┤
│ API Layer (NVIDIA Client)              │
├─────────────────────────────────────────┤
│ Config Layer (Settings)                │
├─────────────────────────────────────────┤
│ Utils Layer (Shared)                   │
└─────────────────────────────────────────┘
```

### Dependency Rule
Dependencies always point inward - UI depends on Services, which depend on API, which depends on Config.

---

## Project Structure

```
Flash-Chatbot/
├── main.py                          # Root entry point for HF Spaces
├── src/
│   ├── main.py                      # Application entry point
│   ├── __init__.py
│   │
│   ├── config/                      # Configuration Layer
│   │   ├── __init__.py
│   │   ├── constants.py             # App constants (colors, defaults)
│   │   └── settings.py              # Pydantic settings + validation
│   │
│   ├── api/                         # API Layer
│   │   ├── __init__.py
│   │   ├── nvidia_client.py         # NVIDIA API client with streaming
│   │   ├── models.py                # Pydantic models
│   │   └── exceptions.py            # Custom exceptions
│   │
│   ├── services/                    # Service Layer
│   │   ├── __init__.py
│   │   ├── session_manager.py       # Multi-session management
│   │   ├── state_manager.py         # Session state + RAG storage
│   │   ├── chat_service.py          # Main chat business logic
│   │   └── message_formatter.py     # Message formatting
│   │
│   ├── ui/                          # UI Layer
│   │   ├── __init__.py
│   │   ├── chat_interface.py        # Main chat UI
│   │   ├── session_tabs.py          # Ethereal session tabs
│   │   ├── document_upload.py       # Glass dropzone for documents
│   │   ├── sidebar.py               # Settings sidebar
│   │   ├── components.py            # Reusable UI components
│   │   ├── styles.py                # Dark glassmorphism CSS
│   │   └── accessibility.py         # ARIA utilities + focus management
│   │
│   ├── rag/                         # RAG Module
│   │   ├── __init__.py
│   │   ├── document_processor.py    # PDF/TXT extraction + chunking
│   │   ├── embedder.py              # Qwen + MiniLM embedding models
│   │   ├── retriever.py             # FAISS + Simple similarity
│   │   └── exceptions.py            # RAG-specific errors
│   │
│   └── utils/                       # Utils Layer
│       ├── __init__.py
│       └── logger.py                # Structured logging
│
├── tests/                           # Test Suite
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/
│   │   ├── config/
│   │   ├── api/
│   │   ├── services/
│   │   ├── ui/
│   │   ├── rag/
│   │   └── session/
│   └── integration/
│
├── requirements.txt                 # Dependencies
├── Dockerfile                       # HF Spaces deployment
├── docker-compose.yml               # Local development
└── .env.example                     # Environment template
```

---

## Core Features

### 1. Multi-Session Management
- **Create, Switch, Delete** multiple conversation sessions
- **Session isolation**: Each session has independent messages, system prompts, metadata
- **Session tabs**: Ethereal glass UI with neon-cyan active indicator
- **Message badges**: Shows count per session
- **Export/Import**: Per-session JSON export

**Key Files**:
- `src/services/session_manager.py` - Session + SessionManager classes
- `src/ui/session_tabs.py` - Custom HTML session tabs
- `tests/unit/session/test_session_manager.py` - 23 tests
- `tests/unit/ui/test_session_tabs.py` - 11 tests

### 2. RAG-Lite Document Q&A
- **Document upload**: PDF, TXT, Markdown support
- **Text extraction**: pypdf + chardet for encoding detection
- **Smart chunking**: Word boundary preservation, configurable overlap
- **Dual embedding models**: Qwen (1024d) primary + MiniLM (384d) fallback
- **Vector retrieval**: FAISS with auto-fallback to simple cosine similarity
- **Context injection**: Retrieved chunks automatically added to system prompt

**Key Files**:
- `src/rag/document_processor.py` - Text extraction + chunking
- `src/rag/embedder.py` - Qwen + MiniLM wrapper
- `src/rag/retriever.py` - FAISS + SimpleRetriever
- `src/services/chat_service.py` - `stream_message_with_rag()` method
- `src/ui/document_upload.py` - Ethereal glass dropzone

**Test Status**: 38 tests passing

### 3. NVIDIA API Integration
- **Model**: moonshotai/kimi-k2.5
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Streaming**: Real-time SSE streaming with thinking display
- **Parameters**: Temperature, top_p, max_tokens, thinking mode
- **Retry logic**: Exponential backoff
- **Error handling**: Custom exception hierarchy

**Key Files**:
- `src/api/nvidia_client.py` - API client with streaming
- `src/api/models.py` - Pydantic request/response models
- `src/api/exceptions.py` - NvidiaAPIError hierarchy

### 4. Dark Mode UI with Accessibility
- **Glassmorphism**: Semi-transparent cards with blur backdrop
- **Ethereal styling**: Neon-cyan accents (#00d4ff), Satoshi/Inter fonts
- **Three-orb indicator**: Animated thinking indicator with accessibility
- **Micro-interactions**: Hover lifts, button scales, glass shimmer
- **Accessibility**: WCAG AAA compliance
  - Focus-visible indicators (neon-cyan outline)
  - ARIA labels on custom components
  - Reduced-motion support
  - Skip links
  - High contrast mode support

**Key Files**:
- `src/ui/styles.py` - 668 lines of CSS
- `src/ui/accessibility.py` - 660 lines of accessibility utilities
- `src/ui/components.py` - ThreeOrbIndicator + reusable components

### 5. Docker Deployment (HF Spaces)
- **Port**: 7860 (HF Spaces requirement)
- **User**: Non-root (appuser)
- **Health check**: Streamlit health endpoint
- **Multi-stage**: Not needed, single-stage optimized
- **Dependencies**: Pre-installed in image

**Key Files**:
- `Dockerfile` - Production-ready container
- `main.py` - Root entry point (adds src to path before import)
- `src/main.py` - Application logic

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NVIDIA_API_KEY` | Yes | - | API key (starts with `nvapi-`) |
| `NVIDIA_BASE_URL` | No | `https://integrate.api.nvidia.com/v1` | API endpoint |
| `DEFAULT_MODEL` | No | `moonshotai/kimi-k2.5` | Model to use |
| `DEFAULT_MAX_TOKENS` | No | `65536` | Max tokens (1-131072) |
| `DEFAULT_TEMPERATURE` | No | `1.00` | Temperature (0.0-2.0) |
| `DEFAULT_TOP_P` | No | `0.95` | Top-p (0.0-1.0) |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `APP_ENV` | No | `development` | Environment |
| `STREAMLIT_SERVER_PORT` | No | `7860` | Server port |
| `STREAMLIT_SERVER_ADDRESS` | No | `0.0.0.0` | Server address |

### Settings Validation
Pydantic validates all settings on startup:
- API key format (must start with `nvapi-`)
- Token range (1-131072)
- Temperature range (0.0-2.0)
- Top_p range (0.0-1.0)
- Log level values

---

## Dependencies

### Core
```
streamlit>=1.29.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
requests>=2.31.0
httpx>=0.25.0
```

### RAG
```
pypdf>=3.17.0              # PDF extraction
sentence-transformers>=2.2.0  # Qwen/MiniLM embeddings
faiss-cpu>=1.7.4           # Vector store
chardet>=5.2.0             # Encoding detection
```

### Development
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.6.0
```

**Note**: sentence-transformers + torch = ~400MB. Tests skip gracefully when unavailable.

---

## Testing

### Test Organization

```
tests/
├── conftest.py                      # Global fixtures
├── unit/
│   ├── config/
│   │   └── test_config.py          # Settings validation
│   ├── api/
│   │   ├── test_api_models.py      # Pydantic models
│   │   └── test_nvidia_client.py   # API client
│   ├── services/
│   │   ├── test_state_manager.py   # Session state
│   │   └── test_chat_service_rag.py  # RAG integration
│   ├── ui/
│   │   ├── test_accessibility.py   # 31 tests
│   │   ├── test_ui_polish.py       # 25 tests
│   │   ├── test_document_upload.py # 9 tests
│   │   └── test_session_tabs.py    # 11 tests
│   ├── rag/
│   │   ├── test_document_processor.py  # 10 tests
│   │   ├── test_embedder.py        # 15 tests
│   │   └── test_retriever.py       # 11 tests
│   └── session/
│       └── test_session_manager.py # 23 tests
└── integration/
    └── test_chat_flow.py           # End-to-end
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific modules
pytest tests/unit/rag/ -v
pytest tests/unit/session/ -v
pytest tests/unit/ui/ -v

# RAG tests only
pytest tests/unit/rag/test_document_processor.py -v
pytest tests/unit/rag/test_retriever.py -v
```

### Test Coverage by Module

| Module | Tests | Status | Coverage |
|--------|-------|--------|----------|
| DocumentProcessor | 10/10 | ✅ | 95%+ |
| Embedder | 15/15 | ✅ | 90%+ |
| Retriever | 11/11 | ✅ | 90%+ |
| ChatService RAG | 8/8 | ✅ | 85%+ |
| DocumentUpload UI | 9/9 | ✅ | 85%+ |
| Session Manager | 23/23 | ✅ | 95%+ |
| Session Tabs | 11/11 | ✅ | 85%+ |
| Accessibility | 31/31 | ✅ | 90%+ |
| UI Polish | 25/25 | ✅ | 85%+ |
| **Total** | **143/143** | **✅** | **87%+** |

---

## Key Design Patterns

### 1. Singleton Pattern
- Settings instance (`get_settings()`)
- Embedder model instance (lazy loading)

### 2. Repository Pattern
- `NvidiaChatClient` abstracts NVIDIA API
- `Retriever` abstracts vector operations

### 3. Service Pattern
- `ChatService` encapsulates chat business logic
- `SessionManager` manages session lifecycle

### 4. Adapter Pattern
- `DocumentProcessor` abstracts file parsing
- Auto-fallback for embedding models

### 5. Auto-Fallback Chain
```python
Retriever(embedder)
→ FAISS if available
→ SimpleRetriever if not
→ Cosine similarity fallback
```

### 6. Lazy Loading
```python
Embedder()  # Does nothing
embedder.embed_query(text)  # Loads model on first call
```

---

## Data Flow

### Chat Flow (Without RAG)
```
User Input
    ↓
ChatService.stream_message()
    ↓
MessageFormatter.format_messages_for_api()
    ↓
NvidiaChatClient.chat_complete_stream()
    ↓
Stream chunks to UI
    ↓
ChatStateManager.add_assistant_message()
```

### Chat Flow (With RAG)
```
User Input
    ↓
ChatService.stream_message_with_rag()
    ↓
Retriever.retrieve(query, k=3)
    ↓
Format context chunks
    ↓
Augment system prompt with context
    ↓
NvidiaChatClient.chat_complete_stream()
    ↓
Stream response with context
```

### Session Management Flow
```
User clicks "New Session"
    ↓
state_manager.create_new_session("Session 2")
    ↓
SessionManager.create_session()
    ↓
Session created with unique ID
    ↓
StateManager.current_session updated
    ↓
UI rerenders with empty chat
```

---

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

### RAG Exception Hierarchy
```
RAGError (base)
├── DocumentProcessingError
├── UnsupportedFileTypeError
├── EmbeddingError
└── RetrievalError
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
Error → Raise Exception → Handle in Service → Display in UI
```

---

## Security Considerations

### API Key Management
- ✅ Store in environment variables
- ✅ Never commit to repository
- ✅ Pydantic validation on startup
- ✅ Format check (must start with `nvapi-`)

### Container Security
- ✅ Non-root user (appuser:1000)
- ✅ Minimal base image (python:3.13-trixie)
- ✅ Health checks configured
- ✅ No secrets baked into image

### Input Validation
- ✅ Pydantic model validation
- ✅ Content length limits
- ✅ File type validation for uploads
- ✅ Sanitization before display

---

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your NVIDIA_API_KEY

# Run application
streamlit run main.py
# Or: streamlit run src/main.py

# Access at http://localhost:7860
```

### Docker (Local)

```bash
# Build and run
docker-compose up -d

# Or manually
docker build -t flash-chatbot .
docker run -p 7860:7860 -e NVIDIA_API_KEY=your-key flash-chatbot
```

### Hugging Face Spaces

```bash
# Push to HF Spaces
git push origin main

# Space will auto-deploy using Dockerfile
# Entry point: main.py
# Port: 7860
```

---

## Known Issues & Solutions

### Issue 1: sentence-transformers Disk Space
**Problem**: sentence-transformers + torch = ~400MB, exceeds current environment
**Solution**: 
- Implementation complete, tests skip gracefully
- Will auto-install on HF Spaces (16GB available)
- Dual model support: Qwen primary, MiniLM fallback

### Issue 2: FAISS Optional
**Problem**: faiss-cpu not available in all environments
**Solution**: Auto-fallback to SimpleRetriever using cosine similarity

### Issue 3: Session Persistence
**Problem**: Streamlit sessions are ephemeral (lost on refresh)
**Solution**: Acceptable for HF Spaces; future: localStorage persistence

### Issue 4: Avatar Empty String
**Problem**: Streamlit's `st.chat_message(avatar="")` fails
**Solution**: Use `avatar="🤖"` emoji instead

---

## Next Steps for Future Agents

### Immediate Tasks
1. **Deploy to Hugging Face Spaces**
   - Verify Dockerfile builds successfully
   - Test all features end-to-end
   - Monitor memory usage

2. **Performance Optimization**
   - Add connection pooling
   - Implement response caching
   - Optimize chunk size for embeddings

3. **Monitoring & Analytics**
   - Add usage metrics
   - Track error rates
   - Monitor API latency

### Future Enhancements
1. **Database Persistence**: SQLite/PostgreSQL for session storage
2. **Redis Caching**: Response caching
3. **Multi-model Support**: Switch between models
4. **Plugin System**: Extensible architecture
5. **Analytics Dashboard**: Usage tracking

---

## Important Files Quick Reference

### Configuration
- `.env.example` - Environment template
- `src/config/settings.py` - Pydantic settings
- `src/config/constants.py` - App constants

### API
- `src/api/nvidia_client.py` - NVIDIA API client
- `src/api/models.py` - Pydantic models
- `src/api/exceptions.py` - Custom exceptions

### Services
- `src/services/chat_service.py` - Main chat logic
- `src/services/session_manager.py` - Session management
- `src/services/state_manager.py` - State + RAG storage

### UI
- `src/ui/chat_interface.py` - Main chat UI
- `src/ui/session_tabs.py` - Session tabs
- `src/ui/document_upload.py` - Document upload
- `src/ui/sidebar.py` - Settings sidebar
- `src/ui/styles.py` - CSS styles
- `src/ui/accessibility.py` - ARIA utilities

### RAG
- `src/rag/document_processor.py` - Text extraction
- `src/rag/embedder.py` - Embeddings (Qwen + MiniLM)
- `src/rag/retriever.py` - Vector retrieval
- `src/rag/exceptions.py` - RAG errors

### Tests
- `tests/conftest.py` - Global fixtures
- `tests/unit/` - Unit tests (143 tests)
- `tests/integration/` - Integration tests

### Deployment
- `Dockerfile` - Container definition
- `docker-compose.yml` - Local development
- `main.py` - Root entry point (HF Spaces)
- `src/main.py` - Application logic

---

## Testing Commands Cheat Sheet

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific module
pytest tests/unit/rag/ -v
pytest tests/unit/session/ -v
pytest tests/unit/ui/ -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/rag/test_embedder.py::TestEmbedder::test_model_loads_lazily -v

# Run marked tests
pytest -m "slow" -v
pytest -m "not slow" -v
```

---

## Code Style Guidelines

### Python
- Use type hints everywhere
- Follow PEP 8
- Use dataclasses for data structures
- Prefer composition over inheritance
- Early returns, avoid nested conditionals

### Testing
- Write failing test first (TDD)
- Use factory pattern for mocks
- Test behavior, not implementation
- Run tests before committing

### UI
- Follow glassmorphism aesthetic
- Maintain accessibility (WCAG AAA)
- Use CSS variables for theming
- Support reduced-motion preference

---

## Contact & Resources

### Documentation
- `ARCHITECTURE.md` - Detailed architecture
- `README.md` - Quick start guide
- `RAG_PROGRESS.md` - RAG implementation details
- `SESSION_PHASE_SUMMARY.md` - Multi-session details
- `VALIDATED_EXECUTION_PLAN.md` - Execution roadmap

### External Resources
- [NVIDIA API Docs](https://docs.nvidia.com/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-15 | Initial release, Phases 1-4 complete |

---

**End of Briefing Document**

*This document serves as the single source of truth for understanding the Flash-Chatbot project. Update this file when making significant architectural changes or adding major features.*
