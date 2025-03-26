import pytest
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def deepseek_api_key():
    return os.getenv("DEEPSEEK_API_KEY")

@pytest.fixture
def grok_api_key():
    return os.getenv("GROK_API_KEY")

@pytest.fixture
def gemini_api_key():
    return os.getenv("GEMINI_API_KEY")

@pytest.fixture
def openai_api_key():
    return os.getenv("OPENAI_API_KEY")

@pytest.fixture
def test_prompt():
    return "What is 2+2? Answer in one word." 