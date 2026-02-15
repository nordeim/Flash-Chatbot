"""Tests for Pydantic V2 migration.

This test suite verifies that all Pydantic V1 syntax has been properly
migrated to Pydantic V2 syntax without breaking functionality.
"""

import pytest
from pydantic import ValidationError


class TestMessageModel:
    """Tests for Message model Pydantic V2 compatibility."""

    def test_message_creation_with_valid_data(self):
        """Test Message can be created with valid data."""
        from src.api.models import Message

        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.reasoning_details is None

    def test_message_with_reasoning_details(self):
        """Test Message with reasoning details."""
        from src.api.models import Message

        msg = Message(
            role="assistant",
            content="Response",
            reasoning_details="<think>Thinking...</think>",
        )
        assert msg.reasoning_details == "<think>Thinking...</think>"

    def test_message_invalid_role(self):
        """Test Message rejects invalid role."""
        from src.api.models import Message

        with pytest.raises(ValidationError):
            Message(role="invalid", content="Hello")

    def test_message_empty_content(self):
        """Test Message rejects empty content."""
        from src.api.models import Message

        with pytest.raises(ValidationError):
            Message(role="user", content="")


class TestChatRequestModel:
    """Tests for ChatRequest model Pydantic V2 compatibility."""

    def test_chat_request_with_valid_messages(self):
        """Test ChatRequest with valid messages."""
        from src.api.models import ChatRequest, Message

        messages = [
            Message(role="system", content="System prompt"),
            Message(role="user", content="Hello"),
        ]
        request = ChatRequest(model="moonshotai/kimi-k2.5", messages=messages)
        assert request.model == "moonshotai/kimi-k2.5"
        assert len(request.messages) == 2

    def test_chat_request_default_values(self):
        """Test ChatRequest has correct defaults."""
        from src.api.models import ChatRequest, Message

        request = ChatRequest(
            model="moonshotai/kimi-k2.5",
            messages=[Message(role="user", content="Hello")],
        )
        assert request.max_tokens == 65536
        assert request.temperature == 1.00
        assert request.top_p == 0.95
        assert request.stream is True

    def test_chat_request_temperature_validation(self):
        """Test temperature range validation."""
        from src.api.models import ChatRequest, Message

        # Valid temperature
        request = ChatRequest(
            model="moonshotai/kimi-k2.5",
            messages=[Message(role="user", content="Hello")],
            temperature=1.5,
        )
        assert request.temperature == 1.5

        # Invalid temperature (too high)
        with pytest.raises(ValidationError):
            ChatRequest(
                model="moonshotai/kimi-k2.5",
                messages=[Message(role="user", content="Hello")],
                temperature=3.0,
            )

        # Invalid temperature (negative)
        with pytest.raises(ValidationError):
            ChatRequest(
                model="moonshotai/kimi-k2.5",
                messages=[Message(role="user", content="Hello")],
                temperature=-1.0,
            )

    def test_chat_request_max_tokens_validation(self):
        """Test max_tokens range validation."""
        from src.api.models import ChatRequest, Message

        # Invalid max_tokens (too high)
        with pytest.raises(ValidationError):
            ChatRequest(
                model="moonshotai/kimi-k2.5",
                messages=[Message(role="user", content="Hello")],
                max_tokens=200000,
            )

        # Invalid max_tokens (zero)
        with pytest.raises(ValidationError):
            ChatRequest(
                model="moonshotai/kimi-k2.5",
                messages=[Message(role="user", content="Hello")],
                max_tokens=0,
            )

    def test_chat_request_empty_messages_rejected(self):
        """Test ChatRequest rejects empty messages list."""
        from src.api.models import ChatRequest

        with pytest.raises(ValidationError):
            ChatRequest(model="moonshotai/kimi-k2.5", messages=[])


class TestReasoningContentModel:
    """Tests for ReasoningContent model Pydantic V2 compatibility."""

    def test_reasoning_content_creation(self):
        """Test ReasoningContent can be created."""
        from src.api.models import ReasoningContent

        rc = ReasoningContent(content="<think>Thinking...</think>")
        assert rc.content == "<think>Thinking...</think>"
        assert rc.cleaned_content == "Thinking..."

    def test_reasoning_content_auto_cleaning(self):
        """Test reasoning content is automatically cleaned."""
        from src.api.models import ReasoningContent

        rc = ReasoningContent(content="<think>Step 1</think>")
        assert rc.cleaned_content == "Step 1"

    def test_reasoning_content_empty_content(self):
        """Test ReasoningContent handles empty content."""
        from src.api.models import ReasoningContent

        rc = ReasoningContent(content="")
        assert rc.cleaned_content == ""


