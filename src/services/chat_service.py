"""Main chat service for business logic."""

from typing import Generator, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from src.api.nvidia_client import NvidiaChatClient
from src.api.models import Message, StreamChunk
from src.services.state_manager import ChatStateManager
from src.services.message_formatter import MessageFormatter
from src.config.constants import (
    DEFAULT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_THINKING,
)
from src.utils.logger import LoggerMixin


@dataclass
class ChatResponse:
    """Chat response data class."""
    
    content: str
    thinking: Optional[str] = None
    reasoning_details: Optional[Any] = None
    finished: bool = False


class ChatService(LoggerMixin):
    """Service for chat operations."""
    
    def __init__(
        self,
        client: Optional[NvidiaChatClient] = None,
        state_manager: Optional[ChatStateManager] = None
    ):
        """Initialize chat service.
        
        Args:
            client: NVIDIA API client
            state_manager: State manager instance
        """
        self.client = client or NvidiaChatClient()
        self.state_manager = state_manager or ChatStateManager()
        self.formatter = MessageFormatter()
        
        self.logger.info("Initialized ChatService")
    
    def send_message(
        self,
        content: str,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        thinking: bool = DEFAULT_THINKING
    ) -> ChatResponse:
        """Send message and get complete response.
        
        Args:
            content: User message content
            system_prompt: Optional system prompt
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Temperature
            top_p: Top-p parameter
            thinking: Enable thinking mode
            
        Returns:
            ChatResponse with content and thinking
        """
        # Add user message to state
        self.state_manager.add_user_message(content)
        
        # Format messages for API
        messages = MessageFormatter.format_messages_for_api(
            self.state_manager.messages[:-1],  # Exclude the message we just added
            system_prompt
        )
        messages = MessageFormatter.add_user_message(messages, content)
        
        # Call API
        try:
            response = self.client.chat_complete(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                thinking=thinking
            )
            
            # Extract content from response
            content = ""
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content or ""
            
            # Save to state
            self.state_manager.add_assistant_message(content)
            
            return ChatResponse(content=content, finished=True)
            
        except Exception as e:
            self.logger.error(f"Error in send_message: {e}")
            error_msg = f"❌ Error: {str(e)}"
            self.state_manager.add_assistant_message(error_msg)
            return ChatResponse(content=error_msg, finished=True)
    
    def stream_message(
        self,
        content: str,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        thinking: bool = DEFAULT_THINKING
    ) -> Generator[Tuple[str, str, Optional[Any]], None, None]:
        """Send message and stream response.
        
        Args:
            content: User message content
            system_prompt: Optional system prompt
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Temperature
            top_p: Top-p parameter
            thinking: Enable thinking mode
            
        Yields:
            Tuple of (thinking, content, reasoning_details)
        """
        # Add user message to state
        self.state_manager.add_user_message(content)
        
        # Format messages for API
        messages = MessageFormatter.format_messages_for_api(
            self.state_manager.messages[:-1],
            system_prompt
        )
        messages = MessageFormatter.add_user_message(messages, content)
        
        # Track accumulated content
        full_thinking = ""
        full_content = ""
        full_reasoning_details = None
        
        try:
            # Stream response
            for chunk in self.client.chat_complete_stream(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                thinking=thinking
            ):
                # Update thinking
                reasoning = chunk.delta_reasoning
                if reasoning:
                    full_thinking += reasoning
                
                # Update content
                delta_content = chunk.delta_content
                if delta_content:
                    full_content += delta_content
                
                # Update reasoning details
                details = chunk.reasoning_details
                if details:
                    full_reasoning_details = details
                
                yield full_thinking, full_content, full_reasoning_details
            
            # Save final message to state
            self.state_manager.add_assistant_message(
                full_content,
                thinking=full_thinking,
                reasoning_details=full_reasoning_details
            )
            
        except Exception as e:
            self.logger.error(f"Error in stream_message: {e}")
            error_msg = f"❌ Error: {str(e)}"
            full_content = error_msg if not full_content else full_content
            yield full_thinking, full_content, full_reasoning_details
            
            # Save error message
            self.state_manager.add_assistant_message(error_msg)
    
    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.state_manager.clear_history()
        self.logger.info("Conversation cleared")
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.state_manager.get_stats()
    
    def export_conversation(self) -> str:
        """Export conversation to JSON.
        
        Returns:
            JSON string
        """
        return self.state_manager.export_to_json()
    
    def import_conversation(self, json_str: str) -> bool:
        """Import conversation from JSON.
        
        Args:
            json_str: JSON string
            
        Returns:
            True if successful
        """
        return self.state_manager.import_from_json(json_str)
    
    def close(self) -> None:
        """Close service and cleanup resources."""
        self.client.close()
        self.logger.info("ChatService closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
