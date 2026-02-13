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
    
    def stream_message_with_rag(
        self,
        content: str,
        retriever: Optional[Any] = None,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        thinking: bool = DEFAULT_THINKING,
        k: int = 3
    ) -> Generator[Tuple[str, str, Optional[Any]], None, None]:
        """Send message with RAG context and stream response.
        
        If retriever is provided and has documents, retrieves relevant chunks
        and injects them into the system prompt for context-aware responses.
        
        Args:
            content: User message content
            retriever: Optional retriever with uploaded documents
            system_prompt: Optional system prompt (will be augmented with context)
            model: Model to use
            max_tokens: Maximum tokens
            temperature: Temperature
            top_p: Top-p parameter
            thinking: Enable thinking mode
            k: Number of chunks to retrieve
            
        Yields:
            Tuple of (thinking, content, reasoning_details)
        """
        # Build augmented system prompt if retriever available
        augmented_prompt = system_prompt
        
        if retriever is not None:
            try:
                # Check if retriever has documents
                has_docs = (
                    hasattr(retriever, 'documents') and len(retriever.documents) > 0
                ) or (
                    hasattr(retriever, 'index') and 
                    retriever.index is not None and 
                    hasattr(retriever.index, 'ntotal') and 
                    retriever.index.ntotal > 0
                )
                
                if has_docs:
                    # Retrieve relevant chunks
                    results = retriever.retrieve(content, k=k)
                    
                    if results:
                        # Format context
                        context_chunks = [doc.text for doc, _ in results]
                        context_text = "\n\n---\n".join(context_chunks)
                        
                        # Augment system prompt
                        if augmented_prompt:
                            augmented_prompt = (
                                f"{augmented_prompt}\n\n"
                                f"Use the following context to answer the user's question:\n\n"
                                f"{context_text}"
                            )
                        else:
                            augmented_prompt = (
                                f"You are a helpful assistant. Use the following context to answer the user's question:\n\n"
                                f"{context_text}"
                            )
                        
                        self.logger.info(f"Injected {len(results)} context chunks into prompt")
                        
            except Exception as e:
                self.logger.warning(f"RAG retrieval failed, proceeding without context: {e}")
                # Continue without context augmentation
        
        # Delegate to regular streaming with augmented prompt
        yield from self.stream_message(
            content=content,
            system_prompt=augmented_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            thinking=thinking
        )

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
