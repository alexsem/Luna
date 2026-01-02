import os
import json
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)

class VaultService:
    def __init__(self) -> None:
        self.config_file = "config.json"
        self.vault_path = self._load_initial_vault_path()
        logger.info(f"VaultService initialized. Current vault: {self.vault_path}")

    def _load_initial_vault_path(self) -> Optional[str]:
        """Retrieves the VAULT_PATH from config.json, fallbacks to env."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    if config.get("vault_path"):
                        return config.get("vault_path")
            except Exception as e:
                logger.error(f"Error reading config: {e}")
                
        return os.getenv("VAULT_PATH")

    def set_vault_path(self, path: str) -> bool:
        """Updates and saves the vault path."""
        config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except:
                pass
                
        config["vault_path"] = path
        self.vault_path = path
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Vault path updated to: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save vault path: {e}")
            return False

    def is_safe_path(self, path: str, follow_symlinks: bool = True) -> bool:
        """Prevents path traversal attacks."""
        if not self.vault_path:
            return False
            
        if follow_symlinks:
            return os.path.realpath(path).startswith(os.path.realpath(self.vault_path))
        return os.path.abspath(path).startswith(os.path.abspath(self.vault_path))

    def list_files(self) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """Returns a hierarchical tree structure of the vault."""
        if not self.vault_path or not os.path.exists(self.vault_path):
            return {"error": "Vault path not configured or does not exist."}

        def get_tree(path):
            d = {'name': os.path.basename(path), 'path': os.path.relpath(path, self.vault_path), 'type': 'directory', 'children': []}
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
                            'path': os.path.relpath(full_path, self.vault_path),
                            'type': 'file'
                        })
            except Exception as e:
                logger.error(f"Error reading path {path}: {e}")
                
            return d

        # Return children of the root
        tree = get_tree(self.vault_path)
        return tree['children']

    def read_file(self, rel_path: str) -> Optional[str]:
        if not self.vault_path: return None
        full_path = os.path.normpath(os.path.join(self.vault_path, rel_path))
        
        if not self.is_safe_path(full_path):
            logger.warning(f"Security Alert: Path traversal attempt blocked for path: {rel_path}")
            raise ValueError("Security Alert: Path traversal attempt blocked.")
            
        if not os.path.exists(full_path): return None
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {full_path}: {e}")
            return None

    def save_file(self, rel_path: str, content: str) -> bool:
        if not self.vault_path: return False
        full_path = os.path.normpath(os.path.join(self.vault_path, rel_path))
        
        if not self.is_safe_path(full_path):
            logger.warning(f"Security Alert: Path traversal attempt blocked for path: {rel_path}")
            raise ValueError("Security Alert: Path traversal attempt blocked.")
            
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error saving file {full_path}: {e}")
            return False

    def create_file(self, rel_path: str) -> Tuple[bool, str]:
        if not self.vault_path: return False, "No vault path"
        
        # Ensure .md extension if not provided
        if not rel_path.endswith(('.md', '.txt')):
            rel_path += ".md"
            
        full_path = os.path.normpath(os.path.join(self.vault_path, rel_path))
        
        if not self.is_safe_path(full_path):
            raise ValueError("Security Alert: Path traversal attempt blocked.")
            
        if os.path.exists(full_path):
            return False, "File already exists"

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write("") 
            return True, rel_path
        except Exception as e:
            logger.error(f"Error creating file {full_path}: {e}")
            return False, str(e)

# Global instance
vault_service = VaultService()
