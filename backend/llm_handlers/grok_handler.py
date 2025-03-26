import aiohttp
from typing import Dict, Any
from .base_handler import BaseLLMHandler
import logging
import ssl
import httpx
import json

class GrokHandler(BaseLLMHandler):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.x.ai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Create SSL context that doesn't verify certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.model = "grok-2-latest"

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

    async def get_response(self, content: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."
                        },
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "stream": False
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