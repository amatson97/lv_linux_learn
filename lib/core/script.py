"""
Script Module - Consolidated script management
Combines script_handler + script_execution + script_manager
Handles metadata building, cache checking, and execution
"""

import json
import os
import re
from pathlib import Path
from typing import Optional, Dict, Tuple, Any

# Debug logging flag (disabled by default). Set LV_DEBUG_CACHE=1 to enable.
DEBUG_CACHE: bool = os.environ.get("LV_DEBUG_CACHE") == "1"

try:
    from lib import config as C
except ImportError:
    C = None


# ============================================================================
# SCRIPT METADATA - Building and parsing
# ============================================================================

class ScriptMetadata:
    """Manages script metadata building and parsing"""
    
    @staticmethod
    def build(
        script_path: str,
        category: str,
        script_name: str = "",
        repository=None,
        custom_script_manager=None,
        script_id_map: Optional[Dict[Tuple[str, str], Tuple[str, str]]] = None
    ) -> Dict[str, Any]:
        """Build metadata for a script based on its source and properties."""
        metadata = {
            "type": "remote",
            "source_type": "unknown",
            "source_name": "",
            "source_url": "",
            "file_exists": False,
            "is_custom": False,
            "script_id": ""
        }
        
        # Check if this is a custom script from CustomScriptManager (user-added scripts)
        if custom_script_manager:
            for custom_script in custom_script_manager.list_scripts():
                if custom_script['path'] == script_path:
                    metadata["type"] = "local"
                    metadata["source_type"] = C.SOURCE_TYPE_CUSTOM_SCRIPT if C else "custom_script"
                    metadata["source_name"] = "Custom Script"
                    metadata["file_exists"] = os.path.exists(script_path)
                    metadata["is_custom"] = True
                    metadata["script_id"] = custom_script.get('id', '')
                    return metadata
        
        # Determine source from script_id_map or script_name tag
        source_type, source_name = ScriptMetadata._determine_source(
            script_path, category, script_name, script_id_map, metadata
        )

        # Detect local custom repository scripts early to avoid cache handling
        local_candidate: Optional[str] = None
        if script_path.startswith('file://'):
            local_candidate = script_path.replace('file://', '')
        elif script_path.startswith('/'):
            local_candidate = script_path
        if local_candidate:
            try:
                path_obj: Path = Path(local_candidate).resolve()
                custom_root: Path = Path.home() / '.lv_linux_learn' / 'custom_manifests'
                if custom_root in path_obj.parents:
                    metadata["type"] = C.SCRIPT_TYPE_LOCAL if C else "local"
                    metadata["source_type"] = C.SOURCE_TYPE_CUSTOM_LOCAL if C else "custom_local"
                    metadata["source_name"] = source_name if source_name else path_obj.parent.name
                    metadata["file_exists"] = path_obj.exists()
                    return metadata
            except Exception:
                pass
        
        # Check cache status
        if ScriptCache.is_cached(repository, script_id=metadata["script_id"], 
                                 script_path=script_path, category=category):
            metadata["type"] = C.SCRIPT_TYPE_CACHED if C else "cached"
            metadata["source_type"] = source_type if source_type != "unknown" else (
                C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo")
            metadata["source_name"] = source_name if source_name else "Public Repository"
            
            # For cached scripts, check if file exists in cache
            if repository:
                cached_path = repository.get_cached_script_path(metadata["script_id"])
                if cached_path:
                    metadata["file_exists"] = os.path.exists(cached_path)
                else:
                    metadata["file_exists"] = os.path.exists(script_path)
            else:
                metadata["file_exists"] = os.path.exists(script_path)
            return metadata
        
        # CRITICAL: Public repo and custom online repo scripts must be cached
        if source_type in (
            C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo",
            C.SOURCE_TYPE_CUSTOM_REPO if C else "custom_repo"
        ):
            metadata["type"] = C.SCRIPT_TYPE_REMOTE if C else "remote"
            metadata["source_type"] = source_type
            metadata["source_name"] = source_name if source_name else "Public Repository"
            return metadata
        
        # Check if it's a local file (custom_local or unknown)
        if script_path.startswith('/') or script_path.startswith('file://'):
            file_path: str = script_path.replace('file://', '')
            
            # Only treat as custom_local if source_type is actually custom_local or unknown
            if source_type in (C.SOURCE_TYPE_CUSTOM_LOCAL if C else "custom_local", "unknown"):
                metadata["type"] = C.SCRIPT_TYPE_LOCAL if C else "local"
                metadata["source_type"] = C.SOURCE_TYPE_CUSTOM_LOCAL if C else "custom_local"
                metadata["source_name"] = source_name if source_name else "Local Repository"
                metadata["file_exists"] = os.path.exists(file_path)
                return metadata
        
        # Default to remote (not yet downloaded)
        metadata["type"] = C.SCRIPT_TYPE_REMOTE if C else "remote"
        metadata["source_type"] = source_type if source_type != "unknown" else (
            C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo")
        metadata["source_name"] = source_name if source_name else "Public Repository"
        return metadata
    
    @staticmethod
    def _determine_source(
        script_path: str,
        category: str,
        script_name: str,
        script_id_map: Optional[Dict[Tuple[str, str], Tuple[str, str]]],
        metadata: Dict[str, Any],
    ) -> Tuple[str, str]:
        """Determine source_type and source_name from various inputs"""
        source_type = "unknown"
        source_name: str = ""
        
        # Try to get from script_id_map
        if script_id_map and (category, script_path) in script_id_map:
            script_id, mapped_source_name = script_id_map[(category, script_path)]
            metadata["script_id"] = script_id
            metadata["source_name"] = mapped_source_name
            
            if "Public Repository" in mapped_source_name:
                source_type: str = C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo"
            else:
                source_type: str = C.SOURCE_TYPE_CUSTOM_REPO if C else "custom_repo"
        
        # Override with script_name tag if present
        if script_name:
            if "[Public Repository]" in script_name:
                source_type: str = C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo"
                source_name = "Public Repository"
            elif "[Custom:" in script_name:
                source_type: str = C.SOURCE_TYPE_CUSTOM_REPO if C else "custom_repo"
                start: int = script_name.index("[Custom:") + 8
                end: int = script_name.index("]", start)
                source_name: str = script_name[start:end].strip()
        
        # Infer from path if still unknown
        if source_type == "unknown":
            if not script_path.startswith('/') and not script_path.startswith('file://'):
                source_type: str = C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo"
                source_name = "Public Repository"
            elif script_path.startswith('/home/') and '/lv_linux_learn/' in script_path:
                source_type: str = C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo"
                source_name = "Public Repository"
            elif 'scripts/' in script_path or 'tools/' in script_path or 'bash_exercises/' in script_path:
                source_type: str = C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo"
                source_name = "Public Repository"

        # Final guard: if the script lives under custom_manifests, treat as custom_local
        try:
            local_candidate: Optional[str] = None
            if script_path.startswith('file://'):
                local_candidate = script_path.replace('file://', '')
            elif script_path.startswith('/'):
                local_candidate = script_path
            if local_candidate:
                path_obj: Path = Path(local_candidate).resolve()
                custom_root: Path = Path.home() / '.lv_linux_learn' / 'custom_manifests'
                if custom_root in path_obj.parents:
                    source_type: str = C.SOURCE_TYPE_CUSTOM_LOCAL if C else "custom_local"
                    if not source_name:
                        source_name: str = path_obj.parent.name
        except Exception:
            pass
        
        return source_type, source_name
    
    @staticmethod
    def parse_from_model(model, treeiter) -> Dict[str, Any]:
        """Extract and parse metadata from GTK liststore row"""
        try:
            COL_METADATA: int = C.COL_METADATA if C else 5
            metadata_json = model.get_value(treeiter, COL_METADATA)
            return json.loads(metadata_json) if metadata_json else {}
        except (IndexError, json.JSONDecodeError) as e:
            print(f"[!] Error parsing metadata: {e}")
        return {}
    
    @staticmethod
    def get_status_icon(metadata: Dict[str, Any]) -> str:
        """Get appropriate status icon for script based on metadata"""
        if metadata.get("is_custom", False):
            return C.ICON_CUSTOM if C else "📝"
        
        script_type = metadata.get("type", "remote")
        if script_type == (C.SCRIPT_TYPE_CACHED if C else "cached"):
            return C.ICON_CACHED if C else "✓"
        else:
            return C.ICON_NOT_CACHED if C else "☁️"
    
    @staticmethod
    def should_use_cache(metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Determine if cache engine should be used for this script."""
        if not metadata:
            return True
        
        source_type = metadata.get("source_type", "public_repo")
        script_type = metadata.get("type", "remote")
        
        # Custom scripts: direct execution
        if source_type == (C.SOURCE_TYPE_CUSTOM_SCRIPT if C else "custom_script"):
            return False
        
        # Local files from custom_local manifests: direct execution
        if source_type == (C.SOURCE_TYPE_CUSTOM_LOCAL if C else "custom_local") and \
           script_type == (C.SCRIPT_TYPE_LOCAL if C else "local"):
            return False
        
        # Public repo and custom online repos: use cache
        return True


# ============================================================================
# SCRIPT CACHE - Status checking and path resolution
# ============================================================================

class ScriptCache:
    """Manages script cache operations"""
    
    @staticmethod
    def is_cached(
        repository,
        script_id: Optional[str] = None,
        script_path: Optional[str] = None,
        category: Optional[str] = None
    ) -> bool:
        """Check if script is in cache."""
        if not repository or not repository.script_cache_dir:
            pass  # removed debug log
            return False
        
        # Method 1: Use script_id (most reliable)
        if script_id:
            cached_path = repository.get_cached_script_path(script_id)
            result: bool = cached_path is not None and os.path.exists(cached_path) if cached_path else False
            pass  # removed debug log
            return result
        
        # Method 2: Check if script_path IS a cache path
        if script_path and str(repository.script_cache_dir) in str(script_path):
            exists: bool = os.path.exists(script_path)
            pass  # removed debug log
            return exists
        
        # Method 3: Construct cache path from script_path and category
        if script_path and category:
            script_name: str = os.path.basename(script_path)
            potential_cache_path = repository.script_cache_dir / category / script_name
            exists_cat = potential_cache_path.exists()
            potential_cache_path2 = repository.script_cache_dir / script_name
            exists_root = potential_cache_path2.exists()
            pass  # removed debug log
            if exists_cat or exists_root:
                return True
        
        pass  # removed debug log
        return False


# ============================================================================
# SCRIPT ENVIRONMENT - Variable management and validation
# ============================================================================

class ScriptEnvironment:
    """Manages environment variables required by scripts"""
    
    @staticmethod
    def get_required_vars(script_name: str) -> Dict[str, Dict[str, Any]]:
        """Determine which environment variables a script requires."""
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
    def validate_var(var_name: str, value: str) -> Tuple[bool, str]:
        """Validate an environment variable value"""
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
    def is_var_set(var_name: str) -> bool:
        """Check if environment variable is already set"""
        return var_name in os.environ and bool(os.environ[var_name])
    
    @staticmethod
    def build_exports(env_vars: Dict[str, str]) -> str:
        """Build shell export commands for environment variables"""
        if not env_vars:
            return ""
        
        exports = []
        for key, value in env_vars.items():
            # Escape single quotes in value
            escaped_value: str = value.replace("'", "'\\''")
            exports.append(f"export {key}='{escaped_value}'")
        
        return "; ".join(exports) + "; " if exports else ""


# ============================================================================
# SCRIPT EXECUTOR - Command building and validation
# ============================================================================

class ScriptExecutor:
    """Builds and validates script execution commands"""
    
    @staticmethod
    def build_command(
        script_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        use_source: bool = False
    ) -> Tuple[str, str]:
        """Build execution command for a script."""
        # Determine script type and source
        script_type: str = ScriptExecutor._get_type(script_path, metadata)
        source_type: str = ScriptExecutor._get_source_type(script_path, metadata)
        
        # Validate execution readiness
        is_ready, message = ScriptExecutor.validate_readiness(script_path, script_type, metadata)
        if not is_ready:
            return "", message
        
        # Build environment exports
        env_exports: str = ScriptEnvironment.build_exports(env_vars or {})
        
        # Build command
        executor: str = "bash" if not use_source else "source"
        
        # Local custom scripts - execute directly
        if script_type == "local" or source_type == "custom_local":
            abs_path: str = os.path.abspath(script_path)
            return f"{env_exports}{executor} '{abs_path}'\n", "Command built successfully"
        
        # Cached scripts - execute from cache with cd (use subshell)
        elif script_type == "cached":
            cache_root: str = os.path.expanduser("~/.lv_linux_learn/script_cache")
            return f"{env_exports}(cd '{cache_root}' && {executor} '{script_path}')\n", "Command built successfully"
        
        # Remote - shouldn't execute
        return "", "Script must be downloaded first"
    
    @staticmethod
    def validate_readiness(
        script_path: str,
        script_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Validate that script is ready for execution"""
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
        file_path: str = script_path[7:] if script_path.startswith('file://') else script_path
        
        if not os.path.exists(file_path):
            return False, f"Script file not found: {file_path}"
        
        if not os.path.isfile(file_path):
            return False, f"Path is not a file: {file_path}"
        
        return True, "Ready to execute"
    
    @staticmethod
    def _get_type(script_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Determine script type"""
        if metadata:
            return metadata.get('type', 'remote')
        
        if os.path.isfile(script_path):
            if '/.lv_linux_learn/script_cache/' in script_path:
                return 'cached'
            return 'local'
        
        return 'remote'
    
    @staticmethod
    def _get_source_type(script_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Determine script source type"""
        if metadata:
            return metadata.get('source_type', 'unknown')
        
        if 'custom_scripts' in script_path:
            return 'custom_script'
        elif 'custom_manifests' in script_path:
            return 'custom_local'
        elif '/.lv_linux_learn/script_cache/' in script_path:
            return 'public_repo'
        
        return 'unknown'


# ============================================================================
# SCRIPT NAVIGATOR - Directory navigation logic
# ============================================================================

class ScriptNavigator:
    """Handles script directory navigation"""
    
    @staticmethod
    def get_directory(script_path: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Get the directory to navigate to for a script."""
        script_type: str = ScriptExecutor._get_type(script_path, metadata)
        
        if script_type == "local":
            file_path: str = script_path[7:] if script_path.startswith('file://') else script_path
            if os.path.isfile(file_path):
                return os.path.dirname(os.path.abspath(file_path))
        
        elif script_type == "cached":
            if os.path.isfile(script_path):
                return os.path.dirname(os.path.abspath(script_path))
        
        return None
    
    @staticmethod
    def should_prompt_for_download(script_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Check if script needs to be downloaded before navigation"""
        script_type: str = ScriptExecutor._get_type(script_path, metadata)
        return script_type == "remote"


# ============================================================================
# PUBLIC API - Backward compatibility functions
# ============================================================================

def build_script_metadata(
    script_path: str,
    category: str,
    script_name: str = "",
    repository=None,
    custom_script_manager=None,
    script_id_map: Optional[Dict[Tuple[str, str], Tuple[str, str]]] = None,
) -> Dict[str, Any]:
    """Build metadata for a script - backward compatibility wrapper"""
    return ScriptMetadata.build(script_path, category, script_name, 
                               repository, custom_script_manager, script_id_map)


def is_script_cached(
    repository,
    script_id: Optional[str] = None,
    script_path: Optional[str] = None,
    category: Optional[str] = None,
) -> bool:
    """Check if script is cached - backward compatibility wrapper"""
    return ScriptCache.is_cached(repository, script_id, script_path, category)


def should_use_cache_engine(metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Check if cache should be used - backward compatibility wrapper"""
    return ScriptMetadata.should_use_cache(metadata)


def get_script_status_icon(metadata: Dict[str, Any]) -> str:
    """Get status icon - backward compatibility wrapper"""
    return ScriptMetadata.get_status_icon(metadata)


def get_script_metadata_from_model(model, treeiter) -> Dict[str, Any]:
    """Parse metadata from model - backward compatibility wrapper"""
    return ScriptMetadata.parse_from_model(model, treeiter)


def get_script_env_requirements(script_name: str) -> Dict[str, Dict]:
    """Get environment requirements - backward compatibility wrapper"""
    return ScriptEnvironment.get_required_vars(script_name)


def validate_script_env_var(var_name: str, value: str) -> Tuple[bool, str]:
    """Validate environment variable - backward compatibility wrapper"""
    return ScriptEnvironment.validate_var(var_name, value)


def build_script_command(
    script_path: str,
    metadata: Optional[Dict[str, Any]] = None,
    env_vars: Optional[Dict[str, str]] = None,
) -> Tuple[str, str]:
    """Build execution command - backward compatibility wrapper"""
    return ScriptExecutor.build_command(script_path, metadata, env_vars)