class TestStreamChunkModel:
    """Tests for StreamChunk model Pydantic V2 compatibility."""

    def test_stream_chunk_creation(self):
        """Test StreamChunk can be created."""
        from src.api.models import StreamChunk, Choice

        chunk = StreamChunk(
            id="chunk-1",
            object="chat.completion.chunk",
            created=1234567890,
            model="moonshotai/kimi-k2.5",
            choices=[Choice(index=0, delta={"content": "Hello"})],
        )
        assert chunk.id == "chunk-1"

    def test_stream_chunk_delta_content_property(self):
        """Test StreamChunk delta_content property."""
        from src.api.models import StreamChunk, Choice

        chunk = StreamChunk(
            id="chunk-1",
            object="chat.completion.chunk",
            created=1234567890,
            model="moonshotai/kimi-k2.5",
            choices=[Choice(index=0, delta={"content": "Hello"})],
        )
        assert chunk.delta_content == "Hello"

    def test_stream_chunk_reasoning_details_property(self):
        """Test StreamChunk reasoning_details property (CRIT-3 fix)."""
        from src.api.models import StreamChunk, Choice, Message

        # With message containing reasoning_details
        message = Message(
            role="assistant",
            content="Response",
            reasoning_details="<think>Thinking...</think>",
        )
        chunk = StreamChunk(
            id="chunk-1",
            object="chat.completion.chunk",
            created=1234567890,
            model="moonshotai/kimi-k2.5",
            choices=[Choice(index=0, message=message)],
        )
        assert chunk.reasoning_details == "<think>Thinking...</think>"

    def test_stream_chunk_is_done_property(self):
        """Test StreamChunk is_done property."""
        from src.api.models import StreamChunk, Choice

        # Not done
        chunk = StreamChunk(
            id="chunk-1",
            object="chat.completion.chunk",
            created=1234567890,
            model="moonshotai/kimi-k2.5",
            choices=[Choice(index=0, delta={"content": "Hello"})],
        )
        assert chunk.is_done is False

        # Done
        chunk_done = StreamChunk(
            id="chunk-1",
            object="chat.completion.chunk",
            created=1234567890,
            model="moonshotai/kimi-k2.5",
            choices=[Choice(index=0, delta={}, finish_reason="stop")],
        )
        assert chunk_done.is_done is True


