import aiohttp
from typing import Dict, Any
from .base_handler import BaseLLMHandler
import logging
import httpx
import json

# Configure logger
logger = logging.getLogger(__name__)

class DeepseekHandler(BaseLLMHandler):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.model_name = "deepseek-chat"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(headers=self.headers)

    async def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            logger.info("Starting Deepseek response generation")
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 1000)
                }
                
                async with session.post(self.base_url, headers=self.headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API request failed with status {response.status}: {error_text}")
                    
                    result = await response.json()
                    logger.info("Successfully received response from Deepseek")
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Deepseek API error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
            return self._handle_error(e)

    async def validate_api_key(self) -> bool:
        try:
            logger.info("Validating Deepseek API key")
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Test"}],
                    "max_tokens": 5
                }
                
                async with session.post(self.base_url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        logger.info("Deepseek API key validation successful")
                        return True
                    else:
                        logger.error(f"Deepseek API key validation failed with status {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Deepseek API validation error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
            return False

    async def get_response(self, user_input: str) -> str:
        """Get response from Deepseek API"""
        try:
            prompt = f"""Before answering this question: "{user_input}", think about the three most important questions that you need to understand to understand the deepness of the initial question.

Then, provide a 300-word answer in the most concise way.

Your response should be structured as follows:
1. First, list the three key questions you identified
2. Then, provide your concise 300-word answer

Remember to be precise and focused in your response."""

            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant that provides thoughtful, concise responses."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_message = f"API request failed with status {response.status}: {error_text}"
                        logger.error(f"Error in DeepseekHandler: {error_message}")
                        return f"Error: {error_message}"
                    
                    result = await response.json()
                    if not result.get('choices') or not result['choices'][0].get('message', {}).get('content'):
                        error_message = "Invalid response format from Deepseek API"
                        logger.error(f"Error in DeepseekHandler: {error_message}")
                        return f"Error: {error_message}"
                    
                    return result['choices'][0]['message']['content']
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in DeepseekHandler: {error_message}")
            return f"Error: {error_message}" 