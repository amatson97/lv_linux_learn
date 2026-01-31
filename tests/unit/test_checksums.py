"""
Unit tests for checksum retry logic and update detection features.

Tests:
1. Checksum verification retry with cache-busted URLs
2. Update detection logic for tab indicators
3. Return value consistency from download_script
"""

import pytest
import tempfile
import json
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import urllib.error

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.repository import ScriptRepository, ChecksumVerificationError


class TestChecksumRetryLogic:
    """Test that checksum verification properly retries with cache-busted URLs"""
    
    def test_checksum_mismatch_triggers_retry(self):
        """Test that checksum mismatch triggers a retry with cache-busted URL"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir)
            repo.script_cache_dir = Path(tmpdir) / "script_cache"
            repo.script_cache_dir.mkdir(parents=True)
            
            # Create mock manifest with script
            script_id = "test-script"
            correct_content = b"#!/bin/bash\necho 'updated version'\n"
            stale_content = b"#!/bin/bash\necho 'old version'\n"
            correct_checksum = hashlib.sha256(correct_content).hexdigest()
            
            manifest = {
                "scripts": [{
                    "id": script_id,
                    "category": "install",
                    "file_name": "test.sh",
                    "download_url": "https://example.com/test.sh",
                    "checksum": correct_checksum
                }]
            }
            
            manifest_file = Path(tmpdir) / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f)
            repo.manifest_file = manifest_file
            
            # Mock urllib.request.urlopen to return stale content first, then correct content
            call_count = 0
            cache_bust_used = False
            
            def mock_urlopen(url, timeout=None):
                nonlocal call_count, cache_bust_used
                call_count += 1
                mock_response = MagicMock()
                if call_count == 1:
                    # First call returns stale content
                    mock_response.read.return_value = stale_content
                else:
                    # Second call (retry with cache-bust) returns correct content
                    mock_response.read.return_value = correct_content
                    # Track if cache-bust param was added
                    if "?t=" in url:
                        cache_bust_used = True
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=False)
                return mock_response
            
            with patch('urllib.request.urlopen', side_effect=mock_urlopen):
                # Mock ensure_includes_available to avoid extra network calls
                with patch.object(repo, 'ensure_includes_available', return_value=True):
                    success, url, error = repo.download_script(script_id)
                
                # Should succeed after retry
                assert success is True, "Download should succeed after retry"
                assert call_count == 2, "Should have retried once with cache-bust URL"
                assert cache_bust_used is True, "Cache-bust parameter should have been added to retry URL"
                
                # Verify correct content was saved
                cached_file = repo.script_cache_dir / "install" / "test.sh"
                assert cached_file.exists()
                with open(cached_file, 'rb') as f:
                    saved_content = f.read()
                assert saved_content == correct_content
    
    def test_checksum_fails_after_retry(self):
        """Test that download fails if checksum still wrong after retry"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir)
            repo.script_cache_dir = Path(tmpdir) / "script_cache"
            repo.script_cache_dir.mkdir(parents=True)
            
            script_id = "test-script"
            wrong_content = b"#!/bin/bash\necho 'wrong version'\n"
            expected_checksum = "0" * 64  # Impossible checksum
            
            manifest = {
                "scripts": [{
                    "id": script_id,
                    "category": "install",
                    "file_name": "test.sh",
                    "download_url": "https://example.com/test.sh",
                    "checksum": expected_checksum
                }]
            }
            
            manifest_file = Path(tmpdir) / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f)
            repo.manifest_file = manifest_file
            
            # Mock urllib to always return wrong content
            def mock_urlopen(url, timeout=None):
                mock_response = MagicMock()
                mock_response.read.return_value = wrong_content
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=False)
                return mock_response
            
            with patch('urllib.request.urlopen', side_effect=mock_urlopen):
                # Mock ensure_includes_available to avoid network calls
                with patch.object(repo, 'ensure_includes_available', return_value=True):
                    success, url, error = repo.download_script(script_id)
                
                # Should fail after retry
                assert success is False
                assert error is not None
                assert "Checksum verification failed" in error


