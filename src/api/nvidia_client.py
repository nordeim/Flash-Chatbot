"""NVIDIA API client for chat completions with streaming support."""

import json
import time
from typing import Generator, List, Optional, Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config.constants import (
    NVIDIA_API_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_STREAMING,
    DEFAULT_THINKING,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)
from src.config.settings import Settings, get_settings
from src.api.models import Message, ChatRequest, ChatResponse, StreamChunk
from src.api.exceptions import (
    NvidiaAPIError,
    NvidiaAuthError,
    NvidiaRateLimitError,
    NvidiaStreamError,
    NvidiaTimeoutError,
    raise_for_status,
)
from src.utils.logger import get_logger, LoggerMixin

logger = get_logger(__name__)


class NvidiaChatClient(LoggerMixin):
    """Client for NVIDIA Chat Completions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        """Initialize NVIDIA API client.

        Args:
            api_key: NVIDIA API key (defaults to env var)
            base_url: API base URL (defaults to NVIDIA endpoint)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        # Get settings if not provided
        settings = get_settings()

        self.api_key = api_key or settings.nvidia_api_key
        self.base_url = base_url or settings.nvidia_base_url
        self.timeout = timeout
        self.max_retries = max_retries

        # Validate API key
        if not self.api_key:
            raise NvidiaAuthError("API key is required")

        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.logger.info(f"Initialized NVIDIA client with base_url: {self.base_url}")

    def _get_headers(self, stream: bool = False) -> Dict[str, str]:
        """Get request headers.

        Args:
            stream: Whether this is a streaming request

        Returns:
            Headers dictionary
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if stream:
            headers["Accept"] = "text/event-stream"
        else:
            headers["Accept"] = "application/json"

        return headers

    def _make_request(
        self,
        messages: List[Message],
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        stream: bool = DEFAULT_STREAMING,
        thinking: bool = DEFAULT_THINKING,
    ) -> requests.Response:
        """Make API request.

        Args:
            messages: List of messages
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stream: Whether to stream response
            thinking: Whether to enable thinking mode

        Returns:
            Response object

        Raises:
            NvidiaAPIError: On API errors
        """
        # Build request
        from src.api.models import ChatTemplateKwargs

        request = ChatRequest(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=stream,
            chat_template_kwargs=ChatTemplateKwargs(thinking=thinking),
        )

        url = f"{self.base_url}/chat/completions"
        headers = self._get_headers(stream=stream)

        self.logger.debug(f"Sending request to {url} with model {model}")

        try:
            response = self.session.post(
                url,
                headers=headers,
                json=request.model_dump(),
                timeout=self.timeout,
                stream=stream,
            )

            # Check status code
            if response.status_code != 200:
                try:
                    body = response.json()
                except:
                    body = None
                raise_for_status(response.status_code, body)

            return response

        except requests.exceptions.Timeout as e:
            self.logger.error(f"Request timed out: {e}")
            raise NvidiaTimeoutError(timeout=self.timeout)
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {e}")
            raise NvidiaAPIError(f"Failed to connect to API: {e}")
        except NvidiaAPIError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise NvidiaAPIError(f"Unexpected error: {e}")

    def chat_complete(
        self,
        messages: List[Message],
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        thinking: bool = DEFAULT_THINKING,
    ) -> ChatResponse:
        """Send non-streaming chat completion request.

        Args:
            messages: List of messages
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            thinking: Whether to enable thinking mode

        Returns:
            Chat completion response
        """
        response = self._make_request(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=False,
            thinking=thinking,
        )

        data = response.json()
        return ChatResponse(**data)

    def chat_complete_stream(
        self,
        messages: List[Message],
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        thinking: bool = DEFAULT_THINKING,
    ) -> Generator[StreamChunk, None, None]:
        """Send streaming chat completion request.

        Args:
            messages: List of messages
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            thinking: Whether to enable thinking mode

        Yields:
            StreamChunk objects
        """
        response = self._make_request(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=True,
            thinking=thinking,
        )

        for line in response.iter_lines():
            if not line:
                continue

            try:
                line_text = line.decode("utf-8")

                # Skip lines that don't start with "data: "
                if not line_text.startswith("data: "):
                    continue

                data_str = line_text[6:]  # Remove "data: " prefix

                # Check for stream end
                if data_str == "[DONE]":
                    self.logger.debug("Stream completed")
                    break

                # Parse JSON
                data = json.loads(data_str)
                chunk = StreamChunk(**data)

                yield chunk

            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse JSON: {e}, line: {line}")
                continue
            except Exception as e:
                self.logger.error(f"Error processing stream chunk: {e}")
                raise NvidiaStreamError(
                    f"Error processing chunk: {e}", chunk=line.decode("utf-8")
                )

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
