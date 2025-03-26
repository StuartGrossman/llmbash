from typing import Dict, Type
from .base_handler import BaseLLMHandler
from .deepseek_handler import DeepseekHandler
from .grok_handler import GrokHandler
from .gemini_handler import GeminiHandler
from .openai_handler import OpenAIChatHandler

class LLMHandlerFactory:
    _handlers: Dict[str, Type[BaseLLMHandler]] = {
        "deepseek": DeepseekHandler,
        "grok": GrokHandler,
        "gemini": GeminiHandler,
        "openai": OpenAIChatHandler
    }

    @classmethod
    def get_handler(cls, model_name: str, api_key: str) -> BaseLLMHandler:
        """Get the appropriate handler for the specified model."""
        handler_class = cls._handlers.get(model_name.lower())
        if not handler_class:
            raise ValueError(f"No handler found for model: {model_name}")
        return handler_class(api_key)

    @classmethod
    def get_available_models(cls) -> list:
        """Get a list of available model names."""
        return list(cls._handlers.keys()) 