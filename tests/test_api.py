import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_chat_empty_message():
    response = client.post("/api/chat", json={"message": ""})
    # Pydantic validation should fail this before reaching the endpoint logic
    assert response.status_code == 422 

def test_chat_whitespace_message():
    response = client.post("/api/chat", json={"message": "   "})
    # Our manual validation in the endpoint should catch this
    assert response.status_code == 400
    assert response.json() == {"detail": "Message cannot be empty"}

# We won't test the actual Gemini API call in CI to avoid hitting rate limits or needing keys,
# but we test the structure of the request.
# For a real project, we would mock the `get_gemini_response` function here.
