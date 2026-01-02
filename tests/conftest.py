import pytest
import os
import shutil
from unittest.mock import MagicMock, patch

# Add backend to path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from project_service import ProjectService

@pytest.fixture
def temp_workspace(tmp_path):
    """Creates a temporary workspace and project root for testing."""
    workspace = tmp_path / "luna_test_ws"
    workspace.mkdir()
    
    # Mock base_dir and registry_file in ProjectService
    with patch.object(ProjectService, "__init__", lambda self: None):
        with patch("project_service.ProjectService.base_dir", str(workspace), create=True):
             with patch("project_service.ProjectService.registry_file", str(workspace / "known_projects.json"), create=True):
                yield workspace

@pytest.fixture
def mock_ollama():
    """Mocks the Ollama API calls."""
    with patch("general_functions.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "Mocked AI Response"}}
        mock_post.return_value = mock_response
        yield mock_post

@pytest.fixture
def mock_chroma():
    """Mocks the ChromaDB client."""
    with patch("knowledge_base_service.chromadb.HttpClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance
