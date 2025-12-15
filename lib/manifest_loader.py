"""
Manifest Loader Module
Handles fetching, parsing, and loading scripts from manifest.json files
Supports multi-repository system with public + custom manifests
"""

import json
import os
import time
from pathlib import Path
from typing import Optional, Callable
from urllib.request import urlopen

try:
    from lib import constants as C
except ImportError:
    C = None

try:
    from lib.repository import ScriptRepository
except ImportError:
    ScriptRepository = None


# ============================================================================
# MANIFEST FETCHING
# ============================================================================

def fetch_manifest(
    terminal_widget=None,
    repository=None
) -> list[tuple[Path, str]]:
    """
    Fetch manifest.json from configured repository/repositories
    Returns list of (Path, source_name) tuples for all active manifests
    
    Multi-Manifest System:
    - Public repository (if use_public_repository=true)
    - Custom manifest(s) (if custom_manifest_url is configured)
    - Both can be active simultaneously
    
    Args:
        terminal_widget: Optional terminal widget to send output to
        repository: Optional repository instance for custom configuration
        
    Returns:
        List of tuples containing (manifest_path, source_name) for each loaded manifest
        
    Raises:
        Exception: If no manifests are configured or all fetches fail
    """
    manifests_to_load = []  # List of (url, source_name) tuples
    
    # Determine default manifest URL
    default_url = C.DEFAULT_MANIFEST_URL if C else "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/manifest.json"
    manifest_url = os.environ.get('CUSTOM_MANIFEST_URL', default_url)
    
    # Check repository config
    if repository:
        try:
            config = repository.load_config()
            
            # Check if public repository is enabled
            if config.get('use_public_repository', True):
                manifests_to_load.append((manifest_url, 'Public Repository'))
            
            # Check for custom manifest
            custom_url = config.get('custom_manifest_url', '')
            if custom_url:
                custom_name = config.get('custom_manifest_name', 'Custom Repository')
                manifests_to_load.append((custom_url, custom_name))
            
        except Exception as e:
            print(f"[!] Error loading repository config: {e}")
            manifests_to_load.append((manifest_url, 'Default'))
            
    else:
        # No repository instance, use global MANIFEST_URL
        manifests_to_load.append((manifest_url, 'Default'))
    
    # If no manifests configured, show error
    if not manifests_to_load:
        error_msg = C.ERROR_NO_MANIFESTS if C else "No manifests configured"
        _terminal_output(terminal_widget, f"[!] {error_msg}")
        raise Exception(error_msg)
    
    # Ensure cache directory exists
    cache_dir = C.CONFIG_DIR if C else Path.home() / '.lv_linux_learn'
    cache_dir.mkdir(exist_ok=True)
    
    # Fetch and cache each manifest
    loaded_manifests = []
    _terminal_output(terminal_widget, f"[*] Loading {len(manifests_to_load)} manifest(s)...")
    
    for manifest_url, source_name in manifests_to_load:
        try:
            _terminal_output(terminal_widget, f"[*] Fetching manifest from: {source_name}")
            
            # Create cache filename based on source
            cache_filename = f"manifest_{source_name.lower().replace(' ', '_')}.json"
            cache_path = cache_dir / cache_filename
            
            # Try to load from cache first
            use_cache = False
            max_age = C.MANIFEST_CACHE_MAX_AGE if C else 3600
            
            if cache_path.exists():
                age = time.time() - cache_path.stat().st_mtime
                if age < max_age:
                    use_cache = True
                    _terminal_output(terminal_widget, f"[*] Using cached manifest (age: {int(age)}s)")
            
            if not use_cache:
                # Fetch from URL - handle both remote URLs and local file:// paths
                if manifest_url.startswith('file://'):
                    # Local file path
                    local_path = manifest_url[7:]  # Remove 'file://' prefix
                    _terminal_output(terminal_widget, f"[*] Loading local manifest from {local_path}")
                    manifest_content = Path(local_path).read_text()
                elif os.path.isfile(manifest_url):
                    # Direct file path (no file:// prefix)
                    _terminal_output(terminal_widget, f"[*] Loading local manifest from {manifest_url}")
                    manifest_content = Path(manifest_url).read_text()
                else:
                    # Remote URL (http/https)
                    _terminal_output(terminal_widget, f"[*] Downloading from {manifest_url}")
                    response = urlopen(manifest_url, timeout=10)
                    manifest_content = response.read().decode('utf-8')
                
                # Save to cache
                cache_path.write_text(manifest_content)
                _terminal_output(terminal_widget, f"[✓] Cached manifest: {cache_path.name}")
            
            loaded_manifests.append((cache_path, source_name))
            
        except Exception as e:
            _terminal_output(terminal_widget, f"[!] Failed to load manifest from {source_name}: {e}")
            continue
    
    if not loaded_manifests:
        error_msg = C.ERROR_MANIFEST_LOAD_FAILED if C else "Failed to load any manifests"
        raise Exception(error_msg)
    
    return loaded_manifests


# ============================================================================
# SCRIPT LOADING FROM MANIFESTS
# ============================================================================