class TestModelDumpVsDict:
    """Tests for model_dump() vs deprecated dict() method."""

    def test_chat_request_model_dump(self):
        """Test ChatRequest can be serialized with model_dump()."""
        from src.api.models import ChatRequest, Message

        request = ChatRequest(
            model="moonshotai/kimi-k2.5",
            messages=[Message(role="user", content="Hello")],
        )
        data = request.model_dump()
        assert "model" in data
        assert "messages" in data
        assert data["model"] == "moonshotai/kimi-k2.5"

    def test_message_model_dump(self):
        """Test Message can be serialized with model_dump()."""
        from src.api.models import Message

        msg = Message(role="user", content="Hello")
        data = msg.model_dump()
        assert data["role"] == "user"
        assert data["content"] == "Hello"

    def test_no_dict_deprecation_warning(self):
        """Test that dict() method doesn't cause deprecation warnings."""
        import warnings
        from src.api.models import ChatRequest, Message

        request = ChatRequest(
            model="moonshotai/kimi-k2.5",
            messages=[Message(role="user", content="Hello")],
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Try using model_dump (should not produce deprecation warning)
            request.model_dump()
            # Check no deprecation warnings
            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0


class TestSettingsModel:
    """Tests for Settings model Pydantic V2 compatibility."""

    def test_settings_default_values(self, monkeypatch):
        """Test Settings has correct defaults."""
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test-key-12345")
        from src.config.settings import Settings

        settings = Settings()
        assert settings.nvidia_api_key == "nvapi-test-key-12345"
        assert settings.default_max_tokens == 65536
        assert settings.default_temperature == 1.00
        assert settings.default_top_p == 0.95

    def test_settings_api_key_validation(self, monkeypatch):
        """Test Settings API key validation."""
        from src.config.settings import Settings

        # Invalid API key (wrong prefix)
        monkeypatch.setenv("NVIDIA_API_KEY", "invalid-key")
        with pytest.raises(ValidationError):
            Settings()

        # Empty API key
        monkeypatch.setenv("NVIDIA_API_KEY", "")
        with pytest.raises(ValidationError):
            Settings()

    def test_settings_max_tokens_validation(self, monkeypatch):
        """Test Settings max_tokens validation."""
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test-key-12345")
        from src.config.settings import Settings

        # Invalid max_tokens (too high)
        monkeypatch.setenv("DEFAULT_MAX_TOKENS", "200000")
        with pytest.raises(ValidationError):
            Settings()

        # Invalid max_tokens (zero)
        monkeypatch.setenv("DEFAULT_MAX_TOKENS", "0")
        with pytest.raises(ValidationError):
            Settings()

    def test_settings_temperature_validation(self, monkeypatch):
        """Test Settings temperature validation."""
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test-key-12345")
        from src.config.settings import Settings

        # Invalid temperature (too high)
        monkeypatch.setenv("DEFAULT_TEMPERATURE", "3.0")
        with pytest.raises(ValidationError):
            Settings()

        # Invalid temperature (negative)
        monkeypatch.setenv("DEFAULT_TEMPERATURE", "-1.0")
        with pytest.raises(ValidationError):
            Settings()

    def test_settings_top_p_validation(self, monkeypatch):
        """Test Settings top_p validation."""
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test-key-12345")
        from src.config.settings import Settings

        # Invalid top_p (too high)
        monkeypatch.setenv("DEFAULT_TOP_P", "1.5")
        with pytest.raises(ValidationError):
            Settings()

        # Invalid top_p (negative)
        monkeypatch.setenv("DEFAULT_TOP_P", "-0.1")
        with pytest.raises(ValidationError):
            Settings()

    def test_settings_log_level_validation(self, monkeypatch):
        """Test Settings log_level validation."""
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test-key-12345")
        from src.config.settings import Settings

        # Invalid log level
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        with pytest.raises(ValidationError):
            Settings()

        # Valid log levels (case insensitive)
        for level in ["debug", "info", "warning", "error", "critical"]:
            monkeypatch.setenv("LOG_LEVEL", level)
            settings = Settings()
            assert settings.log_level == level.upper()

    def test_settings_environment_properties(self, monkeypatch):
        """Test Settings environment properties."""
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test-key-12345")
        from src.config.settings import Settings

        # Development mode
        monkeypatch.setenv("APP_ENV", "development")
        settings = Settings()
        assert settings.is_development is True
        assert settings.is_production is False

        # Production mode
        monkeypatch.setenv("APP_ENV", "production")
        settings = Settings()
        assert settings.is_development is False
        assert settings.is_production is True


class TestNoPydanticV1Syntax:
    """Tests to ensure no Pydantic V1 syntax remains."""

    def test_no_validator_import_in_models(self):
        """Test that validator is not imported from pydantic."""
        import ast
        import inspect
        from src.api import models

        source = inspect.getsource(models)
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "pydantic":
                    names = [alias.name for alias in node.names]
                    assert "validator" not in names, (
                        "validator should not be imported, use field_validator instead"
                    )

    def test_no_config_class_in_models(self):
        """Test that Config class is not used in models."""
        import ast
        import inspect
        from src.api import models

        source = inspect.getsource(models)
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == "Config":
                    # Check if this is a nested class (Config inside a model)
                    parent = None
                    for n in ast.walk(tree):
                        if isinstance(n, ast.ClassDef) and n != node:
                            for child in ast.iter_child_nodes(n):
                                if child is node:
                                    parent = n
                                    break
                    if parent:
                        pytest.fail(
                            f"Found deprecated Config class nested in {parent.name}"
                        )

    def test_no_dict_method_calls(self):
        """Test that .dict() method is not called on models."""
        import ast
        import inspect
        from src.api import nvidia_client

        source = inspect.getsource(nvidia_client)
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "dict":
                        pytest.fail(
                            f"Found deprecated .dict() call at line {node.lineno}. "
                            "Use .model_dump() instead"
                        )


class TestValidationErrorMessages:
    """Tests to verify ValidationError messages are user-friendly."""

    def test_message_validation_error_message(self):
        """Test that Message validation errors are clear."""
        from src.api.models import Message

        try:
            Message(role="invalid", content="Hello")
        except ValidationError as e:
            error_msg = str(e)
            assert "role" in error_msg or "input" in error_msg.lower()

    def test_settings_validation_error_messages(self, monkeypatch):
        """Test that Settings validation errors are clear."""
        monkeypatch.setenv("NVIDIA_API_KEY", "invalid-key")
        from src.config.settings import Settings

        try:
            Settings()
        except ValidationError as e:
            error_msg = str(e)
            # Should mention the key requirement
            assert "nvapi-" in error_msg or "API" in error_msg
