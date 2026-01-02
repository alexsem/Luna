import requests
import json
import threading
import queue
from typing import List, Dict, Any, Optional, Generator, Union, Tuple
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
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for factual information, scientific data, or real-world knowledge to verify accuracy and consistency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for factual or scientific information."
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
) -> Generator[Tuple[str, str], None, None]:
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    context_msgs = chat_history[-MAX_HISTORY_MESSAGES:]
    for msg in context_msgs:
        messages.append({"role": "user" if msg.get("role") == "user" else "assistant", 
                         "content": msg.get("content", "")})
    messages.append({"role": "user", "content": prompt})
    
    chat_url = OLLAMA_URL.replace("/api/generate", "/api/chat")
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True, # ¡STREAMING SIEMPRE!
        "options": {"temperature": 0.7},
        "tools": TOOLS_SCHEMA if tool_handlers else None
    }

    try:
        with requests.post(chat_url, json=payload, stream=True) as response:
            response.raise_for_status()
            
            full_tool_calls = []
            
            for line in response.iter_lines():
                if stop_event and stop_event.is_set(): return
                if not line: continue
                
                chunk = json.loads(line)
                msg_chunk = chunk.get("message", {})
                
                # Si Ollama decide usar una herramienta (vía streaming)
                if msg_chunk.get("tool_calls"):
                    full_tool_calls.extend(msg_chunk["tool_calls"])
                
                # Si llega contenido de texto, lo enviamos YA al cliente
                content = msg_chunk.get("content", "")
                if content:
                    yield ("chunk", content)

                if chunk.get("done"):
                    break

            # Si hubo llamadas a herramientas, procesarlas y RECURSAR una sola vez
            if full_tool_calls:
                messages.append({"role": "assistant", "tool_calls": full_tool_calls})
                
                for tool_call in full_tool_calls:
                    func_name = tool_call["function"]["name"]
                    args = tool_call["function"]["arguments"]
                    yield ("thought", f"Luna consultando {func_name}...")
                    
                    if tool_handlers and func_name in tool_handlers:
                        result = tool_handlers[func_name](**args)
                        messages.append({
                            "role": "tool",
                            "content": json.dumps(result),
                            "name": func_name
                        })

                # Segunda llamada para procesar los resultados de la herramienta
                # Llamada recursiva simple o un nuevo loop de streaming
                yield from ask_ollama_final_step(messages, stop_event)

    except Exception as e:
        yield ("error", str(e))

def ask_ollama_final_step(messages, stop_event):
    # Función auxiliar para el streaming final tras la herramienta
    chat_url = OLLAMA_URL.replace("/api/generate", "/api/chat")
    payload = {"model": MODEL, "messages": messages, "stream": True}
    with requests.post(chat_url, json=payload, stream=True) as response:
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content: yield ("chunk", content)



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


