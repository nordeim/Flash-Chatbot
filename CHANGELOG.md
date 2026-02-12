# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-13

### Major Changes

#### Added
- **NVIDIA API Integration**: Migrated from OpenRouter to NVIDIA API for chat completions
  - Uses `moonshotai/kimi-k2.5` model
  - Supports streaming responses via SSE
  - Thinking/reasoning mode support
  - Custom exception handling for API errors
  
- **Clean Architecture**: Refactored from monolithic single-file app to modular architecture
  - Separation of concerns with distinct layers
  - Dependency injection pattern
  - Service-oriented design
  
- **Configuration Management**: Environment-based configuration with Pydantic
  - Type-safe settings validation
  - Environment variable support
  - Singleton pattern for settings
  
- **Dark Mode UI**: Modern glassmorphism design
  - Dark theme by default
  - Custom CSS with glassmorphism effects
  - Animated gradients and transitions
  - Responsive layout
  
- **State Management**: Session-based conversation management
  - Persistent conversation history
  - Export/import functionality
  - Message statistics tracking
  
- **Comprehensive Testing**: Full test suite
  - Unit tests for all modules
  - Integration tests for chat flows
  - Pytest configuration
  - Mock fixtures for dependencies
  
- **Production Infrastructure**:
  - Multi-stage Dockerfile
  - Docker Compose configuration
  - Health checks
  - Non-root user security
  
- **Documentation**:
  - Comprehensive README
  - Architecture documentation
  - API reference
  - Configuration guide

### Changed
- **Entry Point**: Changed from `app.py` to `src/main.py`
- **API Client**: Replaced `httpx` with `requests` for NVIDIA API compatibility
- **Error Handling**: Improved error handling with custom exceptions
- **Logging**: Added structured logging with colored output

### Removed
- **Legacy Files**:
  - `app.py` (replaced with `src/main.py`)
  - `src/streamlit_app.py` (demo file)
  - OpenRouter API integration
  - StepFun logo downloading functionality

### Technical Details

#### Dependencies
- Added: `pydantic`, `pydantic-settings`, `python-dotenv`
- Updated: `requests` (primary), `streamlit`
- Removed: `httpx` (kept for compatibility), `altair`, `pandas`, `regex`

#### API Changes
- **Request Format**: Now uses `chat_template_kwargs` for thinking mode
- **Response Format**: Streaming responses use SSE format
- **Error Handling**: Custom exceptions with HTTP status code mapping

### Migration Guide

To migrate from the old version:

1. Update environment variables:
   ```bash
   # Old
   OPENROUTER_API_KEY=your-key
   
   # New
   NVIDIA_API_KEY=nvapi-your-key
   ```

2. Install new dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run with new entry point:
   ```bash
   streamlit run src/main.py
   ```

### Known Issues
- Type hints show warnings in some IDEs due to Pydantic v2 compatibility (runtime works fine)

### Contributors
- Development Team

---

## [0.1.0] - Initial Release (Legacy)

### Features
- Basic chat interface with Streamlit
- OpenRouter API integration
- Multi-turn conversations
- Parameter controls (temperature, top_p, max_tokens)
- Thinking process display

### Dependencies
- streamlit
- httpx
- regex
