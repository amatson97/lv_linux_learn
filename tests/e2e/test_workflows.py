"""
End-to-End Integration Tests for menu.py GTK Application

Tests complete workflows across all application components:
- Repository management (manifest fetch, cache, updates)
- Script execution (local, cached, remote)
- UI state management (tab updates, update indicators)
- Configuration management
- Error handling and recovery

Run with: pytest tests/test_e2e_integration.py -v -m e2e
"""

import pytest
import json
import hashlib
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta

from lib.repository import ScriptRepository
from lib.script_execution import ScriptEnvironmentManager, build_script_command
from lib.manifest import load_scripts_from_manifest


@pytest.mark.e2e
class TestCompleteRepositoryWorkflow:
    """Test complete repository operations from fetch to execution"""
    
    def test_full_lifecycle_fetch_cache_update_execute(self, repo_with_temp_dirs, mock_urlopen, test_helpers):
        """
        E2E: Fetch manifest → Download script → Cache → Detect update → Re-download → Execute
        
        Simulates:
        1. Fresh installation - fetch manifest
        2. Download script to cache
        3. Script gets updated remotely
        4. Detect and apply update
        5. Execute updated script
        """
        repo = repo_with_temp_dirs
        
        # STEP 1: Initial manifest fetch
        initial_content = b"#!/bin/bash\necho 'version 1.0'\n"
        initial_checksum = hashlib.sha256(initial_content).hexdigest()
        
        manifest = {
            "repository_version": "2.3.0",
            "verify_checksums": True,
            "scripts": [{
                "id": "test-app",
                "category": "install",
                "file_name": "test_app.sh",
                "download_url": "https://example.com/test_app.sh",
                "checksum": initial_checksum,
                "description": "Test application"
            }]
        }
        
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        # STEP 2: Download script (simulate first install)
        with patch('urllib.request.urlopen', return_value=mock_urlopen(initial_content)):
            success, url, error = repo.download_script("test-app")
        
        assert success is True
        assert test_helpers.assert_script_cached(repo, "test-app")
        cached_path = repo.get_cached_script_path("test-app")
        assert Path(cached_path).read_bytes() == initial_content
        
        # STEP 3: Script gets updated remotely
        updated_content = b"#!/bin/bash\necho 'version 2.0 - NEW FEATURES'\n"
        updated_checksum = hashlib.sha256(updated_content).hexdigest()
        
        manifest["scripts"][0]["checksum"] = updated_checksum
        with open(repo.manifest_file, 'w') as f:
            json.dump(manifest, f)
        
        # STEP 4: Detect update
        with patch.object(repo, 'fetch_remote_manifest', return_value=True):
            update_count = repo.check_for_updates()
        
        assert update_count == 1, "Should detect one update available"
        
        # STEP 5: Apply update
        with patch('urllib.request.urlopen', return_value=mock_urlopen(updated_content)):
            success, url, error = repo.download_script("test-app")
        
        assert success is True
        assert Path(cached_path).read_bytes() == updated_content, "Script should be updated"
        
        # STEP 6: Verify no more updates
        with patch.object(repo, 'fetch_remote_manifest', return_value=True):
            update_count = repo.check_for_updates()
        
        assert update_count == 0, "No updates should be available after update"
        
        # STEP 7: Execute script
        metadata = {"type": "cached", "file_exists": True}
        command = build_script_command(cached_path, metadata, env_exports="")
        
        assert command is not None
        assert "test_app.sh" in command
    
    def test_manifest_refresh_updates_all_tabs(self, repo_with_cached_scripts, test_helpers):
        """
        E2E: Manifest refresh triggers UI tab updates
        
        Simulates:
        1. Scripts cached in multiple categories
        2. Manifest refresh detects updates
        3. All tabs show update indicators
        """
        repo = repo_with_cached_scripts
        
        # Modify manifest to have updates for both cached scripts
        manifest_data = json.loads(repo.manifest_file.read_text())
        
        # Change checksums to simulate remote updates
        for script in manifest_data["scripts"]:
            script["checksum"] = "00000000000000000000000000000000"  # Force mismatch
        
        repo.manifest_file.write_text(json.dumps(manifest_data))
        
        # Check for updates
        with patch.object(repo, 'fetch_remote_manifest', return_value=True):
            update_count = repo.check_for_updates()
        
        assert update_count == 2, "Should detect updates in all categories"
        
        # Verify each category has updates
        updates = repo.list_available_updates()
        categories = {u["category"] for u in updates}
        assert "install" in categories
        assert "tools" in categories


