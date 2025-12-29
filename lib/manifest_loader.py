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
    from lib import config as C
except ImportError:
    C = None

try:
    from lib.repository_service import ScriptRepository
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
    
    # Ensure cache directory exists FIRST
    cache_dir = C.CONFIG_DIR if C else Path.home() / '.lv_linux_learn'
    cache_dir.mkdir(exist_ok=True)
    
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
                # Validate that local files actually exist before trying to load
                if custom_url.startswith('file://'):
                    local_path = custom_url.replace('file://', '')
                    if not os.path.exists(local_path):
                        _terminal_output(terminal_widget, f"[!] Custom manifest not found: {local_path}")
                        _terminal_output(terminal_widget, f"[!] Clearing invalid manifest from configuration")
                        # Clear the invalid configuration
                        config['custom_manifest_url'] = ''
                        config['custom_manifest_name'] = ''
                        if repository:
                            repository.save_config(config)
                    else:
                        custom_name = config.get('custom_manifest_name', 'Custom Repository')
                        manifests_to_load.append((custom_url, custom_name))
                elif os.path.isfile(custom_url):
                    # Direct path without file:// prefix
                    if not os.path.exists(custom_url):
                        _terminal_output(terminal_widget, f"[!] Custom manifest not found: {custom_url}")
                        _terminal_output(terminal_widget, f"[!] Clearing invalid manifest from configuration")
                        config['custom_manifest_url'] = ''
                        config['custom_manifest_name'] = ''
                        if repository:
                            repository.save_config(config)
                    else:
                        custom_name = config.get('custom_manifest_name', 'Custom Repository')
                        manifests_to_load.append((custom_url, custom_name))
                else:
                    # Remote URL - add without validation (will fail later if unreachable)
                    custom_name = config.get('custom_manifest_name', 'Custom Repository')
                    manifests_to_load.append((custom_url, custom_name))
            
            # CRITICAL: Scan for local repository manifests in custom_manifests directory
            custom_manifests_dir = cache_dir / 'custom_manifests'
            if custom_manifests_dir.exists():
                for manifest_file in custom_manifests_dir.glob('*/manifest.json'):
                    # Get repository name from directory
                    repo_name = manifest_file.parent.name
                    local_manifest_url = f"file://{manifest_file}"
                    manifests_to_load.append((local_manifest_url, repo_name))
                    if terminal_widget:
                        _terminal_output(terminal_widget, f"[*] Found local repository: {repo_name}")
            
        except Exception as e:
            print(f"[!] Error loading repository config: {e}")
            # Don't add default manifest on error - respect user configuration
            
    else:
        # No repository instance - only load if public repository would be enabled by default
        # Don't force-load manifests when repository system isn't available
        pass
    
    # If no manifests configured, raise error silently (expected when public repo disabled)
    if not manifests_to_load:
        error_msg = C.ERROR_NO_MANIFESTS if C else "No manifests configured. Enable public repository or add local repositories."
        # Don't output to terminal - this is an expected state when public repo is disabled
        raise Exception(error_msg)
    
    # Fetch and cache each manifest
    loaded_manifests = []
    
    for manifest_url, source_name in manifests_to_load:
        try:
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
            
            if not use_cache:
                # Fetch from URL - handle both remote URLs and local file:// paths
                if manifest_url.startswith('file://'):
                    # Local file path
                    local_path = manifest_url[7:]  # Remove 'file://' prefix
                    manifest_content = Path(local_path).read_text()
                elif os.path.isfile(manifest_url):
                    # Direct file path (no file:// prefix)
                    manifest_content = Path(manifest_url).read_text()
                else:
                    # Remote URL (http/https)
                    response = urlopen(manifest_url, timeout=10)
                    manifest_content = response.read().decode('utf-8')
                
                # Save to cache (no output message)
                cache_path.write_text(manifest_content)
            
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
        
        # Track script IDs to prevent duplicates
        seen_script_ids = set()
        
        for manifest_path, source_name in manifests:
            try:
                with open(manifest_path, 'r') as f:
                    manifest_data = json.load(f)
                
                # Get manifest version and repository_url (for internal use, no output)
                manifest_version = manifest_data.get('version', 'unknown')
                repository_url = manifest_data.get('repository_url', '')
                
                # Load scripts from manifest - handle both flat and nested structures
                manifest_scripts_raw = manifest_data.get('scripts', [])
                manifest_scripts = []
                
                # Check if scripts is a dict (nested by category) or list (flat)
                if isinstance(manifest_scripts_raw, dict):
                    # Nested structure: {"category": [scripts]}
                    _terminal_output(terminal_widget, f"[*] Processing nested manifest structure")
                    for cat, cat_scripts in manifest_scripts_raw.items():
                        if isinstance(cat_scripts, list):
                            _terminal_output(terminal_widget, f"[*] Processing {len(cat_scripts)} scripts in category '{cat}'")
                            for script in cat_scripts:
                                # CRITICAL: In nested structure, the category key is authoritative
                                # Always set category from the dict key, overriding any field value
                                script['category'] = cat
                                manifest_scripts.append(script)
                else:
                    # Flat structure: [scripts]
                    manifest_scripts = manifest_scripts_raw
                
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
                    
                    # Skip duplicates - check if script ID already processed
                    if script_id and script_id in seen_script_ids:
                        _terminal_output(terminal_widget, f"[*] Skipping duplicate: {script_name} (ID: {script_id})")
                        continue
                    
                    # Mark as seen
                    if script_id:
                        seen_script_ids.add(script_id)
                    
                    # Determine script path based on source type
                    script_path = relative_path
                    is_cached = False
                    is_local = False
                    
                    # Check if this is a local file:// URL (from local repository)
                    if download_url and download_url.startswith('file://'):
                        # Local file - use the file path directly
                        script_path = download_url.replace('file://', '')
                        is_local = True
                        _terminal_output(terminal_widget, f"[*] Local script: {script_name} -> {script_path}")
                    elif repo and script_id:
                        # Check if script is cached (online repositories)
                        cached_path = repo.get_cached_script_path(script_id)
                        if cached_path and os.path.exists(cached_path):
                            script_path = cached_path
                            is_cached = True
                            cached_count += 1
                    
                    # Build display name with source tag
                    base_name = script_name
                    
                    # Add source identifier to name
                    if is_local:
                        display_name = f"{base_name} [Local: {source_name}]"
                    elif source_name == 'Public Repository':
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
                
                # Concise per-source summary
                _terminal_output(terminal_widget, f"[✓] {source_name}: {total_scripts} scripts ({cached_count} cached)")
                
            except Exception as e:
                _terminal_output(terminal_widget, f"[!] {source_name}: Failed - {e}")
                continue
        
        # Ensure all standard categories exist even if empty
        for cat in standard_cats:
            if cat not in scripts:
                scripts[cat] = []
                names[cat] = []
                descriptions[cat] = []
        
        # Display concise summary
        categories_summary = ", ".join([f"{cat}:{len(scripts[cat])}" for cat in sorted(scripts.keys()) if len(scripts[cat]) > 0])
        _terminal_output(terminal_widget, f"\n[✓] Loaded {total_scripts_all} scripts from {len(manifests)} source(s) - {categories_summary}")
        
        return scripts, names, descriptions, script_id_map
        
    except Exception as e:
        # Suppress "No manifests configured" error - it's expected when public repo is disabled
        error_str = str(e)
        if "No manifests configured" not in error_str:
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
    """Helper function to output to terminal or stdout - only errors displayed to terminal"""
    # Only show error messages in terminal to avoid cluttering output during background refreshes
    # Status/info messages are logged but not displayed
    if msg.startswith("[!]") or msg.startswith("[✗]"):
        if terminal_widget:
            terminal_widget.feed(f"{msg}\r\n".encode())
        else:
            print(msg)
    # All other messages silently logged (could be logged to file if needed)
