import requests
import json
import threading
import queue
from typing import List, Dict, Any, Optional, Generator, Union
from transformers import pipeline


import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("MODEL", "llama3.2")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", 10))
APP_LANG = os.getenv("APP_LANG", "ENG")

if APP_LANG == "ESP":
    MODEL_NAME = "finiteautomata/beto-sentiment-analysis"
elif APP_LANG == "ENG":
    MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"
else:
    # Default to ENG model if unknown
    MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

emotion_classifier = pipeline(
    "text-classification",
    model=MODEL_NAME
)

SYSTEM_PROMPT = """
You are "Luna," an advanced and highly specialized dual-purpose LLM designed to be an expert companion.

***LANGUAGE CONSTRAINT: ALL OUTPUTS MUST BE IN ENGLISH.***

### 1. ROLE:
    CREATIVE WRITING ASSISTANT: For queries about scripts, novels, plotting, character development, or prose 
    improvement, adopt a tone that is **creative, inspirational, and detailed**.

### 2. FORMAT & STYLE:
    * Use **neutral English**.
    * Your gender is female, make sure to use it when you refer to yourself. 
    * Be **direct and helpful**. Avoid unnecessary conversational filler.

### 3. CONVERSATION FLOW:
    * Maintain context and coherence with the chat history.
    
"""



def check_ollama_connection() -> bool:
    try:
        base_url = OLLAMA_URL.replace("/api/generate", "")
        response = requests.get(base_url, timeout=2)
        return True
    except:
        return False



# Refactored for Web API

# Tool Definitions
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_vault",
            "description": "Search the local knowledge base (Obsidian Vault) for specific information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant notes."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def ask_ollama(
    prompt: str, 
    chat_history: List[Dict[str, Any]], 
    stop_event: Optional[threading.Event] = None, 
    tool_handlers: Optional[Dict[str, Any]] = None
) -> Generator[str, None, None]:
    """
    Agentic generator using /api/chat. Supported Tool Calling.
    """
    # Prepare messages
    messages = []
    
    # Add System Prompt
    messages.append({"role": "system", "content": SYSTEM_PROMPT})
    
    # Add History (last N)
    context_msgs = chat_history[-MAX_HISTORY_MESSAGES:]
    for msg in context_msgs:
        role = "user" if msg.get("role") == "user" else "assistant"
        content = msg.get("content", "")
        messages.append({"role": role, "content": content})
        
    # Add current prompt
    messages.append({"role": "user", "content": prompt})
    
    chat_url = OLLAMA_URL.replace("/api/generate", "/api/chat")
    
    # Step 1: Initial Request (Non-streaming to detect tools safely)
    # Note: We prioritize tools if handlers provided
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7}
    }
    
    if tool_handlers:
        payload["tools"] = TOOLS_SCHEMA

    try:
        response = requests.post(chat_url, json=payload)
        response.raise_for_status()
        resp_json = response.json()
        message = resp_json.get("message", {})
        
        # Check for tool calls
        if message.get("tool_calls"):
            # Tool Usage Detected
            tool_calls = message["tool_calls"]
            messages.append(message) # Add the assistant's tool_call message
            
            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                args = tool_call["function"]["arguments"]
                
                # Execute Tool
                if tool_handlers and func_name in tool_handlers:
                    # Notify user we are using the tool (yield meta event?)
                    # For now just do it silently or yield a special event if app supports it
                    try:
                        result = tool_handlers[func_name](**args)
                        content = json.dumps(result)
                    except Exception as e:
                        content = f"Error executing tool: {e}"
                else:
                    content = "Tool not found or not implemented."

                # Append Tool Result
                messages.append({
                    "role": "tool",
                    "content": content,
                    "name": func_name
                })
            
            # Step 2: Follow-up Request (Streaming final answer)
            payload["messages"] = messages
            payload["stream"] = True
            # Remove tools for final answer to force text generation? 
            # Or keep them allowed? Usually keep them allowed for multi-step, but for now remove to prevent loop.
            del payload["tools"] 

            with requests.post(chat_url, json=payload, stream=True) as stream_resp:
                stream_resp.raise_for_status()
                for line in stream_resp.iter_lines():
                    if stop_event and stop_event.is_set():
                        break
                    if line:
                        chunk_json = json.loads(line)
                        content = chunk_json.get("message", {}).get("content", "")
                        if content:
                            yield content
        else:
            # No tool use, just yield the content we got (or stream it again if preferred)
            # Since we did stream=False initially, we have the full text.
            # We can yield it chunnked or all at once.
            content = message.get("content", "")
            yield content

    except Exception as e:
        yield f"[Error: {str(e)}]"



def get_mood_from_text(text: str) -> str:
    """
    Analyzes the text using the loaded emotion_classifier and returns 
    one of the three supported moods: 'happy', 'sad', 'neutral'.
    """
    if not text:
        return "neutral"
        
    # FORCE 'thinking' for specialized task prompts
    if text.strip().startswith("#task:"):
        return "thinking"

    try:
        # The classifier returns a list of dicts, e.g. [{'label': 'joy', 'score': 0.95}]
        # Truncate text if too long for the model? Pipeline handles it usually but good to be safe.
        results = emotion_classifier(text[:512]) 
        
        if not results:
            return "neutral"
            
        top_emotion = results[0]['label']
        
        # Mappings for j-hartmann/emotion-english-distilroberta-base:
        # labels: anger, disgust, fear, joy, neutral, sadness, surprise
        
        if top_emotion == "joy":
            return "happy"
        elif top_emotion == "sadness":
            return "sad"
        elif top_emotion == "anger":
            return "angry"
        elif top_emotion == "fear":
            return "scared"
        elif top_emotion == "surprise":
            return "surprised"
        elif top_emotion == "disgust":
            return "scared" # Fallback for disgust
        else:
            return "neutral"
            
    except Exception as e:
        print(f"Error in mood analysis: {e}")
        return "neutral"