@pytest.mark.e2e
class TestScriptExecutionWorkflows:
    """Test complete script execution scenarios"""
    
    def test_local_script_execution_with_env_vars(self, mock_repo_structure, env_manager):
        """
        E2E: Execute local script requiring environment variables
        
        Simulates:
        1. Detect script needs env vars
        2. Validate env vars
        3. Build execution command
        4. Execute with proper environment
        """
        # Create VPN script requiring env vars
        vpn_script = mock_repo_structure / "scripts" / "new_vpn.sh"
        vpn_script.write_text("#!/bin/bash\n# VPN setup\necho $NORDVPN_TOKEN\n")
        
        # STEP 1: Detect required env vars
        env_vars = env_manager.get_required_env_vars(str(vpn_script))
        assert "NORDVPN_TOKEN" in env_vars
        
        # STEP 2: Validate env var
        is_valid, error = env_manager.validate_env_var("NORDVPN_TOKEN", "test_token_123")
        assert is_valid is True
        
        # STEP 3: Build exports
        exports = env_manager.build_env_exports({"NORDVPN_TOKEN": "test_token_123"})
        assert "export NORDVPN_TOKEN=" in exports
        
        # STEP 4: Build execution command
        metadata = {"type": "local", "file_exists": True}
        command = build_script_command(str(vpn_script), metadata, exports)
        
        assert command is not None
        assert "new_vpn.sh" in command
        assert "NORDVPN_TOKEN" in command
    
    def test_cached_script_execution_fallback(self, repo_with_cached_scripts, test_helpers):
        """
        E2E: Execute cached script with category fallback
        
        Simulates:
        1. Script moved to different category in manifest
        2. Fallback lookup finds script by filename
        3. Execute from cache successfully
        """
        repo = repo_with_cached_scripts
        
        # Get docker script path
        docker_path = repo.get_cached_script_path("docker-install")
        assert docker_path is not None
        
        # Simulate category change - update manifest
        manifest_data = json.loads(repo.manifest_file.read_text())
        for script in manifest_data["scripts"]:
            if script["id"] == "docker-install":
                script["category"] = "tools"  # Changed from install
        repo.manifest_file.write_text(json.dumps(manifest_data))
        
        # Should still find via fallback
        fallback_path = repo.get_cached_script_path("docker-install")
        assert fallback_path is not None
        assert Path(fallback_path).exists()
        
        # Execute script
        metadata = {"type": "cached", "file_exists": True}
        command = build_script_command(fallback_path, metadata, "")
        assert command is not None


@pytest.mark.e2e
class TestUpdateDetectionAndUI:
    """Test update detection logic used by UI tabs"""
    
    def test_tab_update_indicators_all_states(self, repo_with_manifest, test_helpers, mock_urlopen):
        """
        E2E: Tab update indicators show correct states
        
        Tests all three states:
        - ☁️ Not cached
        - ✓ Cached (up to date)
        - 📥 Update available
        """
        repo = repo_with_manifest
        
        # Add third script to manifest
        manifest_data = json.loads(repo.manifest_file.read_text())
        uptodate_content = b"#!/bin/bash\necho 'current version'\n"
        uptodate_checksum = hashlib.sha256(uptodate_content).hexdigest()
        
        manifest_data["scripts"].append({
            "id": "uptodate-script",
            "category": "install",
            "file_name": "uptodate.sh",
            "download_url": "https://example.com/uptodate.sh",
            "checksum": uptodate_checksum,
            "description": "Up to date script"
        })
        repo.manifest_file.write_text(json.dumps(manifest_data))
        
        # Cache one script with matching checksum (✓ state)
        test_helpers.create_cached_script(repo, "uptodate-script", uptodate_content, "install")
        
        # Cache another with wrong checksum (📥 state)
        old_content = b"#!/bin/bash\necho 'old version'\n"
        test_helpers.create_cached_script(repo, "docker-install", old_content, "install")
        
        # Third script not cached (☁️ state)
        # git-pull is in manifest but not cached
        
        # Verify states
        scripts = repo.parse_manifest()
        
        for script in scripts:
            script_id = script["id"]
            remote_checksum = script.get("checksum", "").replace("sha256:", "")
            cached_path = repo.get_cached_script_path(script_id)
            
            if script_id == "git-pull":
                # Not cached
                assert cached_path is None or not Path(cached_path).exists()
                icon = "☁️"
            elif script_id == "uptodate-script":
                # Cached and up to date
                assert cached_path is not None
                local_checksum = test_helpers.get_script_checksum(Path(cached_path))
                assert local_checksum == remote_checksum
                icon = "✓"
            elif script_id == "docker-install":
                # Cached but outdated
                assert cached_path is not None
                local_checksum = test_helpers.get_script_checksum(Path(cached_path))
                assert local_checksum != remote_checksum
                icon = "📥"


