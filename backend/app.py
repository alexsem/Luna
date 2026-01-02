
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
import os
import threading
import json
from typing import List, Dict, Any, Optional, Union, Tuple, Generator
from general_functions import check_ollama_connection, get_mood_from_text, ask_ollama

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Allow CORS for development (React runs on 5173, Flask on 5000)
CORS(app)
CORS(app)

# Init Services
from project_service import project_service
from vault_service import vault_service
from knowledge_base_service import kb_service

kb_service.init_db()

# Global control for stopping generation
stop_event = threading.Event()

@app.route('/projects', methods=['GET'])
def get_projects() -> Response:
    return jsonify(project_service.list_projects())

@app.route('/projects', methods=['POST'])
def create_project() -> Response:
    data = request.json
    name = data.get("name")
    history = data.get("history", [])
    config = data.get("config", {}) 
    trigger_init = data.get("trigger_init", False)
    description = data.get("description")
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    project_data = project_service.save_project(name, history, config, trigger_init=trigger_init, description=description)
    return jsonify({"status": "created", "project": project_data})

@app.route('/projects/<name>', methods=['PATCH'])
def update_project_config(name: str) -> Response:
    data = request.json
    config = data.get("config", {})
    history = data.get("history", [])
    
    # Check if description is passed in config or root
    description = config.pop("description", None) or data.get("description")
    
    # Load old project to verify existence
    old = project_service.load_project(name)
    if not old: return jsonify({"error": "Project not found"}), 404
    
    # If no new description, fallback to the one in the file
    if description is None:
        description = old.get("description")

    # We use save_project to overwrite with new config/description
    project_data = project_service.save_project(name, history, config, description=description)
    return jsonify({"status": "updated", "project": project_data})

@app.route('/projects/<name>', methods=['DELETE'])
def remove_project(name: str) -> Response:
    delete_files = request.args.get("delete_files") == "true"
    if project_service.delete_project(name, delete_physical=delete_files):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Project not found"}), 404

@app.route('/projects/<name>/load', methods=['POST'])
def load_project_route(name: str) -> Response:
    project_data = project_service.load_project(name)
    if project_data:
        # Switch Vault Path if exists in config
        vp = project_data.get("config", {}).get("vault_path")
        if vp:
            vault_service.set_vault_path(vp)
            
        return jsonify(project_data)
    return jsonify({"error": "Project not found"}), 404


@app.route('/health', methods=['GET'])
def health_check() -> Response:
    """Check if the backend and Ollama are running."""
    ollama_status = check_ollama_connection()
    return jsonify({
        "status": "online",
        "ollama": "connected" if ollama_status else "disconnected"
    })

@app.route('/chat', methods=['POST'])
def chat() -> Response:
    """
    Stream chat response.
    Expects JSON: { "prompt": "...", "history": [...] }
    """
    data = request.json
    prompt = data.get("prompt", "")
    history = data.get("history", [])
    
    stop_event.clear()

        
    def generate():
        # Step 1: Immediate Empathetic Mood Analysis
        # We analyze what the USER wrote to set Luna's expression as she starts thinking
        mood = get_mood_from_text(prompt)
        yield json.dumps({"type": "mood", "content": mood}) + "\n"
        
        # Step 2: Define tools
        tool_handlers = {
            "search_vault": lambda query: kb_service.search(query)
        }
        
        # TASK HANDLING: Check for Writer Mode tags
        task_prompt = ""
        if prompt.startswith("#task:fact_check"):
            task_prompt = (
                "SYSTEM: You are a rigorous Fact Checker. "
                "1. Analyze the user's text. "
                "2. Identify every factual claim. "
                "3. Use the `search_vault` tool to find evidence for each claim. "
                "4. OUTPUT REPORT: List each claim and mark it [VERIFIED] or [CONTRADICTED] with a citation to the source file. "
                "If no evidence is found, mark [NO EVIDENCE].\n\n"
            )
        elif prompt.startswith("#task:fix_grammar"):
            task_prompt = (
                "SYSTEM: You are a Professional Editor. "
                "Improve the grammar, flow, and clarity of the text. "
                "Maintain the author's voice but remove redundancy. "
                "Output ONLY the rewritten text, followed by a bullet list of changes made.\n\n"
            )

        # Apply task prompt
        current_prompt = task_prompt + prompt if task_prompt else prompt

        try:
            full_response = ""
            for chunk in ask_ollama(current_prompt, history, stop_event, tool_handlers):
                if stop_event.is_set():
                    yield json.dumps({"type": "stop"}) + "\n"
                    break
                
                if chunk.startswith("[Error:"):
                    yield json.dumps({"type": "error", "content": chunk}) + "\n"
                    break
                
                full_response += chunk
                yield json.dumps({"type": "chunk", "content": chunk}) + "\n"
                
            yield json.dumps({"type": "done"}) + "\n"
            
        except Exception as e:
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    return Response(stream_with_context(generate()), mimetype='application/json')

