# -*- coding: utf-8 -*-
"""
Enhanced Test Suite for Repository Operations
Covers all repository workflows with comprehensive scenarios

Run with: pytest tests/unit/test_repository_enhanced.py -v
"""

import os
import pytest

if os.environ.get("RUN_LEGACY_REPOSITORY_ENHANCED_TESTS") != "1":
    pytest.skip(
        "Legacy repository tests are skipped by default; set RUN_LEGACY_REPOSITORY_ENHANCED_TESTS=1 to run.",
        allow_module_level=True,
    )

import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.core.repository import ScriptRepository, ChecksumVerificationError


@dataclass
class MockScript:
    """Mock script data for testing."""
    id: str
    name: str
    path: str
    category: str = "install"
    version: str = "1.0"
    checksum: str = "abc123"


class TestRepositoryInitialization:
    """Test repository initialization and configuration."""
    
    def test_repository_creates_config_dir_on_init(self, tmp_path):
        """Repository should create config directory if missing."""
        config_dir = tmp_path / ".lv_linux_learn"
        assert not config_dir.exists()
        
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            assert config_dir.exists()
    
    def test_repository_loads_existing_config(self, tmp_path):
        """Repository should load existing configuration."""
        config_dir = tmp_path / ".lv_linux_learn"
        config_dir.mkdir(parents=True)
        
        config_file = config_dir / "config.json"
        test_config = {
            "auto_check_updates": False,
            "force_remote_downloads": True
        }
        config_file.write_text(json.dumps(test_config))
        
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            config = repo.load_config()
            assert config["force_remote_downloads"] == True
    
    def test_repository_creates_default_config(self, tmp_path):
        """Repository should create default config if missing."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            config = repo.load_config()
            
            assert "auto_check_updates" in config
            assert "force_remote_downloads" in config
            assert "verify_checksums" in config


class TestRepositoryForceRemoteDownloads:
    """Test force_remote_downloads configuration behavior."""
    
    def test_force_remote_downloads_default_true(self, tmp_path):
        """force_remote_downloads should default to True."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            config = repo.load_config()
            assert config.get("force_remote_downloads") == True
    
    def test_force_remote_downloads_env_override(self, tmp_path):
        """LV_FORCE_REMOTE environment variable should override config."""
        config_dir = tmp_path / ".lv_linux_learn"
        config_dir.mkdir(parents=True)
        
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({"force_remote_downloads": False}))
        
        with patch.dict(os.environ, {
            "HOME": str(tmp_path),
            "LV_FORCE_REMOTE": "1"
        }):
            repo = ScriptRepository()
            # Should detect local repo disabled
            result = repo.detect_local_repository()
            assert result is None  # Returns None when local detection disabled
    
    def test_force_remote_downloads_disables_local_detection(self, tmp_path):
        """When force_remote_downloads=True, local repo should not be detected."""
        config_dir = tmp_path / ".lv_linux_learn"
        config_dir.mkdir(parents=True)
        
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({"force_remote_downloads": True}))
        
        # Create a fake local repo structure
        local_repo = tmp_path / "lv_linux_learn"
        local_repo.mkdir()
        (local_repo / "scripts").mkdir()
        
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            with patch("lib.repository.Path") as mock_path:
                repo = ScriptRepository()
                result = repo.detect_local_repository()
                assert result is None  # Should not find local repo


