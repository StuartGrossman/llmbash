import pytest
from fastapi.testclient import TestClient
from main import app
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json

# Initialize test client
client = TestClient(app)

def test_message_with_id():
    # Test data
    test_message = {
        "content": "Test message",
        "id": "test123"
    }
    
    # Send POST request
    response = client.post("/api/message", json=test_message)
    
    # Check response
    assert response.status_code == 200
    assert response.json()["response"] == f"Message saved with ID: {test_message['id']}"
    
    # Verify data in Firebase
    ref = db.reference(f'/question/{test_message["id"]}')
    data = ref.get()
    
    assert data is not None
    assert data["content"] == test_message["content"]
    assert "timestamp" in data

def test_message_without_id():
    # Test data without ID
    test_message = {
        "content": "Test message"
    }
    
    # Send POST request
    response = client.post("/api/message", json=test_message)
    
    # Check response (should fail)
    assert response.status_code == 422  # Validation error 