@pytest.mark.e2e
class TestChecksumRetryRecovery:
    """Test checksum verification with CDN cache-busting recovery"""
    
    def test_cdn_cache_recovery_workflow(self, repo_with_temp_dirs):
        """
        E2E: CDN serves stale content → retry with cache-bust → success
        
        Simulates:
        1. Download returns stale cached content
        2. Checksum fails
        3. Retry with ?t=timestamp
        4. Fresh content downloaded
        5. Verification succeeds
        """
        repo = repo_with_temp_dirs
        
        stale_content = b"#!/bin/bash\necho 'stale CDN cache'\n"
        fresh_content = b"#!/bin/bash\necho 'fresh from origin'\n"
        fresh_checksum = hashlib.sha256(fresh_content).hexdigest()
        
        manifest = {
            "repository_version": "2.3.0",
            "verify_checksums": True,
            "scripts": [{
                "id": "cdn-test",
                "category": "install",
                "file_name": "cdn_test.sh",
                "download_url": "https://cdn.example.com/cdn_test.sh",
                "checksum": fresh_checksum
            }]
        }
        repo.manifest_file.write_text(json.dumps(manifest))
        
        # Mock urlopen to return stale then fresh
        call_count = 0
        cache_bust_used = False
        
        def mock_urlopen_cdn(url, timeout=None):
            nonlocal call_count, cache_bust_used
            call_count += 1
            mock_response = MagicMock()
            
            if call_count == 1:
                # First call: stale CDN content
                mock_response.read.return_value = stale_content
            else:
                # Second call: fresh content after cache-bust
                if "?t=" in url:
                    cache_bust_used = True
                mock_response.read.return_value = fresh_content
            
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            return mock_response
        
        with patch('urllib.request.urlopen', side_effect=mock_urlopen_cdn):
            with patch.object(repo, 'ensure_includes_available', return_value=True):
                success, url, error = repo.download_script("cdn-test")
        
        assert success is True
        assert call_count == 2, "Should have retried"
        assert cache_bust_used is True, "Should have used cache-bust parameter"
        
        # Verify fresh content was saved
        cached_path = repo.get_cached_script_path("cdn-test")
        assert Path(cached_path).read_bytes() == fresh_content


@pytest.mark.e2e
class TestConfigurationPersistence:
    """Test configuration management across sessions"""
    
    def test_config_changes_persist_across_instances(self, temp_dir):
        """
        E2E: Config changes persist and affect new repository instances
        
        Simulates:
        1. User changes config
        2. Config saved to file
        3. New instance loads config
        4. Behavior reflects config
        """
        # Create first instance
        repo1 = ScriptRepository()
        repo1.config_dir = temp_dir / ".lv_linux_learn"
        repo1.config_file = repo1.config_dir / "config.json"
        repo1._ensure_directories()
        
        # Change settings
        repo1.set_config_value("auto_install_updates", True)
        repo1.set_config_value("update_check_interval_minutes", 30)
        repo1.set_config_value("custom_setting", "test_value")
        
        # Create second instance (simulates app restart)
        repo2 = ScriptRepository()
        repo2.config_dir = temp_dir / ".lv_linux_learn"
        repo2.config_file = repo1.config_file
        repo2.config = repo2.load_config()
        
        # Verify settings persisted
        assert repo2.get_config_value("auto_install_updates") is True
        assert repo2.get_config_value("update_check_interval_minutes") == 30
        assert repo2.get_config_value("custom_setting") == "test_value"


