
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
CORS(app)

# Init RAG DB
from rag_chroma import init_db, sync_vault, search_knowledge_base
init_db()

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
    config = data.get("config", {}) 
    trigger_init = data.get("trigger_init", False)
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    project_data = save_project(name, history, config, trigger_init=trigger_init)
    return jsonify({"status": "created", "project": project_data})

@app.route('/projects/<name>', methods=['PATCH'])
def update_project_config(name):
    data = request.json
    config = data.get("config")
    history = data.get("history", []) # Usually we just want to update config
    
    # Load old project to keep summary if not provided
    old = load_project(name)
    if not old: return jsonify({"error": "Project not found"}), 404
    
    # We use save_project to overwrite with new config
    project_data = save_project(name, history or old.get("summary"), config)
    return jsonify({"status": "updated", "project": project_data})

@app.route('/projects/<name>', methods=['DELETE'])
def remove_project(name):
    delete_files = request.args.get("delete_files") == "true"
    if delete_project(name, delete_physical=delete_files):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Project not found"}), 404

@app.route('/projects/<name>/load', methods=['POST'])
def load_project_route(name):
    project_data = load_project(name)
    if project_data:
        # Switch Vault Path if exists in config
        vp = project_data.get("config", {}).get("vault_path")
        if vp:
            set_vault_path(vp)
            
        return jsonify(project_data)
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
        # Define tools
        tool_handlers = {
            "search_vault": lambda query: search_knowledge_base(query)
        }
        
        # TASK HANDLING: Check for Writer Mode tags
        # We prepend a system instruction to the last message or prompt
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
            for chunk in ask_ollama(current_prompt, history, stop_event, tool_handlers):
                if stop_event.is_set():
                    yield json.dumps({"type": "stop"}) + "\n"
                    break
                
                # check if chunk starts with [Error:
                if chunk.startswith("[Error:"):
                    yield json.dumps({"type": "error", "content": chunk}) + "\n"
                    break

                yield json.dumps({"type": "chunk", "content": chunk}) + "\n"
                
            # Note: We can accumulate text and calc mood, or just skip mood for tool responses for now
            mood = "neutral" 
            yield json.dumps({"type": "done", "mood": mood}) + "\n"
            
        except Exception as e:
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    return Response(stream_with_context(generate()), mimetype='application/json')

@app.route('/stop', methods=['POST'])
def stop_generation():
    stop_event.set()
    return jsonify({"status": "stopped"})


# Vault Integration
from vault_utils import get_vault_path, list_vault_files, read_vault_file, set_vault_path

@app.route('/config', methods=['GET'])
def get_config():
    return jsonify({"vault_path": get_vault_path()})

@app.route('/config', methods=['POST'])
def update_config():
    data = request.json
    path = data.get("vault_path")
    if not path:
        return jsonify({"error": "Path required"}), 400
    
    if set_vault_path(path):
        return jsonify({"status": "updated", "vault_path": path})
    return jsonify({"error": "Failed to save"}), 500

@app.route('/vault/files', methods=['GET'])
def get_vault_files():
    vault_path = get_vault_path()
    if not vault_path:
        return jsonify({"error": "VAULT_PATH not loaded in environment"}), 400
    
    files = list_vault_files(vault_path)
    if isinstance(files, dict) and "error" in files:
         return jsonify(files), 400
         
    return jsonify(files)

@app.route('/vault/read', methods=['POST'])
def read_vault_file_route():
    data = request.json
    rel_path = data.get("path")
    vault_path = get_vault_path()
    
    if not vault_path:
        return jsonify({"error": "VAULT_PATH not loaded"}), 400
    if not rel_path:
        return jsonify({"error": "No path provided"}), 400
        
    try:
        content = read_vault_file(vault_path, rel_path)
        if content is None:
            return jsonify({"error": "File not found"}), 404
        return jsonify({"content": content})
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from vault_utils import save_vault_file

@app.route('/vault/save', methods=['POST'])
def save_vault_file_route():
    data = request.json
    rel_path = data.get("path")
    content = data.get("content")
    vault_path = get_vault_path()

    if not vault_path:
        return jsonify({"error": "VAULT_PATH not loaded"}), 400
    if not rel_path or content is None:
        return jsonify({"error": "Path and content are required"}), 400

    try:
        save_vault_file(vault_path, rel_path, content)
        return jsonify({"status": "saved", "path": rel_path})
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/vault/create', methods=['POST'])
def create_vault_file_route():
    data = request.json
    rel_path = data.get("path")
    vault_path = get_vault_path()
    if not vault_path: return jsonify({"error": "Vault path not set"}), 400
    if not rel_path: return jsonify({"error": "Path required"}), 400
    
    from vault_utils import create_vault_file
    success, result = create_vault_file(vault_path, rel_path)
    if success:
        return jsonify({"status": "created", "path": result})
    return jsonify({"error": result}), 400

@app.route('/vault/fix-grammar', methods=['POST'])
def fix_grammar_route():
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
def sync_vault_route():
    vault_path = get_vault_path()
    if not vault_path:
        return jsonify({"error": "VAULT_PATH not set"}), 400

    def generate_progress():
        for progress in sync_vault(vault_path):
            yield json.dumps(progress) + "\n"
            
    return Response(stream_with_context(generate_progress()), mimetype='application/json')


if __name__ == '__main__':
    port = int(os.getenv("BACKEND_PORT", 5000))
    app.run(debug=True, port=port)

