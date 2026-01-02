import pytest
import json
from app import app
from unittest.mock import patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_health(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json['status'] == 'online'

def test_chat_stream_structure(client, mock_ollama):
    # Test that /chat sends mood first, then chunks
    payload = {
        "prompt": "Hello Luna",
        "history": []
    }
    
    # Mock sentiment analysis to return 'happy'
    with patch("app.get_mood_from_text", return_value="happy"):
        response = client.post('/chat', json=payload)
        assert response.status_code == 200
        
        # Parse NDJSON stream
        lines = response.data.decode().split('\n')
        events = [json.loads(l) for l in lines if l.strip()]
        
        # First event should be mood
        assert events[0]["type"] == "mood"
        assert events[0]["content"] == "happy"
        
        # Subsequent events should be chunks
        assert any(e["type"] == "chunk" for e in events)

def test_grammar_checker_payload(client, mock_ollama):
    # Test /vault/fix-grammar
    payload = {"content": "I has a pencil."}
    
    response = client.post('/vault/fix-grammar', json=payload)
    assert response.status_code == 200
    assert "fixed" in response.json
    assert "original" in response.json
