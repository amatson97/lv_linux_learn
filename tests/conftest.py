"""
Pytest configuration and shared fixtures for lv_linux_learn test suite

Provides:
- Common test fixtures (repository instances, temp directories, mock data)
- Test helpers and utilities
- Shared test data generators
- GTK mock helpers for UI testing
"""

import pytest
import tempfile
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.repository import ScriptRepository
from lib.script_execution import ScriptEnvironmentManager, ScriptExecutionContext, ScriptValidator


# ============================================================================
# Repository Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Provide a temporary directory that's cleaned up after test"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_repo_structure(temp_dir):
    """Create a mock lv_linux_learn repository structure"""
    repo_root = temp_dir / "lv_linux_learn"
    repo_root.mkdir()
    
    # Create directory structure
    (repo_root / "scripts").mkdir()
    (repo_root / "tools").mkdir()
    (repo_root / "includes").mkdir()
    (repo_root / "uninstallers").mkdir()
    
    # Create sample scripts
    test_script = repo_root / "scripts" / "test_install.sh"
    test_script.write_text("#!/bin/bash\necho 'test install'\n")
    test_script.chmod(0o755)
    
    tool_script = repo_root / "tools" / "test_tool.sh"
    tool_script.write_text("#!/bin/bash\necho 'test tool'\n")
    tool_script.chmod(0o755)
    
    # Create includes
    main_include = repo_root / "includes" / "main.sh"
    main_include.write_text("#!/bin/bash\n# Main helpers\ngreen_echo() { echo -e \"\\033[32m$*\\033[0m\"; }\n")
    
    return repo_root


@pytest.fixture
def repo_with_temp_dirs(temp_dir):
    """Create ScriptRepository instance with isolated temp directories"""
    repo = ScriptRepository()
    
    # Override all paths to use temp directory
    config_dir = temp_dir / ".lv_linux_learn"
    repo.config_dir = config_dir
    repo.config_file = config_dir / "config.json"
    repo.manifest_file = config_dir / "manifest.json"
    repo.manifest_meta_file = config_dir / "manifest_metadata.json"
    repo.script_cache_dir = config_dir / "script_cache"
    repo.log_file = config_dir / "logs" / "repository.log"
    
    # Create directories
    repo._ensure_directories()
    
    # Initialize with default config
    repo.config = {
        "auto_install_updates": False,
        "verify_checksums": True,
        "update_check_interval_minutes": 60,
        "manifest_cache_max_age_seconds": 60
    }
    repo.save_config(repo.config)
    
    yield repo


@pytest.fixture
def repo_with_manifest(repo_with_temp_dirs):
    """Repository with a sample manifest already loaded"""
    repo = repo_with_temp_dirs
    
    manifest = {
        "repository_version": "2.3.0",
        "verify_checksums": True,
        "scripts": [
            {
                "id": "docker-install",
                "category": "install",
                "file_name": "docker_install.sh",
                "download_url": "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/scripts/docker_install.sh",
                "checksum": "abc123",
                "size": 2048,
                "description": "Install Docker"
            },
            {
                "id": "git-pull",
                "category": "tools",
                "file_name": "git_pull.sh",
                "download_url": "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/tools/git_pull.sh",
                "checksum": "def456",
                "size": 1024,
                "description": "Git pull tool"
            }
        ]
    }
    
    with open(repo.manifest_file, 'w') as f:
        json.dump(manifest, f)
    
    yield repo


@pytest.fixture
def repo_with_cached_scripts(repo_with_manifest):
    """Repository with manifest and cached scripts"""
    repo = repo_with_manifest
    
    # Cache docker script
    docker_dir = repo.script_cache_dir / "install"
    docker_dir.mkdir(parents=True, exist_ok=True)
    docker_script = docker_dir / "docker_install.sh"
    docker_content = b"#!/bin/bash\necho 'docker install'\n"
    docker_script.write_bytes(docker_content)
    docker_script.chmod(0o755)
    
    # Cache git tool
    tools_dir = repo.script_cache_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    git_script = tools_dir / "git_pull.sh"
    git_content = b"#!/bin/bash\necho 'git pull'\n"
    git_script.write_bytes(git_content)
    git_script.chmod(0o755)
    
    yield repo


# ============================================================================
# Data Generation Helpers
# ============================================================================

