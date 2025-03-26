import httpx
import os
from typing import Dict, Any
import logging
import json
import re

class AnalysisHandler:
    def __init__(self):
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model = "deepseek-chat"
        self.timeout = 30.0

    async def analyze_responses(self, question: str, responses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze responses from different LLMs and determine the best one.
        """
        try:
            # Prepare the prompt for analysis
            prompt = f"""You are an expert at analyzing LLM responses. Please analyze these responses to the question: "{question}"

Responses from different models:

1. OpenAI:
{responses.get('openai', {}).get('answer', 'No response')}

2. Gemini:
{responses.get('gemini', {}).get('answer', 'No response')}

3. Grok:
{responses.get('grok', {}).get('answer', 'No response')}

4. Deepseek:
{responses.get('deepseek', {}).get('answer', 'No response')}

Please analyze these responses and provide:
1. A comprehensive summary that combines the best aspects of all responses
2. Identify which model provided the most accurate and helpful response (must be one of: openai, gemini, grok, deepseek)
3. Explain why that model's response was the best

Format your response exactly like this:
SUMMARY: [your comprehensive summary here]
BEST_MODEL: [model name]
EXPLANATION: [your explanation here]"""

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are an expert at analyzing LLM responses. Always format your response with SUMMARY:, BEST_MODEL:, and EXPLANATION: sections."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000
                    }
                )

                if response.status_code != 200:
                    logging.error(f"Analysis API error: {response.text}")
                    return {
                        "error": f"Analysis failed: {response.text}",
                        "summary": "Analysis failed",
                        "bestModel": "unknown"
                    }

                result = response.json()
                try:
                    content = result["choices"][0]["message"]["content"]
                    
                    # Parse the response sections
                    summary_match = re.search(r'SUMMARY:\s*(.*?)(?=BEST_MODEL:|$)', content, re.DOTALL)
                    best_model_match = re.search(r'BEST_MODEL:\s*(.*?)(?=EXPLANATION:|$)', content, re.DOTALL)
                    explanation_match = re.search(r'EXPLANATION:\s*(.*?)$', content, re.DOTALL)
                    
                    if not all([summary_match, best_model_match, explanation_match]):
                        raise ValueError("Missing required sections in response")
                    
                    summary = summary_match.group(1).strip()
                    best_model = best_model_match.group(1).strip().lower()
                    explanation = explanation_match.group(1).strip()
                    
                    # Validate the model name
                    valid_models = ['openai', 'gemini', 'grok', 'deepseek']
                    if best_model not in valid_models:
                        raise ValueError(f"Invalid model name: {best_model}")
                    
                    return {
                        "summary": summary,
                        "bestModel": best_model,
                        "explanation": explanation
                    }
                except (KeyError, ValueError, AttributeError) as e:
                    logging.error(f"Failed to parse analysis response: {str(e)}")
                    logging.error(f"Raw content: {content}")
                    return {
                        "error": "Failed to parse analysis response",
                        "summary": "Analysis failed",
                        "bestModel": "unknown"
                    }

        except Exception as e:
            logging.error(f"Error in analysis: {str(e)}")
            return {
                "error": str(e),
                "summary": "Analysis failed",
                "bestModel": "unknown"
            } 