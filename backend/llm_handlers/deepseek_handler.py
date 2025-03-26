import aiohttp
from typing import Dict, Any
from .base_handler import BaseLLMHandler
import logging
import httpx
import json

class DeepseekHandler(BaseLLMHandler):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)

    async def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            self.logger.info("Starting Deepseek response generation")
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
                    self.logger.info("Successfully received response from Deepseek")
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            self.logger.error(f"Deepseek API error: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
            return self._handle_error(e)

    async def validate_api_key(self) -> bool:
        try:
            self.logger.info("Validating Deepseek API key")
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Test"}],
                    "max_tokens": 5
                }
                
                async with session.post(self.base_url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        self.logger.info("Deepseek API key validation successful")
                        return True
                    else:
                        self.logger.error(f"Deepseek API key validation failed with status {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"Deepseek API validation error: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
            return False

    async def get_response(self, content: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": content}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                else:
                    error_message = f"API request failed with status {response.status_code}: {response.text}"
                    self.logger.error(f"Error in {self.__class__.__name__}: {error_message}")
                    return f"Error: {error_message}"
                    
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Error in {self.__class__.__name__}: {error_message}")
            return f"Error: {error_message}" 