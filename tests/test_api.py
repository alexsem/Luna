import pytest
import json
from fastapi.testclient import TestClient
import sys
import os
import asyncio

# Add backend to path if needed
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import app
from unittest.mock import patch

@pytest.fixture
def client():
    return TestClient(app)

def test_api_health(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json()['status'] == 'online'

def test_chat_stream_structure(client):
    # Test that /chat sends events
    payload = {
        "prompt": "Hello Luna",
        "history": []
    }
    
    # Mock sentiment analysis and ask_ollama
    with patch("app.get_mood_from_text", return_value="happy"), \
         patch("app.ask_ollama") as mock_ask:
        
        async def mock_gen(*args, **kwargs):
            await asyncio.sleep(0.2) # Give mood task time to run
            yield "chunk", "Hello"
            yield "done", ""

        mock_ask.return_value = mock_gen()
        
        with client.stream("POST", "/chat", json=payload) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/x-ndjson"

            # Parse NDJSON stream
            events = []
            for line in response.iter_lines():
                if line.strip():
                    events.append(json.loads(line))

            print(f"DEBUG: events received: {events}")
            assert any(e["type"] == "mood" and e["content"] == "happy" for e in events)
            assert any(e["type"] == "chunk" and e["content"] == "Hello" for e in events)

def test_grammar_checker_payload(client):
    # Test /vault/fix-grammar
    payload = {"content": "I has a pencil."}
    
    with patch("app.ask_ollama") as mock_ask:
        async def mock_gen(*args, **kwargs):
            yield "chunk", "I have a pencil."

        mock_ask.return_value = mock_gen()

        response = client.post('/vault/fix-grammar', json=payload)
        assert response.status_code == 200
        assert response.json()["fixed"] == "I have a pencil."
        assert response.json()["original"] == "I has a pencil."
