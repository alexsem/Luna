import os
import json

CONFIG_FILE = "config.json"

def get_vault_path():
    """Retrieves the VAULT_PATH from config.json, fallbacks to env."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                if config.get("vault_path"):
                    return config.get("vault_path")
        except Exception as e:
            print(f"Error reading config: {e}")
            
    return os.getenv("VAULT_PATH")

def set_vault_path(path):
    """Saves the VAULT_PATH to config.json."""
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        except:
            pass
            
    config["vault_path"] = path
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    return True

def is_safe_path(basedir, path, follow_symlinks=True):
    if follow_symlinks:
        return os.path.realpath(path).startswith(os.path.realpath(basedir))
    return os.path.abspath(path).startswith(os.path.abspath(basedir))

def list_vault_files(vault_path):
    """
    Returns a hierarchical tree structure of the vault.
    """
    if not vault_path or not os.path.exists(vault_path):
        return {"error": "Vault path not configured or does not exist."}

    def get_tree(path):
        d = {'name': os.path.basename(path), 'path': os.path.relpath(path, vault_path), 'type': 'directory', 'children': []}
        try:
            entries = os.listdir(path)
            # Skip hidden
            entries = [e for e in entries if not e.startswith('.')]
            
            for entry in sorted(entries):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    d['children'].append(get_tree(full_path))
                elif entry.lower().endswith(('.md', '.txt')):
                    d['children'].append({
                        'name': entry,
                        'path': os.path.relpath(full_path, vault_path),
                        'type': 'file'
                    })
        except Exception as e:
            print(f"Error reading path {path}: {e}")
            
        return d

    # Return children of the root to avoid showing the root folder itself in the sidebar
    tree = get_tree(vault_path)
    return tree['children']

def read_vault_file(vault_path, rel_path):
    if not vault_path: return None
    full_path = os.path.join(vault_path, rel_path)
    if not is_safe_path(vault_path, full_path):
        raise ValueError("Security Alert: Path traversal attempt blocked.")
    if not os.path.exists(full_path): return None
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()

def save_vault_file(vault_path, rel_path, content):
    if not vault_path: return False
    full_path = os.path.join(vault_path, rel_path)
    if not is_safe_path(vault_path, full_path):
        raise ValueError("Security Alert: Path traversal attempt blocked.")
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True

def create_vault_file(vault_path, rel_path):
    """
    Creates an empty file at the specified relative path.
    """
    if not vault_path: return False
    full_path = os.path.join(vault_path, rel_path)
    if not is_safe_path(vault_path, full_path):
        raise ValueError("Security Alert: Path traversal attempt blocked.")
    
    # Ensure .md extension if not provided
    if not full_path.endswith(('.md', '.txt')):
        full_path += ".md"
        rel_path += ".md"

    if os.path.exists(full_path):
        return False, "File already exists"

    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("") # Empty file
        return True, rel_path
    except Exception as e:
        return False, str(e)
