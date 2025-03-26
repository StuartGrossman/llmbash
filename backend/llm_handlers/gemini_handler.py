import google.generativeai as genai
from typing import Dict, Any
from .base_handler import BaseLLMHandler
import logging
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logger
logger = logging.getLogger(__name__)

class GeminiHandler(BaseLLMHandler):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        genai.configure(api_key=self.api_key)
        self.model_name = 'gemini-1.5-pro'
        self.model = genai.GenerativeModel(self.model_name)
        self.logger = logging.getLogger(__name__)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def _make_request(self, prompt: str, **kwargs) -> str:
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_output_tokens": kwargs.get("max_tokens", 1000),
                    "top_p": 0.8,
                    "top_k": 40
                }
            )
            
            if not response or not response.candidates:
                raise Exception("Empty response from Gemini API")
                
            if not response.candidates[0].content or not response.candidates[0].content.parts:
                raise Exception("No content parts in response")
                
            return response.candidates[0].content.parts[0].text
        except Exception as e:
            self.logger.error(f"Gemini API request error: {str(e)}")
            raise

    async def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            self.logger.info("Starting Gemini response generation")
            
            try:
                response = await self._make_request(prompt, **kwargs)
                self.logger.info("Successfully received response from Gemini")
                return response
            except Exception as e:
                self.logger.error(f"Failed to get response after retries: {str(e)}")
                return self._handle_error(e)
                
        except Exception as e:
            self.logger.error(f"Gemini API error: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
            return self._handle_error(e)

    async def validate_api_key(self) -> bool:
        try:
            self.logger.info("Validating Gemini API key")
            genai.configure(api_key=self.api_key)
            
            try:
                await self._make_request("Test")
                self.logger.info("Gemini API key validation successful")
                return True
            except Exception as e:
                self.logger.error(f"Gemini API validation failed: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Gemini API validation error: {str(e)}")
            return False

    async def get_response(self, user_input: str) -> str:
        """Get response from Gemini API"""
        try:
            prompt = f"""Before answering this question: "{user_input}", think about the three most important questions that you need to understand to understand the deepness of the initial question.

Then, provide a 300-word answer in the most concise way.

Your response should be structured as follows:
1. First, list the three key questions you identified
2. Then, provide your concise 300-word answer

Remember to be precise and focused in your response."""

            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error in GeminiHandler: {str(e)}")
            raise 