def load_scripts_from_manifest(
    terminal_widget=None,
    repository=None
) -> tuple[dict[str, list], dict[str, list], dict[str, list]]:
    """
    Load scripts dynamically from manifest.json files (supports multiple manifests)
    Returns: tuple of (scripts_dict, names_dict, descriptions_dict)
    Each dict has keys: 'install', 'tools', 'exercises', 'uninstall', and dynamic categories
    
    Multi-Manifest Support:
    - Merges scripts from public repository + custom manifests
    - Tracks source for each script
    
    Args:
        terminal_widget: Optional terminal widget to send output to
        repository: Optional repository instance for custom configuration
        
    Returns:
        Tuple of (scripts_dict, names_dict, descriptions_dict) containing categorized script data
    """
    
    try:
        # Fetch all active manifests (returns list of (path, source_name) tuples)
        manifests = fetch_manifest(terminal_widget, repository)
        
        # Initialize merged structures
        standard_cats = C.STANDARD_CATEGORIES if C else ['install', 'tools', 'exercises', 'uninstall']
        all_categories = set(standard_cats)
        scripts = {}
        names = {}
        descriptions = {}
        
        # Initialize repository for cache management
        repo = repository if repository else (ScriptRepository() if ScriptRepository else None)
        
        # Process each manifest
        total_scripts_all = 0
        total_cached_all = 0
        
        # Global script ID mapping for metadata building
        script_id_map = {}
        
        for manifest_path, source_name in manifests:
            _terminal_output(terminal_widget, f"\n[*] Processing manifest: {source_name}")
            
            try:
                with open(manifest_path, 'r') as f:
                    manifest_data = json.load(f)
                
                # Get manifest version and repository_url
                manifest_version = manifest_data.get('version', 'unknown')
                repository_url = manifest_data.get('repository_url', '')
                _terminal_output(terminal_widget, f"[*] Manifest version: {manifest_version}")
                
                if repository_url:
                    _terminal_output(terminal_widget, f"[*] Repository URL: {repository_url}")
                
                # Load scripts from manifest
                manifest_scripts = manifest_data.get('scripts', [])
                total_scripts = len(manifest_scripts)
                cached_count = 0
                
                _terminal_output(terminal_widget, f"[*] Found {total_scripts} scripts in manifest")
                
                for script_entry in manifest_scripts:
                    category = script_entry.get('category', 'install')
                    
                    # Add category if not seen before
                    if category not in all_categories:
                        all_categories.add(category)
                    
                    # Initialize category if needed
                    if category not in scripts:
                        scripts[category] = []
                        names[category] = []
                        descriptions[category] = []
                    
                    # Get script details
                    script_id = script_entry.get('id', '')
                    script_name = script_entry.get('name', '')
                    file_name = script_entry.get('file_name', '')
                    relative_path = script_entry.get('relative_path', '')
                    download_url = script_entry.get('download_url', '')
                    description = script_entry.get('description', 'No description available')
                    
                    # Determine script path based on cache status
                    script_path = relative_path
                    
                    # Check if script is cached (if repository is available)
                    is_cached = False
                    if repo and script_id:
                        cached_path = repo.get_cached_script_path(script_id)
                        if cached_path and os.path.exists(cached_path):
                            script_path = cached_path
                            is_cached = True
                            cached_count += 1
                    
                    # Build display name with source tag
                    if is_cached:
                        base_name = script_name
                    else:
                        base_name = script_name
                    
                    # Add source identifier to name
                    if source_name == 'Public Repository':
                        display_name = f"{base_name} [Public Repository]"
                    else:
                        display_name = f"{base_name} [Custom: {source_name}]"
                    
                    # Add to lists
                    scripts[category].append(script_path)
                    names[category].append(display_name)
                    descriptions[category].append(description)
                    
                    # Store in global mapping for metadata building
                    script_id_map[(category, script_path)] = (script_id, source_name)
                
                total_scripts_all += total_scripts
                total_cached_all += cached_count
                
                _terminal_output(terminal_widget, f"[*] {source_name}: {cached_count}/{total_scripts} scripts cached")
                
            except Exception as e:
                _terminal_output(terminal_widget, f"[!] Error processing manifest {source_name}: {e}")
                continue
        
        # Ensure all standard categories exist even if empty
        for cat in standard_cats:
            if cat not in scripts:
                scripts[cat] = []
                names[cat] = []
                descriptions[cat] = []
        
        # Display summary
        _terminal_output(terminal_widget, f"\n[*] Total: {total_scripts_all} scripts from {len(manifests)} source(s)")
        _terminal_output(terminal_widget, f"[*] Cache status: {total_cached_all}/{total_scripts_all} scripts cached")
        
        # Display per-category breakdown
        _terminal_output(terminal_widget, "[*] Script breakdown by category:")
        for category in sorted(scripts.keys()):
            count = len(scripts[category])
            _terminal_output(terminal_widget, f"    • {category}: {count} scripts")
        
        return scripts, names, descriptions, script_id_map
        
    except Exception as e:
        _terminal_output(terminal_widget, f"[!] Error loading manifests: {e}")
        # Return empty structures
        default_categories = C.STANDARD_CATEGORIES if C else ['install', 'tools', 'exercises', 'uninstall']
        scripts = {cat: [] for cat in default_categories}
        names = {cat: [] for cat in default_categories}
        descriptions = {cat: [] for cat in default_categories}
        return scripts, names, descriptions, {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _terminal_output(terminal_widget, msg: str):
    """Helper function to output to terminal or stdout"""
    if terminal_widget:
        terminal_widget.feed(f"{msg}\r\n".encode())
    else:
        print(msg)
