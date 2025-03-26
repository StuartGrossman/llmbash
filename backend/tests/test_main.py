import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import firebase_admin
from firebase_admin import credentials
from main import app
from llm_handlers import LLMHandlerFactory

# Test data
TEST_USER_ID = "test_user_123"
TEST_MESSAGE_ID = "test_message_456"
TEST_MESSAGE = {
    "user_id": TEST_USER_ID,
    "message_id": TEST_MESSAGE_ID,
    "content": "Hello, how are you?",
    "llm_types": ["deepseek", "grok", "gemini", "openai"]
}

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
def test_client(setup_and_teardown_firebase):
    """Create a test client for the FastAPI app."""
    return TestClient(app)

def test_send_message(test_client):
    """Test sending a message through the API."""
    response = test_client.post("/api/send_message", json=TEST_MESSAGE)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Message sent successfully"
    assert data["message_id"] == TEST_MESSAGE_ID

def test_send_message_invalid_data(test_client):
    """Test sending invalid message data."""
    invalid_message = {
        "user_id": TEST_USER_ID,
        "content": "Hello"  # Missing required fields
    }
    response = test_client.post("/api/send_message", json=invalid_message)
    assert response.status_code == 422  # Validation error

def test_analyze_responses(test_client):
    """Test analyzing LLM responses."""
    test_data = {
        "user_id": TEST_USER_ID,
        "message_id": TEST_MESSAGE_ID,
        "responses": {
            "deepseek": "Response from Deepseek",
            "grok": "Response from Grok",
            "gemini": "Response from Gemini",
            "openai": "Response from OpenAI"
        }
    }
    response = test_client.post("/api/analyze_responses", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert isinstance(data["analysis"], str)

def test_analyze_responses_no_data(test_client):
    """Test analyzing responses with no data."""
    response = test_client.post("/api/analyze_responses", json={})
    assert response.status_code == 422  # Validation error

def test_analyze_responses_invalid_format(test_client):
    """Test analyzing responses with invalid format."""
    invalid_data = {
        "user_id": TEST_USER_ID,
        "message_id": TEST_MESSAGE_ID,
        "responses": "not_a_dict"  # Invalid format
    }
    response = test_client.post("/api/analyze_responses", json=invalid_data)
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_llm_handlers():
    """Test LLM handler initialization and response generation."""
    factory = LLMHandlerFactory()
    for llm_type in ["deepseek", "grok", "gemini", "openai"]:
        handler = factory.get_handler(llm_type, "test_api_key")
        response = await handler.generate_response("Test message")
        assert isinstance(response, str)

def test_error_handling(test_client):
    """Test API error handling."""
    # Test invalid endpoint
    response = test_client.get("/api/invalid_endpoint")
    assert response.status_code == 404
    
    # Test method not allowed
    response = test_client.get("/api/send_message")
    assert response.status_code == 405

@pytest.mark.asyncio
async def test_firebase_integration(setup_and_teardown_firebase):
    """Test Firebase integration."""
    from firebase_admin import db
    
    # Test writing to Firebase
    ref = db.reference(f'messages/{TEST_USER_ID}/{TEST_MESSAGE_ID}')
    await ref.set({
        'content': TEST_MESSAGE['content'],
        'timestamp': {'serverValue': 'timestamp'}
    })
    
    # Test reading from Firebase
    data = await ref.get()
    assert data['content'] == TEST_MESSAGE['content']

@pytest.mark.asyncio
async def test_concurrent_requests(test_client):
    """Test handling concurrent API requests."""
    import asyncio
    
    async def make_request():
        return test_client.post("/api/send_message", json=TEST_MESSAGE)
    
    # Make 5 concurrent requests
    responses = await asyncio.gather(*[make_request() for _ in range(5)])
    
    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Message sent successfully" 