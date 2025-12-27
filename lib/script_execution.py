"""
Script Execution Business Logic

Pure functions for script execution, validation, and environment variable management.
Separated from UI concerns for testability.
"""

import os
import re
from typing import Optional, Dict, Tuple
from pathlib import Path


class ScriptEnvironmentManager:
    """Manages environment variables required by scripts"""
    
    @staticmethod
    def get_required_env_vars(script_name: str) -> Dict[str, Dict]:
        """
        Determine which environment variables a script requires.
        
        Args:
            script_name: Name of the script (e.g., 'new_vpn.sh')
        
        Returns:
            Dict mapping env var name to requirements:
            {
                'ZEROTIER_NETWORK_ID': {
                    'required': True,
                    'validator': 'zerotier_network_id',
                    'prompt': 'Enter your ZeroTier Network ID',
                    'description': 'ZeroTier network identifier (16 hex chars)'
                }
            }
        """
        env_requirements = {}
        
        # Check for VPN/ZeroTier scripts
        if 'vpn' in script_name.lower() or 'zerotier' in script_name.lower():
            env_requirements['ZEROTIER_NETWORK_ID'] = {
                'required': True,
                'validator': 'zerotier_network_id',
                'prompt': 'Enter your ZeroTier Network ID',
                'description': 'ZeroTier network identifier (16 hex characters)',
                'help_url': 'https://my.zerotier.com/',
                'example': '8bd5124fd60a971f'
            }
        
        return env_requirements
    
    @staticmethod
    def validate_env_var(var_name: str, value: str) -> Tuple[bool, str]:
        """
        Validate an environment variable value.
        
        Args:
            var_name: Name of the environment variable
            value: Value to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not value:
            return False, f"{var_name} cannot be empty"
        
        # ZeroTier network ID validation
        if var_name == 'ZEROTIER_NETWORK_ID':
            if not re.match(r'^[0-9a-fA-F]{16}$', value):
                return False, "Invalid network ID format (must be 16 hexadecimal characters)"
            return True, ""
        
        # Default: any non-empty value is valid
        return True, ""
    
    @staticmethod
    def is_env_var_set(var_name: str) -> bool:
        """Check if environment variable is already set"""
        return var_name in os.environ and bool(os.environ[var_name])
    
    @staticmethod
    def build_env_exports(env_vars: Dict[str, str]) -> str:
        """
        Build shell export commands for environment variables.
        
        Args:
            env_vars: Dict mapping var names to values
        
        Returns:
            Shell command string with exports (e.g., "export VAR1='val1'; export VAR2='val2'; ")
        """
        if not env_vars:
            return ""
        
        exports = []
        for key, value in env_vars.items():
            # Escape single quotes in value
            escaped_value = value.replace("'", "'\\''")
            exports.append(f"export {key}='{escaped_value}'")
        
        return "; ".join(exports) + "; " if exports else ""


class ScriptExecutionContext:
    """Determines and manages script execution context"""
    
    @staticmethod
    def determine_script_type(script_path: str, metadata: Optional[Dict] = None) -> str:
        """
        Determine script type from path and metadata.
        
        Args:
            script_path: Full path to script
            metadata: Optional metadata dict
        
        Returns:
            One of: 'local', 'cached', 'remote'
        """
        if metadata:
            return metadata.get('type', 'remote')
        
        # Heuristic determination
        if os.path.isfile(script_path):
            if '/.lv_linux_learn/script_cache/' in script_path:
                return 'cached'
            return 'local'
        
        return 'remote'
    
    @staticmethod
    def determine_source_type(script_path: str, metadata: Optional[Dict] = None) -> str:
        """
        Determine script source type.
        
        Args:
            script_path: Full path to script
            metadata: Optional metadata dict
        
        Returns:
            One of: 'custom_script', 'custom_local', 'public_repo', 'custom_repo'
        """
        if metadata:
            return metadata.get('source_type', 'unknown')
        
        # Heuristic determination
        if 'custom_scripts' in script_path:
            return 'custom_script'
        elif 'custom_manifests' in script_path:
            return 'custom_local'
        elif '/.lv_linux_learn/script_cache/' in script_path:
            return 'public_repo'
        
        return 'unknown'
    
    @staticmethod
    def build_execution_command(
        script_path: str,
        script_type: str,
        source_type: str,
        env_exports: str = "",
        use_source: bool = True
    ) -> str:
        """
        Build the command to execute a script.
        
        Args:
            script_path: Full path to script
            script_type: 'local', 'cached', or 'remote'
            source_type: Source type of script
            env_exports: Environment variable export commands
            use_source: If True, use 'source' instead of 'bash' for interactive scripts
        
        Returns:
            Shell command string to execute
        """
        executor = "source" if use_source else "bash"
        
        # Local custom scripts - execute directly from original location
        if script_type == "local" or source_type == "custom_local":
            abs_path = os.path.abspath(script_path)
            return f"{env_exports}{executor} '{abs_path}'\n"
        
        # Cached scripts - execute from cache with cd
        elif script_type == "cached":
            cache_root = os.path.expanduser("~/.lv_linux_learn/script_cache")
            return f"{env_exports}cd '{cache_root}' && {executor} '{script_path}'\n"
        
        # Remote - shouldn't execute, return empty
        return ""
    
    @staticmethod
    def get_script_directory(script_path: str, script_type: str) -> Optional[str]:
        """
        Get the directory to navigate to for a script.
        
        Args:
            script_path: Full path to script
            script_type: 'local', 'cached', or 'remote'
        
        Returns:
            Directory path or None if not applicable
        """
        if script_type == "local":
            file_path = script_path[7:] if script_path.startswith('file://') else script_path
            if os.path.isfile(file_path):
                return os.path.dirname(os.path.abspath(file_path))
        
        elif script_type == "cached":
            if os.path.isfile(script_path):
                return os.path.dirname(os.path.abspath(script_path))
        
        return None
    
    @staticmethod
    def should_prompt_for_download(script_type: str) -> bool:
        """Check if script needs to be downloaded before execution"""
        return script_type == "remote"


class ScriptValidator:
    """Validates script paths and requirements"""
    
    @staticmethod
    def validate_script_path(script_path: str) -> Tuple[bool, str]:
        """
        Validate that a script path is accessible.
        
        Args:
            script_path: Path to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not script_path:
            return False, "Script path is empty"
        
        # Handle file:// URIs
        file_path = script_path[7:] if script_path.startswith('file://') else script_path
        
        if not os.path.exists(file_path):
            return False, f"Script file not found: {file_path}"
        
        if not os.path.isfile(file_path):
            return False, f"Path is not a file: {file_path}"
        
        return True, ""
    
    @staticmethod
    def validate_execution_readiness(
        script_path: str,
        script_type: str,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Validate that script is ready for execution.
        
        Args:
            script_path: Path to script
            script_type: Type of script
            metadata: Optional metadata
        
        Returns:
            Tuple of (is_ready, status_message)
        """
        # Remote scripts need to be downloaded first
        if script_type == "remote":
            source_type = metadata.get('source_type', 'unknown') if metadata else 'unknown'
            if source_type == "public_repo":
                return False, "Online Public script not cached. Use Download button first."
            elif source_type == "custom_repo":
                return False, "Online Custom script not cached. Use Download button first."
            else:
                return False, "Script not cached. Use Download button first."
        
        # Validate path for local/cached scripts
        is_valid, error = ScriptValidator.validate_script_path(script_path)
        if not is_valid:
            return False, error
        
        return True, "Ready to execute"


# Convenience functions for common operations

def get_script_env_requirements(script_name: str) -> Dict[str, Dict]:
    """Get environment variable requirements for a script"""
    manager = ScriptEnvironmentManager()
    return manager.get_required_env_vars(script_name)


def validate_script_env_var(var_name: str, value: str) -> Tuple[bool, str]:
    """Validate an environment variable value"""
    manager = ScriptEnvironmentManager()
    return manager.validate_env_var(var_name, value)


def build_script_command(
    script_path: str,
    metadata: Optional[Dict] = None,
    env_vars: Optional[Dict[str, str]] = None
) -> Tuple[str, str]:
    """
    Build execution command for a script.
    
    Args:
        script_path: Path to script
        metadata: Script metadata
        env_vars: Environment variables to export
    
    Returns:
        Tuple of (command, status_message)
    """
    context = ScriptExecutionContext()
    env_manager = ScriptEnvironmentManager()
    validator = ScriptValidator()
    
    # Determine script type and source
    script_type = context.determine_script_type(script_path, metadata)
    source_type = context.determine_source_type(script_path, metadata)
    
    # Validate execution readiness
    is_ready, message = validator.validate_execution_readiness(script_path, script_type, metadata)
    if not is_ready:
        return "", message
    
    # Build environment exports
    env_exports = env_manager.build_env_exports(env_vars or {})
    
    # Build command
    command = context.build_execution_command(
        script_path, script_type, source_type, env_exports
    )
    
    return command, "Command built successfully"
