import os
import json
import shutil
from general_functions import ask_ollama

PROJECTS_DIR = "saved_projects"

def ensure_project_dir():
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)

def list_projects():
    ensure_project_dir()
    projects = []
    for filename in os.listdir(PROJECTS_DIR):
        if filename.endswith(".json"):
            projects.append(filename[:-5])
        elif filename.endswith(".txt"):
            projects.append(filename[:-4])
    return sorted(list(set(projects))) # Dedup and sort

def load_project(name):
    ensure_project_dir()
    json_path = os.path.join(PROJECTS_DIR, f"{name}.json")
    txt_path = os.path.join(PROJECTS_DIR, f"{name}.txt")
    
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            return {"summary": f.read(), "config": {}}
    return None

def init_workspace(base_path, project_name):
    """
    Creates the project folder and the World/Novel subfolders.
    """
    try:
        project_path = os.path.join(base_path, project_name)
        os.makedirs(os.path.join(project_path, "World"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "Novel"), exist_ok=True)
        return project_path
    except Exception as e:
        print(f"Error initializing workspace: {e}")
        return None

def delete_project(name, delete_physical=False):
    ensure_project_dir()
    json_path = os.path.join(PROJECTS_DIR, f"{name}.json")
    txt_path = os.path.join(PROJECTS_DIR, f"{name}.txt")
    
    # Load config to find path if we need to delete physical
    if delete_physical:
        project_data = load_project(name)
        if project_data:
            vp = project_data.get("config", {}).get("vault_path")
            if vp and os.path.exists(vp):
                try:
                    shutil.rmtree(vp)
                except Exception as e:
                    print(f"Error deleting physical files: {e}")

    deleted = False
    if os.path.exists(json_path):
        os.remove(json_path)
        deleted = True
    if os.path.exists(txt_path):
        os.remove(txt_path)
        deleted = True
    return deleted

def save_project(name, history, config=None, trigger_init=False):
    """
    Summarizes the chat history and saves it to a JSON file with config.
    """
    ensure_project_dir()
    
    # Initialization Logic
    if trigger_init and config and config.get("vault_path"):
        # We assume vault_path given by user is the BASE path for new projects
        # or the exact path they want. 
        # User said: "you will create a folder on that path and also create the World and Novel folders"
        base_path = config["vault_path"]
        new_path = init_workspace(base_path, name)
        if new_path:
            config["vault_path"] = new_path # Update to the specific project folder

    prompt = "Please summarize the entire conversation above, focusing on key creative decisions, plot points, and characters. format it as a project memory."
    
    full_text = ""
    for chunk in ask_ollama(prompt, history):
        full_text += chunk
        
    project_data = {
        "summary": full_text,
        "config": config or {}
    }
    
    filepath = os.path.join(PROJECTS_DIR, f"{name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=4)
    
    # Remove old txt if it exists to clean up
    old_txt = os.path.join(PROJECTS_DIR, f"{name}.txt")
    if os.path.exists(old_txt): os.remove(old_txt)
    
    return project_data
