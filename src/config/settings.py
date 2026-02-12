"""Configuration management with Pydantic settings."""

from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings

from src.config.constants import (
    NVIDIA_API_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_TIMEOUT,
)


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # NVIDIA API Configuration
    nvidia_api_key: str = Field(
        ...,  # Required
        description="NVIDIA API key for authentication",
        env="NVIDIA_API_KEY"
    )
    
    nvidia_base_url: str = Field(
        default=NVIDIA_API_BASE_URL,
        description="NVIDIA API base URL",
        env="NVIDIA_BASE_URL"
    )
    
    # Model Configuration
    default_model: str = Field(
        default=DEFAULT_MODEL,
        description="Default model to use",
        env="DEFAULT_MODEL"
    )
    
    default_max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        description="Maximum tokens to generate",
        env="DEFAULT_MAX_TOKENS"
    )
    
    default_temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        description="Sampling temperature",
        env="DEFAULT_TEMPERATURE"
    )
    
    default_top_p: float = Field(
        default=DEFAULT_TOP_P,
        description="Nucleus sampling parameter",
        env="DEFAULT_TOP_P"
    )
    
    # Request Configuration
    request_timeout: float = Field(
        default=DEFAULT_TIMEOUT,
        description="API request timeout in seconds",
        env="REQUEST_TIMEOUT"
    )
    
    # Application Settings
    app_env: str = Field(
        default="development",
        description="Application environment",
        env="APP_ENV"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        env="LOG_LEVEL"
    )
    
    # Streamlit Configuration
    streamlit_server_port: int = Field(
        default=8501,
        description="Streamlit server port",
        env="STREAMLIT_SERVER_PORT"
    )
    
    streamlit_server_address: str = Field(
        default="0.0.0.0",
        description="Streamlit server address",
        env="STREAMLIT_SERVER_ADDRESS"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator('nvidia_api_key')
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        if not v or v.strip() == '':
            raise ValueError("NVIDIA_API_KEY cannot be empty")
        if not v.startswith('nvapi-'):
            raise ValueError("NVIDIA_API_KEY should start with 'nvapi-'")
        return v.strip()
    
    @validator('default_max_tokens')
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max tokens range."""
        if v < 1:
            raise ValueError("max_tokens must be at least 1")
        if v > 131072:
            raise ValueError("max_tokens cannot exceed 131072")
        return v
    
    @validator('default_temperature')
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature range."""
        if v < 0.0:
            raise ValueError("temperature must be >= 0.0")
        if v > 2.0:
            raise ValueError("temperature must be <= 2.0")
        return v
    
    @validator('default_top_p')
    def validate_top_p(cls, v: float) -> float:
        """Validate top_p range."""
        if v < 0.0:
            raise ValueError("top_p must be >= 0.0")
        if v > 1.0:
            raise ValueError("top_p must be <= 1.0")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env.lower() == "production"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
