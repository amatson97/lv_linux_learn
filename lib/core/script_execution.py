"""
Compatibility layer for script execution tests.
Provides thin wrappers around existing logic in lib.script.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import os

from lib.core.script import (
    ScriptEnvironment,
    ScriptExecutor,
    get_script_env_requirements,
    validate_script_env_var,
)


class ScriptEnvironmentManager:
    """Wrapper that delegates to ScriptEnvironment for env var handling."""

    def get_required_env_vars(self, script_name: str) -> Dict[str, Dict]:
        return ScriptEnvironment.get_required_vars(script_name)

    def validate_env_var(self, var_name: str, value: str) -> Tuple[bool, str]:
        return ScriptEnvironment.validate_var(var_name, value)

    def build_env_exports(self, env_vars: Dict[str, str]) -> str:
        return ScriptEnvironment.build_exports(env_vars)


class ScriptExecutionContext:
    """Wrapper that delegates to ScriptExecutor for type/source/command building."""

    def determine_script_type(self, script_path: str, metadata: Optional[Dict] = None) -> str:
        return ScriptExecutor._get_type(script_path, metadata)

    def determine_source_type(self, script_path: str, metadata: Optional[Dict] = None) -> str:
        return ScriptExecutor._get_source_type(script_path, metadata)

    def build_execution_command(
        self,
        script_path: str,
        script_type: str,
        source_type: str,
        env_exports: str = "",
        use_source: bool = False,
    ) -> str:
        executor = "source" if use_source else "bash"

        # Remote scripts are not executable until downloaded
        if script_type == "remote":
            return ""

        # Local/custom scripts: run directly from path
        if script_type == "local" or source_type == "custom_local":
            abs_path = script_path[7:] if script_path.startswith("file://") else script_path
            command = f"{executor} '{abs_path}'\n"
        elif script_type == "cached":
            cache_root = os.path.expanduser("~/.lv_linux_learn/script_cache")
            command = f"(cd '{cache_root}' && {executor} '{script_path}')\n"
        else:
            return ""

        if env_exports:
            return f"{env_exports}{command}"
        return command


class ScriptValidator:
    """Basic validation helpers for tests."""

    def validate_script_path(self, script_path: str) -> Tuple[bool, str]:
        if not script_path:
            return False, "Script path cannot be empty"
        path = script_path[7:] if script_path.startswith("file://") else script_path
        if not os.path.exists(path):
            return False, f"Script file not found: {path}"
        if not os.path.isfile(path):
            return False, f"Path is not a file: {path}"
        return True, ""

    def validate_execution_readiness(
        self,
        script_path: str,
        script_type: str,
        metadata: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        return ScriptExecutor.validate_readiness(script_path, script_type, metadata)


def build_script_command(
    script_path: str,
    metadata: Optional[Dict] = None,
    env_vars: Optional[Dict[str, str]] = None,
) -> Tuple[str, str]:
    """Compatibility wrapper that prefers source execution for local/custom scripts."""
    env_exports = ScriptEnvironment.build_exports(env_vars or {})
    script_type = metadata.get("type") if metadata else "remote"
    source_type = metadata.get("source_type") if metadata else "unknown"
    use_source = True if script_type in ("local", "cached") or source_type == "custom_local" else False
    command = ScriptExecutionContext().build_execution_command(
        script_path=script_path,
        script_type=script_type,
        source_type=source_type,
        env_exports=env_exports,
        use_source=use_source,
    )
    status = "Command built successfully" if command else "Script must be downloaded first or file missing"
    return command, status


# Re-export convenience functions for compatibility
__all__ = [
    "ScriptEnvironmentManager",
    "ScriptExecutionContext",
    "ScriptValidator",
    "get_script_env_requirements",
    "validate_script_env_var",
    "build_script_command",
]
