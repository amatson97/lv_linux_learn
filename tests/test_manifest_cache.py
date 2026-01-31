"""
Unit tests for manifest cache refresh behavior
"""

import os
import time
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.repository import ScriptRepository
from lib.manifest import ManifestLoader
import lib.manifest as manifest_module


def _setup_repo(tmpdir: str) -> ScriptRepository:
    repo = ScriptRepository()
    repo.config_dir = Path(tmpdir) / ".lv_linux_learn"
    repo.config_file = repo.config_dir / "config.json"
    repo.manifest_file = repo.config_dir / "manifest.json"
    repo.manifest_meta_file = repo.config_dir / "manifest_metadata.json"
    repo.script_cache_dir = repo.config_dir / "script_cache"
    repo._ensure_directories()
    return repo


def test_load_config_adds_manifest_cache_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = _setup_repo(tmpdir)
        repo.config_file.parent.mkdir(parents=True, exist_ok=True)
        # Write config without manifest_cache_max_age_seconds
        with open(repo.config_file, 'w') as f:
            json.dump({"use_public_repository": True}, f)

        config = repo.load_config()
        assert config.get("manifest_cache_max_age_seconds") == 60


def test_manifest_cache_respects_config_override(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = _setup_repo(tmpdir)

        repo.config = {
            "use_public_repository": True,
            "manifest_cache_max_age_seconds": 1
        }

        # fetch_manifest() reads config via load_config
        repo.load_config = lambda: dict(repo.config)

        # Point manifest cache dir to temp
        monkeypatch.setattr(manifest_module.C, "CONFIG_DIR", repo.config_dir)
        monkeypatch.setattr(
            manifest_module.C,
            "DEFAULT_MANIFEST_URL",
            "https://example.com/manifest.json"
        )

        cache_path = repo.config_dir / "manifest_public_repository.json"
        cache_path.write_text("old")
        os.utime(cache_path, (time.time() - 3600, time.time() - 3600))

        mock_response = Mock()
        mock_response.read.return_value = b'{"scripts": []}'

        with patch("lib.manifest.urlopen", return_value=mock_response) as mock_urlopen:
            manifests = ManifestLoader.fetch_manifest(repository=repo)

        assert mock_urlopen.called is True
        assert cache_path.read_text() == '{"scripts": []}'
        assert any(str(cache_path) == str(path) for path, _ in manifests)
