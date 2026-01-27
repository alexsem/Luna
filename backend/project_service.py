import os
import json
import shutil
import logging
from typing import List, Dict, Any, Optional, Union
from general_functions import ask_ollama

logger = logging.getLogger(__name__)

class ProjectService:
    _instance = None

    def __new__(cls) -> "ProjectService":
        if cls._instance is None:
            cls._instance = super(ProjectService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        
        # Root directory for general config
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.registry_file = os.path.join(self.base_dir, "known_projects.json")
        self._initialized = True
        logger.info(f"ProjectService initialized with registry: {self.registry_file}")

    def _load_registry(self) -> Dict[str, str]:
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading registry: {e}")
                return {}
        return {}

    def _save_registry(self, registry: Dict[str, str]) -> None:
        try:
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving registry: {e}")

    def list_projects(self) -> List[str]:
        registry = self._load_registry()
        existing_projects = []
        updated_registry = {}
        
        for name, path in registry.items():
            # Check if the project file still exists at the registered path
            project_file = os.path.join(path, f"{name}.json")
            if os.path.exists(project_file):
                existing_projects.append(name)
                updated_registry[name] = path
        
        # Clean up registry if any projects were moved/deleted
        if len(updated_registry) != len(registry):
            self._save_registry(updated_registry)
            
        return sorted(existing_projects)

    def load_project(self, name: str) -> Optional[Dict[str, Any]]:
        registry = self._load_registry()
        path = registry.get(name)
        if not path:
            return None
            
        project_file = os.path.join(path, f"{name}.json")
        if os.path.exists(project_file):
            try:
                with open(project_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Ensure path is in config for safety
                    if "config" not in data: data["config"] = {}
                    data["config"]["vault_path"] = path
                    return data
            except Exception as e:
                logger.error(f"Error loading project {name}: {e}")
                return None
        return None

    async def save_project(self, name: str, history: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None, trigger_init: bool = False, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Saves project metadata locally to its vault path.
        Registers the project path in the central registry.
        """
        if not config or not config.get("vault_path"):
            raise ValueError("Project vault path is required for saving.")

        vault_path = config["vault_path"]
        
        # Initialization Logic
        if trigger_init:
            new_path = self.init_workspace(vault_path, name)
            if new_path:
                vault_path = new_path
                config["vault_path"] = vault_path

        summary = ""
        if not description and history and isinstance(history, list):
            prompt = "Please summarize the entire conversation above, focusing on key creative decisions, plot points, and characters. format it as a project memory."
            try:
                async for event_type, content in ask_ollama(prompt, history):
                    if event_type == "chunk":
                        summary += content
            except Exception as e:
                logger.warning(f"Failed to generate AI summary for project {name}: {e}")
        
        project_data = {
            "description": description or summary,
            "summary": summary,
            "config": config or {}
        }
        
        # Ensure project directory exists
        if not os.path.exists(vault_path):
            os.makedirs(vault_path, exist_ok=True)
            
        # Save locally to project folder
        filepath = os.path.join(vault_path, f"{name}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(project_data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving project file {filepath}: {e}")
            raise
            
        # Update Registry
        registry = self._load_registry()
        registry[name] = vault_path
        self._save_registry(registry)
        
        return project_data

    def init_workspace(self, base_path: str, project_name: str) -> Optional[str]:
        try:
            project_path = os.path.join(base_path, project_name)
            os.makedirs(os.path.join(project_path, "World"), exist_ok=True)
            os.makedirs(os.path.join(project_path, "Novel"), exist_ok=True)
            return project_path
        except Exception as e:
            logger.error(f"Error initializing workspace at {base_path}: {e}")
            return None

    def delete_project(self, name: str, delete_physical: bool = False) -> bool:
        registry = self._load_registry()
        path = registry.get(name)
        if not path:
            return False
            
        if delete_physical:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                except Exception as e:
                    logger.error(f"Error deleting physical files for {name}: {e}")

        # Remove from registry
        if name in registry:
            del registry[name]
            self._save_registry(registry)
            return True
        return False

# Global instance
project_service = ProjectService()