@app.route('/stop', methods=['POST'])
def stop_generation() -> Response:
    stop_event.set()
    return jsonify({"status": "stopped"})


# Vault Routes
@app.route('/config', methods=['GET'])
def get_config() -> Response:
    return jsonify({"vault_path": vault_service.vault_path})

@app.route('/config', methods=['POST'])
def update_config() -> Response:
    data = request.json
    path = data.get("vault_path")
    if not path:
        return jsonify({"error": "Path required"}), 400
    
    if vault_service.set_vault_path(path):
        return jsonify({"status": "updated", "vault_path": path})
    return jsonify({"error": "Failed to save"}), 500

@app.route('/vault/files', methods=['GET'])
def get_vault_files() -> Response:
    files = vault_service.list_files()
    if isinstance(files, dict) and "error" in files:
         return jsonify(files), 400
         
    return jsonify(files)

@app.route('/vault/read', methods=['POST'])
def read_vault_file_route() -> Response:
    data = request.json
    rel_path = data.get("path")
    
    if not rel_path:
        return jsonify({"error": "No path provided"}), 400
        
    try:
        content = vault_service.read_file(rel_path)
        if content is None:
            return jsonify({"error": "File not found"}), 404
        return jsonify({"content": content})
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/vault/save', methods=['POST'])
def save_vault_file_route() -> Response:
    data = request.json
    rel_path = data.get("path")
    content = data.get("content")

    if not rel_path or content is None:
        return jsonify({"error": "Path and content are required"}), 400

    try:
        if vault_service.save_file(rel_path, content):
            return jsonify({"status": "saved", "path": rel_path})
        return jsonify({"error": "Failed to save file"}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/vault/create', methods=['POST'])
def create_vault_file_route() -> Response:
    data = request.json
    rel_path = data.get("path")
    if not rel_path: return jsonify({"error": "Path required"}), 400
    
    success, result = vault_service.create_file(rel_path)
    if success:
        return jsonify({"status": "created", "path": result})
    return jsonify({"error": result}), 400

@app.route('/vault/fix-grammar', methods=['POST'])
def fix_grammar_route() -> Response:
    data = request.json
    content = data.get("content")
    if not content:
        return jsonify({"error": "Content required"}), 400

    # Strict prompt to get ONLY the corrected text
    prompt = (
        "Correct the grammar, spelling, and punctuation of the following text. "
        "Maintain the original tone and style. "
        "IMPORTANT: RETURN ONLY THE CORRECTED TEXT. DO NOT EXPLAIN OR ADD CONVERSATIONAL FILLER.\n\n"
        "### TEXT TO CORRECT:\n"
        f"{content}"
    )

    from general_functions import ask_ollama
    # We use ask_ollama but we only need the total text
    corrected_text = ""
    try:
        for chunk in ask_ollama(prompt, []): # Empty history to focus only on the text
            corrected_text += chunk
        
        return jsonify({"original": content, "fixed": corrected_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/vault/sync', methods=['POST'])
def sync_vault_route() -> Response:
    vault_path = vault_service.vault_path
    if not vault_path:
        return jsonify({"error": "Vault path not set"}), 400

    def generate_progress():
        for progress in kb_service.sync_vault(vault_path):
            yield json.dumps(progress) + "\n"
            
    return Response(stream_with_context(generate_progress()), mimetype='application/json')


if __name__ == '__main__':
    port = int(os.getenv("BACKEND_PORT", 5000))
    app.run(debug=True, port=port)

