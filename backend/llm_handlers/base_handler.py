from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

class BaseLLMHandler(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def validate_api_key(self) -> bool:
        """Validate the API key by making a test request."""
        pass

    def _handle_error(self, error: Exception) -> str:
        """Handle errors in a consistent way across all handlers."""
        error_message = str(error)
        self.logger.error(f"Error in {self.__class__.__name__}: {error_message}")
        return f"Error: {error_message}"

class BaseChatHandler(ABC):
    @abstractmethod
    async def get_response(self, content: str) -> str:
        pass 