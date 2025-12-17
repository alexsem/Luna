
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
import os
import threading
import json
from general_functions import check_ollama_connection, get_mood_from_text, ask_ollama

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Allow CORS for development (React runs on 5173, Flask on 5000)
CORS(app)

# Global control for stopping generation
stop_event = threading.Event()

# Project Utils
from project_utils import list_projects, load_project, save_project, delete_project

@app.route('/projects', methods=['GET'])
def get_projects():
    return jsonify(list_projects())

@app.route('/projects', methods=['POST'])
def create_project():
    data = request.json
    name = data.get("name")
    history = data.get("history", [])
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    # Start a thread so we don't block? Or just wait?
    # Summarization might take a moment. Let's wait for now.
    summary = save_project(name, history)
    return jsonify({"status": "created", "summary": summary})

@app.route('/projects/<name>', methods=['DELETE'])
def remove_project(name):
    if delete_project(name):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Project not found"}), 404

@app.route('/projects/<name>/load', methods=['POST'])
def load_project_route(name):
    # Retrieve the summary to inject into frontend state
    summary = load_project(name)
    if summary:
        return jsonify({"summary": summary})
    return jsonify({"error": "Project not found"}), 404


@app.route('/health', methods=['GET'])
def health_check():
    """Check if the backend and Ollama are running."""
    ollama_status = check_ollama_connection()
    return jsonify({
        "status": "online",
        "ollama": "connected" if ollama_status else "disconnected"
    })

@app.route('/chat', methods=['POST'])
def chat():
    """
    Stream chat response.
    Expects JSON: { "prompt": "...", "history": [...] }
    """
    data = request.json
    prompt = data.get("prompt", "")
    history = data.get("history", [])
    
    stop_event.clear()

    def generate():
        # Using ask_ollama generator from general_functions
        # We need to adapt ask_ollama to respect stop_event or pass it down
        # For now, ask_ollama in general_functions might need a slight refactor to accept a stop_event
        # OR we check it here? ask_ollama yields chunks.
        
        full_response_text = ""
        
        try:
            for chunk in ask_ollama(prompt, history, stop_event):
                if stop_event.is_set():
                    yield json.dumps({"type": "stop"}) + "\n"
                    break
                
                full_response_text += chunk
                # SSE format or just raw JSON lines?
                # Using JSON lines is easier for fetch() reader
                yield json.dumps({"type": "chunk", "content": chunk}) + "\n"
            
            # After generation, calculate mood
            mood = get_mood_from_text(full_response_text)
            yield json.dumps({"type": "done", "mood": mood}) + "\n"
            
        except Exception as e:
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    return Response(stream_with_context(generate()), mimetype='application/json')

@app.route('/stop', methods=['POST'])
def stop_generation():
    stop_event.set()
    return jsonify({"status": "stopped"})

if __name__ == '__main__':
    port = int(os.getenv("BACKEND_PORT", 5000))
    app.run(debug=True, port=port)

