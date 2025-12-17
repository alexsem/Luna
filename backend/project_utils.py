
import os
import json
from general_functions import ask_ollama

PROJECTS_DIR = "saved_projects"

def ensure_project_dir():
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)

def list_projects():
    ensure_project_dir()
    projects = []
    for filename in os.listdir(PROJECTS_DIR):
        if filename.endswith(".txt"):
            projects.append(filename[:-4]) # Remove .txt
    return sorted(projects)

def load_project(name):
    ensure_project_dir()
    filepath = os.path.join(PROJECTS_DIR, f"{name}.txt")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return None

def delete_project(name):
    ensure_project_dir()
    filepath = os.path.join(PROJECTS_DIR, f"{name}.txt")
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False

def save_project(name, history):
    """
    Summarizes the chat history and saves it to a file.
    """
    ensure_project_dir()
    
    # Generate Summary
    # We construct a specific prompt for summarization
    summary_prompt = (
        "Analyze the following conversation and create a concise but detailed summary "
        "of the creative ideas, plot points, and character details discussed. "
        "Focus on saving the 'State' of the project so we can resume later.\n\n"
    )
    
    # We reuse ask_ollama but we need to consume the generator
    # We pass an empty history for the summarization context itself to avoid confusion, 
    # or we just pass the history as the "prompt context"?
    # Actually ask_ollama builds the prompt using the history. 
    # Let's just create a raw request or use ask_ollama nicely.
    # To keep it simple, we'll implement a synchronous helper here or consume ask_ollama.
    
    # Consuming ask_ollama:
    # prompt="Generate Summary...", chat_history=history
    # But ask_ollama appends prompt to history. 
    pass
    # Wait, ask_ollama uses the history variables to build the context string.
    # If we want to summarize the history, "prompt" should be the request to summarize.
    
    full_text = ""
    # We can use a special system instruction or just append the request.
    prompt = "Please summarize the entire conversation above, focusing on key creative decisions, plot points, and characters. format it as a project memory."
    
    # ask_ollama yields chunks
    for chunk in ask_ollama(prompt, history):
        full_text += chunk
        
    filepath = os.path.join(PROJECTS_DIR, f"{name}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    return full_text
