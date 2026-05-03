import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app

client = TestClient(app)

# Helper to clear slowapi limits for testing
@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    
def test_security_headers():
    response = client.get("/api/health")
    assert "Strict-Transport-Security" in response.headers
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers

def test_chat_empty_message():
    response = client.post("/api/chat", json={"message": ""})
    # Pydantic validation catches this
    assert response.status_code == 422 

def test_chat_whitespace_message():
    response = client.post("/api/chat", json={"message": "   "})
    # Custom endpoint logic catches this
    assert response.status_code == 400
    assert response.json() == {"detail": "Message cannot be empty"}

def test_chat_too_long_message():
    long_msg = "A" * 1001
    response = client.post("/api/chat", json={"message": long_msg})
    # Pydantic max_length=1000
    assert response.status_code == 422

@patch("backend.main.get_gemini_response", new_callable=AsyncMock)
def test_chat_success(mock_gemini):
    mock_gemini.return_value = "This is a mock response from Gemini."
    response = client.post("/api/chat", json={"message": "How do elections work?"})
    
    assert response.status_code == 200
    assert response.json() == {"reply": "This is a mock response from Gemini."}
    mock_gemini.assert_called_once_with("How do elections work?")

def test_rate_limiting():
    # Health check limit is 60/minute, Chat is 20/minute.
    # We will spam the chat endpoint to hit the limit.
    # Note: We must mock gemini to avoid actually making 20 API calls.
    with patch("backend.main.get_gemini_response", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = "Mock"
        for _ in range(20):
            response = client.post("/api/chat", json={"message": "test"})
            assert response.status_code == 200
            
        # The 21st request should fail
        response = client.post("/api/chat", json={"message": "test"})
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.text