def create_mock_script(content: bytes, category: str = "install", script_id: str = "test-script") -> dict:
    """Generate a mock script manifest entry with checksum"""
    checksum = hashlib.sha256(content).hexdigest()
    
    return {
        "id": script_id,
        "category": category,
        "file_name": f"{script_id.replace('-', '_')}.sh",
        "download_url": f"https://example.com/{category}/{script_id}.sh",
        "checksum": checksum,
        "size": len(content),
        "description": f"Test {script_id}"
    }


def create_mock_manifest(scripts: list = None, version: str = "2.3.0") -> dict:
    """Generate a complete mock manifest"""
    if scripts is None:
        scripts = []
    
    return {
        "repository_version": version,
        "verify_checksums": True,
        "scripts": scripts
    }


# ============================================================================
# Script Execution Fixtures
# ============================================================================

@pytest.fixture
def env_manager():
    """Provide ScriptEnvironmentManager instance"""
    return ScriptEnvironmentManager()


@pytest.fixture
def execution_context():
    """Provide ScriptExecutionContext instance"""
    return ScriptExecutionContext()


@pytest.fixture
def script_validator():
    """Provide ScriptValidator instance"""
    return ScriptValidator()


@pytest.fixture
def mock_script_metadata():
    """Provide sample script metadata"""
    return {
        "type": "local",
        "file_exists": True,
        "script_id": "test-script",
        "category": "install"
    }


# ============================================================================
# GTK/UI Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_gtk():
    """Mock GTK modules for UI testing"""
    gtk_mock = MagicMock()
    
    # Mock common GTK types
    gtk_mock.Window = MagicMock
    gtk_mock.Box = MagicMock
    gtk_mock.Button = MagicMock
    gtk_mock.Label = MagicMock
    gtk_mock.TreeView = MagicMock
    gtk_mock.ListStore = MagicMock
    
    with patch.dict('sys.modules', {
        'gi': MagicMock(),
        'gi.repository': MagicMock(),
        'gi.repository.Gtk': gtk_mock,
        'gi.repository.GLib': MagicMock(),
        'gi.repository.Vte': MagicMock()
    }):
        yield gtk_mock


@pytest.fixture
def mock_terminal():
    """Mock VTE terminal for testing"""
    terminal = MagicMock()
    terminal.feed = MagicMock()
    terminal.feed_child = MagicMock()
    terminal.spawn_sync = MagicMock(return_value=True)
    return terminal


# ============================================================================
# Network Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_urlopen():
    """Mock urllib.request.urlopen for download tests"""
    def _mock_urlopen(content: bytes = b"test content"):
        """Create a mock urlopen response"""
        mock_response = MagicMock()
        mock_response.read.return_value = content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        return mock_response
    
    return _mock_urlopen


@pytest.fixture
def mock_successful_download(mock_urlopen):
    """Mock successful script download"""
    def _download(content: bytes = b"#!/bin/bash\necho 'test'\n"):
        with patch('urllib.request.urlopen', return_value=mock_urlopen(content)):
            yield content
    
    return _download


# ============================================================================
# Test Markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "e2e: end-to-end tests covering full application workflows"
    )
    config.addinivalue_line(
        "markers", "repository: tests for repository/manifest management"
    )
    config.addinivalue_line(
        "markers", "execution: tests for script execution logic"
    )
    config.addinivalue_line(
        "markers", "ui_integration: tests requiring UI components"
    )


# ============================================================================
# Test Helpers
# ============================================================================

class TestHelpers:
    """Shared helper methods for tests"""
    
    @staticmethod
    def create_cached_script(repo: ScriptRepository, script_id: str, content: bytes, category: str = "install") -> Path:
        """Create a cached script file for testing"""
        category_dir = repo.script_cache_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{script_id.replace('-', '_')}.sh"
        script_path = category_dir / filename
        script_path.write_bytes(content)
        script_path.chmod(0o755)
        
        return script_path
    
    @staticmethod
    def assert_script_cached(repo: ScriptRepository, script_id: str) -> bool:
        """Check if a script is properly cached"""
        cached_path = repo.get_cached_script_path(script_id)
        return cached_path is not None and Path(cached_path).exists()
    
    @staticmethod
    def get_script_checksum(path: Path) -> str:
        """Calculate checksum of a script file"""
        return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def test_helpers():
    """Provide TestHelpers instance"""
    return TestHelpers()
