import pytest
import asyncio
import logging
from llm_handlers.deepseek_handler import DeepseekHandler
from llm_handlers.grok_handler import GrokHandler
from llm_handlers.gemini_handler import GeminiHandler
from llm_handlers.openai_handler import OpenAIChatHandler
from llm_handlers.handler_factory import LLMHandlerFactory

# Configure logging
logging.basicConfig(level=logging.INFO)

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
async def test_concurrent_llm_responses(deepseek_api_key, grok_api_key, gemini_api_key, openai_api_key):
    handlers = [
        DeepseekHandler(deepseek_api_key),
        GrokHandler(grok_api_key),
        GeminiHandler(gemini_api_key),
        OpenAIChatHandler(openai_api_key)
    ]
    
    responses = await asyncio.gather(*[
        handler.generate_response("Hi", max_tokens=10)
        for handler in handlers
    ])
    
    for response in responses:
        assert isinstance(response, (str, dict))
        if isinstance(response, str):
            assert response != "" 