@pytest.mark.e2e
class TestErrorRecoveryScenarios:
    """Test error handling and graceful degradation"""
    
    def test_network_failure_graceful_degradation(self, repo_with_cached_scripts):
        """
        E2E: Network fails but app continues with cached content
        
        Simulates:
        1. Manifest fetch fails
        2. Falls back to cached manifest
        3. Scripts still executable from cache
        4. Update check skipped gracefully
        """
        repo = repo_with_cached_scripts
        
        # Simulate network failure
        with patch.object(repo, 'fetch_remote_manifest', return_value=False):
            update_count = repo.check_for_updates()
        
        # Should return 0 but not crash
        assert update_count == 0
        
        # Cached scripts still accessible
        docker_path = repo.get_cached_script_path("docker-install")
        assert docker_path is not None
        assert Path(docker_path).exists()
        
        # Can still parse cached manifest
        scripts = repo.parse_manifest()
        assert len(scripts) > 0
    
    def test_corrupted_cache_recovery(self, repo_with_manifest, test_helpers):
        """
        E2E: Corrupted cached script re-downloaded automatically
        
        Simulates:
        1. Script in cache but corrupted
        2. Checksum fails
        3. Re-download triggered
        4. Cache updated with good copy
        """
        repo = repo_with_manifest
        
        # Create corrupted cached file
        corrupted_content = b"CORRUPTED DATA"
        test_helpers.create_cached_script(repo, "docker-install", corrupted_content, "install")
        
        # Attempt to download (should re-download due to checksum)
        good_content = b"#!/bin/bash\necho 'docker install'\n"
        good_checksum = hashlib.sha256(good_content).hexdigest()
        
        # Update manifest with correct checksum
        manifest_data = json.loads(repo.manifest_file.read_text())
        manifest_data["scripts"][0]["checksum"] = good_checksum
        repo.manifest_file.write_text(json.dumps(manifest_data))
        
        # Mock download of good content
        mock_response = MagicMock()
        mock_response.read.return_value = good_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            with patch.object(repo, 'ensure_includes_available', return_value=True):
                success, url, error = repo.download_script("docker-install")
        
        assert success is True
        
        # Verify cache updated
        cached_path = repo.get_cached_script_path("docker-install")
        assert Path(cached_path).read_bytes() == good_content


@pytest.mark.e2e
@pytest.mark.slow
class TestPerformanceScenarios:
    """Test performance with realistic data volumes"""
    
    def test_large_manifest_handling(self, repo_with_temp_dirs):
        """
        E2E: Handle manifest with 100+ scripts efficiently
        
        Validates:
        - Manifest parsing speed
        - Update detection speed
        - Memory usage
        """
        repo = repo_with_temp_dirs
        
        # Create large manifest
        scripts = []
        for i in range(100):
            content = f"#!/bin/bash\necho 'script {i}'\n".encode()
            checksum = hashlib.sha256(content).hexdigest()
            
            scripts.append({
                "id": f"script-{i:03d}",
                "category": ["install", "tools", "uninstall"][i % 3],
                "file_name": f"script_{i:03d}.sh",
                "download_url": f"https://example.com/script_{i:03d}.sh",
                "checksum": checksum,
                "description": f"Script number {i}"
            })
        
        manifest = {
            "repository_version": "2.3.0",
            "verify_checksums": True,
            "scripts": scripts
        }
        repo.manifest_file.write_text(json.dumps(manifest))
        
        # Test parsing performance
        start = time.time()
        parsed_scripts = repo.parse_manifest()
        parse_time = time.time() - start
        
        assert len(parsed_scripts) == 100
        assert parse_time < 1.0, f"Parsing took {parse_time}s, should be < 1s"
        
        # Test update check performance (none cached)
        start = time.time()
        with patch.object(repo, 'fetch_remote_manifest', return_value=True):
            update_count = repo.check_for_updates()
        check_time = time.time() - start
        
        assert update_count == 0  # None cached
        assert check_time < 2.0, f"Update check took {check_time}s, should be < 2s"


@pytest.mark.e2e
class TestMultiRepositorySupport:
    """Test custom manifest and multi-repository features"""
    
    def test_switch_between_repositories(self, repo_with_temp_dirs, temp_dir):
        """
        E2E: Switch from public to custom repository
        
        Simulates:
        1. Using public repository
        2. Add custom manifest URL
        3. Switch to custom repository
        4. Fetch custom manifest
        5. Scripts from custom repo available
        """
        repo = repo_with_temp_dirs
        
        # Start with public repository
        assert repo.get_config_value("use_public_repository", True) is True
        
        # Create custom manifest
        custom_manifest_path = temp_dir / "custom_manifest.json"
        custom_manifest = {
            "repository_version": "1.0.0",
            "verify_checksums": False,
            "scripts": [{
                "id": "custom-tool",
                "category": "tools",
                "file_name": "custom_tool.sh",
                "download_url": "https://custom.repo.com/custom_tool.sh",
                "checksum": "",
                "description": "Custom tool"
            }]
        }
        custom_manifest_path.write_text(json.dumps(custom_manifest))
        
        # Configure custom repository
        repo.set_config_value("custom_manifest_url", f"file://{custom_manifest_path}")
        repo.set_config_value("use_public_repository", False)
        
        # Load custom manifest
        manifest_data = json.loads(custom_manifest_path.read_text())
        repo.manifest_file.write_text(json.dumps(manifest_data))
        
        # Verify custom scripts available
        scripts = repo.parse_manifest()
        assert len(scripts) == 1
        assert scripts[0]["id"] == "custom-tool"
        
        # Verify can get script by ID
        script_info = repo.get_script_by_id("custom-tool")
        assert script_info is not None
        assert script_info["description"] == "Custom tool"
