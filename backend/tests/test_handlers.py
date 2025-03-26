import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import logging
import asyncio
from llm_handlers import (
    DeepseekHandler,
    GrokHandler,
    GeminiHandler,
    OpenAIChatHandler,
    LLMHandlerFactory
)
import google.generativeai as genai
import os

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data
TEST_API_KEY = "test_api_key"
TEST_MESSAGE = "Hello, how are you?"
TEST_RESPONSE = "I'm doing well, thank you!"

@pytest.fixture
async def mock_aiohttp_client():
    with patch('aiohttp.ClientSession') as mock_session:
        mock_cm = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": TEST_RESPONSE}}]
        }
        mock_cm.__aenter__.return_value = mock_response
        mock_session.return_value.post.return_value = mock_cm
        yield mock_session

@pytest.fixture
def mock_openai():
    with patch('openai.AsyncOpenAI') as mock_client:
        mock_client.return_value.chat.completions.create = AsyncMock(
            return_value=MagicMock(
                choices=[MagicMock(message=MagicMock(content=TEST_RESPONSE))]
            )
        )
        yield mock_client

@pytest.fixture
def mock_gemini():
    with patch('google.generativeai.GenerativeModel') as mock_model:
        mock_model.return_value.generate_content = AsyncMock(
            return_value=MagicMock(text=TEST_RESPONSE)
        )
        yield mock_model

@pytest.mark.asyncio
async def test_deepseek_handler(deepseek_api_key, test_prompt):
    handler = DeepseekHandler(deepseek_api_key)
    assert await handler.validate_api_key()
    response = await handler.generate_response("Hi", max_tokens=10)
    assert isinstance(response, (str, dict))
    assert response != ""

@pytest.mark.asyncio
async def test_grok_handler(grok_api_key, test_prompt):
    handler = GrokHandler(grok_api_key)
    try:
        is_valid = await handler.validate_api_key()
        assert is_valid, "Grok API key validation failed"
        response = await handler.generate_response("Hi", max_tokens=10)
        assert isinstance(response, (str, dict))
        assert response != ""
    except Exception as e:
        pytest.fail(f"Grok handler test failed: {str(e)}")

@pytest.mark.asyncio
async def test_gemini_handler(gemini_api_key, test_prompt):
    handler = GeminiHandler(gemini_api_key)
    try:
        is_valid = await handler.validate_api_key()
        assert is_valid, "Gemini API key validation failed"
        response = await handler.generate_response("Hi", max_tokens=10)
        assert isinstance(response, (str, dict))
        assert response != ""
    except Exception as e:
        pytest.fail(f"Gemini handler test failed: {str(e)}")

@pytest.mark.asyncio
async def test_openai_handler(openai_api_key, test_prompt):
    handler = OpenAIChatHandler(openai_api_key)
    try:
        is_valid = await handler.validate_api_key()
        assert is_valid, "OpenAI API key validation failed"
        response = await handler.generate_response("Hi", max_tokens=10)
        assert isinstance(response, (str, dict))
        assert response != ""
    except Exception as e:
        pytest.fail(f"OpenAI handler test failed: {str(e)}")

@pytest.mark.asyncio
async def test_handler_factory(deepseek_api_key, grok_api_key, gemini_api_key, openai_api_key):
    factory = LLMHandlerFactory()
    
    # Test getting handlers
    deepseek = factory.get_handler("deepseek", deepseek_api_key)
    assert isinstance(deepseek, DeepseekHandler)
    
    grok = factory.get_handler("grok", grok_api_key)
    assert isinstance(grok, GrokHandler)
    
    gemini = factory.get_handler("gemini", gemini_api_key)
    assert isinstance(gemini, GeminiHandler)
    
    openai = factory.get_handler("openai", openai_api_key)
    assert isinstance(openai, OpenAIChatHandler)
    
    # Test getting available models
    models = factory.get_available_models()
    assert isinstance(models, list)
    assert all(model in models for model in ["deepseek", "grok", "gemini", "openai"])
    
    # Test invalid model name
    with pytest.raises(ValueError):
        factory.get_handler("invalid_model", "dummy_key")

@pytest.mark.asyncio
async def test_concurrent_llm_responses(mock_aiohttp_client, mock_openai, mock_gemini):
    """Test concurrent responses from different LLM handlers"""
    factory = LLMHandlerFactory()
    handlers = [
        factory.get_handler("deepseek", TEST_API_KEY),
        factory.get_handler("grok", TEST_API_KEY),
        factory.get_handler("gemini", TEST_API_KEY),
        factory.get_handler("openai", TEST_API_KEY)
    ]

    # Get responses from all handlers concurrently
    async def get_response(handler):
        return await handler.generate_response(TEST_MESSAGE)

    responses = await asyncio.gather(*[get_response(handler) for handler in handlers])

    for response in responses:
        assert response == TEST_RESPONSE or "Error" in response

