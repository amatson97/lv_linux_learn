"""
Script Handler Module
Centralized logic for script metadata building, cache checking, and execution
Handles all script types: local, cached, and remote
"""

import json
import os
from pathlib import Path
from typing import Optional

try:
    from lib import config as C
except ImportError:
    C = None


# ============================================================================
# CACHE STATUS CHECKING
# ============================================================================

def is_script_cached(
    repository,
    script_id: str = None,
    script_path: str = None,
    category: str = None
) -> bool:
    """
    CENTRALIZED cache status checker - single source of truth for cache status.
    All cache checks should use this function.
    
    Args:
        repository: ScriptRepository instance
        script_id: Script ID from manifest (preferred)
        script_path: Script path (fallback)
        category: Script category (used with script_path)
    
    Returns:
        True if script is in cache, False otherwise
    """
    if not repository or not repository.script_cache_dir:
        return False
    
    # Method 1: Use script_id (most reliable)
    if script_id:
        cached_path = repository.get_cached_script_path(script_id)
        return cached_path is not None and os.path.exists(cached_path)
    
    # Method 2: Check if script_path IS a cache path
    if script_path and str(repository.script_cache_dir) in str(script_path):
        return os.path.exists(script_path)
    
    # Method 3: Construct cache path from script_path and category
    if script_path and category:
        script_name = os.path.basename(script_path)
        potential_cache_path = repository.script_cache_dir / category / script_name
        if potential_cache_path.exists():
            return True
        # Also check without category subdirectory
        potential_cache_path = repository.script_cache_dir / script_name
        if potential_cache_path.exists():
            return True
    
    return False


# ============================================================================
# SCRIPT METADATA BUILDING
# ============================================================================