class TestRepositoryCheckForUpdates:
    """Test update detection mechanisms."""
    
    def test_check_for_updates_returns_count(self, tmp_path):
        """check_for_updates() should return number of updates found."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            
            with patch.object(repo, "list_available_updates") as mock_list:
                mock_list.return_value = [
                    MockScript("script1", "Script 1", "script1.sh"),
                    MockScript("script2", "Script 2", "script2.sh"),
                ]
                
                count = repo.check_for_updates()
                assert count == 2
    
    def test_check_for_updates_respects_throttle(self, tmp_path):
        """check_for_updates() should throttle repeated checks."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            
            with patch.object(repo, "is_update_check_needed") as mock_check:
                mock_check.return_value = False
                
                with patch.object(repo, "list_available_updates") as mock_list:
                    repo.check_for_updates()
                    mock_list.assert_not_called()
    
    def test_check_for_updates_updates_timestamp(self, tmp_path):
        """check_for_updates() should update last_update_check timestamp."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            
            with patch.object(repo, "is_update_check_needed", return_value=True):
                with patch.object(repo, "list_available_updates", return_value=[]):
                    repo.check_for_updates()
                    
                    config = repo.load_config()
                    assert config.get("last_update_check") is not None


class TestRepositoryChecksumVerification:
    """Test checksum handling and verification."""
    
    def test_verify_script_checksum_success(self, tmp_path):
        """verify_script_checksum() should succeed with matching checksum."""
        script_file = tmp_path / "test_script.sh"
        script_file.write_text("#!/bin/bash\necho 'test'")
        
        # Calculate actual checksum
        import hashlib
        with open(script_file, "rb") as f:
            actual_checksum = hashlib.sha256(f.read()).hexdigest()
        
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            result = repo.verify_script_checksum(
                str(script_file),
                actual_checksum
            )
            assert result == True
    
    def test_verify_script_checksum_failure(self, tmp_path):
        """verify_script_checksum() should fail with mismatched checksum."""
        script_file = tmp_path / "test_script.sh"
        script_file.write_text("#!/bin/bash\necho 'test'")
        
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            
            with pytest.raises(ChecksumVerificationError):
                repo.verify_script_checksum(
                    str(script_file),
                    "invalid_checksum_hash"
                )
    
    def test_verify_checksum_disabled_in_config(self, tmp_path):
        """Should skip checksum verification if disabled in config."""
        config_dir = tmp_path / ".lv_linux_learn"
        config_dir.mkdir(parents=True)
        
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({"verify_checksums": False}))
        
        script_file = tmp_path / "test_script.sh"
        script_file.write_text("#!/bin/bash\necho 'test'")
        
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            # Should not raise error even with wrong checksum
            result = repo.verify_script_checksum(
                str(script_file),
                "invalid_hash",
                verify=False  # Explicitly skip verification
            )
            assert result == True


class TestRepositoryCacheOperations:
    """Test cache download/update/remove operations."""
    
    def test_download_script_creates_cache_file(self, tmp_path):
        """Downloading script should create cache file."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            
            script_content = "#!/bin/bash\necho 'installed'"
            
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = script_content.encode()
                mock_response.__enter__ = lambda s: s
                mock_response.__exit__ = lambda s, *args: None
                mock_urlopen.return_value = mock_response
                
                cache_file = repo.download_script("test_script", "test_script.sh")
                assert cache_file.exists()
    
    def test_update_script_replaces_existing(self, tmp_path):
        """Updating script should replace cached version."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            
            old_content = "#!/bin/bash\necho 'v1'"
            new_content = "#!/bin/bash\necho 'v2'"
            
            # Create initial cache
            cache_dir = repo.script_cache_dir
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / "test_script.sh"
            cache_file.write_text(old_content)
            
            # Update with new content
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = new_content.encode()
                mock_response.__enter__ = lambda s: s
                mock_response.__exit__ = lambda s, *args: None
                mock_urlopen.return_value = mock_response
                
                repo.update_script("test_script", "test_script.sh")
                assert cache_file.read_text() == new_content
    
    def test_remove_script_deletes_cache_file(self, tmp_path):
        """Removing script should delete cache file."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            
            cache_dir = repo.script_cache_dir
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / "test_script.sh"
            cache_file.write_text("#!/bin/bash\necho 'test'")
            
            assert cache_file.exists()
            repo.remove_script("test_script")
            assert not cache_file.exists()


class TestRepositoryErrorHandling:
    """Test error scenarios and recovery."""
    
    def test_handles_network_error_gracefully(self, tmp_path):
        """Repository should handle network errors gracefully."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_urlopen.side_effect = IOError("Network error")
                
                with pytest.raises(IOError):
                    repo.download_script("test_script", "test_script.sh")
    
    def test_handles_corrupted_manifest(self, tmp_path):
        """Repository should handle corrupted manifest gracefully."""
        config_dir = tmp_path / ".lv_linux_learn"
        config_dir.mkdir(parents=True)
        
        manifest_file = config_dir / "manifest.json"
        manifest_file.write_text("{ invalid json }")
        
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            
            with pytest.raises(json.JSONDecodeError):
                repo.load_manifest()
    
    def test_handles_missing_cache_directory(self, tmp_path):
        """Repository should create cache directory if missing."""
        with patch.dict(os.environ, {"HOME": str(tmp_path)}):
            repo = ScriptRepository()
            
            cache_dir = repo.script_cache_dir
            assert cache_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