class TestReturnValueConsistency:
    """Test that download_script always returns consistent tuple"""
    
    def test_download_script_returns_three_values_on_success(self):
        """Test that download_script returns (True, url, None) on success"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir)
            repo.script_cache_dir = Path(tmpdir) / "script_cache"
            repo.script_cache_dir.mkdir(parents=True)
            
            script_id = "test-script"
            content = b"#!/bin/bash\necho 'test'\n"
            checksum = hashlib.sha256(content).hexdigest()
            
            manifest = {
                "scripts": [{
                    "id": script_id,
                    "category": "install",
                    "file_name": "test.sh",
                    "download_url": "https://example.com/test.sh",
                    "checksum": checksum
                }]
            }
            
            manifest_file = Path(tmpdir) / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f)
            repo.manifest_file = manifest_file
            
            def mock_urlopen(url, timeout=None):
                mock_response = MagicMock()
                mock_response.read.return_value = content
                mock_response.__enter__ = Mock(return_value=mock_response)
                mock_response.__exit__ = Mock(return_value=False)
                return mock_response
            
            with patch('urllib.request.urlopen', side_effect=mock_urlopen):
                # Mock ensure_includes_available to avoid network calls
                with patch.object(repo, 'ensure_includes_available', return_value=True):
                    result = repo.download_script(script_id)
                
                # Must return exactly 3 values
                assert isinstance(result, tuple), "Should return tuple"
                assert len(result) == 3, f"Should return 3 values, got {len(result)}"
                success, url, error = result
                assert success is True
                assert url is not None
                assert error is None
    
    def test_download_script_returns_three_values_on_local_copy(self):
        """Test that local file copy also returns 3 values"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir)
            repo.script_cache_dir = Path(tmpdir) / "script_cache"
            repo.script_cache_dir.mkdir(parents=True)
            
            # Create a local repository structure
            local_repo = Path(tmpdir) / "local_repo"
            local_repo.mkdir()
            scripts_dir = local_repo / "scripts"
            scripts_dir.mkdir()
            
            # Create local script file
            local_script = scripts_dir / "test.sh"
            content = b"#!/bin/bash\necho 'local test'\n"
            with open(local_script, 'wb') as f:
                f.write(content)
            
            checksum = hashlib.sha256(content).hexdigest()
            
            script_id = "test-script"
            manifest = {
                "scripts": [{
                    "id": script_id,
                    "category": "install",
                    "file_name": "test.sh",
                    "download_url": "https://example.com/test.sh",
                    "checksum": checksum
                }]
            }
            
            manifest_file = Path(tmpdir) / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f)
            repo.manifest_file = manifest_file
            repo.local_repo_root = local_repo
            
            result = repo.download_script(script_id)
            
            # Must return exactly 3 values even when using local file
            assert isinstance(result, tuple), "Should return tuple"
            assert len(result) == 3, f"Should return 3 values from local copy, got {len(result)}"
            success, url, error = result
            assert success is True
            assert error is None