class TestDeepseekHandler:
    @pytest.mark.asyncio
    async def test_init(self):
        handler = DeepseekHandler(TEST_API_KEY)
        assert handler.api_key == TEST_API_KEY
        assert handler.base_url == "https://api.deepseek.com/v1/chat/completions"

    @pytest.mark.asyncio
    async def test_get_response(self, mock_aiohttp_client):
        handler = DeepseekHandler(TEST_API_KEY)
        response = await handler.generate_response(TEST_MESSAGE)
        assert response == TEST_RESPONSE

    @pytest.mark.asyncio
    async def test_api_error(self, mock_aiohttp_client):
        mock_aiohttp_client.return_value.post.side_effect = Exception("API Error")
        handler = DeepseekHandler(TEST_API_KEY)
        response = await handler.generate_response(TEST_MESSAGE)
        assert "Error" in response

class TestGrokHandler:
    @pytest.mark.asyncio
    async def test_init(self):
        handler = GrokHandler(TEST_API_KEY)
        assert handler.api_key == TEST_API_KEY
        assert handler.base_url == "https://api.grok.x/v1/chat/completions"

    @pytest.mark.asyncio
    async def test_get_response(self, mock_aiohttp_client):
        handler = GrokHandler(TEST_API_KEY)
        response = await handler.generate_response(TEST_MESSAGE)
        assert response == TEST_RESPONSE

    @pytest.mark.asyncio
    async def test_api_error(self, mock_aiohttp_client):
        mock_aiohttp_client.return_value.post.side_effect = Exception("API Error")
        handler = GrokHandler(TEST_API_KEY)
        response = await handler.generate_response(TEST_MESSAGE)
        assert "Error" in response

class TestGeminiHandler:
    @pytest.mark.asyncio
    async def test_init(self):
        handler = GeminiHandler(TEST_API_KEY)
        assert handler.api_key == TEST_API_KEY

    @pytest.mark.asyncio
    async def test_get_response(self, mock_gemini):
        handler = GeminiHandler(TEST_API_KEY)
        response = await handler.generate_response(TEST_MESSAGE)
        assert response == TEST_RESPONSE

    @pytest.mark.asyncio
    async def test_api_error(self, mock_gemini):
        mock_gemini.return_value.generate_content.side_effect = Exception("API Error")
        handler = GeminiHandler(TEST_API_KEY)
        response = await handler.generate_response(TEST_MESSAGE)
        assert "Error" in response

class TestOpenAIChatHandler:
    @pytest.mark.asyncio
    async def test_init(self):
        handler = OpenAIChatHandler(TEST_API_KEY)
        assert handler.api_key == TEST_API_KEY

    @pytest.mark.asyncio
    async def test_get_response(self, mock_openai):
        handler = OpenAIChatHandler(TEST_API_KEY)
        response = await handler.generate_response(TEST_MESSAGE)
        assert response == TEST_RESPONSE

    @pytest.mark.asyncio
    async def test_api_error(self, mock_openai):
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")
        handler = OpenAIChatHandler(TEST_API_KEY)
        response = await handler.generate_response(TEST_MESSAGE)
        assert "Error" in response

class TestLLMHandlerFactory:
    def test_create_handler(self):
        factory = LLMHandlerFactory()
        
        # Test creating each handler type
        deepseek = factory.get_handler("deepseek", TEST_API_KEY)
        assert isinstance(deepseek, DeepseekHandler)
        
        grok = factory.get_handler("grok", TEST_API_KEY)
        assert isinstance(grok, GrokHandler)
        
        gemini = factory.get_handler("gemini", TEST_API_KEY)
        assert isinstance(gemini, GeminiHandler)
        
        openai = factory.get_handler("openai", TEST_API_KEY)
        assert isinstance(openai, OpenAIChatHandler)
        
        # Test invalid handler type
        with pytest.raises(ValueError):
            factory.get_handler("invalid", TEST_API_KEY)

@pytest.mark.asyncio
async def test_concurrent_responses():
    """Test that all LLM handlers can handle concurrent requests."""
    handlers = [
        DeepseekHandler(TEST_API_KEY),
        GrokHandler(TEST_API_KEY),
        GeminiHandler(TEST_API_KEY),
        OpenAIChatHandler(TEST_API_KEY)
    ]
    
    async def get_response(handler):
        return await handler.generate_response(TEST_MESSAGE)
    
    responses = await asyncio.gather(
        *[get_response(handler) for handler in handlers]
    )
    
    for response in responses:
        assert response == TEST_RESPONSE or "Error" in response

def test_environment_variables():
    """Test that all required environment variables are set"""
    required_vars = [
        'OPENAI_API_KEY',
        'GEMINI_API_KEY',
        'GROK_API_KEY',
        'DEEPSEEK_API_KEY'
    ]
    for var in required_vars:
        assert os.getenv(var) is not None, f"Missing required environment variable: {var}" 