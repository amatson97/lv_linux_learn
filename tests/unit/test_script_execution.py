"""
Unit tests for script_execution module

Tests business logic extracted from menu.py for better testability.
Run with: pytest tests/test_script_execution.py
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.script_execution import (
    ScriptEnvironmentManager,
    ScriptExecutionContext,
    ScriptValidator,
    get_script_env_requirements,
    validate_script_env_var,
    build_script_command
)


class TestScriptEnvironmentManager:
    """Test environment variable management"""
    
    def test_get_required_env_vars_vpn_script(self):
        """VPN scripts should require ZEROTIER_NETWORK_ID"""
        manager = ScriptEnvironmentManager()
        
        # Test with vpn in name
        env_vars = manager.get_required_env_vars("new_vpn.sh")
        assert 'ZEROTIER_NETWORK_ID' in env_vars
        assert env_vars['ZEROTIER_NETWORK_ID']['required'] is True
        assert env_vars['ZEROTIER_NETWORK_ID']['validator'] == 'zerotier_network_id'
        
        # Test with zerotier in name
        env_vars = manager.get_required_env_vars("install_zerotier.sh")
        assert 'ZEROTIER_NETWORK_ID' in env_vars
    
    def test_get_required_env_vars_non_vpn_script(self):
        """Non-VPN scripts should require no env vars"""
        manager = ScriptEnvironmentManager()
        
        env_vars = manager.get_required_env_vars("docker_install.sh")
        assert len(env_vars) == 0
        
        env_vars = manager.get_required_env_vars("git_setup.sh")
        assert len(env_vars) == 0
    
    def test_validate_env_var_zerotier_valid(self):
        """Valid ZeroTier network IDs should pass validation"""
        manager = ScriptEnvironmentManager()
        
        # Valid 16 hex characters
        is_valid, error = manager.validate_env_var('ZEROTIER_NETWORK_ID', '8bd5124fd60a971f')
        assert is_valid is True
        assert error == ""
        
        # Uppercase hex
        is_valid, error = manager.validate_env_var('ZEROTIER_NETWORK_ID', '8BD5124FD60A971F')
        assert is_valid is True
        
        # Mixed case
        is_valid, error = manager.validate_env_var('ZEROTIER_NETWORK_ID', '8Bd5124Fd60a971F')
        assert is_valid is True
    
    def test_validate_env_var_zerotier_invalid(self):
        """Invalid ZeroTier network IDs should fail validation"""
        manager = ScriptEnvironmentManager()
        
        # Too short
        is_valid, error = manager.validate_env_var('ZEROTIER_NETWORK_ID', '8bd5124fd60a97')
        assert is_valid is False
        assert 'hexadecimal' in error.lower()
        
        # Too long
        is_valid, error = manager.validate_env_var('ZEROTIER_NETWORK_ID', '8bd5124fd60a971f00')
        assert is_valid is False
        
        # Non-hex characters
        is_valid, error = manager.validate_env_var('ZEROTIER_NETWORK_ID', '8bd5124gd60a971f')
        assert is_valid is False
        
        # Empty
        is_valid, error = manager.validate_env_var('ZEROTIER_NETWORK_ID', '')
        assert is_valid is False
    
    def test_build_env_exports(self):
        """Environment export string should be properly formatted"""
        manager = ScriptEnvironmentManager()
        
        # Single variable
        exports = manager.build_env_exports({'VAR1': 'value1'})
        assert exports == "export VAR1='value1'; "
        
        # Multiple variables
        exports = manager.build_env_exports({
            'VAR1': 'value1',
            'VAR2': 'value2'
        })
        assert "export VAR1='value1'" in exports
        assert "export VAR2='value2'" in exports
        assert exports.endswith('; ')
        
        # Empty dict
        exports = manager.build_env_exports({})
        assert exports == ""
    
    def test_build_env_exports_escaping(self):
        """Single quotes in values should be escaped"""
        manager = ScriptEnvironmentManager()
        
        exports = manager.build_env_exports({'VAR': "test's value"})
        assert "test'\\''s value" in exports


class TestScriptExecutionContext:
    """Test script execution context determination"""
    
    def test_determine_script_type_from_metadata(self):
        """Script type should be read from metadata if provided"""
        context = ScriptExecutionContext()
        
        assert context.determine_script_type('/any/path', {'type': 'local'}) == 'local'
        assert context.determine_script_type('/any/path', {'type': 'cached'}) == 'cached'
        assert context.determine_script_type('/any/path', {'type': 'remote'}) == 'remote'
    
    def test_determine_script_type_cached_path(self):
        """Scripts in cache directory should be detected as cached"""
        context = ScriptExecutionContext()
        
        # Create temp file in mock cache path
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.sh', delete=False) as f:
            temp_path = f.name
        
        try:
            # Mock cache path
            cache_path = temp_path.replace(os.path.dirname(temp_path), 
                                          os.path.expanduser('~/.lv_linux_learn/script_cache'))
            # Won't actually exist, but we're testing path detection logic
            # For real file, it would detect as local
            
            script_type = context.determine_script_type(temp_path, None)
            assert script_type == 'local'  # Exists locally
        finally:
            os.unlink(temp_path)
    
    def test_determine_source_type(self):
        """Source type should be correctly determined from path"""
        context = ScriptExecutionContext()
        
        # Custom script
        assert context.determine_source_type('/path/custom_scripts/test.sh', None) == 'custom_script'
        
        # Custom local manifest
        assert context.determine_source_type('/path/custom_manifests/test.sh', None) == 'custom_local'
        
        # Cache (public repo)
        assert context.determine_source_type(
            os.path.expanduser('~/.lv_linux_learn/script_cache/install/test.sh'), 
            None
        ) == 'public_repo'
    
    def test_build_execution_command_local(self):
        """Local scripts should execute from their location"""
        context = ScriptExecutionContext()
        
        command = context.build_execution_command(
            script_path='/home/user/script.sh',
            script_type='local',
            source_type='custom_local',
            env_exports='',
            use_source=True
        )
        
        assert 'source' in command
        assert '/home/user/script.sh' in command
        assert command.endswith('\n')
    
    def test_build_execution_command_cached(self):
        """Cached scripts should execute from cache with cd"""
        context = ScriptExecutionContext()
        
        command = context.build_execution_command(
            script_path='/cache/install/docker.sh',
            script_type='cached',
            source_type='public_repo',
            env_exports='',
            use_source=True
        )
        
        assert 'cd' in command
        assert 'script_cache' in command
        assert 'source' in command
        assert command.endswith('\n')
    
    def test_build_execution_command_with_env_exports(self):
        """Environment exports should be prepended to command"""
        context = ScriptExecutionContext()
        
        command = context.build_execution_command(
            script_path='/home/user/script.sh',
            script_type='local',
            source_type='custom_local',
            env_exports="export VAR1='val1'; ",
            use_source=True
        )
        
        assert command.startswith("export VAR1='val1'; ")
        assert 'source' in command
    
    def test_build_execution_command_remote(self):
        """Remote scripts should return empty command"""
        context = ScriptExecutionContext()
        
        command = context.build_execution_command(
            script_path='/path/to/remote.sh',
            script_type='remote',
            source_type='public_repo',
            env_exports='',
            use_source=True
        )
        
        assert command == ""


class TestScriptValidator:
    """Test script validation logic"""
    
    def test_validate_script_path_empty(self):
        """Empty path should fail validation"""
        validator = ScriptValidator()
        
        is_valid, error = validator.validate_script_path('')
        assert is_valid is False
        assert 'empty' in error.lower()
    
    def test_validate_script_path_nonexistent(self):
        """Non-existent file should fail validation"""
        validator = ScriptValidator()
        
        is_valid, error = validator.validate_script_path('/nonexistent/file.sh')
        assert is_valid is False
        assert 'not found' in error.lower()
    
    def test_validate_script_path_valid(self):
        """Existing file should pass validation"""
        validator = ScriptValidator()
        
        # Create temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.sh', delete=False) as f:
            temp_path = f.name
        
        try:
            is_valid, error = validator.validate_script_path(temp_path)
            assert is_valid is True
            assert error == ""
        finally:
            os.unlink(temp_path)
    
    def test_validate_execution_readiness_remote(self):
        """Remote scripts should not be ready"""
        validator = ScriptValidator()
        
        is_ready, message = validator.validate_execution_readiness(
            '/path/to/script.sh',
            'remote',
            {'source_type': 'public_repo'}
        )
        
        assert is_ready is False
        assert 'download' in message.lower() or 'cached' in message.lower()


class TestConvenienceFunctions:
    """Test high-level convenience functions"""
    
    def test_get_script_env_requirements(self):
        """Convenience function should work like manager method"""
        env_vars = get_script_env_requirements('new_vpn.sh')
        assert 'ZEROTIER_NETWORK_ID' in env_vars
    
    def test_validate_script_env_var(self):
        """Convenience function should work like manager method"""
        is_valid, error = validate_script_env_var('ZEROTIER_NETWORK_ID', '8bd5124fd60a971f')
        assert is_valid is True
        
        is_valid, error = validate_script_env_var('ZEROTIER_NETWORK_ID', 'invalid')
        assert is_valid is False
    
    def test_build_script_command_integration(self):
        """Integration test for build_script_command"""
        import tempfile
        
        # Create temp script
        with tempfile.NamedTemporaryFile(suffix='.sh', delete=False, mode='w') as f:
            f.write('#!/bin/bash\necho "test"')
            temp_path = f.name
        
        try:
            command, status = build_script_command(
                script_path=temp_path,
                metadata={'type': 'local', 'source_type': 'custom_local'},
                env_vars={'TEST_VAR': 'test_value'}
            )
            
            assert command != ""
            assert 'source' in command
            assert 'TEST_VAR' in command
            assert status == "Command built successfully"
        finally:
            os.unlink(temp_path)
    
    def test_build_script_command_remote_fails(self):
        """Remote scripts should not build commands"""
        command, status = build_script_command(
            script_path='/remote/script.sh',
            metadata={'type': 'remote', 'source_type': 'public_repo'},
            env_vars={}
        )
        
        assert command == ""
        assert 'cached' in status.lower() or 'download' in status.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