class TestUpdateDetectionLogic:
    """Test update detection logic used in tab population"""
    
    def test_detects_update_when_checksums_differ(self):
        """Test that update is detected when local and remote checksums differ"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir)
            repo.script_cache_dir = Path(tmpdir) / "script_cache"
            repo.script_cache_dir.mkdir(parents=True)
            
            # Create cached file with old content
            category_dir = repo.script_cache_dir / "install"
            category_dir.mkdir(parents=True)
            cached_file = category_dir / "test.sh"
            old_content = b"#!/bin/bash\necho 'old version'\n"
            with open(cached_file, 'wb') as f:
                f.write(old_content)
            
            # Manifest has new content checksum
            new_content = b"#!/bin/bash\necho 'new version'\n"
            remote_checksum = hashlib.sha256(new_content).hexdigest()
            
            script_id = "test-script"
            manifest = {
                "scripts": [{
                    "id": script_id,
                    "category": "install",
                    "file_name": "test.sh",
                    "download_url": "https://example.com/test.sh",
                    "checksum": remote_checksum
                }]
            }
            
            manifest_file = Path(tmpdir) / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f)
            repo.manifest_file = manifest_file
            
            # Simulate update detection logic
            script_info = repo.get_script_by_id(script_id)
            assert script_info is not None
            
            remote_checksum_normalized = script_info.get('checksum', '').replace('sha256:', '')
            cached_path = repo.get_cached_script_path(script_id)
            
            assert cached_path is not None
            assert Path(cached_path).exists()
            
            # Calculate local checksum
            with open(cached_path, 'rb') as f:
                local_checksum = hashlib.sha256(f.read()).hexdigest()
            
            # Should detect update
            has_update = local_checksum != remote_checksum_normalized
            assert has_update is True, "Should detect update when checksums differ"
    
    def test_no_update_when_checksums_match(self):
        """Test that no update is detected when checksums match"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir)
            repo.script_cache_dir = Path(tmpdir) / "script_cache"
            repo.script_cache_dir.mkdir(parents=True)
            
            # Create cached file
            category_dir = repo.script_cache_dir / "install"
            category_dir.mkdir(parents=True)
            cached_file = category_dir / "test.sh"
            content = b"#!/bin/bash\necho 'same version'\n"
            with open(cached_file, 'wb') as f:
                f.write(content)
            
            # Manifest has same checksum
            checksum = hashlib.sha256(content).hexdigest()
            
            script_id = "test-script"
            manifest = {
                "scripts": [{
                    "id": script_id,
                    "category": "install",
                    "file_name": "test.sh",
                    "download_url": "https://example.com/test.sh",
                    "checksum": checksum
                }]
            }
            
            manifest_file = Path(tmpdir) / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f)
            repo.manifest_file = manifest_file
            
            # Simulate update detection logic
            script_info = repo.get_script_by_id(script_id)
            remote_checksum_normalized = script_info.get('checksum', '').replace('sha256:', '')
            cached_path = repo.get_cached_script_path(script_id)
            
            with open(cached_path, 'rb') as f:
                local_checksum = hashlib.sha256(f.read()).hexdigest()
            
            # Should NOT detect update
            has_update = local_checksum != remote_checksum_normalized
            assert has_update is False, "Should not detect update when checksums match"
    
    def test_update_detection_handles_missing_checksum(self):
        """Test that update detection gracefully handles missing checksums"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir)
            repo.script_cache_dir = Path(tmpdir) / "script_cache"
            repo.script_cache_dir.mkdir(parents=True)
            
            # Create cached file
            category_dir = repo.script_cache_dir / "install"
            category_dir.mkdir(parents=True)
            cached_file = category_dir / "test.sh"
            with open(cached_file, 'wb') as f:
                f.write(b"#!/bin/bash\necho 'test'\n")
            
            # Manifest without checksum
            script_id = "test-script"
            manifest = {
                "scripts": [{
                    "id": script_id,
                    "category": "install",
                    "file_name": "test.sh",
                    "download_url": "https://example.com/test.sh"
                    # No checksum field
                }]
            }
            
            manifest_file = Path(tmpdir) / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f)
            repo.manifest_file = manifest_file
            
            # Simulate update detection logic with error handling
            has_update = False
            try:
                script_info = repo.get_script_by_id(script_id)
                if script_info:
                    remote_checksum = script_info.get('checksum', '').replace('sha256:', '')
                    if remote_checksum:  # Only check if checksum exists
                        cached_path = repo.get_cached_script_path(script_id)
                        if cached_path and Path(cached_path).exists():
                            with open(cached_path, 'rb') as f:
                                local_checksum = hashlib.sha256(f.read()).hexdigest()
                            has_update = local_checksum != remote_checksum
            except Exception:
                pass
            
            # Should not crash and should default to False
            assert has_update is False, "Should handle missing checksum gracefully"


class TestCheckForUpdatesCount:
    """Test that check_for_updates correctly counts available updates"""
    
    def test_check_for_updates_counts_correctly(self):
        """Test that check_for_updates returns correct count"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = ScriptRepository()
            repo.config_dir = Path(tmpdir)
            repo.script_cache_dir = Path(tmpdir) / "script_cache"
            repo.script_cache_dir.mkdir(parents=True)
            
            # Ensure auto_install_updates is disabled
            repo.config = {"auto_install_updates": False}
            
            # Create 2 cached scripts - one outdated, one current
            old_content = b"#!/bin/bash\necho 'old'\n"
            new_content = b"#!/bin/bash\necho 'new'\n"
            
            # Script 1 - outdated
            script1_dir = repo.script_cache_dir / "install"
            script1_dir.mkdir(parents=True)
            script1_file = script1_dir / "script1.sh"
            with open(script1_file, 'wb') as f:
                f.write(old_content)
            
            # Script 2 - current
            script2_file = script1_dir / "script2.sh"
            with open(script2_file, 'wb') as f:
                f.write(new_content)
            
            new_checksum = hashlib.sha256(new_content).hexdigest()
            
            manifest = {
                "scripts": [
                    {
                        "id": "script1",
                        "category": "install",
                        "file_name": "script1.sh",
                        "download_url": "https://example.com/script1.sh",
                        "checksum": new_checksum  # Different from cached
                    },
                    {
                        "id": "script2",
                        "category": "install",
                        "file_name": "script2.sh",
                        "download_url": "https://example.com/script2.sh",
                        "checksum": new_checksum  # Same as cached
                    }
                ]
            }
            
            manifest_file = Path(tmpdir) / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f)
            repo.manifest_file = manifest_file
            
            # Mock fetch to avoid network call
            with patch.object(repo, 'fetch_remote_manifest', return_value=True):
                update_count = repo.check_for_updates()
            
            assert update_count == 1, f"Should find 1 update, found {update_count}"
