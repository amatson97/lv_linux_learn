"""
Unit tests for ScriptRepository update functionality

Tests the core update detection and handling mechanisms:
- check_for_updates()
- update_all_scripts()
- is_update_check_needed()
- list_available_updates()

Run with: pytest tests/test_repository_updates.py -v
"""

import pytest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.repository import ScriptRepository, ChecksumVerificationError


class TestUpdateCheckTiming:
    """Test update check timing and throttling logic"""
    
    @pytest.fixture
    def repo_with_temp_dirs(self):
        """Create repository with temporary directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            # Override paths to use temp directory
            repo.config_dir = Path(tmpdir) / ".lv_linux_learn"
            repo.config_file = repo.config_dir / "config.json"
            repo.manifest_file = repo.config_dir / "manifest.json"
            repo.manifest_meta_file = repo.config_dir / "manifest_metadata.json"
            repo.script_cache_dir = repo.config_dir / "script_cache"
            repo._ensure_directories()
            yield repo
    
    def test_is_update_check_needed_no_last_check(self, repo_with_temp_dirs):
        """Should return True when no previous check recorded"""
        repo = repo_with_temp_dirs
        assert repo.is_update_check_needed() is True
    
    def test_is_update_check_needed_within_interval(self, repo_with_temp_dirs):
        """Should return False when check was recent (within interval)"""
        repo = repo_with_temp_dirs
        now = datetime.now()
        repo.set_config_value("last_update_check", now.isoformat())
        
        assert repo.is_update_check_needed() is False
    
    def test_is_update_check_needed_past_interval(self, repo_with_temp_dirs):
        """Should return True when interval has passed"""
        repo = repo_with_temp_dirs
        past_time = datetime.now() - timedelta(minutes=45)
        repo.set_config_value("last_update_check", past_time.isoformat())
        repo.set_config_value("update_check_interval_minutes", 30)
        
        assert repo.is_update_check_needed() is True
    
    def test_is_update_check_needed_custom_interval(self, repo_with_temp_dirs):
        """Should respect custom update interval"""
        repo = repo_with_temp_dirs
        past_time = datetime.now() - timedelta(minutes=10)
        repo.set_config_value("last_update_check", past_time.isoformat())
        repo.set_config_value("update_check_interval_minutes", 5)
        
        assert repo.is_update_check_needed() is True
    
    def test_is_update_check_needed_invalid_timestamp(self, repo_with_temp_dirs):
        """Should return True when stored timestamp is invalid"""
        repo = repo_with_temp_dirs
        repo.set_config_value("last_update_check", "invalid-timestamp")
        
        assert repo.is_update_check_needed() is True


class TestCheckForUpdates:
    """Test the check_for_updates() method"""
    
    @pytest.fixture
    def repo_with_temp_dirs(self):
        """Create repository with temporary directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir) / ".lv_linux_learn"
            repo.config_file = repo.config_dir / "config.json"
            repo.manifest_file = repo.config_dir / "manifest.json"
            repo.manifest_meta_file = repo.config_dir / "manifest_metadata.json"
            repo.script_cache_dir = repo.config_dir / "script_cache"
            repo._ensure_directories()
            yield repo
    
    def _create_sample_manifest(self, repo, num_scripts=3):
        """Create a sample manifest with test scripts"""
        manifest = {
            "repository_version": "1.0",
            "scripts": [
                {
                    "id": f"script_{i}",
                    "file_name": f"test_script_{i}.sh",
                    "category": "test_scripts",
                    "download_url": f"https://example.com/test_script_{i}.sh",
                    "checksum": f"sha256:{'0' * 64}"
                }
                for i in range(num_scripts)
            ]
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        return manifest
    
    def _create_cached_script(self, repo, script_id, content=b"test script", category="test_scripts"):
        """Create a cached script file"""
        script_name = f"{script_id}.sh"
        cache_path = repo.script_cache_dir / category / script_name
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'wb') as f:
            f.write(content)
        return cache_path
    
    @patch('lib.repository.ScriptRepository.fetch_remote_manifest')
    def test_check_for_updates_manifest_fetch_fails(self, mock_fetch, repo_with_temp_dirs):
        """Should return 0 when remote manifest fetch fails"""
        repo = repo_with_temp_dirs
        mock_fetch.return_value = False
        
        result = repo.check_for_updates()
        
        assert result == 0
        mock_fetch.assert_called_once()
    
    @patch('lib.repository.ScriptRepository.fetch_remote_manifest')
    def test_check_for_updates_no_cached_scripts(self, mock_fetch, repo_with_temp_dirs):
        """Should return 0 when no scripts are cached"""
        repo = repo_with_temp_dirs
        mock_fetch.return_value = True
        self._create_sample_manifest(repo, num_scripts=3)
        
        # Don't cache any scripts
        result = repo.check_for_updates()
        
        assert result == 0
    
    @patch('lib.repository.ScriptRepository.fetch_remote_manifest')
    def test_check_for_updates_detects_updated_scripts(self, mock_fetch, repo_with_temp_dirs):
        """Should detect when cached scripts have different checksums"""
        repo = repo_with_temp_dirs
        mock_fetch.return_value = True
        
        # Disable auto-install for this test
        repo.set_config_value("auto_install_updates", False)
        
        # Create manifest with specific checksums
        manifest = {
            "repository_version": "1.0",
            "scripts": [
                {
                    "id": "script_1",
                    "file_name": "script_1.sh",
                    "category": "test",
                    "download_url": "https://example.com/script_1.sh",
                    "checksum": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                }
            ]
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        # Cache script with different content (different checksum)
        self._create_cached_script(repo, "script_1", b"different content", category="test")
        
        result = repo.check_for_updates()
        
        # Should detect this as an update
        assert result > 0
    
    @patch('lib.repository.ScriptRepository.fetch_remote_manifest')
    def test_check_for_updates_ignores_unchanged_scripts(self, mock_fetch, repo_with_temp_dirs):
        """Should not count scripts with matching checksums as updates"""
        repo = repo_with_temp_dirs
        mock_fetch.return_value = True
        
        # Create script content
        script_content = b"#!/bin/bash\necho 'test'\n"
        
        # Create manifest with correct checksum
        import hashlib
        correct_checksum = hashlib.sha256(script_content).hexdigest()
        
        manifest = {
            "repository_version": "1.0",
            "scripts": [
                {
                    "id": "script_1",
                    "file_name": "script_1.sh",
                    "category": "test",
                    "download_url": "https://example.com/script_1.sh",
                    "checksum": f"sha256:{correct_checksum}"
                }
            ]
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        # Cache script with matching content
        self._create_cached_script(repo, "script_1", script_content)
        
        result = repo.check_for_updates()
        
        # Should NOT detect as update
        assert result == 0
    
    @patch('lib.repository.ScriptRepository.fetch_remote_manifest')
    def test_check_for_updates_updates_timestamp(self, mock_fetch, repo_with_temp_dirs):
        """Should update last_update_check timestamp on successful check"""
        repo = repo_with_temp_dirs
        mock_fetch.return_value = True
        self._create_sample_manifest(repo)
        
        before = datetime.now()
        repo.check_for_updates()
        after = datetime.now()
        
        timestamp_str = repo.get_config_value("last_update_check")
        assert timestamp_str is not None
        
        timestamp = datetime.fromisoformat(timestamp_str)
        assert before <= timestamp <= after
    
    @patch('lib.repository.ScriptRepository.fetch_remote_manifest')
    @patch('lib.repository.ScriptRepository.update_all_scripts_silent')
    def test_check_for_updates_auto_install_enabled(self, mock_auto_install, mock_fetch, repo_with_temp_dirs):
        """Should auto-install updates when enabled"""
        repo = repo_with_temp_dirs
        mock_fetch.return_value = True
        mock_auto_install.return_value = 2
        
        # Create manifest with updates available
        import hashlib
        manifest = {
            "repository_version": "1.0",
            "scripts": [
                {
                    "id": "script_1",
                    "file_name": "script_1.sh",
                    "category": "test",
                    "download_url": "https://example.com/script_1.sh",
                    "checksum": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                }
            ]
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        # Cache script with different content (use correct category)
        self._create_cached_script(repo, "script_1", b"old version", category="test")
        
        # Enable auto-install
        repo.set_config_value("auto_install_updates", True)
        
        result = repo.check_for_updates()
        
        # Auto-install returns 0 on success
        assert result == 0
        mock_auto_install.assert_called_once()


class TestCachedScriptLookup:
    """Test cached script lookup behavior"""

    @pytest.fixture
    def repo_with_temp_dirs(self):
        """Create repository with temporary directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir) / ".lv_linux_learn"
            repo.config_file = repo.config_dir / "config.json"
            repo.manifest_file = repo.config_dir / "manifest.json"
            repo.manifest_meta_file = repo.config_dir / "manifest_metadata.json"
            repo.script_cache_dir = repo.config_dir / "script_cache"
            repo._ensure_directories()
            yield repo

    def test_get_cached_script_path_fallback_searches_by_filename(self, repo_with_temp_dirs):
        """Should find cached file by filename even if category changed"""
        repo = repo_with_temp_dirs

        # Manifest says category is install
        manifest = {
            "repository_version": "1.0",
            "scripts": [
                {
                    "id": "script_1",
                    "file_name": "script_1.sh",
                    "category": "install",
                    "download_url": "https://example.com/script_1.sh",
                    "checksum": "sha256:" + "0" * 64
                }
            ]
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)

        # Cached file exists in a different category (tools)
        cached_path = repo.script_cache_dir / "tools" / "script_1.sh"
        cached_path.parent.mkdir(parents=True, exist_ok=True)
        cached_path.write_text("echo test")

        result = repo.get_cached_script_path(script_id="script_1")
        assert result == str(cached_path)


class TestUpdateAllScripts:
    """Test the update_all_scripts() method"""
    
    @pytest.fixture
    def repo_with_temp_dirs(self):
        """Create repository with temporary directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir) / ".lv_linux_learn"
            repo.config_file = repo.config_dir / "config.json"
            repo.manifest_file = repo.config_dir / "manifest.json"
            repo.manifest_meta_file = repo.config_dir / "manifest_metadata.json"
            repo.script_cache_dir = repo.config_dir / "script_cache"
            repo._ensure_directories()
            yield repo
    
    def _create_sample_manifest(self, repo, num_scripts=3):
        """Create a sample manifest"""
        manifest = {
            "repository_version": "1.0",
            "scripts": [
                {
                    "id": f"script_{i}",
                    "file_name": f"script_{i}.sh",
                    "category": "test",
                    "download_url": f"https://example.com/script_{i}.sh",
                    "checksum": f"sha256:{'0' * 64}"
                }
                for i in range(num_scripts)
            ]
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        return manifest
    
    def _create_cached_script(self, repo, script_id):
        """Create a cached script file"""
        script_name = f"{script_id}.sh"
        cache_path = repo.script_cache_dir / "test" / script_name
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w') as f:
            f.write("#!/bin/bash\necho 'test'\n")
        return cache_path
    
    @patch('lib.repository.ScriptRepository.download_script')
    def test_update_all_scripts_only_updates_cached(self, mock_download, repo_with_temp_dirs):
        """Should only update scripts that are already cached"""
        repo = repo_with_temp_dirs
        self._create_sample_manifest(repo, num_scripts=5)
        
        # Cache only 2 scripts
        self._create_cached_script(repo, "script_0")
        self._create_cached_script(repo, "script_1")
        # script_2, script_3, script_4 are NOT cached
        
        mock_download.return_value = True
        
        updated, failed = repo.update_all_scripts()
        
        # Should only call download for cached scripts
        assert mock_download.call_count == 2
    
    @patch('lib.repository.ScriptRepository.download_script')
    def test_update_all_scripts_counts_failures(self, mock_download, repo_with_temp_dirs):
        """Should count download failures"""
        repo = repo_with_temp_dirs
        self._create_sample_manifest(repo, num_scripts=3)
        
        # Cache all scripts
        for i in range(3):
            self._create_cached_script(repo, f"script_{i}")
        
        # Simulate 2 successes and 1 failure
        mock_download.side_effect = [True, True, False]
        
        updated, failed = repo.update_all_scripts()
        
        assert updated == 2
        assert failed == 1
    
    @patch('lib.repository.ScriptRepository.download_script')
    def test_update_all_scripts_returns_tuple(self, mock_download, repo_with_temp_dirs):
        """Should return tuple of (updated, failed)"""
        repo = repo_with_temp_dirs
        self._create_sample_manifest(repo, num_scripts=2)
        self._create_cached_script(repo, "script_0")
        self._create_cached_script(repo, "script_1")
        
        mock_download.return_value = True
        
        result = repo.update_all_scripts()
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        updated, failed = result
        assert isinstance(updated, int)
        assert isinstance(failed, int)


class TestListAvailableUpdates:
    """Test the list_available_updates() method"""
    
    @pytest.fixture
    def repo_with_temp_dirs(self):
        """Create repository with temporary directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir) / ".lv_linux_learn"
            repo.config_file = repo.config_dir / "config.json"
            repo.manifest_file = repo.config_dir / "manifest.json"
            repo.manifest_meta_file = repo.config_dir / "manifest_metadata.json"
            repo.script_cache_dir = repo.config_dir / "script_cache"
            repo._ensure_directories()
            yield repo
    
    def _create_sample_manifest(self, repo):
        """Create a sample manifest"""
        import hashlib
        script_content = b"old version"
        old_checksum = hashlib.sha256(script_content).hexdigest()
        new_checksum = hashlib.sha256(b"new version").hexdigest()
        
        manifest = {
            "repository_version": "1.0",
            "scripts": [
                {
                    "id": "updated_script",
                    "file_name": "updated.sh",
                    "category": "test",
                    "download_url": "https://example.com/updated.sh",
                    "checksum": f"sha256:{new_checksum}"
                },
                {
                    "id": "unchanged_script",
                    "file_name": "unchanged.sh",
                    "category": "test",
                    "download_url": "https://example.com/unchanged.sh",
                    "checksum": f"sha256:{old_checksum}"
                }
            ]
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        # Cache both scripts
        for script in manifest["scripts"]:
            cache_path = repo.script_cache_dir / script["category"] / script["file_name"]
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            # Use old version for both initially
            with open(cache_path, 'wb') as f:
                f.write(script_content)
    
    def test_list_available_updates_identifies_changed_scripts(self, repo_with_temp_dirs):
        """Should identify scripts with different checksums"""
        repo = repo_with_temp_dirs
        self._create_sample_manifest(repo)
        
        updates = repo.list_available_updates()
        
        assert len(updates) == 1
        assert updates[0]['id'] == 'updated_script'
    
    def test_list_available_updates_excludes_unchanged(self, repo_with_temp_dirs):
        """Should not include scripts with matching checksums"""
        repo = repo_with_temp_dirs
        self._create_sample_manifest(repo)
        
        updates = repo.list_available_updates()
        
        script_ids = [s['id'] for s in updates]
        assert 'unchanged_script' not in script_ids
    
    def test_list_available_updates_ignores_uncached_scripts(self, repo_with_temp_dirs):
        """Should only list updates for cached scripts"""
        repo = repo_with_temp_dirs
        
        manifest = {
            "repository_version": "1.0",
            "scripts": [
                {
                    "id": "cached",
                    "file_name": "cached.sh",
                    "category": "test",
                    "download_url": "https://example.com/cached.sh",
                    "checksum": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                },
                {
                    "id": "not_cached",
                    "file_name": "not_cached.sh",
                    "category": "test",
                    "download_url": "https://example.com/not_cached.sh",
                    "checksum": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
                }
            ]
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        # Only cache one script
        cache_path = repo.script_cache_dir / "test" / "cached.sh"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w') as f:
            f.write("cached content")
        
        updates = repo.list_available_updates()
        
        # Should only process the cached one
        assert all(u['id'] == 'cached' for u in updates)


class TestManifestParsing:
    """Test manifest parsing and handling"""
    
    @pytest.fixture
    def repo_with_temp_dirs(self):
        """Create repository with temporary directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir) / ".lv_linux_learn"
            repo.config_file = repo.config_dir / "config.json"
            repo.manifest_file = repo.config_dir / "manifest.json"
            repo.manifest_meta_file = repo.config_dir / "manifest_metadata.json"
            repo.script_cache_dir = repo.config_dir / "script_cache"
            repo._ensure_directories()
            yield repo
    
    def test_parse_manifest_flat_format(self, repo_with_temp_dirs):
        """Should parse flat array format manifest"""
        repo = repo_with_temp_dirs
        
        manifest = {
            "repository_version": "1.0",
            "scripts": [
                {"id": "script_1", "file_name": "script_1.sh", "category": "tools"},
                {"id": "script_2", "file_name": "script_2.sh", "category": "tools"}
            ]
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        scripts = repo.parse_manifest()
        
        assert len(scripts) == 2
        assert scripts[0]['id'] == 'script_1'
        assert scripts[1]['id'] == 'script_2'
    
    def test_parse_manifest_nested_format(self, repo_with_temp_dirs):
        """Should parse nested dictionary format manifest"""
        repo = repo_with_temp_dirs
        
        manifest = {
            "repository_version": "1.0",
            "scripts": {
                "tools": [
                    {"id": "script_1", "file_name": "script_1.sh"},
                    {"id": "script_2", "file_name": "script_2.sh"}
                ],
                "installers": [
                    {"id": "script_3", "file_name": "script_3.sh"}
                ]
            }
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        scripts = repo.parse_manifest()
        
        assert len(scripts) == 3
        # Verify category is set
        assert scripts[0]['category'] == 'tools'
        assert scripts[2]['category'] == 'installers'
    
    def test_parse_manifest_missing_file(self, repo_with_temp_dirs):
        """Should return empty list when manifest doesn't exist"""
        repo = repo_with_temp_dirs
        
        scripts = repo.parse_manifest()
        
        assert scripts == []


class TestChecksumHandling:
    """Test checksum verification in updates"""
    
    @pytest.fixture
    def repo_with_temp_dirs(self):
        """Create repository with temporary directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir) / ".lv_linux_learn"
            repo.config_file = repo.config_dir / "config.json"
            repo.manifest_file = repo.config_dir / "manifest.json"
            repo.manifest_meta_file = repo.config_dir / "manifest_metadata.json"
            repo.script_cache_dir = repo.config_dir / "script_cache"
            repo._ensure_directories()
            yield repo
    
    def test_checksum_mismatch_detection(self, repo_with_temp_dirs):
        """Should detect when local and remote checksums don't match"""
        repo = repo_with_temp_dirs
        
        import hashlib
        local_content = b"local version"
        remote_content = b"remote version"
        
        local_checksum = hashlib.sha256(local_content).hexdigest()
        remote_checksum = hashlib.sha256(remote_content).hexdigest()
        
        # Cache local version
        cache_path = repo.script_cache_dir / "test" / "test.sh"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'wb') as f:
            f.write(local_content)
        
        # Manifest has remote version
        manifest = {
            "repository_version": "1.0",
            "scripts": [
                {
                    "id": "test",
                    "file_name": "test.sh",
                    "category": "test",
                    "download_url": "https://example.com/test.sh",
                    "checksum": f"sha256:{remote_checksum}"
                }
            ]
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        updates = repo.list_available_updates()
        
        assert len(updates) > 0, "Should detect checksum mismatch as update"


class TestIntegrationScenarios:
    """Integration tests for realistic update scenarios"""
    
    @pytest.fixture
    def repo_with_temp_dirs(self):
        """Create repository with temporary directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir) / ".lv_linux_learn"
            repo.config_file = repo.config_dir / "config.json"
            repo.manifest_file = repo.config_dir / "manifest.json"
            repo.manifest_meta_file = repo.config_dir / "manifest_metadata.json"
            repo.script_cache_dir = repo.config_dir / "script_cache"
            repo._ensure_directories()
            yield repo
    
    @patch('lib.repository.ScriptRepository.fetch_remote_manifest')
    @patch('lib.repository.ScriptRepository.download_script')
    def test_full_update_workflow(self, mock_download, mock_fetch, repo_with_temp_dirs):
        """Test complete update detection and installation flow"""
        repo = repo_with_temp_dirs
        mock_fetch.return_value = True
        mock_download.return_value = True
        
        # Disable auto-install for this test
        repo.set_config_value("auto_install_updates", False)
        
        # Create initial manifest and cache
        import hashlib
        content = b"v1.0"
        manifest = {
            "repository_version": "1.0",
            "scripts": [
                {
                    "id": "tool1",
                    "file_name": "tool1.sh",
                    "category": "tools",
                    "download_url": "https://example.com/tool1.sh",
                    "checksum": f"sha256:{hashlib.sha256(b'v2.0').hexdigest()}"
                }
            ]
        }
        repo.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        # Cache v1.0
        cache_path = repo.script_cache_dir / "tools" / "tool1.sh"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'wb') as f:
            f.write(content)
        
        # Check for updates
        update_count = repo.check_for_updates()
        assert update_count > 0, "Should detect update available"
        
        # Update all scripts
        updated, failed = repo.update_all_scripts()
        assert updated > 0, "Should have updated scripts"
        assert failed == 0, "Should have no failures"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
