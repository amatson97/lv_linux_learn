#!/usr/bin/env python3
"""
Simple test runner for script_execution module
Doesn't require pytest - can be run directly
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.script_execution import (
    ScriptEnvironmentManager,
    ScriptExecutionContext,
    ScriptValidator,
    get_script_env_requirements,
    validate_script_env_var,
    build_script_command
)


class TestRunner:
    """Simple test runner"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def assert_equal(self, actual, expected, msg=""):
        if actual != expected:
            error = f"FAIL: {msg}\n  Expected: {expected}\n  Got: {actual}"
            self.errors.append(error)
            self.failed += 1
            print(f"✗ {error}")
            return False
        self.passed += 1
        return True
    
    def assert_true(self, condition, msg=""):
        return self.assert_equal(condition, True, msg)
    
    def assert_false(self, condition, msg=""):
        return self.assert_equal(condition, False, msg)
    
    def assert_in(self, needle, haystack, msg=""):
        if needle not in haystack:
            error = f"FAIL: {msg}\n  '{needle}' not in '{haystack}'"
            self.errors.append(error)
            self.failed += 1
            print(f"✗ {error}")
            return False
        self.passed += 1
        return True
    
    def run_test(self, test_func, name):
        """Run a single test function"""
        try:
            print(f"  Testing: {name}...", end=" ")
            test_func(self)
            print("✓")
        except Exception as e:
            self.failed += 1
            self.errors.append(f"ERROR in {name}: {e}")
            print(f"✗ ERROR: {e}")
    
    def summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print(f"Tests: {self.passed + self.failed} total")
        print(f"  ✓ Passed: {self.passed}")
        print(f"  ✗ Failed: {self.failed}")
        
        if self.errors:
            print("\nFailures:")
            for error in self.errors:
                print(f"  {error}")
        
        return 0 if self.failed == 0 else 1


def test_env_manager_vpn_detection(runner):
    """VPN scripts should require ZEROTIER_NETWORK_ID"""
    manager = ScriptEnvironmentManager()
    
    env_vars = manager.get_required_env_vars("new_vpn.sh")
    runner.assert_in('ZEROTIER_NETWORK_ID', env_vars, 
                     "VPN script should require ZEROTIER_NETWORK_ID")
    
    env_vars = manager.get_required_env_vars("docker_install.sh")
    runner.assert_equal(len(env_vars), 0, 
                       "Non-VPN script should require no env vars")


def test_env_manager_validation_valid(runner):
    """Valid network IDs should pass validation"""
    manager = ScriptEnvironmentManager()
    
    is_valid, _ = manager.validate_env_var('ZEROTIER_NETWORK_ID', '8bd5124fd60a971f')
    runner.assert_true(is_valid, "Valid lowercase hex should pass")
    
    is_valid, _ = manager.validate_env_var('ZEROTIER_NETWORK_ID', '8BD5124FD60A971F')
    runner.assert_true(is_valid, "Valid uppercase hex should pass")


def test_env_manager_validation_invalid(runner):
    """Invalid network IDs should fail validation"""
    manager = ScriptEnvironmentManager()
    
    is_valid, error = manager.validate_env_var('ZEROTIER_NETWORK_ID', 'invalid')
    runner.assert_false(is_valid, "Invalid format should fail")
    runner.assert_in('hexadecimal', error.lower(), "Error should mention hexadecimal")
    
    is_valid, _ = manager.validate_env_var('ZEROTIER_NETWORK_ID', '')
    runner.assert_false(is_valid, "Empty value should fail")


def test_env_manager_build_exports(runner):
    """Environment export string should be properly formatted"""
    manager = ScriptEnvironmentManager()
    
    exports = manager.build_env_exports({'VAR1': 'value1'})
    runner.assert_in("export VAR1='value1'", exports, "Export should contain variable")
    
    exports = manager.build_env_exports({})
    runner.assert_equal(exports, "", "Empty dict should return empty string")


def test_execution_context_command_local(runner):
    """Local scripts should execute from their location"""
    context = ScriptExecutionContext()
    
    command = context.build_execution_command(
        script_path='/home/user/script.sh',
        script_type='local',
        source_type='custom_local',
        env_exports='',
        use_source=True
    )
    
    runner.assert_in('source', command, "Command should use source")
    runner.assert_in('/home/user/script.sh', command, "Command should include script path")


def test_execution_context_command_cached(runner):
    """Cached scripts should execute from cache with cd"""
    context = ScriptExecutionContext()
    
    command = context.build_execution_command(
        script_path='/cache/install/docker.sh',
        script_type='cached',
        source_type='public_repo',
        env_exports='',
        use_source=True
    )
    
    runner.assert_in('cd', command, "Command should include cd")
    runner.assert_in('script_cache', command, "Command should reference cache directory")


def test_validator_empty_path(runner):
    """Empty path should fail validation"""
    validator = ScriptValidator()
    
    is_valid, error = validator.validate_script_path('')
    runner.assert_false(is_valid, "Empty path should be invalid")
    runner.assert_in('empty', error.lower(), "Error should mention empty")


def test_validator_nonexistent_file(runner):
    """Non-existent file should fail validation"""
    validator = ScriptValidator()
    
    is_valid, error = validator.validate_script_path('/nonexistent/file.sh')
    runner.assert_false(is_valid, "Non-existent file should be invalid")
    runner.assert_in('not found', error.lower(), "Error should mention not found")


def test_convenience_functions(runner):
    """High-level convenience functions should work"""
    # Test get_script_env_requirements
    env_vars = get_script_env_requirements('new_vpn.sh')
    runner.assert_in('ZEROTIER_NETWORK_ID', env_vars, 
                     "Convenience function should detect VPN requirements")
    
    # Test validate_script_env_var
    is_valid, _ = validate_script_env_var('ZEROTIER_NETWORK_ID', '8bd5124fd60a971f')
    runner.assert_true(is_valid, "Convenience validation should work")


def main():
    """Run all tests"""
    print("="*70)
    print("Testing lib/script_execution.py")
    print("="*70)
    
    runner = TestRunner()
    
    print("\n📋 ScriptEnvironmentManager Tests:")
    runner.run_test(test_env_manager_vpn_detection, "VPN detection")
    runner.run_test(test_env_manager_validation_valid, "Valid network ID validation")
    runner.run_test(test_env_manager_validation_invalid, "Invalid network ID validation")
    runner.run_test(test_env_manager_build_exports, "Environment export building")
    
    print("\n📋 ScriptExecutionContext Tests:")
    runner.run_test(test_execution_context_command_local, "Local script command building")
    runner.run_test(test_execution_context_command_cached, "Cached script command building")
    
    print("\n📋 ScriptValidator Tests:")
    runner.run_test(test_validator_empty_path, "Empty path validation")
    runner.run_test(test_validator_nonexistent_file, "Non-existent file validation")
    
    print("\n📋 Convenience Function Tests:")
    runner.run_test(test_convenience_functions, "High-level API functions")
    
    return runner.summary()


if __name__ == '__main__':
    sys.exit(main())
