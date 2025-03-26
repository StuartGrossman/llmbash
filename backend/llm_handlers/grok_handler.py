import aiohttp
from typing import Dict, Any
from .base_handler import BaseLLMHandler
import logging
import ssl
import httpx
import json

# Configure logger
logger = logging.getLogger(__name__)

class GrokHandler(BaseLLMHandler):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.grok.x/v1/chat/completions"
        self.model_name = "grok-2-latest"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.client = httpx.AsyncClient(headers=self.headers)
        # Create SSL context that doesn't verify certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                payload = {
                    "model": "grok-2-latest",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 1000),
                    "stream": False
                }
                
                async with session.post(self.base_url, headers=self.headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API request failed with status {response.status}: {error_text}")
                    
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            self.logger.error(f"Grok API error: {str(e)}")
            return self._handle_error(e)

    async def validate_api_key(self) -> bool:
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                payload = {
                    "model": "grok-2-latest",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."
                        },
                        {
                            "role": "user",
                            "content": "Test"
                        }
                    ],
                    "max_tokens": 5,
                    "stream": False
                }
                
                async with session.post(self.base_url, headers=self.headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Grok API validation failed: {response.status} - {error_text}")
                        return False
                    return True
        except Exception as e:
            self.logger.error(f"Grok API validation error: {str(e)}")
            return False

    async def get_response(self, user_input: str) -> str:
        """Get response from Grok API"""
        try:
            prompt = f"""Before answering this question: "{user_input}", think about the three most important questions that you need to understand to understand the deepness of the initial question.

Then, provide a 300-word answer in the most concise way.

Your response should be structured as follows:
1. First, list the three key questions you identified
2. Then, provide your concise 300-word answer

Remember to be precise and focused in your response."""

            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant that provides thoughtful, concise responses."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "stream": False
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
                        self.logger.error(f"Error in GrokHandler: {error_message}")
                        return f"Error: {error_message}"
                    
                    result = await response.json()
                    if not result.get('choices') or not result['choices'][0].get('message', {}).get('content'):
                        error_message = "Invalid response format from Grok API"
                        self.logger.error(f"Error in GrokHandler: {error_message}")
                        return f"Error: {error_message}"
                    
                    return result['choices'][0]['message']['content']
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Error in GrokHandler: {error_message}")
            return f"Error: {error_message}" 