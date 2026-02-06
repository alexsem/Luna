import pytest
import os
import sys

# Add backend to path if needed
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from project_service import ProjectService
from vault_service import VaultService

@pytest.mark.asyncio
async def test_project_service_lifecycle(temp_workspace):
    ps = ProjectService()
    ps.registry_file = str(temp_workspace / "known_projects.json")
    
    # 1. Create Project
    ps.init_workspace(str(temp_workspace), "MyStory")
    project_path = os.path.join(str(temp_workspace), "MyStory")
    
    # Save project so list_projects can find it (it checks for MyStory.json)
    await ps.save_project("MyStory", [], config={"vault_path": project_path})
    
    assert os.path.exists(os.path.join(project_path, "World"))
    
    # 2. List Projects
    projects = ps.list_projects()
    assert "MyStory" in projects
    
    # 3. Load Project
    data = ps.load_project("MyStory")
    assert data is not None
    
    # 4. Delete Project
    ps.delete_project("MyStory", delete_physical=True)
    assert "MyStory" not in ps.list_projects()
    assert not os.path.exists(project_path)

def test_vault_service_operations(temp_workspace):
    vs = VaultService()
    vault_path = str(temp_workspace / "Vault")
    os.makedirs(vault_path)
    vs.set_vault_path(vault_path)
    vs.config_file = str(temp_workspace / "config.json")
    
    # 1. Create File
    success, rel_path = vs.create_file("Chapter1.md")
    assert success is True
    assert rel_path == "Chapter1.md"
    
    # 2. Save/Write
    vs.save_file("Chapter1.md", "Once upon a time...")
    
    # 3. Read
    content = vs.read_file("Chapter1.md")
    assert content == "Once upon a time..."
    
    # 4. List Files
    files = vs.list_files()
    assert any(f["name"] == "Chapter1.md" for f in files)
    
    # 5. Security Check (Path Traversal)
    with pytest.raises(ValueError):
        vs.read_file("../../secret.txt")
