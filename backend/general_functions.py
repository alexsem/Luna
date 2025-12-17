import requests
import json
import threading
import queue
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



def check_ollama_connection():
    try:
        base_url = OLLAMA_URL.replace("/api/generate", "")
        response = requests.get(base_url, timeout=2)
        return True
    except:
        return False



# Refactored for Web API
def ask_ollama(prompt, chat_history, stop_event=None):
    """
    Generator that yields chunks of text from Ollama.
    """
    # Context Management: Keep only the last N messages
    context_messages = chat_history[-MAX_HISTORY_MESSAGES:]
    
    # Reconstruct conversation for context
    conversation_text = ""
    for msg in context_messages:
        # standardizing role names for the prompt
        role = "USUARIO" if msg.get("role") == "user" or msg.get("type") == "user" else "LUNA"
        content = msg.get("content") or msg.get("text") or ""
        conversation_text += f"{role}: {content}\n"
    
    full_prompt = SYSTEM_PROMPT + "\n\n" + conversation_text + "\nUSUARIO: " + prompt
    data = {"model": MODEL, "prompt": full_prompt, "stream": True}

    with requests.post(OLLAMA_URL, json=data, stream=True) as response:
        response.raise_for_status()

        for line in response.iter_lines():
            if stop_event and stop_event.is_set():
                break
            if line:
                try:
                    json_chunk = json.loads(line)
                    chunk = json_chunk.get("response", "")
                    
                    if chunk:
                        yield chunk

                    if json_chunk.get("done"):
                        break

                except json.JSONDecodeError:
                    continue


def get_mood_from_text(text):
    """
    Analyzes the text using the loaded emotion_classifier and returns 
    one of the three supported moods: 'happy', 'sad', 'neutral'.
    """
    if not text:
        return "neutral"
        
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
        elif top_emotion in ["sadness", "anger", "fear", "disgust"]:
            return "sad"
        else:
            return "neutral"
            
    except Exception as e:
        print(f"Error in mood analysis: {e}")
        return "neutral"


