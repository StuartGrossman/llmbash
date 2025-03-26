import pytest
import os
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv
from unittest.mock import MagicMock, AsyncMock, patch

# Load environment variables from .env file
load_dotenv()

# Test data
TEST_API_KEY = "test_api_key"
TEST_MESSAGE = "Hello, how are you?"
TEST_RESPONSE = "I'm doing well, thank you!"

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ['OPENAI_API_KEY'] = 'test_openai_key'
    os.environ['GEMINI_API_KEY'] = 'test_gemini_key'
    os.environ['GROK_API_KEY'] = 'test_grok_key'
    os.environ['DEEPSEEK_API_KEY'] = 'test_deepseek_key'
    yield
    # Clean up environment variables after tests
    os.environ.pop('OPENAI_API_KEY', None)
    os.environ.pop('GEMINI_API_KEY', None)
    os.environ.pop('GROK_API_KEY', None)
    os.environ.pop('DEEPSEEK_API_KEY', None)

@pytest.fixture
def test_prompt():
    return TEST_MESSAGE

@pytest.fixture
def test_response():
    return TEST_RESPONSE

@pytest.fixture
def deepseek_api_key():
    return TEST_API_KEY

@pytest.fixture
def grok_api_key():
    return TEST_API_KEY

@pytest.fixture
def gemini_api_key():
    return TEST_API_KEY

@pytest.fixture
def openai_api_key():
    return TEST_API_KEY

@pytest.fixture
async def mock_aiohttp_client():
    """Mock aiohttp ClientSession for testing."""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session.return_value = AsyncMock()
        mock_session.return_value.post = AsyncMock()
        mock_session.return_value.post.return_value.__aenter__.return_value = AsyncMock(
            status=200,
            json=AsyncMock(
                return_value={"choices": [{"message": {"content": TEST_RESPONSE}}]}
            )
        )
        yield mock_session

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch('openai.AsyncOpenAI') as mock_client:
        mock_client.return_value = AsyncMock()
        mock_client.return_value.chat = AsyncMock()
        mock_client.return_value.chat.completions = AsyncMock()
        mock_client.return_value.chat.completions.create = AsyncMock(
            return_value=MagicMock(
                choices=[MagicMock(message=MagicMock(content=TEST_RESPONSE))]
            )
        )
        yield mock_client

@pytest.fixture
def mock_gemini():
    """Mock Gemini model for testing."""
    with patch('google.generativeai.GenerativeModel') as mock_model:
        mock_model.return_value = AsyncMock()
        mock_model.return_value.generate_content = AsyncMock(
            return_value=AsyncMock(text=TEST_RESPONSE)
        )
        yield mock_model

@pytest.fixture(scope="session")
def setup_and_teardown_firebase():
    """Initialize Firebase for testing and clean up after tests."""
    # Delete any existing Firebase apps
    while firebase_admin._apps:
        app_name = next(iter(firebase_admin._apps))
        firebase_admin.delete_app(firebase_admin.get_app(app_name))
    
    # Initialize test database
    cred = credentials.Certificate("firebase-service-account.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://test-db.firebaseio.com'
    })
    yield
    # Clean up after tests
    while firebase_admin._apps:
        app_name = next(iter(firebase_admin._apps))
        firebase_admin.delete_app(firebase_admin.get_app(app_name))

@pytest.fixture
def test_message():
    return {
        "user_id": "test_user_123",
        "message_id": "test_message_456",
        "content": TEST_MESSAGE,
        "llm_types": ["deepseek", "grok", "gemini", "openai"]
    }

@pytest.fixture
def test_analysis_request():
    return {
        "user_id": "test_user_123",
        "message_id": "test_message_456",
        "responses": {
            "deepseek": "Response from Deepseek",
            "grok": "Response from Grok",
            "gemini": "Response from Gemini",
            "openai": "Response from OpenAI"
        }
    } 