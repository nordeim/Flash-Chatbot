"""Pydantic models for NVIDIA API requests and responses."""

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, validator


class Message(BaseModel):
    """Chat message model."""
    
    role: Literal["system", "user", "assistant"] = Field(
        ...,
        description="Message role"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Message content"
    )
    reasoning_details: Optional[str] = Field(
        default=None,
        description="Reasoning/thinking details for assistant messages"
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Hello, how are you?"
            }
        }


class ChatTemplateKwargs(BaseModel):
    """Chat template kwargs for reasoning mode."""
    
    thinking: bool = Field(
        default=True,
        description="Enable thinking/reasoning mode"
    )


class ChatRequest(BaseModel):
    """Chat completion request model."""
    
    model: str = Field(
        ...,
        description="Model identifier"
    )
    messages: List[Message] = Field(
        ...,
        min_length=1,
        description="Conversation messages"
    )
    max_tokens: int = Field(
        default=65536,
        ge=1,
        le=131072,
        description="Maximum tokens to generate"
    )
    temperature: float = Field(
        default=1.00,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    top_p: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    stream: bool = Field(
        default=True,
        description="Enable streaming response"
    )
    chat_template_kwargs: ChatTemplateKwargs = Field(
        default_factory=ChatTemplateKwargs,
        description="Chat template configuration"
    )
    
    @validator('messages')
    def validate_messages(cls, v: List[Message]) -> List[Message]:
        """Validate message list."""
        if not v:
            raise ValueError("At least one message is required")
        return v


class Usage(BaseModel):
    """Token usage information."""
    
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)


class Choice(BaseModel):
    """Completion choice model."""
    
    index: int = Field(default=0)
    message: Optional[Message] = None
    delta: Optional[Dict[str, Any]] = None  # For streaming
    finish_reason: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat completion response model."""
    
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None


class StreamChunk(BaseModel):
    """Streaming response chunk model."""
    
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    
    @property
    def delta_content(self) -> Optional[str]:
        """Extract content from delta."""
        if self.choices and self.choices[0].delta:
            return self.choices[0].delta.get("content")
        return None
    
    @property
    def delta_reasoning(self) -> Optional[str]:
        """Extract reasoning from delta."""
        if self.choices and self.choices[0].delta:
            return self.choices[0].delta.get("reasoning")
        return None
    
    @property
    def reasoning_details(self) -> Optional[Any]:
        """Extract reasoning details from message."""
        if self.choices and self.choices[0].message:
            return self.choices[0].message.get("reasoning_details")
        return None
    
    @property
    def is_done(self) -> bool:
        """Check if this is the final chunk."""
        if self.choices and self.choices[0].finish_reason:
            return True
        return False


class ReasoningContent(BaseModel):
    """Reasoning/thinking content model."""
    
    content: str = Field(description="Raw reasoning text")
    cleaned_content: Optional[str] = Field(default=None, description="Cleaned reasoning text")
    
    @validator('cleaned_content', always=True)
    def clean_reasoning(cls, v: Optional[str], values: Dict) -> str:
        """Clean reasoning content by removing tags."""
        content = values.get('content', '')
        if not content:
            return ''
        
        # Remove <think> tags
        import re
        cleaned = re.sub(r'</?think>', '', content).strip()
        return cleaned