def build_script_metadata(
    script_path: str,
    category: str,
    script_name: str = "",
    repository=None,
    custom_script_manager=None,
    script_id_map: dict = None
) -> dict[str, any]:
    """
    Build metadata for a script based on its source and properties.
    Sources are determined independently - not from global config state.
    
    Args:
        script_path: Full path to the script
        category: Script category (install, tools, etc.)
        script_name: Optional display name with source tag
        repository: Optional ScriptRepository instance
        custom_script_manager: Optional CustomScriptManager instance
        script_id_map: Optional dict mapping (category, path) -> (script_id, source_name)
    
    Returns dict with:
        - type: "local" | "cached" | "remote"
        - source_type: "custom_script" | "public_repo" | "custom_repo" | "custom_local"
        - source_name: Readable source identifier
        - source_url: Original download URL if applicable
        - file_exists: bool for local files
        - is_custom: bool if script is from CustomScriptManager
        - script_id: ID from manifest or custom script manager
    """
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
    
    # Determine source from script_name tag (e.g., [Public Repository] or [Custom: name])
    source_type = "unknown"
    source_name = ""
    
    # Try to get script_id from global mapping (populated during manifest load)
    # This avoids expensive manifest re-parsing
    if script_id_map and (category, script_path) in script_id_map:
        script_id, mapped_source_name = script_id_map[(category, script_path)]
        metadata["script_id"] = script_id
        metadata["source_name"] = mapped_source_name
        
        # Determine source_type from source_name
        if "Public Repository" in mapped_source_name:
            source_type = C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo"
        else:
            source_type = C.SOURCE_TYPE_CUSTOM_REPO if C else "custom_repo"
    
    # Override with script_name tag if present (more authoritative)
    if script_name:
        if "[Public Repository]" in script_name:
            source_type = C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo"
            source_name = "Public Repository"
        elif "[Custom:" in script_name:
            source_type = C.SOURCE_TYPE_CUSTOM_REPO if C else "custom_repo"
            # Extract custom source name from tag
            start = script_name.index("[Custom:") + 8
            end = script_name.index("]", start)
            source_name = script_name[start:end].strip()
    
    # CRITICAL: For scripts without explicit source, infer from path
    if source_type == "unknown":
        # Check if script path looks like it's from the repository
        if not script_path.startswith('/') and not script_path.startswith('file://'):
            # Relative path - likely from public repository manifest
            source_type = C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo"
            source_name = "Public Repository"
        elif script_path.startswith('/home/') and '/lv_linux_learn/' in script_path:
            # Absolute path in the repository directory - public repo
            source_type = C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo"
            source_name = "Public Repository"
        elif 'scripts/' in script_path or 'tools/' in script_path or 'bash_exercises/' in script_path:
            # Path contains typical repository subdirectories - public repo
            source_type = C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo"
            source_name = "Public Repository"
    
    # CRITICAL: Check cache using centralized cache checker
    if is_script_cached(repository, script_id=metadata["script_id"], script_path=script_path, category=category):
        metadata["type"] = C.SCRIPT_TYPE_CACHED if C else "cached"
        metadata["source_type"] = source_type if source_type != "unknown" else (C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo")
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
    
    # CRITICAL: Public repo and custom online repo scripts must be cached - treat as remote if not cached
    if source_type in (
        C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo",
        C.SOURCE_TYPE_CUSTOM_REPO if C else "custom_repo"
    ):
        metadata["type"] = C.SCRIPT_TYPE_REMOTE if C else "remote"
        metadata["source_type"] = source_type
        metadata["source_name"] = source_name if source_name else "Public Repository"
        return metadata
    
    # Now check if it's a local file (not in cache) - ONLY for custom_local or unknown sources
    if script_path.startswith('/') or script_path.startswith('file://'):
        file_path = script_path.replace('file://', '')
        
        # Only treat as custom_local if source_type is actually custom_local or still unknown
        if source_type in (C.SOURCE_TYPE_CUSTOM_LOCAL if C else "custom_local", "unknown"):
            if os.path.exists(file_path):
                # This is a local file-based manifest (custom_local)
                metadata["type"] = C.SCRIPT_TYPE_LOCAL if C else "local"
                metadata["source_type"] = C.SOURCE_TYPE_CUSTOM_LOCAL if C else "custom_local"
                metadata["source_name"] = source_name if source_name else "Local Repository"
                metadata["file_exists"] = True
                return metadata
            else:
                # Local path specified but file doesn't exist
                metadata["type"] = C.SCRIPT_TYPE_LOCAL if C else "local"
                metadata["source_type"] = C.SOURCE_TYPE_CUSTOM_LOCAL if C else "custom_local"
                metadata["source_name"] = source_name if source_name else "Local Repository"
                metadata["file_exists"] = False
                return metadata
    
    # Default to remote (not yet downloaded)
    metadata["type"] = C.SCRIPT_TYPE_REMOTE if C else "remote"
    metadata["source_type"] = source_type if source_type != "unknown" else (C.SOURCE_TYPE_PUBLIC_REPO if C else "public_repo")
    metadata["source_name"] = source_name if source_name else "Public Repository"
    return metadata


# ============================================================================
# SCRIPT EXECUTION LOGIC
# ============================================================================

def should_use_cache_engine(metadata: dict = None) -> bool:
    """
    Determine if cache engine should be used for this script based on source type.
    
    Each repository source operates independently:
    - public_repo: Always uses cache
    - custom_repo: Uses cache (online custom manifests)
    - custom_local: Direct execution (local file-based manifests)
    - custom_script: Direct execution (user-added scripts)
    
    Args:
        metadata: Script metadata dictionary
    
    Returns:
        True: Use cache engine (public_repo, custom_repo)
        False: Direct execution (custom_local, custom_script)
    """
    if not metadata:
        return True
    
    source_type = metadata.get("source_type", "public_repo")
    script_type = metadata.get("type", "remote")
    
    # Custom scripts from CustomScriptManager: direct execution
    if source_type == (C.SOURCE_TYPE_CUSTOM_SCRIPT if C else "custom_script"):
        return False
    
    # Local files from custom_local manifests: direct execution
    if source_type == (C.SOURCE_TYPE_CUSTOM_LOCAL if C else "custom_local") and script_type == (C.SCRIPT_TYPE_LOCAL if C else "local"):
        return False
    
    # Public repo and custom online repos: use cache
    # This allows both to coexist using the same cache infrastructure
    return True


def get_script_status_icon(metadata: dict) -> str:
    """
    Get appropriate status icon for script based on metadata
    
    Args:
        metadata: Script metadata dictionary
        
    Returns:
        Status icon string (✓, ☁️, or 📝)
    """
    if metadata.get("is_custom", False):
        return C.ICON_CUSTOM if C else "📝"
    
    script_type = metadata.get("type", "remote")
    if script_type == (C.SCRIPT_TYPE_CACHED if C else "cached"):
        return C.ICON_CACHED if C else "✓"
    else:
        return C.ICON_NOT_CACHED if C else "☁️"


def get_script_metadata_from_model(model, treeiter) -> dict[str, any]:
    """
    Extract and parse metadata from GTK liststore row
    
    Args:
        model: GTK TreeModel/ListStore
        treeiter: TreeIter pointing to row
        
    Returns:
        Dictionary containing script metadata
    """
    try:
        COL_METADATA = C.COL_METADATA if C else 5
        metadata_json = model.get_value(treeiter, COL_METADATA)
        return json.loads(metadata_json) if metadata_json else {}
    except (IndexError, json.JSONDecodeError) as e:
        print(f"[!] Error parsing metadata: {e}")
    return {}
