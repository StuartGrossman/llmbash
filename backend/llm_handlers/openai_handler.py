from openai import AsyncOpenAI
from typing import Dict, Any
from .base_handler import BaseLLMHandler
import logging
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
import openai

# Configure logger
logger = logging.getLogger(__name__)

class OpenAIChatHandler(BaseLLMHandler):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=httpx.Timeout(30.0, connect=10.0),
            http_client=httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                verify=True
            )
        )
        self.model = "gpt-4-turbo-preview"
        self.logger = logging.getLogger(__name__)
        openai.api_key = self.api_key

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def _make_request(self, messages: list, max_tokens: int = 1000) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens,
                timeout=30.0
            )
            return response.choices[0].message.content
        except httpx.TimeoutException as e:
            self.logger.error(f"OpenAI API timeout: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            raise

    async def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            self.logger.info(f"Starting OpenAI response generation with model {self.model}")
            messages = [{"role": "user", "content": prompt}]
            
            try:
                response = await self._make_request(messages, kwargs.get("max_tokens", 1000))
                self.logger.info("Successfully received response from OpenAI")
                return response
            except Exception as e:
                self.logger.error(f"Failed to get response after retries: {str(e)}")
                return self._handle_error(e)
                
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
            return self._handle_error(e)

    async def validate_api_key(self) -> bool:
        try:
            self.logger.info("Validating OpenAI API key")
            messages = [{"role": "user", "content": "Test"}]
            
            try:
                await self._make_request(messages, max_tokens=5)
                self.logger.info("OpenAI API key validation successful")
                return True
            except Exception as e:
                self.logger.error(f"OpenAI API validation failed: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"OpenAI API validation error: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
            return False

    async def get_response(self, user_input: str) -> str:
        """Get response from OpenAI API"""
        try:
            prompt = f"""Before answering this question: "{user_input}", think about the three most important questions that you need to understand to understand the deepness of the initial question.

Then, provide a 300-word answer in the most concise way.

Your response should be structured as follows:
1. First, list the three key questions you identified
2. Then, provide your concise 300-word answer

Remember to be precise and focused in your response."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that provides thoughtful, concise responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in OpenAIChatHandler: {str(e)}")
            raise 