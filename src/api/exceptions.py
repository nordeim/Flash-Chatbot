"""Custom exceptions for NVIDIA API client."""


class NvidiaAPIError(Exception):
    """Base exception for NVIDIA API errors."""
    
    def __init__(self, message: str, status_code: int = None, response_body: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
    
    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class NvidiaAuthError(NvidiaAPIError):
    """Raised when authentication fails (401)."""
    
    def __init__(self, message: str = "Authentication failed", response_body: dict = None):
        super().__init__(message, status_code=401, response_body=response_body)


class NvidiaRateLimitError(NvidiaAPIError):
    """Raised when rate limit is exceeded (429)."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class NvidiaStreamError(NvidiaAPIError):
    """Raised when streaming encounters an error."""
    
    def __init__(self, message: str = "Stream processing error", chunk: str = None):
        super().__init__(message)
        self.chunk = chunk


class NvidiaValidationError(NvidiaAPIError):
    """Raised when request validation fails (400)."""
    
    def __init__(self, message: str = "Validation error", response_body: dict = None):
        super().__init__(message, status_code=400, response_body=response_body)


class NvidiaServerError(NvidiaAPIError):
    """Raised when server returns 5xx error."""
    
    def __init__(self, message: str = "Server error", status_code: int = 500):
        super().__init__(message, status_code=status_code)


class NvidiaTimeoutError(NvidiaAPIError):
    """Raised when request times out."""
    
    def __init__(self, message: str = "Request timed out", timeout: float = None):
        super().__init__(message)
        self.timeout = timeout


def raise_for_status(status_code: int, response_body: dict = None) -> None:
    """Raise appropriate exception based on status code.
    
    Args:
        status_code: HTTP status code
        response_body: Optional response body for context
        
    Raises:
        NvidiaAPIError: Appropriate exception for the status code
    """
    if status_code == 200 or status_code == 201:
        return
    elif status_code == 401:
        raise NvidiaAuthError(response_body=response_body)
    elif status_code == 429:
        raise NvidiaRateLimitError()
    elif status_code == 400:
        raise NvidiaValidationError(response_body=response_body)
    elif 500 <= status_code < 600:
        raise NvidiaServerError(status_code=status_code)
    else:
        raise NvidiaAPIError(f"Unexpected status code: {status_code}", status_code=status_code)
