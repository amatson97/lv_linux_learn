#!/usr/bin/env -S python3 -u
"""
Setup Tool - Ubuntu Linux Setup & Management Utility
Requires: python3-gi, gir1.2-gtk-3.0, gir1.2-vte-2.91
"""

import sys
import os

# Check for required Python GTK dependencies before importing
try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Vte", "2.91")
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import Gtk, Gdk, GLib, Vte, Pango, GdkPixbuf
except (ImportError, ValueError) as e:
    print("ERROR: Missing required Python GTK dependencies!")
    print("\nThis application requires:")
    print("  • python3-gi")
    print("  • gir1.2-gtk-3.0")
    print("  • gir1.2-vte-2.91")
    print("\nInstall them with:")
    print("  sudo apt-get update")
    print("  sudo apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91")
    print(f"\nError details: {e}")
    sys.exit(1)

import subprocess
import webbrowser
import shlex
import json
import urllib.request
import urllib.error
import time
import hashlib
from pathlib import Path
from datetime import datetime
import uuid

# Debug logging flag (disabled by default). Set LV_DEBUG_CACHE=1 to enable.
DEBUG_CACHE = os.environ.get("LV_DEBUG_CACHE") == "1"

# Import library modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

# Centralized utilities
try:
    from lib.utilities import (
        PathManager,
        ConfigManager,
        TerminalMessenger,
        FileLoader,
        TimerManager
    )
    from lib.dialog_helpers_extended import show_confirmation, show_error, show_info, show_warning
    from lib.ui_components import create_filtered_treeview
except ImportError as e:
    print(f"Warning: Utility modules not available: {e}")
    PathManager = None
    ConfigManager = None
    TerminalMessenger = None
    FileLoader = None
    TimerManager = None

# Repository management (consolidated)
try:
    from lib.repository import ScriptRepository, ChecksumVerificationError
    from lib.repository import (
        download_script_with_feedback,
        update_script_with_feedback,
        remove_script_with_feedback,
        download_all_scripts_with_feedback,
        update_all_scripts_with_feedback,
        remove_all_scripts_with_feedback,
        clear_cache_with_feedback,
        get_cache_stats
    )
except ImportError:
    print("Warning: Repository module not available")
    ScriptRepository = None
    ChecksumVerificationError = Exception

# Manifest management (consolidated)
try:
    from lib.manifest import (
        ManifestLoader,
        ManifestManager,
        get_local_repository_manifests,
        ScriptScanner,
        CustomManifestCreator,
        load_scripts_from_manifest,
        fetch_manifest,
        refresh_manifest_cache
    )
except ImportError:
    print("Warning: Manifest module not available")
    ManifestManager = None
    ScriptScanner = None
    CustomManifestCreator = None
    get_local_repository_manifests = None
    refresh_manifest_cache = None

# User scripts management
try:
    from lib.user_scripts import CustomScriptManager
except ImportError:
    print("Warning: Custom scripts module not available")
    CustomScriptManager = None

# Configuration
try:
    from lib import config as C
except ImportError:
    print("Warning: Configuration module not available")
    C = None

# UI helpers
try:
    from lib import dialog_helpers as UI
except ImportError:
    print("Warning: UI helpers module not available")
    UI = None

# AI tools
try:
    from lib.ai_categorizer import OllamaAnalyzer, check_ollama_available
except ImportError:
    print("Warning: AI analyzer module not available")
    OllamaAnalyzer = None
    check_ollama_available = None

# Tab handlers (refactored UI components)
try:
    from lib.repository_tab import RepositoryTabHandler
    from lib.local_repository_tab import LocalRepositoryTabHandler
    from lib.custom_manifest_tab import CustomManifestTabHandler
except ImportError as e:
    print(f"Warning: Tab handler modules not available: {e}")
    RepositoryTabHandler = None
    LocalRepositoryTabHandler = None
    CustomManifestTabHandler = None

# Script management (consolidated)
try:
    from lib.script import (
        build_script_metadata,
        is_script_cached,
        should_use_cache_engine,
        get_script_env_requirements,
        validate_script_env_var,
        build_script_command,
        ScriptMetadata,
        ScriptCache,
        ScriptEnvironment,
        ScriptExecutor,
        ScriptNavigator
    )
except ImportError:
    print("Warning: Script module not available")
    build_script_metadata = None
    is_script_cached = None
    should_use_cache_engine = None
    get_script_env_requirements = None
    validate_script_env_var = None
    build_script_command = None
    is_script_cached = None
    should_use_cache_engine = None
    get_script_env_requirements = None
    validate_script_env_var = None
    build_script_command = None

try:
    # optional nicer icons / pixbuf usage if available
    from gi.repository import GdkPixbuf
except Exception:
    GdkPixbuf = None

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

# Import from constants module (fallback to hardcoded if import fails)
if C:
    REQUIRED_PACKAGES = C.REQUIRED_PACKAGES
    OPTIONAL_PACKAGES = C.OPTIONAL_PACKAGES
    OPTIONAL_COMMANDS = C.OPTIONAL_COMMANDS
else:
    REQUIRED_PACKAGES = ["bash", "zenity", "sudo"]
    OPTIONAL_PACKAGES = ["bat", "pygmentize", "highlight"]
    OPTIONAL_COMMANDS = ["batcat", "pygmentize", "highlight"]

# Manifest configuration (can be overridden by config)
if C:
    DEFAULT_MANIFEST_URL = C.DEFAULT_MANIFEST_URL
    MANIFEST_CACHE_DIR = C.CONFIG_DIR
    MANIFEST_CACHE_FILE = C.MANIFEST_CACHE_FILE
    MANIFEST_CACHE_MAX_AGE = C.MANIFEST_CACHE_MAX_AGE
else:
    DEFAULT_MANIFEST_URL = "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/manifest.json"
    MANIFEST_CACHE_DIR = PathManager.get_config_dir() if PathManager else Path.home() / '.lv_linux_learn'
    MANIFEST_CACHE_FILE = PathManager.get_manifest_cache_file() if PathManager else MANIFEST_CACHE_DIR / 'manifest.json'
    MANIFEST_CACHE_MAX_AGE = 3600

MANIFEST_URL = os.environ.get('CUSTOM_MANIFEST_URL', DEFAULT_MANIFEST_URL)


# ============================================================================
# MANIFEST LOADING FUNCTIONS
# ============================================================================

# Note: Global loading doesn't use terminal widget (goes to stdout)
# Try to initialize with repository for custom configuration
try:
    _temp_repo = ScriptRepository() if ScriptRepository else None
    _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, _SCRIPT_ID_MAP = load_scripts_from_manifest(repository=_temp_repo)
except Exception:
    # Fallback to default loading if repository initialization fails
    _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, _SCRIPT_ID_MAP = load_scripts_from_manifest()

# Create flat arrays for backward compatibility
SCRIPTS = _SCRIPTS_DICT.get('install', [])
SCRIPT_NAMES = _NAMES_DICT.get('install', [])

TOOLS_SCRIPTS = _SCRIPTS_DICT.get('tools', [])
TOOLS_NAMES = _NAMES_DICT.get('tools', [])

EXERCISES_SCRIPTS = _SCRIPTS_DICT.get('exercises', [])
EXERCISES_NAMES = _NAMES_DICT.get('exercises', [])

UNINSTALL_SCRIPTS = _SCRIPTS_DICT.get('uninstall', [])
UNINSTALL_NAMES = _NAMES_DICT.get('uninstall', [])

# Create flat descriptions arrays for backward compatibility
DESCRIPTIONS = _DESCRIPTIONS_DICT.get('install', [])
TOOLS_DESCRIPTIONS = _DESCRIPTIONS_DICT.get('tools', [])
EXERCISES_DESCRIPTIONS = _DESCRIPTIONS_DICT.get('exercises', [])
UNINSTALL_DESCRIPTIONS = _DESCRIPTIONS_DICT.get('uninstall', [])

# Global script ID mapping: (category, script_path) -> (script_id, source_name)
# This allows metadata builder to retrieve script IDs without re-parsing manifests
_SCRIPT_ID_MAP = {}


# ============================================================================
# GTK THEME / CSS STYLING
# ============================================================================

DARK_CSS = b"""
/* Modern Light Theme */
* {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Ubuntu', 'Roboto', sans-serif;
}

window {
    background: linear-gradient(to bottom, #f5f7fa 0%, #e8ecf1 100%);
}

/* Modern HeaderBar */
headerbar {
    background: linear-gradient(to bottom, #2c3e50 0%, #34495e 100%);
    color: #ecf0f1;
    border-bottom: 1px solid rgba(0, 0, 0, 0.2);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    min-height: 48px;
    padding: 0 12px;
}

headerbar * {
    color: #ecf0f1;
}

headerbar entry {
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 18px;
    color: #ffffff;
    padding: 8px 16px;
    min-height: 36px;
}

headerbar entry:focus {
    background: rgba(255, 255, 255, 0.25);
    border-color: rgba(255, 255, 255, 0.4);
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.3);
}

/* Modern Notebook (tabs) */
notebook {
    background: transparent;
    border: none;
}

notebook > header {
    background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
    border-bottom: 2px solid #dee2e6;
    padding: 4px 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

notebook > header > tabs > tab {
    background: transparent;
    color: #6c757d;
    border: none;
    border-radius: 8px 8px 0 0;
    padding: 12px 24px;
    margin: 0 2px;
    font-weight: 500;
    font-size: 14px;
}

notebook > header > tabs > tab:hover {
    background: rgba(52, 152, 219, 0.1);
    color: #2c3e50;
}

notebook > header > tabs > tab:checked {
    background: linear-gradient(to bottom, #3498db 0%, #2980b9 100%);
    color: #ffffff;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);
}

/* TreeView (script list) */
treeview {
    background: #ffffff;
    color: #2c3e50;
    border-radius: 8px;
    font-size: 14px;
    border: 1px solid #dee2e6;
}

treeview:selected {
    background: linear-gradient(to right, #3498db 0%, #2980b9 100%);
    color: #ffffff;
}

treeview header button {
    background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);
    color: #495057;
    border: 1px solid #dee2e6;
    padding: 8px 12px;
    font-weight: 600;
}

/* Scrollbars */
scrollbar slider {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 10px;
    min-width: 12px;
    min-height: 12px;
    margin: 2px;
}

scrollbar slider:hover {
    background: rgba(0, 0, 0, 0.3);
}

/* Modern Buttons */
button {
    background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
    color: #495057;
    border: 1px solid #ced4da;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    min-height: 36px;
    min-width: 100px;
}

button:hover {
    background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);
    border-color: #adb5bd;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

button.suggested-action {
    background: linear-gradient(to bottom, #3498db 0%, #2980b9 100%);
    color: #ffffff;
    border-color: #2980b9;
    font-weight: 600;
}

button.suggested-action:hover {
    background: linear-gradient(to bottom, #5dade2 0%, #3498db 100%);
    box-shadow: 0 3px 8px rgba(52, 152, 219, 0.3);
}

button.destructive-action {
    background: linear-gradient(to bottom, #e74c3c 0%, #c0392b 100%);
    color: #ffffff;
    border-color: #c0392b;
}

button.destructive-action:hover {
    background: linear-gradient(to bottom, #ec7063 0%, #e74c3c 100%);
}

/* Frame styling */
frame {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* Terminal frame */
frame:last-child {
    background: #1e1e1e;
    border-color: #343a40;
}

/* Labels */
label {
    color: #2c3e50;
}

#desc_label {
    color: #6c757d;
    font-style: italic;
    font-size: 13px;
}

/* Paned separator */
paned > separator {
    background: #dee2e6;
    min-width: 6px;
    min-height: 6px;
}

paned > separator:hover {
    background: #adb5bd;
}

.scroll {
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
"""


# ============================================================================
# REPOSITORY HANDLERS - Strategy Pattern for Each Repository Type
# ============================================================================

class RepositoryHandler:
    """Base class for repository script handling"""
    
    def __init__(self, repository, config):
        self.repository = repository
        self.config = config
        
    def get_scripts(self):
        """Get all scripts from this repository type. Must be implemented by subclasses."""
        raise NotImplementedError
        
    def build_metadata(self, script, source_name, file_path=None):
        """Build standardized metadata for a script"""
        metadata = {
            'script_id': script.get('id', ''),
            'source_type': self.get_source_type(),
            'source_name': source_name,
            'type': self.get_script_type(script)
        }
        # Add file path for local repositories
        if file_path:
            metadata['file_path'] = file_path
        return metadata
    
    def get_source_type(self):
        """Return the source type identifier"""
        raise NotImplementedError
        
    def get_script_type(self, script):
        """Return whether script is 'local', 'cached', or 'remote'"""
        raise NotImplementedError


class PublicRepositoryHandler(RepositoryHandler):
    """Handler for public repository (cache-based, GitHub)"""
    
    def get_source_type(self):
        return 'public_repo'
    
    def get_script_type(self, script):
        return 'remote'  # Public repo scripts need to be cached
    
    def get_scripts(self):
        """Get all scripts from public repository"""
        scripts_by_category = {}
        
        # Check if public repo is enabled
        if not self.config.get('use_public_repository', True):
            return scripts_by_category
        
        try:
            public_scripts = self.repository.parse_manifest()
            for script in public_scripts:
                category = script.get('category', 'install')
                path = script.get('path', script.get('id', ''))
                name = script.get('name', path)
                desc = script.get('description', '')
                metadata = self.build_metadata(script, 'Public Repository')
                
                if category not in scripts_by_category:
                    scripts_by_category[category] = []
                scripts_by_category[category].append((path, name, desc, metadata))
        except Exception as e:
            print(f"Warning: Could not load public repository: {e}")
        
        return scripts_by_category


class OnlineCustomRepositoryHandler(RepositoryHandler):
    """Handler for online custom repositories (cache-based, URL manifests)"""
    
    def get_source_type(self):
        return 'custom_repo'
    
    def get_script_type(self, script):
        return 'remote'  # Online custom repos need to be cached
    
    def get_scripts(self):
        """Get all scripts from online custom repositories"""
        scripts_by_category = {}
        
        custom_manifests_config = self.config.get('custom_manifests', {})
        if not custom_manifests_config:
            return scripts_by_category
        
        custom_manifests_dir = PathManager.get_custom_manifests_dir() if PathManager else Path.home() / '.lv_linux_learn' / 'custom_manifests'
        if not custom_manifests_dir.exists():
            return scripts_by_category
        
        try:
            for manifest_file in custom_manifests_dir.glob('*.json'):
                manifest_stem = manifest_file.stem
                
                # Only load if configured
                if manifest_stem not in custom_manifests_config:
                    continue
                
                try:
                    if FileLoader:
                        manifest_data = FileLoader.load_json(manifest_file, default={})
                    else:
                        import json
                        with open(manifest_file) as f:
                            manifest_data = json.load(f)
                    
                    repo_url = manifest_data.get('repository_url', '')
                    
                    # Only process URLs (online repos)
                    if not repo_url.startswith(('http://', 'https://')):
                        continue
                    
                    manifest_name = manifest_file.stem.replace('_', ' ').title()
                    self._process_manifest_scripts(manifest_data, manifest_name, scripts_by_category)
                    
                except Exception as e:
                    print(f"Warning: Could not load online manifest {manifest_file.name}: {e}")
        
        except Exception as e:
            print(f"Error loading online custom repositories: {e}")
        
        return scripts_by_category
    
    def _process_manifest_scripts(self, manifest_data, manifest_name, scripts_by_category):
        """Process scripts from manifest data"""
        scripts = manifest_data.get('scripts', [])
        
        if isinstance(scripts, dict):
            for category, category_scripts in scripts.items():
                if isinstance(category_scripts, list):
                    for script in category_scripts:
                        self._add_script_to_category(script, category, manifest_name, scripts_by_category)
        else:
            for script in scripts:
                category = script.get('category', 'install')
                self._add_script_to_category(script, category, manifest_name, scripts_by_category)
    
    def _add_script_to_category(self, script, category, manifest_name, scripts_by_category):
        """Add a script to the appropriate category"""
        path = script.get('path', script.get('id', ''))
        name = script.get('name', path)
        desc = script.get('description', '')
        metadata = self.build_metadata(script, manifest_name)
        
        if category not in scripts_by_category:
            scripts_by_category[category] = []
        scripts_by_category[category].append((path, name, desc, metadata))


class LocalCustomRepositoryHandler(RepositoryHandler):
    """Handler for local custom repositories (direct execution, file-based)"""
    
    def get_source_type(self):
        return 'local_repo'
    
    def get_script_type(self, script):
        return 'local'  # Local scripts are executed directly
    
    def get_scripts(self):
        """Get all scripts from local custom repositories"""
        scripts_by_category = {}
        
        custom_manifests_config = self.config.get('custom_manifests', {})
        if not custom_manifests_config:
            return scripts_by_category
        
        # Use PathManager for custom manifests directory
        custom_manifests_dir = PathManager.get_custom_manifests_dir() if PathManager else Path.home() / '.lv_linux_learn' / 'custom_manifests'
        if not custom_manifests_dir.exists():
            return scripts_by_category
        
        try:
            manifest_files = (
                list(custom_manifests_dir.glob('*/manifest.json')) +
                list(custom_manifests_dir.glob('*_manifest.json'))
            )
            
            for manifest_file in manifest_files:
                # Determine repository name
                if manifest_file.parent != custom_manifests_dir:
                    repo_name = manifest_file.parent.name
                else:
                    repo_name = manifest_file.stem.replace('_manifest', '')
                
                # Only load if configured
                if repo_name not in custom_manifests_config:
                    continue
                
                try:
                    import json
                    with open(manifest_file) as f:
                        manifest_data = json.load(f)
                    
                    repo_url = manifest_data.get('repository_url', '')
                    
                    # Only process local repos (no http/https URLs)
                    if repo_url.startswith(('http://', 'https://')):
                        continue
                    
                    manifest_name = manifest_file.stem.replace('_', ' ').title()
                    base_path = manifest_file.parent  # Use actual manifest directory
                    self._process_manifest_scripts(manifest_data, manifest_name, scripts_by_category, base_path)
                    
                except Exception as e:
                    print(f"Warning: Could not load local manifest {manifest_file.name}: {e}")
        
        except Exception as e:
            print(f"Error loading local custom repositories: {e}")
        
        return scripts_by_category
    
    def _process_manifest_scripts(self, manifest_data, manifest_name, scripts_by_category, base_path):
        """Process scripts from manifest data"""
        scripts = manifest_data.get('scripts', [])
        
        if isinstance(scripts, dict):
            for category, category_scripts in scripts.items():
                if isinstance(category_scripts, list):
                    for script in category_scripts:
                        self._add_script_to_category(script, category, manifest_name, scripts_by_category, base_path)
        else:
            for script in scripts:
                category = script.get('category', 'install')
                self._add_script_to_category(script, category, manifest_name, scripts_by_category, base_path)
    
    def _add_script_to_category(self, script, category, manifest_name, scripts_by_category, base_path):
        """Add a script to the appropriate category"""
        script_id = script.get('id', '')
        name = script.get('name', script_id)
        desc = script.get('description', '')
        
        # Build full local file path (same logic as local_repository_tab.py)
        full_path = None
        
        # Method 1: Check for download_url (file:// URL)
        download_url = script.get('download_url', '')
        if download_url and download_url.startswith('file://'):
            full_path = download_url.replace('file://', '')
        
        # Method 2: Use file_name + base_path + category
        if not full_path:
            file_name = script.get('file_name', '')
            if file_name:
                if os.path.isabs(file_name):
                    full_path = file_name
                elif base_path:
                    full_path = str(base_path / category / file_name)
        
        # Method 3: Try just file_name as relative path from base_path
        if not full_path:
            file_name = script.get('file_name', '')
            if file_name and base_path:
                full_path = str(base_path / file_name)
        
        # Fallback to script_id if no path found
        if not full_path:
            full_path = script_id
        
        metadata = self.build_metadata(script, manifest_name, full_path)
        
        if category not in scripts_by_category:
            scripts_by_category[category] = []
        # Return (file_path, name, description, metadata) - first element is the actual file path
        scripts_by_category[category].append((full_path, name, desc, metadata))


# ============================================================================
# UI REFRESH COORDINATOR - Centralized UI Update Logic
# ============================================================================

class UIRefreshCoordinator:
    """Centralized coordinator for all UI refresh operations"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        
    def refresh_after_repo_toggle(self):
        """Refresh UI after toggling public repository on/off"""
        try:
            # 1. Clear manifest cache
            global MANIFEST_CACHE_FILE
            if MANIFEST_CACHE_FILE.exists():
                MANIFEST_CACHE_FILE.unlink()
            
            # 2. Refresh repository configuration
            if self.parent.repository:
                self.parent.repository.refresh_repository_url()
            
            # 3. Update repository tree if available
            if self.parent.repo_enabled and hasattr(self.parent, '_populate_repository_tree'):
                self.parent._populate_repository_tree()
                self.parent._update_repo_status()
            
            # 4. Reload main tabs with new configuration
            self._reload_main_tabs()
            
        except Exception as e:
            print(f"Error in refresh_after_repo_toggle: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_after_source_change(self):
        """Refresh UI after adding/removing custom sources"""
        try:
            # 1. Reload main tabs
            self._reload_main_tabs()
            
            # 2. Update custom manifests tree
            if hasattr(self.parent, '_populate_custom_manifests'):
                self.parent._populate_custom_manifests()
            
        except Exception as e:
            print(f"Error in refresh_after_source_change: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_after_cache_change(self):
        """Refresh UI after downloading/removing cached scripts"""
        try:
            # 1. Update repository status and tree
            if hasattr(self.parent, '_update_repo_status'):
                self.parent._update_repo_status()
            if hasattr(self.parent, '_populate_repository_tree'):
                self.parent._populate_repository_tree()
            
            # 2. Reload main tabs to show cache status
            self._reload_main_tabs()
            
        except Exception as e:
            print(f"Error in refresh_after_cache_change: {e}")
            import traceback
            traceback.print_exc()
    
    def _reload_main_tabs(self):
        """Reload main tabs with fresh script data"""
        try:
            # Reload global script arrays from manifest
            global SCRIPTS, SCRIPT_NAMES, DESCRIPTIONS
            global TOOLS_SCRIPTS, TOOLS_NAMES, TOOLS_DESCRIPTIONS
            global EXERCISES_SCRIPTS, EXERCISES_NAMES, EXERCISES_DESCRIPTIONS
            global UNINSTALL_SCRIPTS, UNINSTALL_NAMES, UNINSTALL_DESCRIPTIONS
            global _SCRIPT_ID_MAP
            
            _scripts, _names, _descriptions, _SCRIPT_ID_MAP = load_scripts_from_manifest(
                terminal_widget=self.parent.terminal,
                repository=self.parent.repository
            )
            
            # Update global arrays
            SCRIPTS[:] = _scripts.get('install', [])
            SCRIPT_NAMES[:] = _names.get('install', [])
            DESCRIPTIONS[:] = _descriptions.get('install', [])
            
            TOOLS_SCRIPTS[:] = _scripts.get('tools', [])
            TOOLS_NAMES[:] = _names.get('tools', [])
            TOOLS_DESCRIPTIONS[:] = _descriptions.get('tools', [])
            
            EXERCISES_SCRIPTS[:] = _scripts.get('exercises', [])
            EXERCISES_NAMES[:] = _names.get('exercises', [])
            EXERCISES_DESCRIPTIONS[:] = _descriptions.get('exercises', [])
            
            UNINSTALL_SCRIPTS[:] = _scripts.get('uninstall', [])
            UNINSTALL_NAMES[:] = _names.get('uninstall', [])
            UNINSTALL_DESCRIPTIONS[:] = _descriptions.get('uninstall', [])
            
            # Rebuild dynamic tabs using TabManager
            if hasattr(self.parent, 'tab_manager') and self.parent.repository:
                config = self.parent.repository.load_config()
                GLib.timeout_add(50, lambda: self.parent.tab_manager.rebuild_dynamic_tabs(
                    self.parent.repository, config
                ))
            
            # Repopulate tab list stores
            GLib.timeout_add(100, self._repopulate_tab_stores)
            
        except Exception as e:
            print(f"Error reloading main tabs: {e}")
            import traceback
            traceback.print_exc()
    
    def _repopulate_tab_stores(self):
        """Repopulate liststores for all standard tabs"""
        if hasattr(self.parent, '_repopulate_tab_stores'):
            self.parent._repopulate_tab_stores()
        return False


# ============================================================================
# SCRIPT ACTION HANDLER - Unified Button Actions for All Repository Types
# ============================================================================

class ScriptActionHandler:
    """
    Centralized handler for script actions (View, Navigate, Run).
    Works consistently across all repository types and handles cache vs direct execution.
    """
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.repository = parent_window.repository
        self.terminal = parent_window.terminal
    
    def view_script(self, script_path, metadata):
        """
        View script content with syntax highlighting.
        Handles: Local (direct), Cached (view), Remote (download then view)
        """
        source_type = metadata.get("source_type", "unknown")
        source_name = metadata.get("source_name", "Unknown Source")
        script_type = metadata.get("type", "unknown")
        script_name = os.path.basename(script_path)
        
        # === LOCAL REPOSITORY: Direct view ===
        if script_type == "local" or source_type == "local_repo":
            return self._view_local_script(script_path, source_name)
        
        # === CACHED: View from cache ===
        if script_type == "cached" and os.path.isfile(script_path):
            return self._view_file(script_path, source_name, "Cached Script")
        
        # === REMOTE: Download then view ===
        if script_type == "remote":
            return self._view_remote_script(script_path, metadata, source_type, source_name, script_name)
        
        # === FALLBACK: Try viewing if file exists ===
        if os.path.isfile(script_path):
            return self._view_file(script_path, source_name, "Script")
        
        if TerminalMessenger:
            TerminalMessenger(self.terminal).error(f"Cannot view script: {script_path}")
        else:
            self.terminal.feed(f"\x1b[31m[✗] Cannot view script: {script_path}\x1b[0m\r\n".encode())
        return False
    
    def navigate_to_directory(self, script_path, metadata):
        """
        Navigate to script directory in terminal.
        Handles: Local (direct), Cached (navigate), Remote (download then navigate)
        """
        script_type = metadata.get("type", "unknown")
        script_name = os.path.basename(script_path)
        
        # === LOCAL REPOSITORY: Direct navigation ===
        if script_type == "local":
            return self._navigate_local(script_path)
        
        # === CACHED: Navigate to cache directory ===
        if script_type == "cached" and os.path.isfile(script_path):
            return self._navigate_to_file(script_path)
        
        # === REMOTE: Download then navigate ===
        if script_type == "remote":
            return self._navigate_remote_with_download(script_path, metadata, script_name)
        
        # === FALLBACK: Try navigating if file exists ===
        if os.path.isfile(script_path):
            return self._navigate_to_file(script_path)
        
        if TerminalMessenger:
            TerminalMessenger(self.terminal).error("Cannot navigate: script not available")
        else:
            self.terminal.feed(f"\x1b[31m[✗] Cannot navigate: script not available\x1b[0m\r\n".encode())
        return False
    
    def run_script(self, script_path, metadata):
        """
        Execute script in terminal.
        Handles: Local (direct), Cached (execute), Remote (download then execute)
        """
        script_type = metadata.get("type", "unknown")
        script_name = os.path.basename(script_path)
        
        # === LOCAL REPOSITORY: Direct execution ===
        if script_type == "local":
            return self._execute_local(script_path, metadata)
        
        # === CACHED: Execute from cache ===
        if script_type == "cached" and os.path.isfile(script_path):
            return self._execute_file(script_path, metadata)
        
        # === REMOTE: Download then execute ===
        if script_type == "remote":
            return self._execute_remote_with_download(script_path, metadata, script_name)
        
        # === FALLBACK: Try executing if file exists ===
        if os.path.isfile(script_path):
            return self._execute_file(script_path, metadata)
        
        if TerminalMessenger:
            TerminalMessenger(self.terminal).error("Cannot run script: not available")
        else:
            self.terminal.feed(f"\x1b[31m[✗] Cannot run script: not available\x1b[0m\r\n".encode())
        return False
    
    # ========================================================================
    # PRIVATE HELPERS - View Operations
    # ========================================================================
    
    def _view_local_script(self, script_path, source_name):
        """View local repository script directly"""
        file_path = script_path[7:] if script_path.startswith('file://') else script_path
        if os.path.isfile(file_path):
            abs_path = os.path.abspath(file_path)
            return self._view_file(abs_path, source_name, "Local Repository Script")
        if TerminalMessenger:
            TerminalMessenger(self.terminal).error(f"Local script not found: {file_path}")
        else:
            self.terminal.feed(f"\x1b[31m[✗] Local script not found: {file_path}\x1b[0m\r\n".encode())
        return False
    
    def _view_remote_script(self, script_path, metadata, source_type, source_name, script_name):
        """Download and view remote script"""
        script_id = self._get_script_id(script_path, metadata, script_name)
        if not script_id:
            if TerminalMessenger:
                TerminalMessenger(self.terminal).error("Cannot identify script for download")
            else:
                self.terminal.feed(f"\x1b[31m[✗] Cannot identify script for download\x1b[0m\r\n".encode())
            return False
        
        # Check if already cached
        if self.repository:
            cached_path = self.repository.get_cached_script_path(script_id)
            if cached_path and os.path.isfile(cached_path):
                return self._view_file(cached_path, source_name, "Cached Script")
        
        # Download to view
        repo_label = "Public" if source_type == "public_repo" else f"Custom ({source_name})"
        self.terminal.feed(f"\x1b[33m[*] Downloading {repo_label} script '{script_name}' to view...\x1b[0m\r\n".encode())
        
        if self._download_script(script_id, metadata):
            if self.repository:
                cached_path = self.repository.get_cached_script_path(script_id)
                if cached_path and os.path.isfile(cached_path):
                    return self._view_file(cached_path, source_name, "Downloaded Script")
        
        return False
    
    def _view_file(self, file_path, source_name, script_type_label):
        """View file with syntax highlighting"""
        safe_path = shlex.quote(file_path)
        viewer_cmd = (
            f"clear; "
            f"echo ''; "
            f"echo '{'=' * 80}'; "
            f"echo 'Viewing: {file_path}'; "
            f"echo 'Source: {source_name}'; "
            f"echo 'Type: {script_type_label}'; "
            f"echo '{'=' * 80}'; "
            f"echo ''; "
            f"if command -v batcat >/dev/null 2>&1; then "
            f"batcat --paging=never --style=plain --color=always {safe_path}; "
            f"elif command -v bat >/dev/null 2>&1; then "
            f"bat --paging=never --style=plain --color=always {safe_path}; "
            f"elif command -v pygmentize >/dev/null 2>&1; then "
            f"pygmentize -g -f terminal256 {safe_path}; "
            f"else "
            f"cat {safe_path}; "
            f"fi; "
            f"echo ''; "
            f"echo '{'=' * 80}'\n"
        )
        self.terminal.feed_child(viewer_cmd.encode())
        return True
    
    # ========================================================================
    # PRIVATE HELPERS - Navigation Operations
    # ========================================================================
    
    def _navigate_local(self, script_path):
        """Navigate to local repository script directory"""
        file_path = script_path[7:] if script_path.startswith('file://') else script_path
        if os.path.isfile(file_path):
            return self._navigate_to_file(file_path)
        if TerminalMessenger:
            TerminalMessenger(self.terminal).error(f"Local script not found: {file_path}")
        else:
            self.terminal.feed(f"\x1b[31m[✗] Local script not found: {file_path}\x1b[0m\r\n".encode())
        return False
    
    def _navigate_remote_with_download(self, script_path, metadata, script_name):
        """Download and navigate to remote script"""
        script_id = self._get_script_id(script_path, metadata, script_name)
        if not script_id:
            return False
        
        if TerminalMessenger:
            TerminalMessenger(self.terminal).download(f"{script_name} to navigate")
        else:
            self.terminal.feed(f"\x1b[32m[*] Downloading {script_name} to navigate...\x1b[0m\r\n".encode())
        
        if self._download_script(script_id, metadata):
            if self.repository:
                cached_path = self.repository.get_cached_script_path(script_id)
                if cached_path and os.path.isfile(cached_path):
                    return self._navigate_to_file(str(cached_path))
        
        return False
    
    def _navigate_to_file(self, file_path):
        """Navigate terminal to file's directory"""
        abs_path = os.path.abspath(file_path)
        directory = os.path.dirname(abs_path)
        safe_dir = shlex.quote(directory)
        
        cmd = f"clear && cd {safe_dir} && pwd && ls -lah\n"
        self.terminal.feed_child(cmd.encode())
        if TerminalMessenger:
            TerminalMessenger(self.terminal).success(f"Navigated to: {directory}")
        else:
            self.terminal.feed(f"\x1b[32m[✓] Navigated to: {directory}\x1b[0m\r\n".encode())
        return True
    
    # ========================================================================
    # PRIVATE HELPERS - Execution Operations
    # ========================================================================
    
    def _execute_local(self, script_path, metadata):
        """Execute local repository script directly"""
        file_path = script_path[7:] if script_path.startswith('file://') else script_path
        if os.path.isfile(file_path):
            return self._execute_file(file_path, metadata)
        if TerminalMessenger:
            TerminalMessenger(self.terminal).error(f"Local script not found: {file_path}")
        else:
            self.terminal.feed(f"\x1b[31m[✗] Local script not found: {file_path}\x1b[0m\r\n".encode())
        return False
    
    def _execute_remote_with_download(self, script_path, metadata, script_name):
        """Download and execute remote script"""
        script_id = self._get_script_id(script_path, metadata, script_name)
        if not script_id:
            return False
        
        if TerminalMessenger:
            TerminalMessenger(self.terminal).download(f"☁️ {script_name}")
        else:
            self.terminal.feed(f"\x1b[32m[*] Downloading ☁️ {script_name}...\x1b[0m\r\n".encode())
        
        if self._download_script(script_id, metadata):
            if self.repository:
                cached_path = self.repository.get_cached_script_path(script_id)
                if cached_path and os.path.isfile(cached_path):
                    updated_metadata = metadata.copy()
                    updated_metadata["type"] = "cached"
                    return self._execute_file(str(cached_path), updated_metadata)
        
        return False
    
    def _execute_file(self, file_path, metadata):
        """Execute script file"""
        abs_path = os.path.abspath(file_path)
        
        # Determine if we should use cache engine
        use_cache = self._should_use_cache_engine(metadata)
        
        if use_cache:
            # Cache-based execution
            safe_path = shlex.quote(abs_path)
            cmd = f"bash {safe_path}\n"
            self.terminal.feed_child(cmd.encode())
            if TerminalMessenger:
                TerminalMessenger(self.terminal).info(f"Executing cached script: {os.path.basename(file_path)}")
            else:
                self.terminal.feed(f"\x1b[32m[*] Executing cached script: {os.path.basename(file_path)}\x1b[0m\r\n".encode())
        else:
            # Direct execution (local repos, custom scripts)
            safe_path = shlex.quote(abs_path)
            directory = os.path.dirname(abs_path)
            safe_dir = shlex.quote(directory)
            
            cmd = f"cd {safe_dir} && bash {safe_path}\n"
            self.terminal.feed_child(cmd.encode())
            if TerminalMessenger:
                TerminalMessenger(self.terminal).info(f"Executing local script: {os.path.basename(file_path)}")
            else:
                self.terminal.feed(f"\x1b[32m[*] Executing local script: {os.path.basename(file_path)}\x1b[0m\r\n".encode())
        
        return True
    
    # ========================================================================
    # PRIVATE HELPERS - Utility Functions
    # ========================================================================
    
    def _get_script_id(self, script_path, metadata, script_name):
        """Get script ID for cache operations"""
        # Try metadata first
        script_id = metadata.get("script_id")
        if script_id:
            return script_id
        
        # Try pending path
        if str(script_path).startswith("cache://pending/"):
            return script_path.split("/")[-1]
        
        # Fallback to manifest lookup
        if hasattr(self.parent, '_get_manifest_script_id'):
            script_id, _ = self.parent._get_manifest_script_id(script_name, script_path)
            return script_id
        
        return None
    
    def _download_script(self, script_id, metadata):
        """Download script to cache"""
        if not self.repository:
            return False
        
        try:
            # Determine manifest path based on source
            manifest_path = None
            source_name = metadata.get('source', '') or metadata.get('source_name', '')  # Support both field names
            source_type = metadata.get('source_type', '')
            
            print(f"[DEBUG _download_script] script_id={script_id}, source_name={source_name}, source_type={source_type}")
            
            # If it's a custom repository, find the manifest file
            if source_type == 'custom_repo' and source_name:
                config = self.repository.load_config()
                custom_manifests = config.get('custom_manifests', {})
                
                print(f"[DEBUG] custom_manifests keys: {list(custom_manifests.keys())}")
                
                if source_name in custom_manifests:
                    # Custom manifest from config - use temp file
                    cache_dir = PathManager.get_config_dir() if PathManager else Path.home() / '.lv_linux_learn'
                    manifest_path = str(cache_dir / f"temp_{source_name}_manifest.json")
                    
                    # Ensure temp manifest exists with current data
                    manifest_data = custom_manifests[source_name].get('manifest_data')
                    if manifest_data:
                        with open(manifest_path, 'w') as f:
                            json.dump(manifest_data, f, indent=2)
                        print(f"[DEBUG] Created temp manifest: {manifest_path}")
                    else:
                        print(f"[DEBUG] No manifest_data found for {source_name}")
                else:
                    print(f"[DEBUG] source_name '{source_name}' not found in custom_manifests")
            
            print(f"[DEBUG] Using manifest_path: {manifest_path}")
            result = self.repository.download_script(script_id, manifest_path=manifest_path)
            success = result[0] if isinstance(result, tuple) else result
            url = result[1] if isinstance(result, tuple) and len(result) > 1 else None
            
            if success:
                if url:
                    self.terminal.feed(f"\x1b[36m[*] URL: {url}\x1b[0m\r\n".encode())
                if TerminalMessenger:
                    TerminalMessenger(self.terminal).success("Download complete")
                else:
                    self.terminal.feed(f"\x1b[32m[✓] Download complete\x1b[0m\r\n".encode())
                
                # Refresh UI
                if hasattr(self.parent, 'ui_refresh'):
                    GLib.timeout_add(500, lambda: (
                        self.parent.ui_refresh.refresh_after_cache_change(),
                        False
                    )[1])
                return True
            else:
                error_msg = result[2] if isinstance(result, tuple) and len(result) > 2 else "Unknown error"
                self.terminal.feed(f"\x1b[31m[✗] Download failed: {error_msg}\x1b[0m\r\n".encode())
                return False
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[✗] Error: {e}\x1b[0m\r\n".encode())
            return False
    
    def _should_use_cache_engine(self, metadata):
        """Determine if cache engine should be used for execution"""
        source_type = metadata.get("source_type", "unknown")
        script_type = metadata.get("type", "unknown")
        
        # Local repos and custom scripts: direct execution
        if source_type in ["custom_local", "local_repo", "custom_script"]:
            return False
        if script_type == "local":
            return False
        
        # Public and online custom repos: cache execution
        if source_type in ["public_repo", "custom_repo"]:
            return True
        
        # Default to cache if uncertain
        return True


# ============================================================================
# TAB MANAGEMENT CLASS
# ============================================================================

class TabManager:
    """Centralized tab management for all repository types and dynamic categories"""
    
    def __init__(self, notebook, parent_window):
        """
        Initialize TabManager
        
        Args:
            notebook: Gtk.Notebook widget
            parent_window: Reference to ScriptMenuGTK instance for callbacks
        """
        self.notebook = notebook
        self.parent = parent_window
        
        # Tab registry - single source of truth
        self.tabs_registry = {
            'standard': {},      # install, tools, exercises, uninstall
            'repository': {},    # repository_online, repository_local, sources
            'dynamic': {}        # AI-categorized tabs
        }
        
        # Track widget references for safe removal
        self.standard_widgets = set()
        self.repository_widgets = set()
        
    def register_standard_tab(self, name, widget):
        """Register a standard tab (install, tools, exercises, uninstall)"""
        self.tabs_registry['standard'][name] = widget
        self.standard_widgets.add(widget)
        
    def register_repository_tab(self, name, widget):
        """Register a repository tab (online repo, local repo, sources)"""
        self.tabs_registry['repository'][name] = widget
        self.repository_widgets.add(widget)
        
    def get_all_repository_scripts(self, repository, config):
        """
        Unified aggregation of scripts from all repository types using Strategy Pattern.
        Each repository type has its own handler with clear separation of concerns.
        
        Returns:
            dict: {category: [(path, name, desc, metadata_dict), ...]}
        """
        from collections import defaultdict
        all_scripts = defaultdict(list)
        
        if not repository:
            return dict(all_scripts)
        
        try:
            # FIRST: Add scripts from globally-loaded manifest (_SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT)
            # These are loaded at startup and contain all active manifest scripts
            global _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, _SCRIPT_ID_MAP
            for category in _SCRIPTS_DICT.keys():
                scripts_list = _SCRIPTS_DICT.get(category, [])
                names_list = _NAMES_DICT.get(category, [])
                desc_list = _DESCRIPTIONS_DICT.get(category, [])
                
                for i, script_path in enumerate(scripts_list):
                    name = names_list[i] if i < len(names_list) else os.path.basename(script_path)
                    desc = desc_list[i] if i < len(desc_list) else ''
                    
                    # Build metadata from script ID map
                    script_id = ''
                    source_name = 'Unknown'
                    if (category, script_path) in _SCRIPT_ID_MAP:
                        script_id, source_name = _SCRIPT_ID_MAP[(category, script_path)]
                    
                    # Determine source type based on actual source configuration
                    # Check if source is in custom_manifests config (these should use cache engine)
                    custom_manifests = config.get('custom_manifests', {})
                    if source_name in custom_manifests:
                        # Custom manifest from config - always use cache engine
                        source_type = 'custom_repo'
                    elif '[Public Repository]' in name or source_name == 'Public Repository':
                        source_type = 'public_repo'
                    else:
                        # Check if this is truly a local file-based repository
                        # Local repos are discovered via directory scanning, not config
                        custom_manifests_dir = PathManager.get_custom_manifests_dir() if PathManager else Path.home() / '.lv_linux_learn' / 'custom_manifests'
                        try:
                            script_path_obj = Path(script_path.replace('file://', '') if script_path.startswith('file://') else script_path)
                            # If path is under custom_manifests directory structure, it's a true local repo
                            if custom_manifests_dir in script_path_obj.parents:
                                source_type = 'local_repo'
                            else:
                                source_type = 'custom_repo'  # Default to cache-based
                        except Exception:
                            source_type = 'custom_repo'  # Safe default: use cache
                    
                    metadata = {
                        'script_id': script_id,
                        'source_type': source_type,
                        'source': source_name,
                        'category': category,
                        'type': 'local' if source_type == 'local_repo' else 'remote'
                    }
                    
                    all_scripts[category].append((script_path, name, desc, metadata))
            
            # NOTE: Handlers are now deprecated - we load everything from global manifest
            # The global manifest (_SCRIPTS_DICT) already contains all scripts from all sources
            # including public repo, custom repos, and local repos
        
        except Exception as e:
            print(f"Error in get_all_repository_scripts: {e}")
            import traceback
            traceback.print_exc()
        
        return dict(all_scripts)
    
    def clear_dynamic_tabs(self):
        """
        Safely remove only dynamic tabs, preserving standard and repository tabs.
        Uses widget-based tracking instead of fragile index counting.
        """
        try:
            # Build set of all protected widgets (standard + repository tabs)
            protected_widgets = self.standard_widgets | self.repository_widgets
            
            # Remove tabs that are NOT protected (i.e., dynamic tabs only)
            num_pages = self.notebook.get_n_pages()
            
            for i in range(num_pages - 1, -1, -1):
                page = self.notebook.get_nth_page(i)
                is_protected = False
                
                # Direct widget match
                if page in protected_widgets:
                    is_protected = True
                else:
                    # For containers, check all descendants recursively
                    def check_descendants(widget):
                        """Recursively check if widget or any descendant is protected"""
                        if widget in protected_widgets:
                            return True
                        if hasattr(widget, 'get_children'):
                            for child in widget.get_children():
                                if check_descendants(child):
                                    return True
                        if hasattr(widget, 'get_child'):
                            child = widget.get_child()
                            if child and check_descendants(child):
                                return True
                        return False
                    
                    is_protected = check_descendants(page)
                
                # Remove unprotected (dynamic) tabs
                if not is_protected:
                    self.notebook.remove_page(i)
            
            # Clear dynamic registry
            self.tabs_registry['dynamic'].clear()
            
            # Clean up dynamic attributes from parent window
            if hasattr(self.parent, 'dynamic_categories'):
                self.parent.dynamic_categories.clear()
            if hasattr(self.parent, 'dynamic_filters'):
                self.parent.dynamic_filters.clear()
            if hasattr(self.parent, 'dynamic_widgets'):
                self.parent.dynamic_widgets.clear()
            
            # Remove dynamic treeview attributes
            for attr_name in list(self.parent.__dict__.keys()):
                if ('_dynamic_' in attr_name or 
                    (attr_name.endswith('_treeview') and 
                     attr_name not in ['install_treeview', 'tools_treeview', 
                                      'exercises_treeview', 'uninstall_treeview'])):
                    try:
                        delattr(self.parent, attr_name)
                    except Exception:
                        pass
                        
        except Exception as e:
            print(f"Error clearing dynamic tabs: {e}")
            import traceback
            traceback.print_exc()
    
    def rebuild_dynamic_tabs(self, repository, config):
        """
        Clear and rebuild dynamic category tabs from all repository sources.
        Unified method that handles public, online custom, and local repos.
        """
        if not repository:
            return
        
        # Clear existing dynamic tabs first
        self.clear_dynamic_tabs()
        
        # Get all scripts from unified source
        repo_scripts = self.get_all_repository_scripts(repository, config)
        
        # Standard categories that should NOT become tabs (either they're already tabs or they're special)
        excluded_categories = {'install', 'tools', 'exercises', 'uninstall', 'includes'}
        
        # Find dynamic categories (categories that aren't standard and should get their own tabs)
        dynamic_categories = set(repo_scripts.keys()) - excluded_categories
        
        if not dynamic_categories:
            return  # No dynamic categories
        
        # Initialize tracking in parent
        if not hasattr(self.parent, 'dynamic_categories'):
            self.parent.dynamic_categories = {}
        if not hasattr(self.parent, 'dynamic_filters'):
            self.parent.dynamic_filters = {}
        if not hasattr(self.parent, 'dynamic_widgets'):
            self.parent.dynamic_widgets = {}
        
        # Create tabs for each dynamic category
        for category in sorted(dynamic_categories):
            category_scripts = repo_scripts.get(category, [])
            
            if not category_scripts:
                continue
            
            # Extract script data
            scripts = [s[0] for s in category_scripts]
            descriptions = [s[2] for s in category_scripts]
            
            # Create the tab using parent's method
            category_box = self.parent._create_script_tab(scripts, descriptions, category)
            
            # Create tab label with emoji
            emoji = self._get_category_emoji(category)
            tab_label_text = f"{emoji} {category.title()}"
            category_tab_label = self.parent._create_tab_label(tab_label_text, category)
            
            # Add to notebook
            self.notebook.append_page(category_box, category_tab_label)
            self.notebook.show_all()
            
            # Register in dynamic tabs
            self.tabs_registry['dynamic'][category] = category_box
            
            # Store in parent's tracking
            self.parent.dynamic_categories[category] = {
                'scripts': scripts,
                'descriptions': descriptions,
                'box': category_box
            }
    
    def _get_category_emoji(self, category):
        """Get appropriate emoji for category name"""
        category_lower = category.lower()
        
        emoji_map = {
            'custom': '🎨',
            'network': '🌐',
            'security': '🔒',
            'database': '🗄️',
            'docker': '🐳',
            'web': '🌐',
            'development': '💻',
            'system': '⚙️',
            'backup': '💾',
            'media': '🎬',
            'gaming': '🎮',
            'automation': '🤖'
        }
        
        for key, emoji in emoji_map.items():
            if key in category_lower:
                return emoji
        
        return '📁'  # Default
    
    def refresh_all_tabs(self, repository, config):
        """
        Complete tab refresh - clear and rebuild all dynamic tabs.
        Called when repository configuration changes.
        """
        self.rebuild_dynamic_tabs(repository, config)


# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class ScriptMenuGTK(Gtk.ApplicationWindow):
    def __init__(self, app):
        global MANIFEST_URL
        # Use ApplicationWindow so GNOME/WM can associate the window with the Gtk.Application.
        Gtk.ApplicationWindow.__init__(self, application=app, title="LV Script Manager")
        
        # Initialize window state config
        self.config_dir = PathManager.get_config_dir() if PathManager else Path.home() / '.lv_linux_learn'
        self.ui_config_file = PathManager.get_ui_state_file() if PathManager else self.config_dir / 'ui_state.json'
        
        # Load saved window state or use defaults from constants
        window_state = self._load_window_state()
        default_width = C.DEFAULT_WINDOW_WIDTH if C else 996
        default_height = C.DEFAULT_WINDOW_HEIGHT if C else 950
        default_pane = C.DEFAULT_PANE_POSITION if C else 359
        
        self.set_default_size(
            window_state.get('width', default_width),
            window_state.get('height', default_height)
        )
        
        # Restore window position if saved
        if 'x' in window_state and 'y' in window_state:
            self.move(window_state['x'], window_state['y'])
        
        # Set minimum size to ensure usability (from constants)
        min_width = C.MIN_WINDOW_WIDTH if C else 800
        min_height = C.MIN_WINDOW_HEIGHT if C else 600
        border_width = C.WINDOW_BORDER_WIDTH if C else 12
        
        self.set_size_request(min_width, min_height)
        self.set_border_width(border_width)
        self.set_resizable(True)
        
        # Store pane position for later
        self.saved_pane_position = window_state.get('pane_position', default_pane)
        
        # Connect to window events for saving state
        self.connect("configure-event", self._on_window_configure)
        self.connect("delete-event", self._on_window_close)
        
        # Initialize custom script manager
        self.custom_script_manager = CustomScriptManager()
        
        # Initialize custom manifest creator
        self.custom_manifest_creator = None
        if CustomManifestCreator:
            try:
                self.custom_manifest_creator = CustomManifestCreator()
            except Exception as e:
                print(f"Warning: Failed to initialize custom manifest creator: {e}")
        
        # Initialize repository system
        self.repository = None
        self.repo_enabled = False
        self.repo_config = {}  # Initialize early to avoid AttributeError
        self._auto_refresh_timeout_id = None  # Store timeout ID to prevent garbage collection
        
        if ScriptRepository:
            try:
                self.repository = ScriptRepository()
                self.repo_config = self.repository.load_config() if self.repository else {}
                self.repo_enabled = True  # Repository system is always enabled
                
                # Load custom manifest URL if configured
                custom_url = self.repo_config.get('custom_manifest_url', '')
                if custom_url and (custom_url.startswith('http://') or custom_url.startswith('https://')):
                    os.environ['CUSTOM_MANIFEST_URL'] = custom_url
                    global MANIFEST_URL
                    MANIFEST_URL = custom_url
                    
                # Check for updates in background if enabled
                if self.repo_config.get('auto_check_updates', True):
                    GLib.idle_add(self._check_updates_background)
                # Schedule periodic manifest refresh to keep tabs in sync
                self._schedule_manifest_auto_refresh()
            except Exception as e:
                import traceback
                import sys
                print(f"Warning: Failed to initialize repository: {e}", file=sys.stderr, flush=True)
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                # Ensure attributes are set even on failure
                self.repository = None
                self.repo_enabled = False
        
        # CRITICAL: Reload scripts with repository configuration
        # This ensures custom manifest settings are properly loaded
        if self.repository:
            global _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT
            global SCRIPTS, SCRIPT_NAMES, DESCRIPTIONS, TOOLS_SCRIPTS, TOOLS_NAMES, TOOLS_DESCRIPTIONS
            global EXERCISES_SCRIPTS, EXERCISES_NAMES, EXERCISES_DESCRIPTIONS
            global UNINSTALL_SCRIPTS, UNINSTALL_NAMES, UNINSTALL_DESCRIPTIONS
            
            try:
                print("[*] Reloading scripts with repository configuration...", flush=True)
                # Reload with repository instance for proper cache status and custom manifests
                global _SCRIPT_ID_MAP
                _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, _SCRIPT_ID_MAP = load_scripts_from_manifest(repository=self.repository)
                
                print(f"[*] Loaded categories: {list(_SCRIPTS_DICT.keys())}", flush=True)
                print(f"[*] Install scripts: {len(_SCRIPTS_DICT.get('install', []))}")
                print(f"[*] Tools scripts: {len(_SCRIPTS_DICT.get('tools', []))}")
                print(f"[*] Exercises scripts: {len(_SCRIPTS_DICT.get('exercises', []))}")
                print(f"[*] Uninstall scripts: {len(_SCRIPTS_DICT.get('uninstall', []))}", flush=True)
                
                # Update global arrays with cache icons
                SCRIPTS[:] = _SCRIPTS_DICT.get('install', [])
                SCRIPT_NAMES[:] = _NAMES_DICT.get('install', [])
                DESCRIPTIONS[:] = _DESCRIPTIONS_DICT.get('install', [])
                
                TOOLS_SCRIPTS[:] = _SCRIPTS_DICT.get('tools', [])
                TOOLS_NAMES[:] = _NAMES_DICT.get('tools', [])
                TOOLS_DESCRIPTIONS[:] = _DESCRIPTIONS_DICT.get('tools', [])
                
                EXERCISES_SCRIPTS[:] = _SCRIPTS_DICT.get('exercises', [])
                EXERCISES_NAMES[:] = _NAMES_DICT.get('exercises', [])
                EXERCISES_DESCRIPTIONS[:] = _DESCRIPTIONS_DICT.get('exercises', [])
                
                UNINSTALL_SCRIPTS[:] = _SCRIPTS_DICT.get('uninstall', [])
                UNINSTALL_NAMES[:] = _NAMES_DICT.get('uninstall', [])
                UNINSTALL_DESCRIPTIONS[:] = _DESCRIPTIONS_DICT.get('uninstall', [])
                
                print(f"[✓] Scripts reloaded successfully")
            except Exception as e:
                print(f"[!] Error reloading scripts with repository: {e}")
                import traceback
                traceback.print_exc()

        # HeaderBar + integrated search (keeps GNOME decoration/behavior consistent)
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "LV Script Manager"
        self.set_titlebar(hb)
        
        # Create application menu bar
        menubar = self._create_menubar()
        hb.pack_start(menubar)
        # add a small search entry to the headerbar for quick filtering
        self.header_search = Gtk.SearchEntry()
        self.header_search.set_placeholder_text("Search scripts...")
        self.header_search.set_size_request(240, -1)
        hb.pack_end(self.header_search)

        # Main container - vertical split
        main_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.add(main_paned)

        # Top section - tabs
        top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        top_box.set_size_request(-1, 300)  # Minimum height to keep tabs visible

        # Create notebook (tabs)
        self.notebook = Gtk.Notebook()
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        self.notebook.set_scrollable(True)  # Enable scrollable tabs for small windows
        self.notebook.set_show_border(False)
        top_box.pack_start(self.notebook, True, True, 0)
        
        # Initialize centralized tab manager
        self.tab_manager = TabManager(self.notebook, self)
        
        # Initialize centralized UI refresh coordinator
        self.ui_refresh = UIRefreshCoordinator(self)

        # Create Install tab
        install_box = self._create_script_tab(SCRIPTS, DESCRIPTIONS, "install")
        install_tab_label = self._create_tab_label("📦 Install", "install")
        self.notebook.append_page(install_box, install_tab_label)
        self.tab_manager.register_standard_tab('install', self.install_treeview)

        # Create Tools tab
        tools_box = self._create_script_tab(TOOLS_SCRIPTS, TOOLS_DESCRIPTIONS, "tools")
        tools_tab_label = self._create_tab_label("🔧 Tools", "tools")
        self.notebook.append_page(tools_box, tools_tab_label)
        self.tab_manager.register_standard_tab('tools', self.tools_treeview)

        # Create Exercises tab
        exercises_box = self._create_script_tab(EXERCISES_SCRIPTS, EXERCISES_DESCRIPTIONS, "exercises")
        exercises_tab_label = self._create_tab_label("📚 Exercises", "exercises")
        self.notebook.append_page(exercises_box, exercises_tab_label)
        self.tab_manager.register_standard_tab('exercises', self.exercises_treeview)

        # Create Uninstall tab
        uninstall_box = self._create_script_tab(UNINSTALL_SCRIPTS, UNINSTALL_DESCRIPTIONS, "uninstall")
        uninstall_tab_label = self._create_tab_label("⚠️ Uninstall", "uninstall")
        self.notebook.append_page(uninstall_box, uninstall_tab_label)
        self.tab_manager.register_standard_tab('uninstall', self.uninstall_treeview)
        
        # Create dynamic category tabs using centralized TabManager
        if self.repository:
            config = self.repository.load_config()
            self.tab_manager.rebuild_dynamic_tabs(self.repository, config)
        
        # Create Repository tab (if enabled) - Online repos only using handler
        if self.repo_enabled and RepositoryTabHandler:
            try:
                self.repo_handler = RepositoryTabHandler(self)
                repository_box = self.repo_handler.create_tab()
                repository_label = Gtk.Label(label="🌐 Repository (Online)")
                self.notebook.append_page(repository_box, repository_label)
                if hasattr(self, 'repo_tree'):
                    self.tab_manager.register_repository_tab('repository_online', self.repo_tree)
            except Exception as e:
                print(f"Error creating repository tab handler: {e}")
        
        # Create Local Repositories tab - Direct execution, no cache using handler
        if self.repo_enabled and LocalRepositoryTabHandler:
            try:
                self.local_repo_handler = LocalRepositoryTabHandler(self)
                local_repo_box = self.local_repo_handler.create_tab()
                local_repo_label = Gtk.Label(label="💾 Repository (Local)")
                self.notebook.append_page(local_repo_box, local_repo_label)
                if hasattr(self, 'local_repo_tree'):
                    self.tab_manager.register_repository_tab('repository_local', self.local_repo_tree)
            except Exception as e:
                print(f"Error creating local repository tab handler: {e}")
        
        # Create Sources tab (formerly Custom Manifests) using handler
        if CustomManifestCreator and CustomManifestTabHandler:
            try:
                self.custom_manifest_handler = CustomManifestTabHandler(self)
                custom_manifest_box = self.custom_manifest_handler.create_tab()
                custom_manifest_label = Gtk.Label(label="🔗 Sources")
                self.notebook.append_page(custom_manifest_box, custom_manifest_label)
                if hasattr(self, 'custom_manifest_tree'):
                    self.tab_manager.register_repository_tab('sources', self.custom_manifest_tree)
            except Exception as e:
                print(f"Error creating custom manifest tab handler: {e}")

        # Add top section to paned widget (resize=False keeps user-set size, shrink=False maintains minimum)
        main_paned.pack1(top_box, resize=False, shrink=False)

        # Bottom section - embedded terminal
        terminal_frame = Gtk.Frame()
        terminal_frame.set_shadow_type(Gtk.ShadowType.IN)
        
        # Terminal header with controls
        terminal_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        terminal_header_box.set_margin_top(6)
        terminal_header_box.set_margin_bottom(6)
        terminal_header_box.set_margin_start(6)
        terminal_header_box.set_margin_end(6)
        
        terminal_label = Gtk.Label(label="<b>Terminal Output</b>")
        terminal_label.set_use_markup(True)
        terminal_header_box.pack_start(terminal_label, False, False, 0)
        
        # Add clear button
        clear_button = Gtk.Button(label="Clear")
        clear_button.connect("clicked", self.on_terminal_clear)
        terminal_header_box.pack_end(clear_button, False, False, 0)
        
        # Terminal widget
        terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        terminal_box.pack_start(terminal_header_box, False, False, 0)
        
        # Create VTE terminal
        self.terminal = Vte.Terminal()
        self.terminal.set_scroll_on_output(True)
        self.terminal.set_scroll_on_keystroke(True)
        scrollback_lines = C.TERMINAL_SCROLLBACK_LINES if C else 10000
        self.terminal.set_scrollback_lines(scrollback_lines)
        self.terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
        
        # Enable input methods for proper keyboard handling (including Ctrl+C)
        self.terminal.set_input_enabled(True)
        
        # Make terminal focusable and able to receive all keyboard input
        self.terminal.set_can_focus(True)
        
        # Set terminal colors (dark theme)
        fg_color = Gdk.RGBA()
        fg_color.parse("#EBEBEB")
        bg_color = Gdk.RGBA()
        bg_color.parse("#1E1E1E")
        self.terminal.set_color_foreground(fg_color)
        self.terminal.set_color_background(bg_color)
        
        # Enable right-click context menu
        self.terminal.connect("button-press-event", self.on_terminal_button_press)
        
        # Scrolled window for terminal
        terminal_scroll = Gtk.ScrolledWindow()
        terminal_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        terminal_scroll.add(self.terminal)
        terminal_box.pack_start(terminal_scroll, True, True, 0)
        
        # Initialize centralized script action handler (requires self.terminal to exist)
        self.script_actions = ScriptActionHandler(self)
        
        terminal_frame.add(terminal_box)
        
        # Add terminal section to paned widget (resize=True, shrink=True for flexibility)
        main_paned.pack2(terminal_frame, resize=True, shrink=True)
        
        # Store reference to main paned for state saving
        self.main_paned = main_paned
        
        # Set paned position from saved state
        main_paned.set_position(self.saved_pane_position)
        
        # Connect to pane position changes
        main_paned.connect("notify::position", self._on_pane_position_changed)

        # Track current tab
        self.current_tab = "install"
        self.notebook.connect("switch-page", self.on_tab_switched)

        # wire search -> both filters
        self.header_search.connect("search-changed", self.on_search_changed)

        # Initialize terminal with bash shell
        GLib.idle_add(self._init_terminal)

        # Check required packages on launch
        GLib.idle_add(self.check_required_packages)
    
    def _load_window_state(self):
        """Load saved window state from config file"""
        try:
            if self.ui_config_file.exists():
                with open(self.ui_config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load window state: {e}")
        return {}
    
    def _save_window_state(self, state):
        """Save window state to config file"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.ui_config_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save window state: {e}")
    
    def _on_window_configure(self, widget, event):
        """Handle window resize/move events"""
        # Save window size and position
        window_state = self._load_window_state()
        window_state['width'] = event.width
        window_state['height'] = event.height
        window_state['x'] = event.x
        window_state['y'] = event.y
        self._save_window_state(window_state)
        return False
    
    def _on_pane_position_changed(self, paned, param):
        """Handle pane position changes"""
        position = paned.get_position()
        window_state = self._load_window_state()
        window_state['pane_position'] = position
        self._save_window_state(window_state)
    
    def _on_window_close(self, widget, event):
        """Handle window close event to ensure final state is saved"""
        # Final save before closing
        window_state = self._load_window_state()
        width, height = self.get_size()
        x, y = self.get_position()
        
        window_state['width'] = width
        window_state['height'] = height
        window_state['x'] = x
        window_state['y'] = y
        window_state['pane_position'] = self.main_paned.get_position()
        
        self._save_window_state(window_state)
        return False  # Allow window to close normally

    def _get_all_repository_scripts(self):
        """
        Aggregate scripts from all repository sources - delegates to TabManager.
        Returns dict: {category: [(script_path, script_name, description), ...]}
        """
        # Delegate to centralized TabManager
        if hasattr(self, 'tab_manager') and self.repository:
            config = self.repository.load_config()
            return self.tab_manager.get_all_repository_scripts(self.repository, config)
        
        # Fallback if TabManager not initialized
        return {
            'install': [],
            'tools': [],
            'exercises': [],
            'uninstall': []
        }

    def _init_terminal(self):
        """Initialize the terminal with a bash shell"""
        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            os.getcwd(),
            ["/bin/bash"],
            None,
            GLib.SpawnFlags.DEFAULT,
            None,
            None
        )
        return False  # Remove idle handler

    # ========================================================================
    # CENTRALIZED SCRIPT HANDLING METHODS
    # ========================================================================
    
    def _is_script_cached(self, script_id: str = None, script_path: str = None, category: str = None) -> bool:
        """
        CENTRALIZED cache status checker - single source of truth for cache status.
        All cache checks should use this function.
        
        Args:
            script_id: Script ID from manifest (preferred)
            script_path: Script path (fallback)
            category: Script category (used with script_path)
        
        Returns:
            True if script is in cache, False otherwise
        """
        # Local custom repos should never use cache engine
        if script_path:
            try:
                local_candidate = script_path.replace('file://', '') if script_path.startswith('file://') else script_path
                path_obj = Path(local_candidate).resolve()
                custom_root = PathManager.get_custom_manifests_dir() if PathManager else Path.home() / '.lv_linux_learn' / 'custom_manifests'
                if custom_root in path_obj.parents:
                    return False
            except Exception:
                pass

        # Use is_script_cached function if available
        if is_script_cached:
            result = is_script_cached(self.repository, script_id, script_path, category)
            return result
        
        # Fallback implementation
        if not self.repository or not self.repository.script_cache_dir:
            return False
        
        # Method 1: Use script_id (most reliable)
        if script_id:
            cached_path = self.repository.get_cached_script_path(script_id)
            exists = cached_path and os.path.isfile(cached_path)
            if exists:
                return True
        
        # Method 2: Check if script_path IS a cache path
        if script_path and str(self.repository.script_cache_dir) in str(script_path):
            exists = os.path.isfile(script_path)
            return exists
        
        # Method 3: Construct cache path from script_path and category
        if script_path and category:
            if script_path.startswith(('http://', 'https://')):
                filename = script_path.rstrip('/').split('/')[-1]
            else:
                filename = os.path.basename(script_path)
            
            cache_path = self.repository.script_cache_dir / category / filename
            exists = cache_path.exists()
            if exists:
                return True
        
        return False
    
    def _build_script_metadata(self, script_path: str, category: str, script_name: str = "") -> dict[str, any]:
        """
        Build metadata for a script based on its source and properties.
        Sources are determined independently - not from global config state.
        
        Args:
            script_path: Full path to the script
            category: Script category (install, tools, etc.)
            script_name: Optional display name with source tag
        
        Returns dict with:
            - type: "local" | "cached" | "remote"
            - source_type: "custom_script" | "public_repo" | "custom_repo" | "custom_local"
            - source_name: Readable source identifier
            - source_url: Original download URL if applicable
            - file_exists: bool for local files
            - is_custom: bool if script is from CustomScriptManager
            - script_id: ID from manifest or custom script manager
        """
        global _SCRIPT_ID_MAP
        
        # Use build_script_metadata function if available
        if build_script_metadata:
            return build_script_metadata(
                script_path,
                category,
                script_name,
                self.repository,
                self.custom_script_manager if hasattr(self, 'custom_script_manager') else None,
                _SCRIPT_ID_MAP
            )
        
        # Fallback implementation
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
        if hasattr(self, 'custom_script_manager') and self.custom_script_manager:
            custom_scripts = self.custom_script_manager.get_scripts(category=category)
            for custom_script in custom_scripts:
                if custom_script.get('script_path') == script_path:
                    metadata["is_custom"] = True
                    metadata["script_id"] = custom_script.get('id', '')
                    metadata["source_type"] = "custom_script"
                    metadata["source_name"] = "Custom Script"
                    metadata["type"] = "local"
                    metadata["file_exists"] = os.path.isfile(script_path)
                    return metadata
        
        # Determine source from script_name tag (e.g., [Public Repository] or [Custom: name])
        source_type = "unknown"
        source_name = ""
        
        # Try to get script_id from global mapping (populated during manifest load)
        # This avoids expensive manifest re-parsing
        if (category, script_path) in _SCRIPT_ID_MAP:
            script_id_data = _SCRIPT_ID_MAP.get((category, script_path))
            if script_id_data:
                metadata["script_id"] = script_id_data[0]  # script_id
                # Also get source info from mapping
                mapping_source_name = script_id_data[1]  # source_name from manifest
                if mapping_source_name == "Public Repository":
                    source_type = "public_repo"
                    source_name = mapping_source_name
                else:
                    # Default to custom_repo, but will check script_name for [Local:] tag
                    source_type = "custom_repo"
                    source_name = mapping_source_name
        
        # Override with script_name tag if present (most authoritative)
        if script_name:
            if "[Public Repository]" in script_name:
                source_type = "public_repo"
                source_name = "Public Repository"
            elif "[Local:" in script_name:
                # Extract local manifest name
                start = script_name.find("[Local:")
                end = script_name.find("]", start)
                if end > start:
                    source_name = script_name[start+7:end].strip()
                    source_type = "custom_local"  # CRITICAL: Local repository
            elif "[Custom:" in script_name:
                # Extract custom manifest name
                start = script_name.find("[Custom:")
                end = script_name.find("]", start)
                if end > start:
                    source_name = script_name[start+8:end].strip()
                    source_type = "custom_repo"
        
        # CRITICAL: For scripts without explicit source, check if they're from the repository
        # If source_type is still unknown and script exists locally, assume it's from public repo
        if source_type == "unknown":
            # Check if script path looks like it's from the repository
            if not script_path.startswith('/') and not script_path.startswith('file://'):
                # Relative path - likely from public repository manifest
                source_type = "public_repo"
                source_name = "Public Repository"
            elif script_path.startswith('/home/') and '/lv_linux_learn/' in script_path:
                # Absolute path in the repository directory - public repo
                source_type = "public_repo"
                source_name = "Public Repository"
        
        # CRITICAL: Local scripts bypass cache entirely - check early
        if source_type == "custom_local":
            # This is a local custom script - handle as local file
            actual_path = script_path[7:] if script_path.startswith('file://') else script_path
            metadata["type"] = "local"
            metadata["file_exists"] = os.path.isfile(actual_path)
            metadata["source_url"] = f"file://{actual_path}"
            metadata["source_type"] = "custom_local"
            metadata["source_name"] = source_name
            return metadata
        
        # CRITICAL: Check cache using centralized cache checker (only for online repositories)
        is_cached = self._is_script_cached(script_id=metadata["script_id"], script_path=script_path, category=category)
        if is_cached:
            metadata["type"] = "cached"
            metadata["file_exists"] = True
            metadata["source_type"] = source_type if source_type != "unknown" else "public_repo"
            metadata["source_name"] = source_name if source_name else "Public Repository"
            
            # Get actual cached path for future use
            if metadata["script_id"]:
                cached_path = self.repository.get_cached_script_path(metadata["script_id"])
                if cached_path:
                    metadata["cached_path"] = str(cached_path)
            
            return metadata
        
        # CRITICAL: Public repo and custom online repo scripts must be cached - treat as remote if not cached
        if source_type in ("public_repo", "custom_repo"):
            metadata["type"] = "remote"
            metadata["source_type"] = source_type
            metadata["source_name"] = source_name if source_name else "Public Repository"
            return metadata
        
        # Now check if it's a local file (not in cache) - ONLY for custom_local and custom_script
        if script_path.startswith('/') or script_path.startswith('file://'):
            actual_path = script_path[7:] if script_path.startswith('file://') else script_path
            
            # Check if it's from a custom manifest directory
            if source_type == "unknown":
                custom_manifests_dir = PathManager.get_custom_manifests_dir() if PathManager else Path.home() / '.lv_linux_learn' / 'custom_manifests'
                if custom_manifests_dir in Path(actual_path).parents:
                    source_type = "custom_local"
                    # Try to extract manifest name from path
                    try:
                        relative = Path(actual_path).relative_to(custom_manifests_dir)
                        source_name = relative.parts[0] if relative.parts else "Custom Local"
                    except ValueError:
                        source_name = "Custom Local"
            
            # Only treat as local if it's actually from custom_local or custom_script sources
            if source_type in ("custom_local", "custom_script"):
                metadata["type"] = "local"
                metadata["file_exists"] = os.path.isfile(actual_path)
                metadata["source_url"] = f"file://{actual_path}"
                metadata["source_type"] = source_type
                metadata["source_name"] = source_name if source_name else "Local File"
                return metadata
        
        # Default to remote (not yet downloaded) - includes public_repo and custom_repo not yet cached
        metadata["type"] = "remote"
        metadata["source_type"] = source_type if source_type != "unknown" else "public_repo"
        metadata["source_name"] = source_name if source_name else "Public Repository"
        return metadata

    def _get_script_metadata(self, model, treeiter) -> dict:
        """Extract and parse metadata from liststore row"""
        try:
            # COL_METADATA = 5 (not 4 which is COL_IS_CUSTOM)
            COL_METADATA = C.COL_METADATA if C else 5
            COL_SCRIPT_ID = C.COL_SCRIPT_ID if C else 6
            
            metadata_json = model[treeiter][COL_METADATA]
            if metadata_json:
                metadata = json.loads(metadata_json)
                # Also include script_id from column 6 if not already in metadata
                if 'script_id' not in metadata or not metadata['script_id']:
                    script_id = model[treeiter][COL_SCRIPT_ID]
                    if script_id:
                        metadata['script_id'] = script_id
                return metadata
        except (IndexError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to parse script metadata: {e}")
        return {}

    def _has_custom_sources(self) -> bool:
        """Return True if any custom manifests/sources are configured."""
        # Prefer repository config when available
        try:
            if self.repository:
                if self.config_manager:
                    cfg = self.config_manager.get_config()
                else:
                    cfg = self.repository.load_config()
                if cfg.get('custom_manifest_url'):
                    return True
                if cfg.get('custom_manifests'):
                    return True
                if cfg.get('active_custom_manifest'):
                    return True
        except Exception:
            pass

        # Fallback: direct config file read
        try:
            cfg_file = PathManager.get_config_file() if PathManager else Path.home() / '.lv_linux_learn' / 'config.json'
            if cfg_file.exists():
                with open(cfg_file, 'r') as f:
                    cfg = json.load(f)
                if cfg.get('custom_manifest_url'):
                    return True
                if cfg.get('custom_manifests'):
                    return True
                if cfg.get('active_custom_manifest'):
                    return True
        except Exception:
            pass
        return False

    def _prompt_for_script_inputs(self, script_name: str, script_path: str) -> dict:
        """
        Prompt for required environment variables based on script name.
        Returns dict of environment variables to set, or None if user cancelled.
        
        Business logic delegated to ScriptEnvironment for testability.
        """
        # Use business logic module if available, otherwise fallback
        if ScriptEnvironment:
            env_requirements = ScriptEnvironment.get_required_vars(script_name)
        else:
            # Fallback: inline logic
            env_requirements = {}
            if 'vpn' in script_name.lower() or 'zerotier' in script_name.lower():
                env_requirements['ZEROTIER_NETWORK_ID'] = {
                    'required': True,
                    'prompt': 'Enter your ZeroTier Network ID',
                    'description': 'ZeroTier network identifier (16 hex characters)',
                    'help_url': 'https://my.zerotier.com/',
                    'example': '8bd5124fd60a971f'
                }
        
        if not env_requirements:
            return {}
        
        env_vars = {}
        
        # Process each required environment variable
        for var_name, requirements in env_requirements.items():
            # Check if already set in environment
            if ScriptEnvironment:
                if ScriptEnvironment.is_var_set(var_name):
                    continue
            else:
                if var_name in os.environ and os.environ[var_name]:
                    continue
            
            # Show GTK dialog to prompt for value
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text=f"{var_name} Required"
            )
            
            # Build secondary text with help information
            secondary_text = requirements.get('description', f"This script requires {var_name}.")
            if 'help_url' in requirements:
                secondary_text += f"\n\nFind your value at: {requirements['help_url']}"
            if 'example' in requirements:
                secondary_text += f"\nExample: {requirements['example']}"
            secondary_text += f"\n\n{requirements.get('prompt', 'Enter value:')}"
            
            dialog.format_secondary_text(secondary_text)
            
            # Add entry field
            content_area = dialog.get_content_area()
            entry = Gtk.Entry()
            entry.set_placeholder_text(requirements.get('example', ''))
            if var_name == 'ZEROTIER_NETWORK_ID':
                entry.set_max_length(16)
            content_area.pack_start(entry, False, False, 5)
            dialog.show_all()
            
            response = dialog.run()
            value = entry.get_text().strip()
            dialog.destroy()
            
            if response != Gtk.ResponseType.OK:
                return None  # User cancelled
            
            # Validate the input using business logic
            if ScriptEnvironment:
                is_valid, error_msg = ScriptEnvironment.validate_var(var_name, value)
            else:
                # Fallback validation
                if var_name == 'ZEROTIER_NETWORK_ID':
                    import re
                    is_valid = bool(re.match(r'^[0-9a-fA-F]{16}$', value))
                    error_msg = "Invalid Network ID format. Must be 16 hexadecimal characters."
                else:
                    is_valid = bool(value)
                    error_msg = f"{var_name} cannot be empty."
            
            if not is_valid:
                self.show_error_dialog(error_msg)
                return None  # Validation failed
            
            env_vars[var_name] = value
        
        return env_vars

    def _execute_script_unified(self, script_path: str, metadata: dict = None) -> bool:
        """
        Centralized script execution logic handling all manifest types.
        
        Business logic delegated to script_execution module for testability.
        
        Logic:
        - Local Custom (custom_local): Execute directly from original location
        - Online Public (public_repo cached): Execute from cache with includes
        - Online Custom (custom_repo cached): Execute from cache with includes
        - Remote (not cached): Prompt to download first
        """
        script_name = os.path.basename(script_path)
        
        # If no metadata, try to infer from path
        if not metadata:
            metadata = {"type": "remote" if not os.path.isfile(script_path) else "local"}
        
        # Check for required environment variables and prompt if needed
        env_vars = self._prompt_for_script_inputs(script_name, script_path)
        if env_vars is None:  # User cancelled
            self.terminal.feed(b"\x1b[33m[*] Script execution cancelled by user\x1b[0m\r\n")
            return False
        
        # Use business logic module if available
        if build_script_command:
            command, status = build_script_command(script_path, metadata, env_vars)
            
            if not command:
                # Not ready to execute - show status message
                self.terminal.feed(f"\x1b[33m[*] {status}\x1b[0m\r\n".encode())
                return False
            
            # Determine display message based on metadata
            script_type = metadata.get("type", "remote")
            source_type = metadata.get("source_type", "unknown")
            source_name = metadata.get("source_name", "Unknown Source")
            
            # Show appropriate execution message
            if script_type == "local" or source_type == "custom_local":
                self.terminal.feed(f"\x1b[33m[*] Executing Local Custom script: {script_name}\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[36m[*] Source: {source_name}\x1b[0m\r\n".encode())
            elif script_type == "cached":
                if source_type == "public_repo":
                    self.terminal.feed(f"\x1b[33m[*] Executing Online Public script: {script_name}\x1b[0m\r\n".encode())
                elif source_type == "custom_repo":
                    self.terminal.feed(f"\x1b[33m[*] Executing Online Custom script: {script_name}\x1b[0m\r\n".encode())
                    self.terminal.feed(f"\x1b[36m[*] Source: {source_name}\x1b[0m\r\n".encode())
                else:
                    self.terminal.feed(f"\x1b[33m[*] Executing cached script: {script_name}\x1b[0m\r\n".encode())
            
            # Show env var settings
            if env_vars:
                for key in env_vars.keys():
                    self.terminal.feed(f"\x1b[36m[*] Setting {key}\x1b[0m\r\n".encode())
            
            # Execute command in terminal
            self.terminal.feed_child(command.encode())
            return True
        
        # Fallback: inline implementation (original code)
        script_type = metadata.get("type", "remote")
        source_type = metadata.get("source_type", "unknown")
        source_name = metadata.get("source_name", "Unknown Source")
        
        # Build environment variable exports
        env_exports = ""
        if env_vars:
            for key, value in env_vars.items():
                env_exports += f"export {key}='{value}'; "
                self.terminal.feed(f"\x1b[36m[*] Setting {key}\x1b[0m\r\n".encode())
        
        # Handle local custom files - execute directly from original location (no caching)
        if script_type == "local" or source_type == "custom_local":
            file_path = script_path[7:] if script_path.startswith('file://') else script_path
            if os.path.isfile(file_path):
                abs_path = os.path.abspath(file_path)
                # Execute in subshell to prevent terminal blocking
                command = f"{env_exports}bash '{abs_path}'\n"
                self.terminal.feed(f"\x1b[33m[*] Executing Local Custom script: {script_name}\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[36m[*] Source: {source_name}\x1b[0m\r\n".encode())
                self.terminal.feed_child(command.encode())
                return True
            else:
                self.terminal.feed(f"\x1b[31m[!] Local file not found: {file_path}\x1b[0m\r\n".encode())
                return False
        
        # Handle cached files - execute from cache (Online Public or Online Custom)
        elif script_type == "cached":
            if os.path.isfile(script_path):
                self._ensure_includes_available()
                cache_root = PathManager.get_cache_dir() if PathManager else os.path.expanduser("~/.lv_linux_learn/script_cache")
                # Execute in subshell to prevent terminal blocking
                command = f"{env_exports}(cd '{cache_root}' && bash '{script_path}')\n"
                
                # Show appropriate message based on source
                if source_type == "public_repo":
                    self.terminal.feed(f"\x1b[33m[*] Executing Online Public script: {script_name}\x1b[0m\r\n".encode())
                elif source_type == "custom_repo":
                    self.terminal.feed(f"\x1b[33m[*] Executing Online Custom script: {script_name}\x1b[0m\r\n".encode())
                    self.terminal.feed(f"\x1b[36m[*] Source: {source_name}\x1b[0m\r\n".encode())
                else:
                    self.terminal.feed(f"\x1b[33m[*] Executing cached script: {script_name}\x1b[0m\r\n".encode())
                
                self.terminal.feed_child(command.encode())
                return True
            else:
                self.terminal.feed(f"\x1b[31m[!] Cached file not found: {script_path}\x1b[0m\r\n".encode())
                return False
        
        # Handle remote files - need to download first
        else:
            if source_type == "public_repo":
                self.terminal.feed(f"\x1b[33m[*] Online Public script not cached. Use Download button first.\x1b[0m\r\n".encode())
            elif source_type == "custom_repo":
                self.terminal.feed(f"\x1b[33m[*] Online Custom script not cached. Use Download button first.\x1b[0m\r\n".encode())
            else:
                self.terminal.feed(f"\x1b[33m[*] Script not cached. Use Download button first.\x1b[0m\r\n".encode())
            return False

    def _navigate_to_directory_unified(self, script_path: str, metadata: dict = None) -> bool:
        """
        Centralized directory navigation logic handling all manifest types.
        
        Logic:
        - Local Custom (custom_local): Navigate to original script location
        - Online Public (public_repo cached): Navigate to cache directory
        - Online Custom (custom_repo cached): Navigate to cache directory
        - Remote (not cached): Prompt to download first
        """
        script_name = os.path.basename(script_path)
        
        if not metadata:
            metadata = {"type": "remote" if not os.path.isfile(script_path) else "local"}
        
        script_type = metadata.get("type", "remote")
        source_type = metadata.get("source_type", "unknown")
        source_name = metadata.get("source_name", "Unknown Source")
        
        # Handle local custom files - cd to original location in terminal
        if script_type == "local" or source_type == "custom_local":
            file_path = script_path[7:] if script_path.startswith('file://') else script_path
            if os.path.isfile(file_path):
                directory = os.path.dirname(os.path.abspath(file_path))
                command = f"cd '{directory}' && pwd\n"
                self.terminal.feed(f"\x1b[33m[*] Navigating to Local Custom script directory\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[36m[*] Source: {source_name}\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[36m[*] Path: {directory}\x1b[0m\r\n".encode())
                self.terminal.feed_child(command.encode())
                GLib.timeout_add(1000, self._complete_directory_navigation)
                return True
            else:
                self.terminal.feed(f"\x1b[31m[!] Local file not found: {file_path}\x1b[0m\r\n".encode())
                return False
        
        # Handle cached files - cd to cache directory (Online Public or Online Custom)
        elif script_type == "cached":
            if os.path.isfile(script_path):
                directory = os.path.dirname(script_path)
                command = f"cd '{directory}' && pwd\n"
                
                # Show appropriate message based on source
                if source_type == "public_repo":
                    self.terminal.feed(f"\x1b[33m[*] Navigating to Online Public script cache\x1b[0m\r\n".encode())
                elif source_type == "custom_repo":
                    self.terminal.feed(f"\x1b[33m[*] Navigating to Online Custom script cache\x1b[0m\r\n".encode())
                    self.terminal.feed(f"\x1b[36m[*] Source: {source_name}\x1b[0m\r\n".encode())
                else:
                    self.terminal.feed(f"\x1b[33m[*] Navigating to cached script directory\x1b[0m\r\n".encode())
                
                self.terminal.feed(f"\x1b[36m[*] Cache: {directory}\x1b[0m\r\n".encode())
                self.terminal.feed_child(command.encode())
                GLib.timeout_add(1000, self._complete_directory_navigation)
                return True
            else:
                self.terminal.feed(f"\x1b[31m[!] Cached file not found: {script_path}\x1b[0m\r\n".encode())
                return False
        
        # Handle remote files - need to download first
        else:
            self.terminal.feed(f"\x1b[33m╔══════════════════════════════════════════════════╗\x1b[0m\r\n".encode())
            self.terminal.feed(f"\x1b[33m║  Script not cached: {script_name[:30]:<30} ║\x1b[0m\r\n".encode())
            self.terminal.feed(f"\x1b[33m╚══════════════════════════════════════════════════╝\x1b[0m\r\n".encode())
            
            if source_type == "public_repo":
                self.terminal.feed(b"\x1b[36m\r\nOnline Public script - Download required:\x1b[0m\r\n")
            elif source_type == "custom_repo":
                self.terminal.feed(f"\x1b[36m\r\nOnline Custom script ({source_name}) - Download required:\x1b[0m\r\n".encode())
            else:
                self.terminal.feed(b"\x1b[36m\r\nTo access the directory:\x1b[0m\r\n")
            
            self.terminal.feed(b"  1. Click the \xe2\x98\x81\xef\xb8\x8f Download button (or press Run to auto-download)\r\n")
            self.terminal.feed(b"  2. Once cached, the directory will be accessible\r\n\r\n")
            return False

    def _should_use_cache_engine(self, metadata: dict = None) -> bool:
        """
        Determine if cache engine should be used for this script based on source type.
        
        Each repository source operates independently:
        - public_repo: Always uses cache
        - custom_repo: Uses cache (online custom manifests)
        - custom_local: Direct execution (local file-based manifests)
        - custom_script: Direct execution (user-added scripts)
        
        Returns:
            True: Use cache engine (public_repo, custom_repo)
            False: Direct execution (custom_local, custom_script)
        """
        if should_use_cache_engine:
            return should_use_cache_engine(metadata)
        
        # Fallback implementation
        if not metadata:
            return True  # Default to using cache
        
        source_type = metadata.get("source_type", "public_repo")
        script_type = metadata.get("type", "remote")
        
        # Custom scripts from CustomScriptManager: direct execution
        if source_type == "custom_script":
            return False
        
        # Local files from custom_local manifests: direct execution
        if source_type == "custom_local" and script_type == "local":
            return False
        
        # Public repo and custom online repos: use cache
        # This allows both to coexist using the same cache infrastructure
        return True

    # ========================================================================
    # TAB CREATION & UI BUILDING
    # ========================================================================

    def _create_script_tab(self, scripts, descriptions, tab_name, names=None):
        """Create a tab with script list and description panel. Merges static scripts with repository scripts."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        main_box.set_border_width(12)

        # Get the appropriate names array
        if names is None:
            if tab_name == "install":
                names = SCRIPT_NAMES
            elif tab_name == "tools":
                names = TOOLS_NAMES
            elif tab_name == "exercises":
                names = EXERCISES_NAMES
            elif tab_name == "uninstall":
                names = UNINSTALL_NAMES
            else:
                # Fallback for any unexpected tab names
                names = []

        # store: icon, display name, full path, description, is_custom (bool), metadata (str as JSON), script_id
        # Use constants for column indices to prevent bugs
        # COL_ICON=0, COL_NAME=1, COL_PATH=2, COL_DESCRIPTION=3, COL_IS_CUSTOM=4, COL_METADATA=5, COL_SCRIPT_ID=6
        liststore = Gtk.ListStore(str, str, str, str, bool, str, str)


        
        # Add repository scripts (from online and local repositories)
        repo_scripts = self._get_all_repository_scripts()
        category_scripts = repo_scripts.get(tab_name, [])
        
        for script_path, display_name, description, metadata in category_scripts:
            script_id = metadata.get('script_id', '')
            source_type = metadata.get('source_type', '')
            
            # Determine icon based on source and cache status
            if source_type == 'local_repo':
                icon = "📁"  # Local repository icon
                # For local repos, the first element (script_path) is already the actual file path
                path_to_store = script_path
            else:
                # Online repository - check cache
                is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category=tab_name)
                icon = "✓" if is_cached else "☁️"
                
                # Default to provided path
                path_to_store = script_path
                
                # If cached, resolve to actual cached path
                if is_cached and self.repository:
                    cached_path = None
                    if script_id:
                        cached_path = self.repository.get_cached_script_path(script_id)
                    else:
                        # Fallback: resolve by category + filename when script_id is missing
                        filename = os.path.basename(script_path)
                        cached_path = self.repository.get_cached_script_path(category=tab_name, filename=filename)
                    if cached_path and os.path.exists(cached_path):
                        path_to_store = str(cached_path)
                        metadata["type"] = "cached"
                        metadata["file_exists"] = True
                        pass  # removed debug log
            
            liststore.append([icon, display_name, path_to_store, description, False, json.dumps(metadata), script_id])

        # filtered model driven by search entry
        filter_model = liststore.filter_new()
        filter_model.set_visible_func(self._filter_func, tab_name)

        # Store references for both tabs
        if tab_name == "install":
            self.install_liststore = liststore
            self.install_filter = filter_model
        elif tab_name == "tools":
            self.tools_liststore = liststore
            self.tools_filter = filter_model
        elif tab_name == "exercises":
            self.exercises_liststore = liststore
            self.exercises_filter = filter_model
        elif tab_name == "uninstall":
            self.uninstall_liststore = liststore
            self.uninstall_filter = filter_model
        else:
            # Dynamic category - store with category name
            setattr(self, f'{tab_name}_liststore', liststore)
            setattr(self, f'{tab_name}_filter', filter_model)

        treeview = Gtk.TreeView(model=filter_model)
        treeview.set_name("treeview")
        renderer = Gtk.CellRendererText()
        
        # Set column header based on tab type
        if tab_name == "install":
            column_header = "Available Installs"
        elif tab_name == "tools":
            column_header = "Available Tools"
        elif tab_name == "exercises":
            column_header = "Bash Exercises"
        elif tab_name == "uninstall":
            column_header = "Uninstall Options"
        else:
            column_header = "Scripts"
        
        # Create columns for icon and name (use constants)
        COL_ICON = C.COL_ICON if C else 0
        COL_NAME = C.COL_NAME if C else 1
        ICON_WIDTH = C.ICON_COLUMN_WIDTH if C else 30
        
        icon_column = Gtk.TreeViewColumn("", renderer, text=COL_ICON)
        icon_column.set_fixed_width(ICON_WIDTH)
        treeview.append_column(icon_column)
        
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn(column_header, name_renderer, text=COL_NAME)
        treeview.append_column(name_column)
        treeview.set_activate_on_single_click(False)
        treeview.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        # double-click/enter to run
        treeview.connect("row-activated", self.on_row_activated)
        # selection changed handler
        treeview.get_selection().connect("changed", self.on_selection_changed)
        # right-click menu for custom scripts
        treeview.connect("button-press-event", self.on_treeview_button_press)

        # Store treeview reference
        if tab_name == "install":
            self.install_treeview = treeview
        elif tab_name == "tools":
            self.tools_treeview = treeview
        elif tab_name == "exercises":
            self.exercises_treeview = treeview
        elif tab_name == "uninstall":
            self.uninstall_treeview = treeview
        else:
            # Dynamic category - store with category name
            setattr(self, f'{tab_name}_treeview', treeview)

        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        scroll.set_min_content_width(200)
        scroll.set_max_content_width(400)
        scroll.set_name("scroll")
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(treeview)
        main_box.pack_start(scroll, False, True, 0)

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.pack_start(right_box, True, True, 0)

        # Description area
        description_label = Gtk.Label()
        description_label.set_line_wrap(True)
        description_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        description_label.set_max_width_chars(80)
        description_label.set_name("desc_label")
        description_label.set_xalign(0)
        description_label.set_yalign(0)
        description_label.set_use_markup(True)
        description_label.set_selectable(True)
        description_label.connect("activate-link", self.on_link_clicked)
        description_label.set_text("Select a script to see description.")
        description_label.set_margin_top(6)
        description_label.set_margin_bottom(6)
        description_label.set_margin_start(6)
        description_label.set_margin_end(6)

        # Store label reference
        if tab_name == "install":
            self.install_description_label = description_label
        elif tab_name == "tools":
            self.tools_description_label = description_label
        elif tab_name == "exercises":
            self.exercises_description_label = description_label
        elif tab_name == "uninstall":
            self.uninstall_description_label = description_label
        else:
            # Dynamic category - store with category name
            setattr(self, f'{tab_name}_description_label', description_label)

        desc_scroll = Gtk.ScrolledWindow()
        desc_scroll.set_vexpand(True)
        desc_scroll.set_hexpand(True)
        desc_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        desc_scroll.add(description_label)
        right_box.pack_start(desc_scroll, True, True, 0)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_homogeneous(False)  # Allow buttons to size naturally
        right_box.pack_end(button_box, False, False, 0)

        view_button = Gtk.Button(label="View Script")
        view_button.set_sensitive(False)
        view_button.connect("clicked", self.on_view_clicked)
        button_box.pack_start(view_button, True, True, 0)

        cd_button = Gtk.Button(label="Go to Directory")
        cd_button.set_sensitive(False)
        cd_button.connect("clicked", self.on_cd_clicked)
        button_box.pack_start(cd_button, True, True, 0)

        run_button = Gtk.Button(label="Run Script in Terminal")
        run_button.set_sensitive(False)
        run_button.get_style_context().add_class("suggested-action")
        run_button.connect("clicked", self.on_run_clicked)
        button_box.pack_start(run_button, True, True, 0)

        # Store button references
        if tab_name == "install":
            self.install_view_button = view_button
            self.install_cd_button = cd_button
            self.install_run_button = run_button
        elif tab_name == "tools":
            self.tools_view_button = view_button
            self.tools_cd_button = cd_button
            self.tools_run_button = run_button
        elif tab_name == "exercises":
            self.exercises_view_button = view_button
            self.exercises_cd_button = cd_button
            self.exercises_run_button = run_button
        elif tab_name == "uninstall":
            self.uninstall_view_button = view_button
            self.uninstall_cd_button = cd_button
            self.uninstall_run_button = run_button
        else:
            # Dynamic category - store with category name
            setattr(self, f'{tab_name}_view_button', view_button)
            setattr(self, f'{tab_name}_cd_button', cd_button)
            setattr(self, f'{tab_name}_run_button', run_button)

        return main_box

    def on_tab_switched(self, notebook, page, page_num):
        """Handle tab switching (including dynamic categories from all repository types)"""
        if page_num == 0:
            self.current_tab = "install"
            treeview = self.install_treeview
        elif page_num == 1:
            self.current_tab = "tools"
            treeview = self.tools_treeview
        elif page_num == 2:
            self.current_tab = "exercises"
            treeview = self.exercises_treeview
        elif page_num == 3:
            self.current_tab = "uninstall"
            treeview = self.uninstall_treeview
        else:
            # Check if this is a dynamic category tab
            page = notebook.get_nth_page(page_num)
            tab_label = notebook.get_tab_label(page)
            if tab_label:
                label_text = tab_label.get_text()
                # Extract category name (remove emoji and convert to lowercase)
                import re
                category = re.sub(r'^[^\w\s]+\s*', '', label_text).strip().lower()
                
                # Check if widgets exist for this category
                if hasattr(self, f'{category}_treeview'):
                    self.current_tab = category
                    treeview = getattr(self, f'{category}_treeview')
                else:
                    # Other tabs (Repository, Sources, etc.) - no script filtering needed
                    return
            else:
                return
        
        # Reapply search filter
        self.on_search_changed(self.header_search)
        
        # Auto-select first item if nothing is selected
        selection = treeview.get_selection()
        if selection and selection.count_selected_rows() == 0:
            model = treeview.get_model()
            if model and len(model) > 0:
                # Select first row
                selection.select_path(Gtk.TreePath.new_first())
                # Trigger the selection changed event
                self.on_selection_changed(selection)

    def get_current_widgets(self):
        """Get widgets for current tab"""
        if self.current_tab == "install":
            return {
                'treeview': self.install_treeview,
                'description_label': self.install_description_label,
                'run_button': self.install_run_button,
                'view_button': self.install_view_button,
                'cd_button': self.install_cd_button,
                'filter': self.install_filter,
                'scripts': SCRIPTS,
                'descriptions': DESCRIPTIONS
            }
        elif self.current_tab == "tools":
            return {
                'treeview': self.tools_treeview,
                'description_label': self.tools_description_label,
                'run_button': self.tools_run_button,
                'view_button': self.tools_view_button,
                'cd_button': self.tools_cd_button,
                'filter': self.tools_filter,
                'scripts': TOOLS_SCRIPTS,
                'descriptions': TOOLS_DESCRIPTIONS
            }
        elif self.current_tab == "exercises":
            return {
                'treeview': self.exercises_treeview,
                'description_label': self.exercises_description_label,
                'run_button': self.exercises_run_button,
                'view_button': self.exercises_view_button,
                'cd_button': self.exercises_cd_button,
                'filter': self.exercises_filter,
                'scripts': EXERCISES_SCRIPTS,
                'descriptions': EXERCISES_DESCRIPTIONS
            }
        elif self.current_tab == "uninstall":
            return {
                'treeview': self.uninstall_treeview,
                'description_label': self.uninstall_description_label,
                'run_button': self.uninstall_run_button,
                'view_button': self.uninstall_view_button,
                'cd_button': self.uninstall_cd_button,
                'filter': self.uninstall_filter,
                'scripts': UNINSTALL_SCRIPTS,
                'descriptions': UNINSTALL_DESCRIPTIONS
            }
        else:
            # Check for dynamic category tabs (stored with setattr)
            if hasattr(self, f'{self.current_tab}_treeview'):
                # Get dynamic category data if available
                category_data = self.dynamic_categories.get(self.current_tab, {}) if hasattr(self, 'dynamic_categories') else {}
                return {
                    'treeview': getattr(self, f'{self.current_tab}_treeview', None),
                    'description_label': getattr(self, f'{self.current_tab}_description_label', None),
                    'run_button': getattr(self, f'{self.current_tab}_run_button', None),
                    'view_button': getattr(self, f'{self.current_tab}_view_button', None),
                    'cd_button': getattr(self, f'{self.current_tab}_cd_button', None),
                    'filter': getattr(self, f'{self.current_tab}_filter', None),
                    'scripts': category_data.get('scripts', []),
                    'descriptions': category_data.get('descriptions', [])
                }
            # Fallback for any unexpected tab
            return {
                'treeview': None,
                'description_label': None,
                'run_button': None,
                'view_button': None,
                'cd_button': None,
                'filter': None,
                'scripts': [],
                'descriptions': []
            }

    def _create_tab_label(self, label_text, category):
        """Create a tab label"""
        label = Gtk.Label(label=label_text)
        return label
    
    def _clear_dynamic_tabs(self):
        """Remove all dynamically created category tabs - delegates to TabManager"""
        if hasattr(self, 'tab_manager'):
            self.tab_manager.clear_dynamic_tabs()
    
    def _create_dynamic_category_tabs(self):
        """Create tabs for any non-standard categories - delegates to TabManager"""
        if not hasattr(self, 'repository') or not self.repository:
            return
        
        # Use centralized TabManager for all tab operations
        if hasattr(self, 'tab_manager'):
            config = self.repository.load_config()
            self.tab_manager.rebuild_dynamic_tabs(self.repository, config)
            return
        
        # Legacy fallback (should not be reached with TabManager initialized)
        return
        
        if not dynamic_categories:
            return  # No dynamic categories to create
        
        # Initialize dynamic category tracking (fresh after clear)
        self.dynamic_categories = {}
        self.dynamic_filters = {}
        self.dynamic_widgets = {}
        
        # Create a tab for each dynamic category
        for category in sorted(dynamic_categories):
            category_scripts = repo_scripts.get(category, [])
            
            if not category_scripts:
                continue  # Skip empty categories
            
            # Extract script data for this category
            scripts = [s[0] for s in category_scripts]  # paths
            descriptions = [s[2] for s in category_scripts]  # descriptions
            
            # Create the tab - this also creates and stores widget references
            category_box = self._create_script_tab(scripts, descriptions, category)
            
            # Create tab label with emoji based on category name
            emoji = self._get_category_emoji(category)
            tab_label_text = f"{emoji} {category.title()}"
            category_tab_label = self._create_tab_label(tab_label_text, category)
            
            # Add tab to notebook
            self.notebook.append_page(category_box, category_tab_label)
            
            # Show the new tab
            self.notebook.show_all()
            
            # Store reference to dynamic category
            self.dynamic_categories[category] = {
                'scripts': scripts,
                'descriptions': descriptions,
                'box': category_box
            }
    
    def _get_category_emoji(self, category):
        """Get an appropriate emoji for a category name"""
        category_lower = category.lower()
        
        # Map common category types to emojis
        emoji_map = {
            'custom': '🎨',
            'network': '🌐',
            'security': '🔒',
            'database': '🗄️',
            'docker': '🐳',
            'web': '🌐',
            'development': '💻',
            'system': '⚙️',
            'backup': '💾',
            'media': '🎬',
            'gaming': '🎮',
            'automation': '🤖'
        }
        
        # Check if category matches any known types
        for key, emoji in emoji_map.items():
            if key in category_lower:
                return emoji
        
        # Default emoji for unknown categories
        return '📁'



    # ========================================================================
    # PACKAGE MANAGEMENT
    # ========================================================================

    def check_required_packages(self):
        """Check for required packages and prompt to install if missing"""
        missing = []
        for pkg in REQUIRED_PACKAGES:
            if not self.command_exists(pkg):
                missing.append(pkg)
        
        if missing:
            self.show_install_prompt(missing)
        else:
            # Check optional packages and inform user
            missing_optional = []
            for i, cmd in enumerate(OPTIONAL_COMMANDS):
                if not self.command_exists(cmd):
                    missing_optional.append(OPTIONAL_PACKAGES[i])
            
            if missing_optional:
                self.show_optional_packages_info(missing_optional)
        
        return False  # remove idle handler after run once

    def _filter_func(self, model, iter, tab_name):
        if not hasattr(self, 'filter_text'):
            self.filter_text = ""
        if not self.filter_text:
            return True
        
        if tab_name == "repository":
            # For repository tab: search in script name (column 2) and category (column 5)
            name = model[iter][2].lower()  # Script name column
            category = model[iter][5].lower()  # Category column
            return self.filter_text in name or self.filter_text in category
        elif tab_name == "local_repositories":
            # For local repository tab: search in script name (column 2), category (column 5), and repository (column 6)
            name = model[iter][2].lower()  # Script name column
            category = model[iter][5].lower()  # Category column
            repository = model[iter][6].lower()  # Repository column
            return self.filter_text in name or self.filter_text in category or self.filter_text in repository
        else:
            # For main tabs: search in display name (column 0) and path (column 1)
            name = model[iter][0].lower()
            path = model[iter][1].lower()
            return self.filter_text in name or self.filter_text in path

    def on_search_changed(self, entry):
        self.filter_text = entry.get_text().strip().lower()
        self.install_filter.refilter()
        self.tools_filter.refilter()
        self.exercises_filter.refilter()
        self.uninstall_filter.refilter()
        # Filter repository tabs if they exist
        if hasattr(self, 'repo_filter'):
            self.repo_filter.refilter()
        if hasattr(self, 'local_repo_filter'):
            self.local_repo_filter.refilter()
        # Filter dynamic category tabs
        if hasattr(self, 'dynamic_categories'):
            for category in self.dynamic_categories.keys():
                filter_attr = f'{category}_filter'
                if hasattr(self, filter_attr):
                    getattr(self, filter_attr).refilter()
        # Filter dynamic category tabs
        if hasattr(self, 'dynamic_categories'):
            for category in self.dynamic_categories.keys():
                filter_attr = f'{category}_filter'
                if hasattr(self, filter_attr):
                    getattr(self, filter_attr).refilter()
        # Filter dynamic category tabs
        if hasattr(self, 'dynamic_filters'):
            for filter_model in self.dynamic_filters.values():
                filter_model.refilter()

    def command_exists(self, cmd):
        from shutil import which
        return which(cmd) is not None

    def show_install_prompt(self, missing_pkgs):
        """Prompt user to install missing required packages"""
        if UI and UI.show_install_prompt_dialog(self, missing_pkgs, "required"):
            self.install_packages_in_terminal(missing_pkgs, required=True)
        else:
            # User declined install, warn and exit
            if UI:
                UI.show_error_dialog(self, "Cannot continue without required packages. Exiting.")
            Gtk.main_quit()
            sys.exit(1)
    
    def show_optional_packages_info(self, missing_optional):
        """Inform user about missing optional packages"""
        if UI and UI.show_install_prompt_dialog(self, missing_optional, "optional"):
            self.install_packages_in_terminal(missing_optional, required=False)

    # ========================================================================
    # REPOSITORY TAB & MANAGEMENT
    # ========================================================================
    
    def _create_repository_tab(self):
        """Create the repository management tab"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        
        # Control buttons in a single row with logical grouping
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Selection group
        select_all_btn = Gtk.Button(label="Select All")
        select_all_btn.connect("clicked", self._on_select_all)
        button_box.pack_start(select_all_btn, False, False, 0)
        
        select_none_btn = Gtk.Button(label="Select None")
        select_none_btn.connect("clicked", self._on_select_none)
        button_box.pack_start(select_none_btn, False, False, 0)
        
        invert_selection_btn = Gtk.Button(label="Invert")
        invert_selection_btn.connect("clicked", self._on_invert_selection)
        button_box.pack_start(invert_selection_btn, False, False, 0)
        
        # Download/Remove selected
        install_selected_btn = Gtk.Button(label="Download Selected")
        install_selected_btn.get_style_context().add_class("suggested-action")
        install_selected_btn.connect("clicked", self._on_download_selected)
        button_box.pack_start(install_selected_btn, False, False, 0)
        
        remove_selected_btn = Gtk.Button(label="Remove Selected")
        remove_selected_btn.get_style_context().add_class("destructive-action")
        remove_selected_btn.connect("clicked", self._on_remove_selected)
        button_box.pack_start(remove_selected_btn, False, False, 0)
        
        # Bulk operations
        update_all_btn = Gtk.Button(label="Check Updates")
        update_all_btn.connect("clicked", self._on_check_updates)
        button_box.pack_start(update_all_btn, False, False, 0)
        
        download_all_btn = Gtk.Button(label="Download All")
        download_all_btn.connect("clicked", self._on_download_all)
        button_box.pack_start(download_all_btn, False, False, 0)
        
        clear_cache_btn = Gtk.Button(label="Remove All")
        clear_cache_btn.connect("clicked", self._on_clear_cache)
        button_box.pack_start(clear_cache_btn, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        # Scripts list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Store: selected(bool), id(str), name(str), version(str), status(str), category(str), size(str), modified(str), source(str)
        self.repo_store = Gtk.ListStore(bool, str, str, str, str, str, str, str, str)
        
        # Create filter model for repository search
        self.repo_filter = self.repo_store.filter_new()
        self.repo_filter.set_visible_func(self._filter_func, "repository")
        
        self.repo_tree = Gtk.TreeView(model=self.repo_filter)
        
        # Checkbox column
        checkbox_renderer = Gtk.CellRendererToggle()
        checkbox_renderer.set_property("activatable", True)
        checkbox_renderer.connect("toggled", self._on_script_toggled)
        checkbox_column = Gtk.TreeViewColumn("", checkbox_renderer, active=0)
        checkbox_column.set_fixed_width(30)
        self.repo_tree.append_column(checkbox_column)
        
        # Script name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Script Name", name_renderer, text=2)
        name_column.set_resizable(True)
        name_column.set_min_width(200)
        self.repo_tree.append_column(name_column)
        
        # Category column
        cat_renderer = Gtk.CellRendererText()
        cat_column = Gtk.TreeViewColumn("Category", cat_renderer, text=5)
        cat_column.set_resizable(True)
        cat_column.set_min_width(80)
        self.repo_tree.append_column(cat_column)
        
        # Source column
        source_renderer = Gtk.CellRendererText()
        source_column = Gtk.TreeViewColumn("Source", source_renderer, text=8)
        source_column.set_resizable(True)
        source_column.set_min_width(100)
        self.repo_tree.append_column(source_column)
        
        # Version column
        ver_renderer = Gtk.CellRendererText()
        ver_column = Gtk.TreeViewColumn("Version", ver_renderer, text=3)
        ver_column.set_min_width(60)
        self.repo_tree.append_column(ver_column)
        
        # Status column
        status_renderer = Gtk.CellRendererText()
        status_column = Gtk.TreeViewColumn("Cache Status", status_renderer, text=4)
        status_column.set_min_width(100)
        self.repo_tree.append_column(status_column)
        
        # Size column
        size_renderer = Gtk.CellRendererText()
        size_column = Gtk.TreeViewColumn("Size", size_renderer, text=6)
        size_column.set_min_width(60)
        self.repo_tree.append_column(size_column)
        
        # Last Modified column
        modified_renderer = Gtk.CellRendererText()
        modified_column = Gtk.TreeViewColumn("Modified", modified_renderer, text=7)
        modified_column.set_min_width(100)
        self.repo_tree.append_column(modified_column)
        
        scrolled.add(self.repo_tree)
        vbox.pack_start(scrolled, True, True, 0)
        
        # Populate tree
        self._populate_repository_tree()
        
        return vbox
    
    def _populate_repository_tree(self):
        """Populate repository tree view with enhanced information"""
        print("[DEBUG] _populate_repository_tree() called")
        if not self.repository:
            print("[DEBUG] No repository, returning")
            return
        
        print("[DEBUG] Clearing repo_store")
        self.repo_store.clear()
        
        try:
            # Check which manifest sources to use
            config = self.repository.load_config()
            use_public_repo = config.get('use_public_repository', True)
            custom_manifest_url = config.get('custom_manifest_url', '')
            
            # If public repo is enabled but manifest doesn't exist, download it
            if use_public_repo:
                if not self.repository.manifest_file.exists():
                    if hasattr(self, 'terminal'):
                        self.terminal.feed(b"\x1b[36m[*] Downloading public repository manifest for first time...\x1b[0m\r\n")
                    try:
                        self.repository.check_for_updates()
                    except Exception as e:
                        if hasattr(self, 'terminal'):
                            self.terminal.feed(f"\x1b[31m[!] Failed to download manifest: {e}\x1b[0m\r\n".encode())
            
            # Determine which scripts to display - can be multiple sources
            all_scripts = []
            script_ids_seen = set()  # Track to avoid duplicates
            
            # Track which sources have checksum verification disabled
            # Key: source_name, Value: verify_checksums boolean
            manifest_verify_settings = {}
            
            # Get list of custom manifests from Custom Manifests tab system
            custom_manifests_to_load = []
            
            # 1a. Check for custom_manifest_url in config (legacy/direct URL configuration)
            if custom_manifest_url and custom_manifest_url.startswith(('http://', 'https://')):
                # Get custom manifest name from config, with fallback
                custom_name = config.get('custom_manifest_name', 'Custom Repository')
                custom_manifests_to_load.append(('custom_manifest_url', custom_manifest_url, custom_name))
            
            # 1b. Check for manifests in config['custom_manifests'] (new system)
            custom_manifests_from_config = config.get('custom_manifests', {})
            if hasattr(self, 'terminal'):
                self.terminal.feed(f"\x1b[36m[DEBUG] Found {len(custom_manifests_from_config)} custom manifests in config\x1b[0m\r\n".encode())
            
            for manifest_name, manifest_config in custom_manifests_from_config.items():
                if hasattr(self, 'terminal'):
                    self.terminal.feed(f"\x1b[36m[DEBUG] Processing manifest: {manifest_name}\x1b[0m\r\n".encode())
                # Skip if manifest_data is not present (shouldn't happen, but safe check)
                if 'manifest_data' not in manifest_config:
                    if hasattr(self, 'terminal'):
                        self.terminal.feed(f"\x1b[33m[DEBUG] Skipping {manifest_name} - no manifest_data\x1b[0m\r\n".encode())
                    continue
                # Add all custom manifests, including local file:// ones (they should show in Repository tab)
                custom_manifests_to_load.append((manifest_name, manifest_name, manifest_name))
                if hasattr(self, 'terminal'):
                    self.terminal.feed(f"\x1b[36m[*] Found custom manifest from config: {manifest_name}\x1b[0m\r\n".encode())
            
            # 1c. Check for manifests created through Custom Manifests tab
            if hasattr(self, 'custom_manifest_creator') and self.custom_manifest_creator:
                try:
                    # Load manifest metadata file
                    manifests_dir = PathManager.get_custom_manifests_dir() if PathManager else Path.home() / '.lv_linux_learn' / 'custom_manifests'
                    if manifests_dir.exists():
                        for manifest_file in manifests_dir.glob('*.json'):
                            try:
                                if FileLoader:
                                    manifest_data = FileLoader.load_json(manifest_file, default={})
                                else:
                                    import json
                                    with open(manifest_file) as f:
                                        manifest_data = json.load(f)
                                
                                # Get repository URL from manifest
                                repo_url = manifest_data.get('repository_url')
                                # Only add online repositories (http/https), skip local ones (they appear in Repository (Local) tab)
                                if repo_url and repo_url.startswith(('http://', 'https://')):
                                    manifest_name = manifest_file.stem.replace('_', ' ').title()
                                    # Store the local file path for this manifest
                                    custom_manifests_to_load.append((manifest_file.stem, str(manifest_file), manifest_name))
                                    if hasattr(self, 'terminal'):
                                        self.terminal.feed(f"\x1b[36m[*] Found custom online manifest: {manifest_name} ({repo_url})\x1b[0m\r\n".encode())
                            except Exception as e:
                                if hasattr(self, 'terminal'):
                                    self.terminal.feed(f"\x1b[33m[!] Could not load manifest {manifest_file.name}: {e}\x1b[0m\r\n".encode())
                except Exception as e:
                    if hasattr(self, 'terminal'):
                        self.terminal.feed(f"\x1b[33m[!] Error scanning custom manifests: {e}\x1b[0m\r\n".encode())
            
            # Load all custom manifests
            for manifest_id, manifest_path, custom_manifest_name in custom_manifests_to_load:
                import json
                
                if hasattr(self, 'terminal'):
                    self.terminal.feed(f"\x1b[36m[DEBUG] Loading manifest: {custom_manifest_name} (id={manifest_id}, path={manifest_path})\x1b[0m\r\n".encode())
                
                custom_scripts = []
                try:
                    # Try to load from config first (new system)
                    custom_manifest = None
                    if custom_manifest_name in config.get('custom_manifests', {}):
                        custom_manifest = config['custom_manifests'][custom_manifest_name].get('manifest_data')
                        if hasattr(self, 'terminal'):
                            self.terminal.feed(f"\x1b[36m[DEBUG] Loaded manifest_data from config for {custom_manifest_name}\x1b[0m\r\n".encode())
                    
                    # Fall back to loading from file (old system)
                    if not custom_manifest and Path(manifest_path).exists():
                        with open(manifest_path, 'r') as f:
                            custom_manifest = json.load(f)
                        if hasattr(self, 'terminal'):
                            self.terminal.feed(f"\x1b[36m[DEBUG] Loaded manifest from file: {manifest_path}\x1b[0m\r\n".encode())
                    
                    if not custom_manifest:
                        if hasattr(self, 'terminal'):
                            self.terminal.feed(f"\x1b[33m[!] Could not load manifest: {custom_manifest_name}\x1b[0m\r\n".encode())
                        continue
                    
                    # Track checksum verification setting for this manifest
                    verify_checksums = config.get('custom_manifests', {}).get(custom_manifest_name, {}).get('verify_checksums', True)
                    manifest_verify_settings[custom_manifest_name] = verify_checksums
                    
                    if hasattr(self, 'terminal'):
                        self.terminal.feed(f"\x1b[36m[*] Loaded custom manifest: {custom_manifest_name}\x1b[0m\r\n".encode())
                        if not verify_checksums:
                            self.terminal.feed(f"\x1b[33m[*] Note: Checksum verification disabled for '{custom_manifest_name}'\x1b[0m\r\n".encode())
                    
                    if custom_manifest:
                        # Handle both flat and nested script structures
                        manifest_scripts = custom_manifest.get('scripts', [])
                        
                        if hasattr(self, 'terminal'):
                            self.terminal.feed(f"\x1b[36m[DEBUG] Manifest scripts type: {type(manifest_scripts)}, count: {len(manifest_scripts) if isinstance(manifest_scripts, (list, dict)) else 'N/A'}\x1b[0m\r\n".encode())
                        
                        if isinstance(manifest_scripts, dict):
                            # Nested structure (by category)
                            for category, category_scripts in manifest_scripts.items():
                                if isinstance(category_scripts, list):
                                    if hasattr(self, 'terminal'):
                                        self.terminal.feed(f"\x1b[36m[DEBUG] Processing {len(category_scripts)} scripts from category '{category}'\x1b[0m\r\n".encode())
                                    for script in category_scripts:
                                        script['category'] = category
                                        script['_source'] = 'custom'
                                        script['_source_name'] = custom_manifest_name
                                        custom_scripts.append(script)
                        else:
                            # Flat structure (list of scripts)
                            for script in manifest_scripts:
                                script['_source'] = 'custom'
                                script['_source_name'] = custom_manifest_name
                                custom_scripts.append(script)
                        
                        # Add custom scripts and track IDs
                        for script in custom_scripts:
                            script_id = script.get('id')
                            if script_id:
                                if script_id not in script_ids_seen:
                                    all_scripts.append(script)
                                    script_ids_seen.add(script_id)
                                else:
                                    if hasattr(self, 'terminal'):
                                        self.terminal.feed(f"\x1b[33m[!] Skipping duplicate script ID: {script_id}\x1b[0m\r\n".encode())
                            else:
                                if hasattr(self, 'terminal'):
                                    self.terminal.feed(f"\x1b[33m[!] Script missing ID: {script.get('name', 'unknown')}\x1b[0m\r\n".encode())
                        
                except Exception as e:
                    if hasattr(self, 'terminal'):
                        self.terminal.feed(f"\x1b[31m[!] Could not load custom manifest: {e}\x1b[0m\r\n".encode())
                        import traceback
                        error_details = traceback.format_exc()
                        self.terminal.feed(f"\x1b[31m{error_details}\x1b[0m\r\n".encode())
            
            # 2. Load public repository scripts if enabled
            if use_public_repo:
                try:
                    # Track public repo verify_checksums setting
                    public_manifest = self.repository.load_local_manifest()
                    if public_manifest:
                        manifest_verify_settings['Public Repository'] = public_manifest.get('verify_checksums', True)
                    
                    public_scripts = self.repository.parse_manifest()
                    for script in public_scripts:
                        script['_source'] = 'public'
                        script['_source_name'] = 'Public Repository'
                        script_id = script.get('id')
                        if script_id and script_id not in script_ids_seen:
                            all_scripts.append(script)
                            script_ids_seen.add(script_id)
                except Exception as e:
                    if hasattr(self, 'terminal'):
                        self.terminal.feed(f"\x1b[33m[!] Could not load public repository: {e}\x1b[0m\r\n".encode())
            
            # If no scripts from any source, return silently (empty state)
            if not all_scripts:
                if hasattr(self, 'terminal'):
                    self.terminal.feed(f"\x1b[33m[!] No scripts loaded from any source\x1b[0m\r\n".encode())
                    self.terminal.feed(f"\x1b[33m[!] Public repo enabled: {use_public_repo}\x1b[0m\r\n".encode())
                    self.terminal.feed(f"\x1b[33m[!] Custom manifests to load: {len(custom_manifests_to_load)}\x1b[0m\r\n".encode())
                return
            
            # Process all scripts from all sources (exclude local repositories - they have their own tab)
            for script in all_scripts:
                script_id = script.get('id')
                name = script.get('name')
                version = script.get('version', '1.0')
                category = script.get('category', 'tools')
                file_name = script.get('file_name', '')
                source = script.get('_source', 'unknown')
                source_name = script.get('_source_name', 'Unknown Source')
                source_type = script.get('source_type', '')
                
                # Note: Local repositories appear in BOTH Local Repositories tab AND interaction tabs
                # The Local Repositories tab is for management, interaction tabs show ALL scripts
                # Only skip if the script has an invalid path or is marked for exclusion
                # if source_type == 'custom_local' or (source == 'custom' and not script.get('download_url', '').startswith(('http://', 'https://'))):
                #     continue
                
                # If file_name is missing, try to extract from download_url
                if not file_name:
                    download_url = script.get('download_url', '')
                    if download_url:
                        file_name = download_url.split('/')[-1]
                
                # Build cached path directly for all manifest types
                if file_name:
                    cached_path = self.repository.script_cache_dir / category / file_name
                else:
                    cached_path = None
                
                # Determine cache status
                if cached_path and cached_path.exists():
                    # Check if this manifest has checksum verification enabled
                    manifest_has_verification = manifest_verify_settings.get(source_name, True)
                    
                    # Check if checksums match (if available AND verification is enabled)
                    remote_checksum = script.get('checksum', '').replace('sha256:', '')
                    if remote_checksum and manifest_has_verification:
                        import hashlib
                        try:
                            with open(cached_path, 'rb') as f:
                                local_checksum = hashlib.sha256(f.read()).hexdigest()
                            if local_checksum == remote_checksum:
                                status_text = '✓ Cached'
                            else:
                                # Only show update available if checksums actually differ
                                status_text = '📥 Update Available'
                        except Exception as e:
                            # If checksum check fails, assume cached is OK
                            # This prevents false "Update Available" messages
                            status_text = '✓ Cached'
                    else:
                        # No checksum available OR verification disabled, just mark as cached
                        status_text = '✓ Cached'
                else:
                    status_text = '☁️ Not Cached'
                
                # Get cached file info if available
                if cached_path and cached_path.exists():
                    import os
                    from datetime import datetime
                    try:
                        stat_info = os.stat(cached_path)
                        size_kb = round(stat_info.st_size / 1024, 1)
                        size_text = f"{size_kb} KB"
                        modified_time = datetime.fromtimestamp(stat_info.st_mtime)
                        modified_text = modified_time.strftime("%Y-%m-%d %H:%M")
                    except:
                        size_text = "-"
                        modified_text = "-"
                else:
                    # Get size from manifest if available
                    size = script.get('size', 0)
                    size_text = f"{round(size/1024, 1)} KB" if size > 0 else "-"
                    modified_text = "-"
                
                # Add to store: [selected, id, name, version, status, category, size, modified, source]
                self.repo_store.append([
                    False,  # checkbox not selected by default
                    script_id, 
                    name, 
                    version, 
                    status_text, 
                    category.capitalize(),
                    size_text,
                    modified_text,
                    source_name  # Use actual source name
                ])
            
            # Display summary in terminal
            custom_count = sum(1 for s in all_scripts if s.get('_source') == 'custom')
            public_count = sum(1 for s in all_scripts if s.get('_source') == 'public')
            cached_count = sum(1 for row in self.repo_store if '✓ Cached' in row[4])
            total_count = len(self.repo_store)
            
            status_parts = []
            if custom_count > 0:
                status_parts.append(f"Custom online manifest ({custom_count} scripts)")
            if public_count > 0:
                status_parts.append(f"Public repository ({public_count} scripts)")
            
            # Status tracking (summary available but not displayed to terminal during refresh)
                
        except Exception as e:
            print(f"Error populating repository tree: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_local_repository_tab(self):
        """Create the local repository management tab (direct execution, no cache)"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        
        # Check Ollama availability first (needed for buttons and banner)
        try:
            from lib.ai_categorizer import check_ollama_available
            self.ollama_available = check_ollama_available()
        except ImportError:
            self.ollama_available = False
        
        # Control buttons at the top - in a single row with logical grouping
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Selection group
        select_all_btn = Gtk.Button(label="Select All")
        select_all_btn.connect("clicked", self._on_local_select_all)
        button_box.pack_start(select_all_btn, False, False, 0)
        
        select_none_btn = Gtk.Button(label="Select None")
        select_none_btn.connect("clicked", self._on_local_select_none)
        button_box.pack_start(select_none_btn, False, False, 0)
        
        # Delete button for removing scripts from local repositories
        delete_btn = Gtk.Button(label="Delete Selected")
        delete_btn.get_style_context().add_class("destructive-action")
        delete_btn.connect("clicked", self._on_delete_selected_local_scripts)
        button_box.pack_start(delete_btn, False, False, 0)
        
        # AI Analyze button
        if self.ollama_available:
            analyze_btn = Gtk.Button(label="AI Analyze Selected")
            analyze_btn.get_style_context().add_class("suggested-action")
            analyze_btn.connect("clicked", self._on_ai_analyze_scripts)
            button_box.pack_start(analyze_btn, False, False, 0)
        
        # Refresh operations
        refresh_btn = Gtk.Button(label="Refresh List")
        refresh_btn.connect("clicked", self._on_refresh_local_repos)
        button_box.pack_start(refresh_btn, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        # AI Analysis banner (ollama_available already set above)
        ai_banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ai_banner.set_margin_bottom(5)
        ai_banner.set_margin_top(5)
        
        if self.ollama_available:
            ai_icon = Gtk.Label(label="🤖")
            ai_banner.pack_start(ai_icon, False, False, 0)
            
            ai_label = Gtk.Label()
            ai_label.set_markup("<span color='#2ecc71'><b>AI Analysis Available:</b> Ollama is ready for script categorization</span>")
            ai_label.set_xalign(0)
            ai_banner.pack_start(ai_label, True, True, 0)
        else:
            ai_icon = Gtk.Label(label="⚠️")
            ai_banner.pack_start(ai_icon, False, False, 0)
            
            ai_label = Gtk.Label()
            ai_label.set_markup("<span color='#e67e22'><b>AI Analysis Unavailable:</b> Install Ollama for automatic script categorization</span>")
            ai_label.set_xalign(0)
            ai_banner.pack_start(ai_label, True, True, 0)
            
            install_ollama_btn = Gtk.Button(label="📥 Install Ollama")
            install_ollama_btn.connect("clicked", self._on_install_ollama)
            ai_banner.pack_end(install_ollama_btn, False, False, 0)
        
        vbox.pack_start(ai_banner, False, False, 0)
        
        # Scripts list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Store: selected(bool), id(str), name(str), version(str), path(str), category(str), source(str), size(str)
        self.local_repo_store = Gtk.ListStore(bool, str, str, str, str, str, str, str)
        
        # Create filter model for local repository search
        self.local_repo_filter = self.local_repo_store.filter_new()
        self.local_repo_filter.set_visible_func(self._filter_func, "local_repositories")
        
        self.local_repo_tree = Gtk.TreeView(model=self.local_repo_filter)
        
        # Checkbox column
        checkbox_renderer = Gtk.CellRendererToggle()
        checkbox_renderer.set_property("activatable", True)
        checkbox_renderer.connect("toggled", self._on_local_script_toggled)
        checkbox_column = Gtk.TreeViewColumn("", checkbox_renderer, active=0)
        checkbox_column.set_fixed_width(30)
        self.local_repo_tree.append_column(checkbox_column)
        
        # Script name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Script Name", name_renderer, text=2)
        name_column.set_resizable(True)
        name_column.set_min_width(200)
        self.local_repo_tree.append_column(name_column)
        
        # Category column
        cat_renderer = Gtk.CellRendererText()
        cat_column = Gtk.TreeViewColumn("Category", cat_renderer, text=5)
        cat_column.set_resizable(True)
        cat_column.set_min_width(80)
        self.local_repo_tree.append_column(cat_column)
        
        # Source column
        source_renderer = Gtk.CellRendererText()
        source_column = Gtk.TreeViewColumn("Repository", source_renderer, text=6)
        source_column.set_resizable(True)
        source_column.set_min_width(150)
        self.local_repo_tree.append_column(source_column)
        
        # Version column
        ver_renderer = Gtk.CellRendererText()
        ver_column = Gtk.TreeViewColumn("Version", ver_renderer, text=3)
        ver_column.set_min_width(60)
        self.local_repo_tree.append_column(ver_column)
        
        # Path column
        path_renderer = Gtk.CellRendererText()
        path_column = Gtk.TreeViewColumn("Local Path", path_renderer, text=4)
        path_column.set_resizable(True)
        path_column.set_min_width(200)
        self.local_repo_tree.append_column(path_column)
        
        # Size column
        size_renderer = Gtk.CellRendererText()
        size_column = Gtk.TreeViewColumn("Size", size_renderer, text=7)
        size_column.set_min_width(60)
        self.local_repo_tree.append_column(size_column)
        
        scrolled.add(self.local_repo_tree)
        vbox.pack_start(scrolled, True, True, 0)
        
        # Populate tree
        self._populate_local_repository_tree()
        
        return vbox
    
    def _populate_local_repository_tree(self):
        """Populate local repository tree view (scripts from file-based manifests)"""
        if not self.repository:
            return
        
        self.local_repo_store.clear()
        
        try:
            local_scripts = []
            
            if hasattr(self, 'terminal'):
                self.terminal.feed(b"\x1b[36m[*] Scanning for local repositories...\x1b[0m\r\n")
            
            # Track script IDs to avoid duplicates between Method 1 and Method 2
            script_ids_seen = set()
            
            # Method 1: Check config.json for local repository (legacy/direct configuration)
            config = self.repository.load_config()
            custom_manifest_url = config.get('custom_manifest_url', '')
            custom_manifests_config = config.get('custom_manifests', {})
            use_public_repo = config.get('use_public_repository', True)
            
            # CRITICAL: If we're using public repository with no custom manifests, exit early
            if use_public_repo and not custom_manifests_config:
                if hasattr(self, 'terminal'):
                    self.terminal.feed(b"\x1b[36m[i] No local repositories configured (using public repository)\x1b[0m\r\n")
                return
            
            if custom_manifest_url and custom_manifest_url.startswith('file://'):
                # This is a file:// URL, but it might point to metadata for an ONLINE repository
                # We need to check the actual manifest to see if it's truly local
                manifest_path = custom_manifest_url.replace('file://', '').strip()
                manifest_name = config.get('custom_manifest_name', 'Local Repository')
                
                try:
                    manifest_file = Path(manifest_path)
                    if manifest_file.exists():
                        with open(manifest_file) as f:
                            manifest_data = json.load(f)
                        
                        # Check if the repository_url inside the manifest is online or local
                        repository_url = manifest_data.get('repository_url', '')
                        
                        # If the repository_url is http/https, this is an ONLINE custom repo
                        # It should NOT appear on the Repository (Local) tab
                        if repository_url.startswith(('http://', 'https://')):
                            if hasattr(self, 'terminal'):
                                self.terminal.feed(f"\x1b[36m[*] Skipping {manifest_name} (online repository, not local)\x1b[0m\r\n".encode())
                        else:
                            # This is truly a local file-based repository
                            if hasattr(self, 'terminal'):
                                self.terminal.feed(f"\x1b[32m[*] Found local repository in config: {manifest_name}\x1b[0m\r\n".encode())
                                self.terminal.feed(f"\x1b[36m[*] Manifest path: {manifest_path}\x1b[0m\r\n".encode())
                            
                            # Get repository base path (parent directory of manifest.json)
                            base_path = str(manifest_file.parent)
                            
                            # Process scripts from manifest
                            scripts = manifest_data.get('scripts', [])
                            
                            # Handle both flat and nested structures
                            if isinstance(scripts, dict):
                                # Nested by category
                                for category, category_scripts in scripts.items():
                                    if isinstance(category_scripts, list):
                                        for script in category_scripts:
                                            script_id = script.get('id', '')
                                            if script_id and script_id not in script_ids_seen:
                                                script['_category'] = category
                                                script['_manifest_name'] = manifest_name
                                                script['_manifest_type'] = 'local'
                                                script['_base_path'] = base_path
                                                local_scripts.append(script)
                                                script_ids_seen.add(script_id)
                            else:
                                # Flat list
                                for script in scripts:
                                    script_id = script.get('id', '')
                                    if script_id and script_id not in script_ids_seen:
                                        script['_manifest_name'] = manifest_name
                                        script['_manifest_type'] = 'local'
                                        script['_base_path'] = base_path
                                        local_scripts.append(script)
                                        script_ids_seen.add(script_id)
                    else:
                        if hasattr(self, 'terminal'):
                            self.terminal.feed(f"\x1b[33m[!] Manifest file not found: {manifest_path}\x1b[0m\r\n".encode())
                except Exception as e:
                    if hasattr(self, 'terminal'):
                        self.terminal.feed(f"\x1b[31m[!] Error loading manifest from config: {e}\x1b[0m\r\n".encode())
            
            # Method 2: Scan custom_manifests directory for all local file-based repositories
            custom_manifests_dir = PathManager.get_custom_manifests_dir() if PathManager else Path.home() / '.lv_linux_learn' / 'custom_manifests'
            
            # Only scan directory if it exists AND we have custom manifests configured
            # Check if use_public_repository is False or if we have explicit custom manifest entries
            use_public_repo = config.get('use_public_repository', True)
            has_custom_manifests = bool(custom_manifests_config) and len(custom_manifests_config) > 0
            
            if custom_manifests_dir.exists() and has_custom_manifests:
                # Look for both subdirectory manifests and flat JSON files
                manifest_files = list(custom_manifests_dir.glob('*/manifest.json')) + list(custom_manifests_dir.glob('*_manifest.json'))
                
                for manifest_file in manifest_files:
                    try:
                        with open(manifest_file) as f:
                            manifest_data = json.load(f)
                        
                        # Check the repository_url to determine if this is truly local
                        repository_url = manifest_data.get('repository_url', '')
                        manifest_name = manifest_file.parent.name.replace('_', ' ').title()
                        
                        # CRITICAL: Skip online repositories (http/https URLs)
                        # These should appear in Repository (Online) tab, not here
                        if repository_url.startswith(('http://', 'https://')):
                            if hasattr(self, 'terminal') and DEBUG_CACHE:
                                self.terminal.feed(f"\x1b[36m[DEBUG] Skipping online repository: {manifest_name}\x1b[0m\r\n".encode())
                            continue
                        
                        # CRITICAL: Also skip if repository_url is empty but manifest is in cache
                        # This catches the public repository manifest cached locally
                        if not repository_url or repository_url == '':
                            # Check if this is actually the public repository manifest
                            manifest_version = manifest_data.get('version', '')
                            if 'github.com/amatson97/lv_linux_learn' in str(manifest_data.get('repository_url', '')):
                                if hasattr(self, 'terminal') and DEBUG_CACHE:
                                    self.terminal.feed(f"\x1b[36m[DEBUG] Skipping public repo manifest: {manifest_file.name}\x1b[0m\r\n".encode())
                                continue
                        
                        # This is a local file-based repository
                        base_path = str(manifest_file.parent) if manifest_file.name == 'manifest.json' else str(manifest_file.parent / manifest_name.lower().replace(' ', '_'))
                        
                        # Process scripts from manifest
                        scripts = manifest_data.get('scripts', [])
                        
                        # Handle both flat and nested structures
                        if isinstance(scripts, dict):
                            # Nested by category
                            for category, category_scripts in scripts.items():
                                if isinstance(category_scripts, list):
                                    for script in category_scripts:
                                        script_id = script.get('id', '')
                                        if script_id and script_id not in script_ids_seen:
                                            script['_category'] = category
                                            script['_manifest_name'] = manifest_name
                                            script['_manifest_type'] = 'local'
                                            script['_base_path'] = base_path
                                            local_scripts.append(script)
                                            script_ids_seen.add(script_id)
                        else:
                            # Flat list
                            for script in scripts:
                                script_id = script.get('id', '')
                                if script_id and script_id not in script_ids_seen:
                                    script['_manifest_name'] = manifest_name
                                    script['_manifest_type'] = 'local'
                                    script['_base_path'] = base_path
                                    local_scripts.append(script)
                                    script_ids_seen.add(script_id)
                    
                    except Exception as e:
                        if hasattr(self, 'terminal'):
                            self.terminal.feed(f"\x1b[33m[!] Error loading {manifest_file.name}: {e}\x1b[0m\r\n".encode())
            
            if not local_scripts:
                if hasattr(self, 'terminal'):
                    self.terminal.feed(b"\x1b[33m[!] No scripts found in local repositories\x1b[0m\r\n")
                    self.terminal.feed(b"\x1b[36m[i] Make sure your local repository has a valid manifest.json\x1b[0m\r\n")
                return
            
            # Add scripts to tree
            for script in local_scripts:
                script_id = script.get('id', '')
                name = script.get('name', 'Unknown')
                version = script.get('version', '1.0')
                category = script.get('_category', script.get('category', 'tools'))
                manifest_name = script.get('_manifest_name', 'Unknown')
                base_path = script.get('_base_path', '')
                
                # Build full local path
                # Try multiple methods to get the script path
                full_path = None
                
                # Method 1: Check for download_url (file:// URL)
                download_url = script.get('download_url', '')
                if download_url and download_url.startswith('file://'):
                    full_path = download_url.replace('file://', '')
                
                # Method 2: Use file_name + base_path + category
                if not full_path:
                    file_name = script.get('file_name', '')
                    if file_name:
                        # If the manifest stored an absolute path, use it directly
                        if os.path.isabs(file_name):
                            full_path = file_name
                        elif base_path:
                            full_path = str(Path(base_path) / category / file_name)
                
                # Method 3: Try just file_name as relative path from base_path
                if not full_path:
                    file_name = script.get('file_name', '')
                    if file_name and base_path:
                        full_path = str(Path(base_path) / file_name)
                
                if full_path:
                    # Check if file exists and get size
                    try:
                        path_obj = Path(full_path)
                        if path_obj.exists():
                            stat_info = path_obj.stat()
                            size_kb = round(stat_info.st_size / 1024, 1)
                            size_text = f"{size_kb} KB"
                        else:
                            size_text = "Missing"
                            full_path = f"{full_path} (NOT FOUND)"
                    except Exception as e:
                        size_text = "Error"
                        if hasattr(self, 'terminal'):
                            self.terminal.feed(f"\x1b[33m[!] Error checking path for {name}: {e}\x1b[0m\r\n".encode())
                else:
                    full_path = "Path not available"
                    size_text = "-"
                
                # Add to store: [selected, id, name, version, path, category, source, size]
                self.local_repo_store.append([
                    False,
                    script_id,
                    name,
                    version,
                    full_path,
                    category.capitalize(),
                    manifest_name,
                    size_text
                ])
            
            # Track summary (scripts loaded from file-based manifests)
            total_count = len(self.local_repo_store)
                
        except Exception as e:
            print(f"Error populating local repository tree: {e}")
            import traceback
            traceback.print_exc()
    
    def _check_updates_background(self):
        """Check for updates in background"""
        if not self.repository or not self.repo_enabled:
            return False
        
        if self.repository.is_update_check_needed():
            try:
                update_count = self.repository.check_for_updates()
                if update_count > 0:
                    self._update_repo_status()
                    if hasattr(self, 'repo_tree'):
                        self._populate_repository_tree()
            except Exception as e:
                print(f"Background update check failed: {e}")
        
        return False
    
    def _on_update_all_scripts(self, button):
        """Update all cached scripts"""
        if not self.repository:
            return
        
        self.terminal.feed(b"\r\n\x1b[32m[*] Updating all cached scripts...\x1b[0m\r\n")
        
        try:
            # Refresh manifest with terminal output (returns 4 values)
            global _SCRIPT_ID_MAP
            _, _, _, _SCRIPT_ID_MAP = load_scripts_from_manifest(terminal_widget=self.terminal)
            
            updated, failed = self.repository.update_all_scripts()
            self.terminal.feed(f"\x1b[32m[*] Update complete: {updated} updated, {failed} failed\x1b[0m\r\n".encode())
            
            # Auto-complete with reduced delay
            if TimerManager:
                TimerManager.schedule_ui_refresh(self._complete_terminal_operation)
            else:
                GLib.timeout_add(500, self._complete_terminal_operation)
            
            # Refresh display
            self._update_repo_status()
            self._populate_repository_tree()
            
            # Reload main tabs to reflect changes
            self._reload_main_tabs()
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            GLib.timeout_add(1500, self._complete_terminal_operation)
    
    def _on_check_updates(self, button):
        """Manually check for updates"""
        if not self.repository:
            return
        
        self.terminal.feed(b"\r\n\x1b[32m[*] Checking for updates...\x1b[0m\r\n")
        
        try:
            # Clear repository's internal cache to force fresh check
            if hasattr(self.repository, '_manifest_cache'):
                self.repository._manifest_cache = None
            if hasattr(self.repository, '_scripts'):
                self.repository._scripts = None
            print("[DEBUG] Cleared repository cache for fresh update check", flush=True)
            
            update_count = self.repository.check_for_updates()
            self.terminal.feed(f"\x1b[32m[*] Found {update_count} updates available\x1b[0m\r\n".encode())
            
            # Auto-complete after short delay
            if TimerManager:
                TimerManager.schedule_ui_refresh(self._check_updates_complete_callback)
            else:
                GLib.timeout_add(500, self._check_updates_complete_callback)
            
            # Refresh display with fresh data
            self._update_repo_status()
            self._populate_repository_tree()
            print("[DEBUG] Repository tree refreshed after check", flush=True)
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            if TimerManager:
                TimerManager.schedule_completion(self._complete_terminal_operation)
            else:
                GLib.timeout_add(1500, self._complete_terminal_operation)
    
    def _complete_terminal_operation(self):
        """Auto-complete terminal operation"""
        # Send newline to complete the current command and return to prompt
        self.terminal.feed_child(b"\n")
        # Return False to stop the timeout from repeating
        return False
    
    def _complete_terminal_silent(self):
        """Silently complete terminal operation without message - just return to prompt"""
        # Send newline to complete the current command and return to prompt
        self.terminal.feed_child(b"\n")
        # Return False to stop the timeout from repeating
        return False
        return False
    
    def _complete_directory_navigation(self):
        """Complete directory navigation silently (pwd output confirms success)"""
        # Just send newline to complete the command - no additional message needed
        # since pwd already confirms successful navigation
        self.terminal.feed_child(b"\n")
        # Return False to stop the timeout from repeating
        return False
    
    def _on_download_all(self, button):
        """Download all scripts from repository (only those currently shown in Repository tab)"""
        if not self.repository:
            return
        
        # Get count of scripts in the repo_store (respects current filtering)
        total = len(self.repo_store)
        
        if total == 0:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="No Scripts Available"
            )
            dialog.format_secondary_text(
                "No scripts are currently available to download.\n\n"
                "Please configure a manifest source:\n"
                "• Enable Public Repository in settings, or\n"
                "• Add a Custom Manifest in the Sources tab"
            )
            dialog.run()
            dialog.destroy()
            return
        
        # Confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Download All Scripts"
        )
        dialog.format_secondary_text(
            f"This will download all {total} scripts shown in the Repository tab.\n\n"
            "This may take a few minutes. Continue?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        self.terminal.feed(f"\r\n\x1b[32m[*] Downloading {total} scripts from configured sources...\x1b[0m\r\n".encode())
        
        # Download each script from the repo_store
        downloaded = 0
        failed = 0
        
        try:
            for row in self.repo_store:
                script_id = row[1]
                script_name = row[2]
                category = row[5].lower()
                
                try:
                    # Download the script
                    self.terminal.feed(f"\x1b[36m[*] Downloading {script_name}...\x1b[0m\r\n".encode())
                    # Process pending GTK events to show terminal output immediately
                    while Gtk.events_pending():
                        Gtk.main_iteration()
                    
                    result = self.repository.download_script(script_id)
                    success = result[0] if isinstance(result, tuple) else bool(result)
                    
                    if success:
                        downloaded += 1
                        # Derive cache path for display
                        script_info = self.repository.get_script_by_id(script_id)
                        file_name = script_info.get('file_name', '') if script_info else ''
                        category_name = script_info.get('category', category) if script_info else category
                        cache_path = os.path.join(str(self.repository.script_cache_dir), category_name, file_name)
                        self.terminal.feed(f"\x1b[32m  ✓ Cached to {cache_path}\x1b[0m\r\n".encode())
                    else:
                        failed += 1
                        self.terminal.feed(f"\x1b[33m  ! Failed to download\x1b[0m\r\n".encode())
                    
                    # Process pending GTK events after download
                    while Gtk.events_pending():
                        Gtk.main_iteration()
                        
                except Exception as e:
                    failed += 1
                    self.terminal.feed(f"\x1b[31m  ✗ Error: {e}\x1b[0m\r\n".encode())
                    # Process pending GTK events for error output
                    while Gtk.events_pending():
                        Gtk.main_iteration()
            
            self.terminal.feed(f"\x1b[32m[*] Download complete: {downloaded} downloaded, {failed} failed\x1b[0m\r\n".encode())
            
            # Auto-complete with reduced delay
            if TimerManager:
                TimerManager.schedule_ui_refresh(self._complete_terminal_operation)
            else:
                GLib.timeout_add(500, self._complete_terminal_operation)
            
            # Refresh display
            self._populate_repository_tree()
            
            # Reload main tabs to reflect changes
            self._reload_main_tabs()
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            import traceback
            self.terminal.feed(f"\x1b[31m{traceback.format_exc()}\x1b[0m\r\n".encode())
            if TimerManager:
                TimerManager.schedule_completion(self._complete_terminal_operation)
            else:
                GLib.timeout_add(1500, self._complete_terminal_operation)
    
    def _on_clear_cache(self, button):
        """Clear script cache"""
        if not self.repository:
            return
        
        # Confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Remove All Scripts"
        )
        
        dialog.format_secondary_text(
            "This will remove all scripts from the cache.\n\n"
            "You can download them again later. Continue?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        try:
            # Clear script cache
            self.repository.clear_cache()
            self.terminal.feed(b"\r\n\x1b[32m[*] Script cache cleared successfully\x1b[0m\r\n")
            
            # Also clear manifest cache files (stale cached manifests)
            self.terminal.feed(b"\x1b[36m[*] Cleaning up manifest cache files...\x1b[0m\r\n")
            try:
                cache_dir = Path.home() / '.lv_linux_learn'
                removed_count = 0
                for cache_file in cache_dir.glob('manifest_*.json'):
                    cache_file.unlink(missing_ok=True)
                    removed_count += 1
                for cache_file in cache_dir.glob('temp_*_manifest.json'):
                    cache_file.unlink(missing_ok=True)
                    removed_count += 1
                if removed_count > 0:
                    self.terminal.feed(f"\x1b[32m[*] Removed {removed_count} cached manifest file(s)\x1b[0m\r\n".encode())
            except Exception as e:
                self.terminal.feed(f"\x1b[33m[!] Manifest cache cleanup warning: {e}\x1b[0m\r\n".encode())
            
            # Auto-complete with reduced delay
            GLib.timeout_add(500, self._complete_terminal_operation)
            
            # Refresh display
            self._update_repo_status()
            self._populate_repository_tree()
            
            # Reload main tabs to reflect changes
            self._reload_main_tabs()
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            GLib.timeout_add(1500, self._complete_terminal_operation)
    
    def _on_repo_settings(self, button):
        """Show repository settings dialog"""
        global MANIFEST_URL
        # Initialize repository if not already done
        if not self.repository:
            try:
                self.repository = ScriptRepository()
                if ConfigManager:
                    try:                        self.repo_config = self.repository.load_config()
                    except Exception as cm_error:
                        print(f"Warning: ConfigManager initialization failed: {cm_error}")
                        self.repo_config = self.repository.load_config()
                else:
                    self.repo_config = self.repository.load_config()
            except Exception as e:
                # Show error dialog if repository can't be initialized
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Repository Error"
                )
                error_dialog.format_secondary_text(f"Failed to initialize repository system:\n{e}")
                error_dialog.run()
                error_dialog.destroy()
                return
        
        dialog = Gtk.Dialog(
            title="Repository Settings",
            parent=self,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(10)
        content.set_margin_end(10)
        content.set_margin_top(10)
        content.set_margin_bottom(10)
        
        # Settings widgets
        auto_check = Gtk.CheckButton(label="Auto-check for manifest updates")
        auto_check.set_active(self.repo_config.get('auto_check_updates', True))
        auto_check.set_tooltip_text("Periodically refresh manifest cache to keep tabs in sync with latest scripts")
        content.pack_start(auto_check, False, False, 0)
        
        auto_install = Gtk.CheckButton(label="Auto-install updates")
        auto_install.set_active(self.repo_config.get('auto_install_updates', True))
        content.pack_start(auto_install, False, False, 0)
        
        interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        interval_label = Gtk.Label(label="Auto-refresh interval (minutes):")
        interval_spin = Gtk.SpinButton()
        interval_spin.set_range(0.1, 1440)  # Allow as low as 6 seconds for testing
        interval_spin.set_increments(0.1, 1)
        interval_spin.set_digits(1)  # Allow decimal values
        interval_spin.set_value(self.repo_config.get('update_check_interval_minutes', 1))
        interval_spin.set_tooltip_text("How often to check for manifest updates (e.g., 0.1 = 6 sec, 1 = 1 min). Requires auto-check to be enabled.")
        interval_box.pack_start(interval_label, False, False, 0)
        interval_box.pack_start(interval_spin, False, False, 0)
        content.pack_start(interval_box, False, False, 0)
        
        # Repository source settings section
        source_separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content.pack_start(source_separator, False, False, 5)
        
        source_label = Gtk.Label()
        source_label.set_markup("<b>Repository Source</b>")
        source_label.set_xalign(0)
        content.pack_start(source_label, False, False, 0)
        
        use_public_repo = Gtk.CheckButton(label="Enable public repository (lv_linux_learn)")
        use_public_repo.set_active(self.repo_config.get('use_public_repository', True))
        use_public_repo.set_tooltip_text("Toggle access to the public lv_linux_learn script repository. Disable to use only custom manifests.")
        content.pack_start(use_public_repo, False, False, 0)
        
        public_repo_note = Gtk.Label()
        public_repo_note.set_markup("<small><i>Note: Custom manifests can be configured in the 'Sources' tab.\nThis includes both local directory scanning and online manifest URLs.</i></small>")
        public_repo_note.set_line_wrap(True)
        public_repo_note.set_xalign(0)
        content.pack_start(public_repo_note, False, False, 0)
        
        dialog.show_all()
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Check if public repository setting changed
            old_public_repo = self.repo_config.get('use_public_repository', True)
            new_public_repo = use_public_repo.get_active()
            
            # Save settings
            self.repo_config['auto_check_updates'] = auto_check.get_active()
            self.repo_config['auto_install_updates'] = auto_install.get_active()
            self.repo_config['update_check_interval_minutes'] = int(interval_spin.get_value())
            self.repo_config['use_public_repository'] = new_public_repo
            # Note: custom_manifest_url is NEVER modified here - managed only by Custom Manifests tab
            # Note: verify_checksums is always True for public repository, per-manifest for custom repos
            
            # Save configuration
            self.repository.save_config(self.repo_config)
            
            # Check if public repository setting changed and refresh UI
            if old_public_repo != new_public_repo:
                # Refresh UI to reflect public repository setting change
                # (refresh will auto-complete terminal operation, so no need to call it here)
                GLib.timeout_add(500, self._refresh_all_script_data)
            else:
                # No refresh needed, complete terminal operation
                GLib.timeout_add(1500, self._complete_terminal_operation)
        
        dialog.destroy()

    # ========================================================================
    # REPOSITORY SELECTION & BULK OPERATIONS
    # ========================================================================
    
    def _on_script_toggled(self, cell_renderer, path):
        """Handle script checkbox toggle"""
        iter = self.repo_store.get_iter(path)
        current_value = self.repo_store.get_value(iter, 0)
        self.repo_store.set_value(iter, 0, not current_value)
    
    def _on_select_all(self, button):
        """Select all scripts in the repository view"""
        for row in self.repo_store:
            row[0] = True  # Set checkbox to True
    
    def _on_select_none(self, button):
        """Deselect all scripts in the repository view"""
        for row in self.repo_store:
            row[0] = False  # Set checkbox to False
    
    def _on_invert_selection(self, button):
        """Invert script selection"""
        for row in self.repo_store:
            row[0] = not row[0]  # Flip checkbox state
    
    def _on_download_selected(self, button):
        """Download selected scripts to cache"""
        selected_scripts = []
        
        # Collect selected script IDs
        for row in self.repo_store:
            if row[0]:  # If checkbox is selected
                script_id = row[1]  # Script ID column
                script_name = row[2]  # Script name column
                selected_scripts.append((script_id, script_name))
        
        if not selected_scripts:
            self.terminal.feed(b"\x1b[33m[!] No scripts selected - please select one or more scripts to download\x1b[0m\r\n")
            return
        
        # Download selected scripts (no confirmation dialog)
        script_names = [name for _, name in selected_scripts]
        self.terminal.feed(f"\x1b[32m[*] Downloading {len(selected_scripts)} selected scripts: {', '.join(script_names[:3])}{'...' if len(script_names) > 3 else ''}\x1b[0m\r\n".encode())
        
        success_count = 0
        failed_count = 0
        local_count = 0
        
        for script_id, script_name in selected_scripts:
            try:
                # Check if this is a local file:// script
                script_info = self.repository.get_script_by_id(script_id)
                if script_info and script_info.get('download_url', '').startswith('file://'):
                    # Local script - no need to download
                    self.terminal.feed(f"  📁 {script_name} (local file - no download needed)\r\n".encode())
                    local_count += 1
                    success_count += 1
                    # Process pending GTK events
                    while Gtk.events_pending():
                        Gtk.main_iteration()
                    continue
                
                # Remote script - download to cache
                self.terminal.feed(f"\x1b[36m[*] Downloading {script_name}...\x1b[0m\r\n".encode())
                # Process pending GTK events to show message immediately
                while Gtk.events_pending():
                    Gtk.main_iteration()
                
                result = self.repository.download_script(script_id)
                success = result[0] if isinstance(result, tuple) else result
                url = result[1] if isinstance(result, tuple) and len(result) > 1 else None
                
                if success:
                    if url:
                        self.terminal.feed(f"  ✓ {script_name}\r\n    URL: {url}\r\n".encode())
                    else:
                        self.terminal.feed(f"  ✓ {script_name}\r\n".encode())
                    success_count += 1
                else:
                    self.terminal.feed(f"  ✗ {script_name} (failed)\r\n".encode())
                    failed_count += 1
                
                # Process pending GTK events after each download
                while Gtk.events_pending():
                    Gtk.main_iteration()
                    
            except Exception as e:
                error_msg = "checksum verification failed" if "Checksum verification failed" in str(e) else f"error: {e}"
                self.terminal.feed(f"  ✗ {script_name} ({error_msg})\r\n".encode())
                failed_count += 1
                # Process pending GTK events for error output
                while Gtk.events_pending():
                    Gtk.main_iteration()
        
        summary_parts = [f"{success_count - local_count} downloaded"]
        if local_count > 0:
            summary_parts.append(f"{local_count} local")
        if failed_count > 0:
            summary_parts.append(f"{failed_count} failed")
        
        self.terminal.feed(f"\x1b[32m[*] Complete: {', '.join(summary_parts)}\x1b[0m\r\n".encode())
        
        # Auto-complete and refresh
        GLib.timeout_add(1500, self._complete_terminal_operation)
        self._update_repo_status()
        self._populate_repository_tree()
        
        # Reload main tabs to update cache status icons
        self._reload_main_tabs()
        
        # Reload main tabs to reflect changes
        self._reload_main_tabs()
    
    def _on_remove_selected(self, button):
        """Remove selected scripts from cache"""
        selected_scripts = []
        
        # Collect selected cached script IDs  
        for row in self.repo_store:
            if row[0]:  # If checkbox is selected
                script_id = row[1]  # Script ID column
                script_name = row[2]  # Script name column
                status = row[4]  # Status column
                
                # Only include cached scripts
                if "Cached" in status or "Update Available" in status:
                    selected_scripts.append((script_id, script_name))
        
        if not selected_scripts:
            self.terminal.feed(b"\x1b[33m[!] No cached scripts selected - please select one or more cached scripts to remove\x1b[0m\r\n")
            return
        
        # Remove selected scripts (no confirmation dialog)
        script_names = [name for _, name in selected_scripts]
        self.terminal.feed(f"\x1b[33m[*] Removing {len(selected_scripts)} cached scripts: {', '.join(script_names[:3])}{'...' if len(script_names) > 3 else ''}\x1b[0m\r\n".encode())
        
        success_count = 0
        failed_count = 0
        
        for script_id, script_name in selected_scripts:
            try:
                cached_path = self.repository.get_cached_script_path(script_id)
                if cached_path and os.path.exists(cached_path):
                    os.remove(cached_path)
                    self.terminal.feed(f"  ✓ {script_name}\r\n".encode())
                    success_count += 1
                else:
                    self.terminal.feed(f"  - {script_name} (not cached)\r\n".encode())
            except Exception as e:
                self.terminal.feed(f"  ✗ {script_name} (error: {e})\r\n".encode())
                failed_count += 1
        
        self.terminal.feed(f"\x1b[32m[*] Removal complete: {success_count} removed, {failed_count} failed\x1b[0m\r\n".encode())
        
        # Auto-complete and refresh
        GLib.timeout_add(1500, self._complete_terminal_operation)
        self._update_repo_status()
        self._populate_repository_tree()
        
        # Reload main tabs to reflect changes  
        self._reload_main_tabs()
    
    def _reload_main_tabs(self):
        """Reload the main script tabs to reflect cache changes"""
        try:
            # Reload global arrays from manifest with terminal output for debugging
            global SCRIPTS, SCRIPT_NAMES, DESCRIPTIONS, TOOLS_SCRIPTS, TOOLS_NAMES, TOOLS_DESCRIPTIONS
            global EXERCISES_SCRIPTS, EXERCISES_NAMES, EXERCISES_DESCRIPTIONS
            global UNINSTALL_SCRIPTS, UNINSTALL_NAMES, UNINSTALL_DESCRIPTIONS
            
            # Refresh repository's cached config to pick up any changes (custom manifests, etc.)
            if self.repository:
                self.repository.config = self.repository.load_config()
            
            # Reload from manifest with repository configuration (this will show cache status in terminal)
            global _SCRIPT_ID_MAP
            _scripts, _names, _descriptions, _SCRIPT_ID_MAP = load_scripts_from_manifest(terminal_widget=self.terminal, repository=self.repository)
            
            # Update global arrays with slice assignment to maintain references
            SCRIPTS[:] = _scripts.get('install', [])
            SCRIPT_NAMES[:] = _names.get('install', [])  
            DESCRIPTIONS[:] = _descriptions.get('install', [])
            
            TOOLS_SCRIPTS[:] = _scripts.get('tools', [])
            TOOLS_NAMES[:] = _names.get('tools', [])
            TOOLS_DESCRIPTIONS[:] = _descriptions.get('tools', [])
            
            EXERCISES_SCRIPTS[:] = _scripts.get('exercises', [])
            EXERCISES_NAMES[:] = _names.get('exercises', [])
            EXERCISES_DESCRIPTIONS[:] = _descriptions.get('exercises', [])
            
            UNINSTALL_SCRIPTS[:] = _scripts.get('uninstall', [])
            UNINSTALL_NAMES[:] = _names.get('uninstall', [])
            UNINSTALL_DESCRIPTIONS[:] = _descriptions.get('uninstall', [])
            
            # Clear and recreate dynamic tabs with fresh data using TabManager
            if hasattr(self, 'tab_manager') and self.repository:
                config = self.repository.load_config()
                GLib.timeout_add(50, lambda: self.tab_manager.rebuild_dynamic_tabs(self.repository, config))
            
            # Use a small delay to ensure the UI updates are visible
            GLib.timeout_add(100, self._delayed_repopulate)

            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error reloading main tabs: {e}\x1b[0m\r\n".encode())
            print(f"Error reloading main tabs: {e}")
    
    def _reload_main_tabs_silent(self):
        """Reload the main script tabs silently (no terminal output)"""
        try:
            # Reload global arrays from manifest WITHOUT terminal output
            global SCRIPTS, SCRIPT_NAMES, DESCRIPTIONS, TOOLS_SCRIPTS, TOOLS_NAMES, TOOLS_DESCRIPTIONS
            global EXERCISES_SCRIPTS, EXERCISES_NAMES, EXERCISES_DESCRIPTIONS
            global UNINSTALL_SCRIPTS, UNINSTALL_NAMES, UNINSTALL_DESCRIPTIONS
            
            # Refresh repository's cached config to pick up any changes (custom manifests, etc.)
            if self.repository:
                self.repository.config = self.repository.load_config()
            
            # Reload from manifest silently with repository configuration (pass None for terminal_widget to suppress output)
            global _SCRIPT_ID_MAP
            _scripts, _names, _descriptions, _SCRIPT_ID_MAP = load_scripts_from_manifest(terminal_widget=None, repository=self.repository)
            
            # Update global arrays with slice assignment to maintain references
            SCRIPTS[:] = _scripts.get('install', [])
            SCRIPT_NAMES[:] = _names.get('install', [])
            DESCRIPTIONS[:] = _descriptions.get('install', [])
            
            TOOLS_SCRIPTS[:] = _scripts.get('tools', [])
            TOOLS_NAMES[:] = _names.get('tools', [])
            TOOLS_DESCRIPTIONS[:] = _descriptions.get('tools', [])
            
            EXERCISES_SCRIPTS[:] = _scripts.get('exercises', [])
            EXERCISES_NAMES[:] = _names.get('exercises', [])
            EXERCISES_DESCRIPTIONS[:] = _descriptions.get('exercises', [])
            
            UNINSTALL_SCRIPTS[:] = _scripts.get('uninstall', [])
            UNINSTALL_NAMES[:] = _names.get('uninstall', [])
            UNINSTALL_DESCRIPTIONS[:] = _descriptions.get('uninstall', [])
            
            # Clear and recreate dynamic tabs with fresh data using TabManager (silently)
            if hasattr(self, 'tab_manager') and self.repository:
                config = self.repository.load_config()
                GLib.timeout_add(50, lambda: self.tab_manager.rebuild_dynamic_tabs(self.repository, config))
            
            # Use a small delay to ensure the UI updates are visible
            GLib.timeout_add(100, self._delayed_repopulate)
            
        except Exception as e:
            print(f"Error reloading main tabs silently: {e}")
    
    def _delayed_repopulate(self):
        """Delayed repopulation to ensure UI updates are visible"""
        try:
            self._repopulate_tab_stores()
            return False  # Don't repeat the timeout
        except Exception as e:
            print(f"Error in delayed repopulate: {e}")
            return False
    
    def _refresh_ui_after_cache_change(self):
        """Refresh all UI elements after a cache change - delegates to UIRefreshCoordinator"""
        try:
            if hasattr(self, 'ui_refresh'):
                self.ui_refresh.refresh_after_cache_change()
            else:
                # Fallback if coordinator not initialized
                self._update_repo_status()
                self._populate_repository_tree()
                self._reload_main_tabs()
            
            return False  # Don't repeat the timeout
        except Exception as e:
            print(f"Error refreshing UI after cache change: {e}")
            return False
    
    def _refresh_ui_silent(self):
        """Silently refresh UI elements without terminal output"""
        try:
            # Update repository status and tree (these don't output to terminal)
            self._update_repo_status()
            
            # Refresh repository tab using handler if available
            if hasattr(self, 'repo_handler') and self.repo_handler:
                self.repo_handler.populate_tree()
            else:
                # Fallback to old method
                self._populate_repository_tree()
            
            # Reload main tabs silently
            self._reload_main_tabs_silent()
            
            return False  # Don't repeat the timeout
        except Exception as e:
            print(f"Error in silent UI refresh: {e}")
            return False
    
    # ========================================================================
    # LOCAL REPOSITORY OPERATIONS (Direct execution, no cache)
    # ========================================================================
    
    def _on_local_script_toggled(self, cell_renderer, path):
        """Handle local script checkbox toggle"""
        iter = self.local_repo_store.get_iter(path)
        current_value = self.local_repo_store.get_value(iter, 0)
        self.local_repo_store.set_value(iter, 0, not current_value)
    
    def _on_local_select_all(self, button):
        """Select all scripts in the local repository view"""
        for row in self.local_repo_store:
            row[0] = True
    
    def _on_local_select_none(self, button):
        """Deselect all scripts in the local repository view"""
        for row in self.local_repo_store:
            row[0] = False
    
    def _on_refresh_local_repos(self, button):
        """Refresh the local repository list with real-time UI updates"""
        self.terminal.feed(b"\x1b[32m[*] Refreshing local repositories...\x1b[0m\r\n")
        # Refresh immediately so user sees changes
        self._populate_local_repository_tree()
        # Also refresh dynamic tabs if any local scripts were categorized
        if TimerManager:
            TimerManager.schedule(self._reload_main_tabs_silent, 200)
            TimerManager.schedule_ui_refresh(self._complete_terminal_operation)
        else:
            GLib.timeout_add(200, self._reload_main_tabs_silent)
            GLib.timeout_add(500, self._complete_terminal_operation)
    
    def _on_delete_selected_local_scripts(self, button):
        """Delete selected scripts from local repositories"""
        selected_scripts = []
        
        # Collect selected scripts
        for row in self.local_repo_store:
            if row[0]:  # If checkbox is selected
                script_name = row[2]
                script_id = row[1]
                script_path = row[4]
                source = row[6]
                selected_scripts.append((script_id, script_name, script_path, source))
        
        if not selected_scripts:
            self.terminal.feed(b"\x1b[33m[!] No scripts selected for deletion\x1b[0m\r\n")
            GLib.timeout_add(100, self._complete_terminal_silent)
            return
        
        # Confirm deletion
        count = len(selected_scripts)
        if count == 1:
            confirm_msg = f"Delete script '{selected_scripts[0][1]}' from local repository?"
            detail_msg = f"This will remove the script from the manifest file.\nThe actual script file will NOT be deleted from disk."
        else:
            confirm_msg = f"Delete {count} scripts from local repositories?"
            detail_msg = f"Scripts to delete:\n" + "\n".join(f"  • {name} ({source})" for _, name, _, source in selected_scripts)
            detail_msg += f"\n\nThis will remove {count} scripts from their manifest files.\nThe actual script files will NOT be deleted from disk."
        
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=confirm_msg
        )
        dialog.format_secondary_text(detail_msg)
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        # Delete scripts from manifests
        self.terminal.feed(f"\x1b[33m[*] Removing {count} script(s) from manifest files...\x1b[0m\r\n".encode())
        
        success_count = 0
        manifest_updates = {}  # Track which manifests need updating
        
        for script_id, script_name, script_path, source in selected_scripts:
            try:
                # Find the manifest file for this script
                custom_manifests_dir = PathManager.get_custom_manifests_dir() if PathManager else Path.home() / '.lv_linux_learn' / 'custom_manifests'
                manifest_files = list(custom_manifests_dir.glob('*/manifest.json')) + list(custom_manifests_dir.glob('*_manifest.json'))
                
                script_removed = False
                for manifest_file in manifest_files:
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest_data = json.load(f)
                        
                        # Check if this script is in this manifest
                        modified = False
                        scripts = manifest_data.get('scripts', {})
                        
                        if isinstance(scripts, dict):
                            # Nested by category
                            for category, category_scripts in scripts.items():
                                if isinstance(category_scripts, list):
                                    # Find and remove script by ID
                                    original_count = len(category_scripts)
                                    category_scripts[:] = [s for s in category_scripts if s.get('id') != script_id]
                                    if len(category_scripts) < original_count:
                                        modified = True
                                        scripts[category] = category_scripts
                        else:
                            # Flat list
                            original_count = len(scripts)
                            scripts[:] = [s for s in scripts if s.get('id') != script_id]
                            if len(scripts) < original_count:
                                modified = True
                        
                        if modified:
                            # Save updated manifest
                            manifest_data['scripts'] = scripts
                            with open(manifest_file, 'w') as f:
                                json.dump(manifest_data, f, indent=2)
                            
                            script_removed = True
                            success_count += 1
                            manifest_updates[str(manifest_file)] = True
                            self.terminal.feed(f"\x1b[32m[✓] Removed {script_name} from {manifest_file.name}\x1b[0m\r\n".encode())
                            break  # Script found and removed
                    
                    except Exception as e:
                        self.terminal.feed(f"\x1b[31m[!] Error checking {manifest_file.name}: {e}\x1b[0m\r\n".encode())
                        continue
                
                if not script_removed:
                    self.terminal.feed(f"\x1b[33m[!] Could not find {script_name} in any manifest\x1b[0m\r\n".encode())
            
            except Exception as e:
                self.terminal.feed(f"\x1b[31m[✗] Error removing {script_name}: {e}\x1b[0m\r\n".encode())
        
        # Refresh UI if any deletions succeeded
        if success_count > 0:
            self.terminal.feed(f"\x1b[32m[✓] Successfully removed {success_count} of {count} script(s)\x1b[0m\r\n".encode())
            
            # Real-time UI updates
            self.terminal.feed(b"\x1b[36m[*] Refreshing UI...\x1b[0m\r\n")
            GLib.timeout_add(100, self._populate_local_repository_tree)
            GLib.timeout_add(200, self._reload_main_tabs_silent)
            GLib.timeout_add(400, self._complete_terminal_silent)
        else:
            self.terminal.feed(b"\x1b[31m[!] No scripts were removed\x1b[0m\r\n")
            GLib.timeout_add(100, self._complete_terminal_silent)
    
    def _on_execute_selected_local(self, button):
        """Execute selected local scripts (direct execution, no caching)"""
        selected_scripts = []
        
        # Collect selected scripts
        for row in self.local_repo_store:
            if row[0]:  # If checkbox is selected
                script_name = row[2]
                script_path = row[4]
                selected_scripts.append((script_name, script_path))
        
        if not selected_scripts:
            self.terminal.feed(b"\x1b[33m[!] No scripts selected - please select at least one script to execute\x1b[0m\r\n")
            return
        
        # Execute scripts directly without confirmation
        script_names = [name for name, _ in selected_scripts]
        self.terminal.feed(f"\x1b[32m[*] Executing {len(selected_scripts)} local scripts: {', '.join(script_names[:3])}{'...' if len(script_names) > 3 else ''}\x1b[0m\r\n".encode())
        self.terminal.feed(b"\r\n\x1b[32m[*] Executing selected local scripts...\x1b[0m\r\n")
        
        success_count = 0
        failed_count = 0
        
        for script_name, script_path in selected_scripts:
            # Check if path contains "(NOT FOUND)" indicator
            if "(NOT FOUND)" in script_path or "not available" in script_path.lower():
                self.terminal.feed(f"  ✗ {script_name} - File not found\r\n".encode())
                failed_count += 1
                continue
            
            # Execute script directly (no caching)
            try:
                path_obj = Path(script_path)
                if not path_obj.exists():
                    self.terminal.feed(f"  ✗ {script_name} - File does not exist: {script_path}\r\n".encode())
                    failed_count += 1
                    continue
                
                self.terminal.feed(f"  ▶️ Executing: {script_name}...\r\n".encode())
                
                # Make executable
                import stat
                current_permissions = path_obj.stat().st_mode
                path_obj.chmod(current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                
                # Execute in terminal using source for interactive scripts
                cmd = f"source {shlex.quote(str(path_obj))}\n"
                self.terminal.feed_child(cmd.encode())
                
                success_count += 1
                
            except Exception as e:
                self.terminal.feed(f"  ✗ {script_name} - Error: {e}\r\n".encode())
                failed_count += 1
        
        self.terminal.feed(f"\x1b[32m[*] Execution queued: {success_count} scripts, {failed_count} failed\x1b[0m\r\n".encode())
        GLib.timeout_add(1000, self._complete_terminal_operation)
    
    def _on_local_repo_row_activated(self, tree_view, path, column):
        """Handle double-click on local repository script (execute directly)"""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        
        script_name = model.get_value(iter, 2)
        script_path = model.get_value(iter, 4)
        
        # Check if path is valid
        if "(NOT FOUND)" in script_path or "not available" in script_path.lower():
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Script Not Found"
            )
            dialog.format_secondary_text(f"The script file does not exist:\n{script_path}")
            dialog.run()
            dialog.destroy()
            return
        
        # Execute directly
        self.terminal.feed(b"\x1b[2J\x1b[H")
        self.terminal.feed(f"\x1b[32m[*] Executing local script: {script_name}\x1b[0m\r\n\r\n".encode())
        
        try:
            path_obj = Path(script_path)
            if not path_obj.exists():
                self.terminal.feed(f"\x1b[31m[!] File not found: {script_path}\x1b[0m\r\n".encode())
                return
            
            # Make executable
            import stat
            current_permissions = path_obj.stat().st_mode
            path_obj.chmod(current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            
            # Execute in terminal using source for interactive scripts
            cmd = f"source {shlex.quote(str(path_obj))}\n"
            self.terminal.feed_child(cmd.encode())
            
            if TimerManager:
                TimerManager.schedule_operation(self._complete_terminal_operation)
            else:
                GLib.timeout_add(1000, self._complete_terminal_operation)
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error executing script: {e}\x1b[0m\r\n".encode())
    
    def _on_install_ollama(self, button):
        """Guide user through Ollama installation"""
        self.terminal.feed(b"\r\n\x1b[36m" + b"="*80 + b"\x1b[0m\r\n")
        self.terminal.feed(b"\x1b[36m  Install Ollama AI Engine\x1b[0m\r\n")
        self.terminal.feed(b"\x1b[36m" + b"="*80 + b"\x1b[0m\r\n\r\n")
        self.terminal.feed(b"\x1b[32mOllama provides local AI-powered script analysis:\x1b[0m\r\n")
        self.terminal.feed("  • Automatic script categorization\r\n".encode())
        self.terminal.feed("  • AI-generated descriptions\r\n".encode())
        self.terminal.feed("  • Dependency detection\r\n".encode())
        self.terminal.feed("  • Security analysis\r\n\r\n".encode())
        self.terminal.feed(b"\x1b[33m[*] Installing Ollama...\x1b[0m\r\n")
        self.terminal.feed(b"curl https://ollama.ai/install.sh | sh\n")
        self.terminal.feed_child(b"curl https://ollama.ai/install.sh | sh\n")
        
        # Show next steps after delay
        GLib.timeout_add(3000, self._show_ollama_next_steps)
    
    def _show_ollama_next_steps(self):
        """Show Ollama post-installation steps"""
        self.terminal.feed(b"\r\n\x1b[32m" + b"="*80 + b"\x1b[0m\r\n")
        self.terminal.feed(b"\x1b[32m  Ollama Installation Next Steps\x1b[0m\r\n")
        self.terminal.feed(b"\x1b[32m" + b"="*80 + b"\x1b[0m\r\n\r\n")
        self.terminal.feed(b"After installation completes:\r\n\r\n")
        self.terminal.feed(b"\x1b[33m1. Pull an AI model:\x1b[0m\r\n")
        self.terminal.feed(b"   ollama pull llama3.2  (recommended, ~2GB)\r\n")
        self.terminal.feed(b"   Or: ollama pull codellama  (code-focused, ~4GB)\r\n\r\n")
        self.terminal.feed(b"\x1b[33m2. Test the installation:\x1b[0m\r\n")
        self.terminal.feed(b"   ollama list\r\n\r\n")
        self.terminal.feed(b"\x1b[33m3. Restart this application\x1b[0m to enable AI features\r\n\r\n")
        self.terminal.feed(b"Visit https://ollama.ai for more information\r\n")
        # Send newline to shell to complete the display without waiting
        GLib.timeout_add(100, self._complete_terminal_silent)
        return False
    
    def _on_ai_analyze_scripts(self, button):
        """Analyze selected scripts using AI"""
        # Collect selected scripts
        selected_scripts = []
        for row in self.local_repo_store:
            if row[0]:  # If checkbox is selected
                script_name = row[2]
                script_path = row[4]
                script_id = row[1]
                if "(NOT FOUND)" not in script_path and "not available" not in script_path.lower():
                    selected_scripts.append((script_id, script_name, script_path))
        
        if not selected_scripts:
            self.terminal.feed(b"\x1b[33m[!] No scripts selected for analysis\x1b[0m\r\n")
            self.terminal.feed(b"Please select at least one script from the Repository (Local) tab\r\n")
            # Complete terminal operation so user doesn't have to press return
            GLib.timeout_add(100, self._complete_terminal_silent)
            return
        
        # Output to terminal instead of showing confirmation dialog
        self.terminal.feed(b"\r\n\x1b[36m" + b"="*70 + b"\x1b[0m\r\n")
        self.terminal.feed(f"\x1b[36m  Starting AI analysis of {len(selected_scripts)} script(s)...\x1b[0m\r\n".encode())
        self.terminal.feed(b"\x1b[36m" + b"="*70 + b"\x1b[0m\r\n\r\n")
        
        # Start analysis directly
        self._run_ai_analysis(selected_scripts)
    
    def _run_ai_analysis(self, scripts):
        """Run AI analysis on scripts with real-time terminal progress"""
        import threading
        from lib.ai_categorizer import OllamaAnalyzer
        
        # Shared state for thread
        state = {
            'results': [],
            'cancelled': False,
            'script_data': scripts,  # Store script metadata for manifest updates
            'current_index': 0,
            'total': len(scripts)
        }
        
        def analysis_complete():
            """Called when analysis finishes"""
            if not state['cancelled'] and state['results']:
                try:
                    # Output results to terminal
                    self.terminal.feed(b"\r\n")
                    self.terminal.feed(b"\x1b[32m" + b"="*70 + b"\x1b[0m\r\n")
                    self.terminal.feed(b"\x1b[32m  AI ANALYSIS RESULTS\x1b[0m\r\n")
                    self.terminal.feed(b"\x1b[32m" + b"="*70 + b"\x1b[0m\r\n\r\n")
                    
                    for script_name, analysis in state['results']:
                        self.terminal.feed(f"\x1b[36m\u25cf {script_name}\x1b[0m\r\n".encode())
                        
                        if 'error' in analysis:
                            error = analysis['error']
                            self.terminal.feed("  \x1b[31mError: {}\x1b[0m\r\n\r\n".format(error).encode())
                        else:
                            category = analysis.get('category', 'unknown')
                            description = analysis.get('description', 'N/A')
                            safety = analysis.get('safety', 'unknown')
                            deps = analysis.get('dependencies', [])
                            
                            # Color-code safety
                            safety_colors = {
                                'safe': '\x1b[32m',
                                'caution': '\x1b[33m',
                                'requires_review': '\x1b[31m'
                            }
                            safety_color = safety_colors.get(safety, '\x1b[37m')
                            
                            self.terminal.feed(f"  Category: \x1b[1m{category}\x1b[0m\r\n".encode())
                            self.terminal.feed(f"  Description: {description}\r\n".encode())
                            self.terminal.feed(f"  Safety: {safety_color}{safety}\x1b[0m\r\n".encode())
                            
                            if deps:
                                deps_str = ', '.join(deps[:5])
                                if len(deps) > 5:
                                    deps_str += f" (+{len(deps)-5} more)"
                                self.terminal.feed(f"  Dependencies: {deps_str}\r\n".encode())
                            
                            self.terminal.feed(b"\r\n")
                    
                    self.terminal.feed(b"\x1b[32m" + b"="*70 + b"\x1b[0m\r\n")
                    self.terminal.feed(f"\x1b[32m  Analysis complete: {len(state['results'])} script(s) processed\x1b[0m\r\n".encode())
                    self.terminal.feed(b"\x1b[32m" + b"="*70 + b"\x1b[0m\r\n\r\n")
                    
                    # Update manifests with AI results
                    if ManifestManager and state.get('script_data'):
                        self._update_manifests_from_ai(state['script_data'], state['results'])
                    
                    # Refresh UI to show updated categories - REAL-TIME UPDATE
                    self.terminal.feed(b"\x1b[36m[*] Refreshing UI with new categories...\x1b[0m\r\n")
                    GLib.timeout_add(100, self._reload_scripts_and_tabs)
                    GLib.timeout_add(300, self._populate_local_repository_tree)
                    return False  # Don't repeat
                    
                except Exception as e:
                    self.terminal.feed(f"\x1b[31m[!] Error displaying results: {e}\x1b[0m\r\n".encode())
                    import traceback
                    self.terminal.feed(traceback.format_exc().encode())
            elif state['cancelled']:
                try:
                    self.terminal.feed(b"\x1b[33m[*] AI analysis cancelled by user\x1b[0m\r\n")
                except:
                    pass
            return False
        
        def run_analysis():
            """Background thread for AI analysis"""
            try:
                analyzer = OllamaAnalyzer()
                total = len(scripts)
                
                for i, (script_id, script_name, script_path) in enumerate(scripts):
                    if state['cancelled']:
                        break
                    
                    # Show progress in terminal
                    GLib.idle_add(lambda i=i, n=script_name, t=total: self.terminal.feed(
                        f"\x1b[36m[{i+1}/{t}] Analyzing: {n}\x1b[0m\r\n".encode()
                    ))
                    
                    # Run analysis (blocking operation in background thread)
                    try:
                        analysis = analyzer.analyze_script(script_path)
                        if analysis and 'error' not in analysis:
                            category = analysis.get('category', 'tools')
                            safety = analysis.get('safety', 'unknown')
                            state['results'].append((script_name, analysis))
                            GLib.idle_add(lambda c=category, s=safety: self.terminal.feed(
                                f"  \u2713 Category: {c}, Safety: {s}\r\n".encode()
                            ))
                        else:
                            error = analysis.get('error', 'Unknown error') if analysis else 'Analysis failed'
                            state['results'].append((script_name, {'error': error}))
                            GLib.idle_add(lambda e=error: self.terminal.feed(
                                "  \u2717 Error: {}\r\n".format(e).encode()
                            ))
                    except Exception as e:
                        error_msg = str(e)
                        state['results'].append((script_name, {'error': error_msg}))
                        GLib.idle_add(lambda e=error_msg: self.terminal.feed(
                            "  \u2717 Error: {}\r\n".format(e).encode()
                        ))
                
            except Exception as e:
                GLib.idle_add(lambda: self.terminal.feed(
                    f"\x1b[31m[!] Analysis error: {e}\x1b[0m\r\n".encode()
                ))
            finally:
                GLib.idle_add(analysis_complete)
        
        # Start analysis in background thread
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()
    
    def _update_manifests_from_ai(self, script_data, results):
        """
        Update local repository manifests with AI analysis results
        
        Args:
            script_data: List of (script_id, script_name, script_path) tuples
            results: List of (script_name, analysis_dict) tuples
        """
        if not ManifestManager:
            self.terminal.feed(b"\x1b[31m[!] ManifestManager not available\x1b[0m\r\n")
            return
        
        try:
            global _SCRIPT_ID_MAP
            
            self.terminal.feed(b"\r\n\x1b[36m" + b"="*70 + b"\x1b[0m\r\n")
            self.terminal.feed(b"\x1b[36m  UPDATING MANIFEST FILES\x1b[0m\r\n")
            self.terminal.feed(b"\x1b[36m" + b"="*70 + b"\x1b[0m\r\n\r\n")
            
            # Map script names to their data
            script_map = {name: (sid, path) for sid, name, path in script_data}
            results_map = {name: analysis for name, analysis in results}
            
            # Find local repository manifests
            manifests_dir = PathManager.get_custom_manifests_dir() if PathManager else Path.home() / '.lv_linux_learn' / 'custom_manifests'
            
            # Ensure manifests directory exists
            if not manifests_dir.exists():
                self.terminal.feed(f"\x1b[33m[!] Manifests directory does not exist: {manifests_dir}\x1b[0m\r\n".encode())
                return
            
            updated_count = 0
            failed_count = 0
            
            for script_name, analysis in results:
                if 'error' in analysis:
                    self.terminal.feed(f"\x1b[33m[-] {script_name}: Analysis error - {analysis.get('error')}\x1b[0m\r\n".encode())
                    failed_count += 1
                    continue
                
                if script_name not in script_map:
                    self.terminal.feed(f"\x1b[33m[!] {script_name}: Not found in script data\x1b[0m\r\n".encode())
                    failed_count += 1
                    continue
                
                script_id, script_path = script_map[script_name]
                
                # Find which manifest this script belongs to using _SCRIPT_ID_MAP
                manifest_path = None
                source_name = None
                
                # Look up the script in _SCRIPT_ID_MAP to find its source
                # Try multiple matching strategies:
                # 1. Exact path match
                # 2. Script ID match  
                # 3. Partial path match (for when paths differ slightly)
                # 4. Name-based fallback (for local repos where ID mapping might be incomplete)
                
                for (category, path), (mapped_id, mapped_source) in _SCRIPT_ID_MAP.items():
                    # Strategy 1: Exact path match
                    if path == script_path:
                        source_name = mapped_source
                        break
                    # Strategy 2: Script ID match
                    if script_id and mapped_id == script_id:
                        source_name = mapped_source
                        break
                    # Strategy 3: Partial path match (e.g., absolute vs relative)
                    if script_path and os.path.basename(script_path) == os.path.basename(path):
                        if os.path.exists(script_path):  # Verify path is valid
                            source_name = mapped_source
                            break
                
                if not source_name:
                    # Strategy 4: Try to find by looking for scripts in local manifests by name
                    self.terminal.feed(f"\x1b[36m[*] {script_name}: Direct mapping failed, searching manifests...\x1b[0m\r\n".encode())
                    
                    for manifest_dir in manifests_dir.glob('*/manifest.json'):
                        try:
                            with open(manifest_dir, 'r') as f:
                                manifest_data = json.load(f)
                                # Check all scripts in this manifest
                                all_scripts = []
                                for cat, scripts_list in manifest_data.get('scripts', {}).items():
                                    if isinstance(scripts_list, list):
                                        all_scripts.extend(scripts_list)
                                
                                for script in all_scripts:
                                    if script.get('name') == script_name or script.get('id') == script_id:
                                        source_name = manifest_dir.parent.name
                                        break
                            if source_name:
                                break
                        except Exception:
                            continue
                
                if not source_name:
                    self.terminal.feed(f"\x1b[33m[!] {script_name}: Could not find source in mapping or manifests\x1b[0m\r\n".encode())
                    failed_count += 1
                    continue
                
                # Try multiple manifest paths
                manifest_candidates = [
                    manifests_dir / source_name / 'manifest.json',  # Directory-based
                    manifests_dir / f"{source_name}.json",           # Direct JSON file
                ]
                
                manifest_path = None
                for candidate in manifest_candidates:
                    if candidate.exists():
                        manifest_path = candidate
                        break
                
                if not manifest_path:
                    self.terminal.feed(f"\x1b[33m[!] {script_name}: Could not find manifest for source '{source_name}'\x1b[0m\r\n".encode())
                    self.terminal.feed(f"\x1b[33m    Checked: {', '.join(str(c) for c in manifest_candidates)}\x1b[0m\r\n".encode())
                    failed_count += 1
                    continue
                
                # Update the manifest
                try:
                    # Verify manifest path is readable
                    if not os.access(manifest_path, os.R_OK):
                        raise PermissionError(f"Cannot read manifest: {manifest_path}")
                    
                    manager = ManifestManager(str(manifest_path))
                    
                    if not manager.manifest_data:
                        raise Exception(f"Failed to load manifest data from {manifest_path}")
                    
                    success = manager.update_script_from_ai_analysis(script_id, analysis)
                    
                    if success:
                        new_category = analysis.get('category', 'custom')
                        self.terminal.feed(f"\x1b[32m\u2713 {script_name}: moved to '{new_category}' category\x1b[0m\r\n".encode())
                        updated_count += 1
                        
                        # CRITICAL: Update the config.json with the updated manifest data
                        # This ensures the next reload will have the updated data in memory
                        try:
                            config_file = Path.home() / '.lv_linux_learn' / 'config.json'
                            config = {}
                            if config_file.exists():
                                with open(config_file, 'r') as f:
                                    config = json.load(f)
                            
                            # Update manifest data in config if it exists there
                            if 'custom_manifests' in config and source_name in config['custom_manifests']:
                                config['custom_manifests'][source_name]['manifest_data'] = manager.manifest_data
                                with open(config_file, 'w') as f:
                                    json.dump(config, f, indent=2)
                                self.terminal.feed(f"\x1b[36m[*] Updated manifest config for '{source_name}'\x1b[0m\r\n".encode())
                        except Exception as cfg_err:
                            self.terminal.feed(f"\x1b[33m[!] Could not update config.json: {cfg_err}\x1b[0m\r\n".encode())
                    else:
                        self.terminal.feed(f"\x1b[31m\u2717 {script_name}: update failed (see logs)\x1b[0m\r\n".encode())
                        failed_count += 1
                
                except PermissionError as e:
                    self.terminal.feed(f"\x1b[31m\u2717 {script_name}: Permission denied - {e}\x1b[0m\r\n".encode())
                    failed_count += 1
                except Exception as e:
                    self.terminal.feed(f"\x1b[31m\u2717 {script_name}: {type(e).__name__}: {e}\x1b[0m\r\n".encode())
                    failed_count += 1
            
            self.terminal.feed(b"\r\n")
            self.terminal.feed(f"\x1b[32mManifest updates: {updated_count} succeeded, {failed_count} failed\x1b[0m\r\n".encode())
            
            if updated_count > 0:
                self.terminal.feed(b"\r\n")
                self.terminal.feed(b"\x1b[36m[*] Reloading scripts to reflect new categories...\x1b[0m\r\n\r\n")
                # Force immediate reload without GLib timeout
                self._reload_scripts_and_tabs()
        
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error updating manifests: {type(e).__name__}: {e}\x1b[0m\r\n".encode())
    
    def _reload_scripts_and_tabs(self):
        """Reload scripts from manifests and refresh all tabs"""
        try:
            global _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT
            global SCRIPTS, SCRIPT_NAMES, DESCRIPTIONS, TOOLS_SCRIPTS, TOOLS_NAMES, TOOLS_DESCRIPTIONS
            global EXERCISES_SCRIPTS, EXERCISES_NAMES, EXERCISES_DESCRIPTIONS
            global UNINSTALL_SCRIPTS, UNINSTALL_NAMES, UNINSTALL_DESCRIPTIONS
            global _SCRIPT_ID_MAP
            
            self.terminal.feed(b"\x1b[36m[*] Reloading scripts from manifests...\x1b[0m\r\n")
            
            # CRITICAL: Ensure we reload the manifest from disk
            # Clear all temp manifest files to force fresh read from config
            config_dir = Path.home() / '.lv_linux_learn'
            
            # Delete temp manifest files (these are recreated from config)
            for temp_file in config_dir.glob('temp_*_manifest.json'):
                try:
                    temp_file.unlink()
                    self.terminal.feed(f"\x1b[36m[*] Cleared temp manifest: {temp_file.name}\x1b[0m\r\n".encode())
                except Exception as e:
                    self.terminal.feed(f"\x1b[33m[!] Could not clear {temp_file.name}: {e}\x1b[0m\r\n".encode())
            
            # Also clear the public repo manifest cache
            manifest_cache = config_dir / 'manifest.json'
            if manifest_cache.exists():
                try:
                    manifest_cache.unlink()
                    self.terminal.feed(b"\x1b[36m[*] Cleared public repository manifest cache\x1b[0m\r\n")
                except Exception as e:
                    self.terminal.feed(f"\x1b[33m[!] Could not clear manifest cache: {e}\x1b[0m\r\n".encode())
            
            # Clear all cached manifest_* files so updated manifest_data is used immediately
            for cached_manifest in config_dir.glob('manifest_*.json'):
                try:
                    cached_manifest.unlink()
                    self.terminal.feed(f"\x1b[36m[*] Cleared cached manifest: {cached_manifest.name}\x1b[0m\r\n".encode())
                except Exception as e:
                    self.terminal.feed(f"\x1b[33m[!] Could not clear cached manifest {cached_manifest.name}: {e}\x1b[0m\r\n".encode())

            # Force repository to reload config from disk to pick up latest changes
            if self.repository:
                if self.config_manager:
                    # Config reload handled by repository
                    self.repository.config = self.config_manager.get_config()
                else:
                    self.repository.config = self.repository.load_config()
                self.terminal.feed(b"\x1b[36m[*] Reloaded repository config from disk\x1b[0m\r\n")
            
            # Reload scripts with repository instance
            if load_scripts_from_manifest and self.repository:
                self.terminal.feed(b"\x1b[36m[*] Loading scripts from all configured manifests...\x1b[0m\r\n")
                _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, _SCRIPT_ID_MAP = \
                    load_scripts_from_manifest(terminal_widget=self.terminal, repository=self.repository)
                
                # CRITICAL: Update global module-level variables by clearing and re-populating
                # This ensures any code referencing these globals gets the updated data
                new_install = _SCRIPTS_DICT.get('install', [])
                new_install_names = _NAMES_DICT.get('install', [])
                new_install_desc = _DESCRIPTIONS_DICT.get('install', [])
                
                new_tools = _SCRIPTS_DICT.get('tools', [])
                new_tools_names = _NAMES_DICT.get('tools', [])
                new_tools_desc = _DESCRIPTIONS_DICT.get('tools', [])
                
                new_exercises = _SCRIPTS_DICT.get('exercises', [])
                new_exercises_names = _NAMES_DICT.get('exercises', [])
                new_exercises_desc = _DESCRIPTIONS_DICT.get('exercises', [])
                
                new_uninstall = _SCRIPTS_DICT.get('uninstall', [])
                new_uninstall_names = _NAMES_DICT.get('uninstall', [])
                new_uninstall_desc = _DESCRIPTIONS_DICT.get('uninstall', [])
                
                # Update global arrays in-place (preserve list identity)
                SCRIPTS.clear()
                SCRIPTS.extend(new_install)
                SCRIPT_NAMES.clear()
                SCRIPT_NAMES.extend(new_install_names)
                DESCRIPTIONS.clear()
                DESCRIPTIONS.extend(new_install_desc)
                
                TOOLS_SCRIPTS.clear()
                TOOLS_SCRIPTS.extend(new_tools)
                TOOLS_NAMES.clear()
                TOOLS_NAMES.extend(new_tools_names)
                TOOLS_DESCRIPTIONS.clear()
                TOOLS_DESCRIPTIONS.extend(new_tools_desc)
                
                EXERCISES_SCRIPTS.clear()
                EXERCISES_SCRIPTS.extend(new_exercises)
                EXERCISES_NAMES.clear()
                EXERCISES_NAMES.extend(new_exercises_names)
                EXERCISES_DESCRIPTIONS.clear()
                EXERCISES_DESCRIPTIONS.extend(new_exercises_desc)
                
                UNINSTALL_SCRIPTS.clear()
                UNINSTALL_SCRIPTS.extend(new_uninstall)
                UNINSTALL_NAMES.clear()
                UNINSTALL_NAMES.extend(new_uninstall_names)
                UNINSTALL_DESCRIPTIONS.clear()
                UNINSTALL_DESCRIPTIONS.extend(new_uninstall_desc)
                
                # Verify update succeeded
                total_scripts = len(SCRIPTS) + len(TOOLS_SCRIPTS) + len(EXERCISES_SCRIPTS) + len(UNINSTALL_SCRIPTS)
                self.terminal.feed(f"\x1b[36m[*] Loaded {total_scripts} scripts across all categories\x1b[0m\r\n".encode())
                self.terminal.feed(f"    - Install: {len(SCRIPTS)}, Tools: {len(TOOLS_SCRIPTS)}, Exercises: {len(EXERCISES_SCRIPTS)}, Uninstall: {len(UNINSTALL_SCRIPTS)}\x1b[0m\r\n".encode())
                
                # Refresh all tabs (this updates the UI)
                self.terminal.feed(b"\x1b[36m[*] Refreshing all tabs...\x1b[0m\r\n")
                self._refresh_script_tabs()
                
                # Recreate dynamic tabs if any non-standard categories exist
                self.terminal.feed(b"\x1b[36m[*] Creating dynamic tabs for any non-standard categories...\x1b[0m\r\n")
                GLib.timeout_add(100, self._create_dynamic_category_tabs)
                
                # Also refresh local repository tab
                if hasattr(self, 'local_repo_store'):
                    self._populate_local_repository_tree()
                
                # Force UI refresh by refiltering
                if hasattr(self, 'install_filter'):
                    self.install_filter.refilter()
                if hasattr(self, 'tools_filter'):
                    self.tools_filter.refilter()
                if hasattr(self, 'exercises_filter'):
                    self.exercises_filter.refilter()
                if hasattr(self, 'uninstall_filter'):
                    self.uninstall_filter.refilter()
                
                self.terminal.feed(b"\x1b[32m[OK] UI refreshed successfully\x1b[0m\r\n\r\n")
                
                # Complete the terminal operation after a brief delay to allow GTK to process
                GLib.timeout_add(300, self._complete_terminal_operation)
        
        except Exception as e:
            import traceback
            self.terminal.feed(f"\x1b[31m[!] Error reloading scripts: {e}\x1b[0m\r\n".encode())
            self.terminal.feed(traceback.format_exc().encode())
            # Complete the operation even on error
            GLib.timeout_add(200, self._complete_terminal_operation)
    
    def _refresh_script_tabs(self):
        """Refresh all script tab liststores with updated data"""
        try:
            # CRITICAL: Clear dynamic tabs before refreshing using TabManager
            if hasattr(self, 'tab_manager'):
                self.tab_manager.clear_dynamic_tabs()
            
            # Refresh Install tab
            if hasattr(self, 'install_liststore'):
                self.terminal.feed(f"\x1b[36m  - Install tab: {len(SCRIPTS)} scripts\x1b[0m\r\n".encode())
                self.install_liststore.clear()
                for i, script_path in enumerate(SCRIPTS):
                    if i < len(SCRIPT_NAMES) and i < len(DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, 'install', SCRIPT_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        source_type = metadata.get('source_type', '')
                        
                        # Local scripts don't use cache
                        if source_type == 'custom_local':
                            icon = "📄"
                            is_cached = False
                        else:
                            is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category='install')
                            icon = "\u2713" if is_cached else "\u2601\ufe0f"
                        
                        path_to_store = script_path
                        if is_cached and self.repository:
                            cached_path = None
                            if script_id:
                                cached_path = self.repository.get_cached_script_path(script_id)
                            else:
                                # Fallback: resolve by category + filename when script_id is missing
                                filename = os.path.basename(script_path)
                                cached_path = self.repository.get_cached_script_path(category='install', filename=filename)
                            if cached_path and os.path.exists(cached_path):
                                path_to_store = cached_path
                                metadata["type"] = "cached"
                                metadata["file_exists"] = True
                                pass  # removed debug log
                        
                        self.install_liststore.append([icon, SCRIPT_NAMES[i], path_to_store, DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
            
            # Refresh Tools tab
            if hasattr(self, 'tools_liststore'):
                self.terminal.feed(f"\x1b[36m  - Tools tab: {len(TOOLS_SCRIPTS)} scripts\x1b[0m\r\n".encode())
                self.tools_liststore.clear()
                for i, script_path in enumerate(TOOLS_SCRIPTS):
                    if i < len(TOOLS_NAMES) and i < len(TOOLS_DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, 'tools', TOOLS_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        source_type = metadata.get('source_type', '')
                        
                        # Local scripts don't use cache
                        if source_type == 'custom_local':
                            icon = "📄"
                            is_cached = False
                        else:
                            is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category='tools')
                            icon = "\u2713" if is_cached else "\u2601\ufe0f"
                        
                        path_to_store = script_path
                        if is_cached and self.repository:
                            cached_path = None
                            if script_id:
                                cached_path = self.repository.get_cached_script_path(script_id)
                            else:
                                filename = os.path.basename(script_path)
                                cached_path = self.repository.get_cached_script_path(category='tools', filename=filename)
                            if cached_path and os.path.exists(cached_path):
                                path_to_store = cached_path
                                metadata["type"] = "cached"
                                metadata["file_exists"] = True
                                pass  # removed debug log
                        
                        self.tools_liststore.append([icon, TOOLS_NAMES[i], path_to_store, TOOLS_DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
            
            # Refresh Exercises tab
            if hasattr(self, 'exercises_liststore'):
                self.terminal.feed(f"\x1b[36m  - Exercises tab: {len(EXERCISES_SCRIPTS)} scripts\x1b[0m\r\n".encode())
                self.exercises_liststore.clear()
                for i, script_path in enumerate(EXERCISES_SCRIPTS):
                    if i < len(EXERCISES_NAMES) and i < len(EXERCISES_DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, 'exercises', EXERCISES_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        source_type = metadata.get('source_type', '')
                        
                        # Local scripts don't use cache
                        if source_type == 'custom_local':
                            icon = "📄"
                            is_cached = False
                        else:
                            is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category='exercises')
                            icon = "\u2713" if is_cached else "\u2601\ufe0f"
                        
                        path_to_store = script_path
                        if is_cached and self.repository:
                            cached_path = None
                            if script_id:
                                cached_path = self.repository.get_cached_script_path(script_id)
                            else:
                                filename = os.path.basename(script_path)
                                cached_path = self.repository.get_cached_script_path(category='exercises', filename=filename)
                            if cached_path and os.path.exists(cached_path):
                                path_to_store = cached_path
                                metadata["type"] = "cached"
                                metadata["file_exists"] = True
                                pass  # removed debug log
                        
                        self.exercises_liststore.append([icon, EXERCISES_NAMES[i], path_to_store, EXERCISES_DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
            
            # Refresh Uninstall tab
            if hasattr(self, 'uninstall_liststore'):
                self.terminal.feed(f"\x1b[36m  - Uninstall tab: {len(UNINSTALL_SCRIPTS)} scripts\x1b[0m\r\n".encode())
                self.uninstall_liststore.clear()
                for i, script_path in enumerate(UNINSTALL_SCRIPTS):
                    if i < len(UNINSTALL_NAMES) and i < len(UNINSTALL_DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, 'uninstall', UNINSTALL_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        source_type = metadata.get('source_type', '')
                        
                        # Local scripts don't use cache
                        if source_type == 'custom_local':
                            icon = "📄"
                            is_cached = False
                        else:
                            is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category='uninstall')
                            icon = "\u2713" if is_cached else "\u2601\ufe0f"
                        
                        path_to_store = script_path
                        if is_cached and self.repository:
                            cached_path = None
                            if script_id:
                                cached_path = self.repository.get_cached_script_path(script_id)
                            else:
                                filename = os.path.basename(script_path)
                                cached_path = self.repository.get_cached_script_path(category='uninstall', filename=filename)
                            if cached_path and os.path.exists(cached_path):
                                path_to_store = cached_path
                                metadata["type"] = "cached"
                                metadata["file_exists"] = True
                                pass  # removed debug log
                        
                        self.uninstall_liststore.append([icon, UNINSTALL_NAMES[i], path_to_store, UNINSTALL_DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
            
        except Exception as e:
            self.terminal.feed(f"[!] Error refreshing tabs: {e}\r\n".encode())

    
    def _update_repo_status(self):
        """Update repository status display and cache statistics"""
        # This method updates any status indicators in the repository tab
        # Currently handles status updates after cache operations
        if not self.repo_enabled or not self.repository:
            return
        
        try:
            # Get cache statistics
            cache_dir = self.repository.script_cache_dir
            if cache_dir and cache_dir.exists():
                cached_count = len(list(cache_dir.glob('**/*.sh')))
                # Status tracking only - no terminal output during script execution
        except Exception as e:
            # Silently handle errors, don't interrupt operations
            pass

    def _on_delete_manifest(self, manifest_name):
        """Delete manifest by name with confirmation"""
        if not self.custom_manifest_creator:
            return
        
        # Confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Delete Custom Manifest"
        )
        dialog.format_secondary_text(
            f"Are you sure you want to delete the manifest '{manifest_name}'?\n\n"
            "This will permanently remove the manifest and all its copied scripts."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            success, message = self.custom_manifest_creator.delete_custom_manifest(manifest_name)
            
            if success:
                self.terminal.feed(f"\x1b[32m[✓] {message}\x1b[0m\r\n".encode())
                
                # Refresh the custom manifest tree
                self._populate_custom_manifest_tree()
                
                # Refresh repository system to reload from new manifest
                if self.repository:
                    self.repository.refresh_repository_url()
                
                # Update repository status and tree
                self._update_repo_status()
                if hasattr(self, '_populate_repository_tree'):
                    self._populate_repository_tree()
                
                # Reload main tabs to remove deleted manifest scripts
                self._reload_main_tabs()
            else:
                self.terminal.feed(f"\x1b[31m[✗] {message}\x1b[0m\r\n".encode())
    
    def _on_switch_to_public_repository(self, button):
        """Toggle public repository on/off"""
        if not self.repository:
            return
        
        self.terminal.feed(b"\x1b[2J\x1b[H")  # Clear screen
        
        try:
            config = self.repository.load_config()
            current_state = config.get('use_public_repository', True)
            new_state = not current_state
            
            config['use_public_repository'] = new_state
            self.repository.save_config(config)
            
            if new_state:
                self.terminal.feed(b"\x1b[32m[*] Public repository enabled\x1b[0m\r\n")
            else:
                self.terminal.feed(b"\x1b[33m[*] Public repository disabled\x1b[0m\r\n")
                # When disabling public repo, clean up its cached files
                self.terminal.feed(b"\x1b[36m[*] Cleaning up public repository cache files...\x1b[0m\r\n")
                try:
                    cache_dir = Path.home() / '.lv_linux_learn'
                    public_cache = cache_dir / 'manifest_public_repository.json'
                    public_cache.unlink(missing_ok=True)
                    self.terminal.feed(b"\x1b[32m[*] Removed cached public repository manifest\x1b[0m\r\n")
                except Exception as e:
                    self.terminal.feed(f"\x1b[33m[!] Cache cleanup warning: {e}\x1b[0m\r\n".encode())
            
            self.terminal.feed(b"\x1b[32m[*] Reloading scripts...\x1b[0m\r\n")
            
            # Refresh UI to reload with new manifest configuration
            self._refresh_ui_after_manifest_switch()
            
            self.terminal.feed(b"\x1b[32m[*] Scripts reloaded successfully\x1b[0m\r\n")
        
        except Exception as e:
            error_msg = f"Failed to toggle public repository: {e}"
            self.terminal.feed(f"\x1b[31m[!] {error_msg}\x1b[0m\r\n".encode())
            import traceback
            traceback.print_exc()
            self._show_error_dialog(self, error_msg)
    
    def _refresh_ui_after_manifest_switch(self):
        """Refresh UI after switching manifests - delegates to UIRefreshCoordinator"""
        try:
            if hasattr(self, 'ui_refresh'):
                self.ui_refresh.refresh_after_repo_toggle()
                self.terminal.feed(b"\x1b[32m[+] UI refreshed successfully\x1b[0m\r\n")
            else:
                # Fallback if coordinator not initialized
                self._reload_main_tabs()
            return False
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error refreshing UI: {e}\x1b[0m\r\n".encode())
            print(f"Error refreshing UI after manifest switch: {e}")
            return False

    # ========================================================================
    # INCLUDES & CACHE MANAGEMENT
    # ========================================================================

    def _ensure_remote_includes(self, cache_root):
        """Download includes from remote repository specified in manifest"""
        import urllib.request
        import json
        import tempfile
        import shutil
        
        includes_cache = os.path.join(cache_root, "includes")
        
        # Get repository URL from manifest
        repo_url = ""
        manifest_path = MANIFEST_CACHE_FILE
        
        if manifest_path and os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                repo_url = manifest.get('repository_url', '')
            except Exception as e:
                print(f"[INFO] Cannot read repository URL from manifest: {e}")
        
        if not repo_url:
            print("[INFO] No repository URL found in manifest, using local includes")
            return False
        
        # Check if we already have remote includes cached
        if os.path.isdir(includes_cache) and not os.path.islink(includes_cache):
            # Check if cached includes are from remote repository
            origin_file = os.path.join(includes_cache, ".origin")
            cached_origin = ""
            if os.path.exists(origin_file):
                try:
                    with open(origin_file, 'r') as f:
                        cached_origin = f.read().strip()
                except Exception:
                    pass
            
            if cached_origin == repo_url:
                # Check freshness (within 24 hours)
                timestamp_file = os.path.join(includes_cache, ".timestamp")
                if os.path.exists(timestamp_file):
                    try:
                        with open(timestamp_file, 'r') as f:
                            cache_time = int(f.read().strip())
                        current_time = int(time.time())
                        age = current_time - cache_time
                        
                        if age < 86400:  # 24 hours
                            print(f"[INFO] Using cached remote includes (age: {age}s)")
                            return True
                    except Exception:
                        pass
        
        # Download remote includes
        print(f"[INFO] Downloading includes from remote repository: {repo_url}")
        
        # Remove existing includes if it exists
        if os.path.exists(includes_cache):
            try:
                if os.path.isdir(includes_cache):
                    shutil.rmtree(includes_cache)
                else:
                    os.remove(includes_cache)
            except Exception as e:
                print(f"[WARNING] Cannot remove existing includes cache: {e}")
                return False
        
        # Create temporary directory for download
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Try to download main.sh and repository.sh
                download_success = False
                
                try:
                    main_url = f"{repo_url}/includes/main.sh"
                    repo_sh_url = f"{repo_url}/includes/repository.sh"
                    
                    main_path = os.path.join(temp_dir, "main.sh")
                    repo_sh_path = os.path.join(temp_dir, "repository.sh")
                    
                    urllib.request.urlretrieve(main_url, main_path)
                    urllib.request.urlretrieve(repo_sh_url, repo_sh_path)
                    
                    download_success = True
                except Exception as e:
                    print(f"[WARNING] Failed to download remote includes: {e}")
                
                if download_success:
                    # Create includes directory and copy files
                    os.makedirs(includes_cache)
                    
                    for filename in os.listdir(temp_dir):
                        if filename.endswith('.sh'):
                            src = os.path.join(temp_dir, filename)
                            dst = os.path.join(includes_cache, filename)
                            shutil.copy2(src, dst)
                            os.chmod(dst, 0o755)
                    
                    # Mark cache with origin and timestamp
                    with open(os.path.join(includes_cache, ".origin"), 'w') as f:
                        f.write(repo_url)
                    
                    with open(os.path.join(includes_cache, ".timestamp"), 'w') as f:
                        f.write(str(int(time.time())))
                    
                    print("[INFO] Successfully downloaded remote includes to cache")
                    return True
                else:
                    print(f"[WARNING] Failed to download remote includes from: {repo_url}")
                    return False
                    
        except Exception as e:
            print(f"[WARNING] Error downloading remote includes: {e}")
            return False

    def _ensure_cache_includes_symlink(self):
        """Ensure that the cache directory has a symlink to the repository includes directory"""
        try:
            cache_root = PathManager.get_cache_dir() if PathManager else os.path.expanduser("~/.lv_linux_learn/script_cache")
            includes_symlink = os.path.join(cache_root, "includes")
            
            # Ensure cache directory exists
            if not os.path.exists(cache_root):
                try:
                    os.makedirs(cache_root, exist_ok=True)
                except PermissionError:
                    print(f"[WARNING] No permission to create cache directory: {cache_root}")
                    return False
                except OSError as e:
                    print(f"[WARNING] Cannot create cache directory: {e}")
                    return False
            
            # Try to get remote includes first, then fall back to local
            if self._ensure_remote_includes(cache_root):
                return True
            
            # Fall back to local repository includes
            repo_includes = os.path.join(os.path.dirname(os.path.abspath(__file__)), "includes")
            if not os.path.exists(repo_includes):
                print(f"[WARNING] Local repository includes directory not found: {repo_includes}")
                return False
            
            # Handle existing symlink/file
            if os.path.exists(includes_symlink) or os.path.islink(includes_symlink):
                # Check if it's a valid symlink pointing to correct location
                if os.path.islink(includes_symlink):
                    current_target = os.readlink(includes_symlink)
                    if os.path.abspath(current_target) == os.path.abspath(repo_includes):
                        # Symlink already correct
                        return True
                    else:
                        # Symlink points to wrong location, remove and recreate
                        try:
                            os.remove(includes_symlink)
                            print(f"[INFO] Removed outdated symlink: {includes_symlink}")
                        except (OSError, PermissionError) as e:
                            print(f"[WARNING] Cannot remove existing symlink: {e}")
                            return False
                else:
                    # Regular file/directory exists with same name
                    print(f"[WARNING] File/directory exists at symlink path: {includes_symlink}")
                    return False
            
            # Create the symlink
            try:
                os.symlink(repo_includes, includes_symlink)
                print(f"[INFO] Created includes symlink: {includes_symlink} -> {repo_includes}")
                return True
                
            except OSError as e:
                if e.errno == 1:  # Operation not permitted (common on some filesystems)
                    print(f"[WARNING] Symlinks not supported on this filesystem: {e}")
                elif e.errno == 17:  # File exists (race condition)
                    print(f"[INFO] Symlink already created by another process")
                    return True
                else:
                    print(f"[WARNING] Cannot create symlink (filesystem issue): {e}")
                return False
                
            except PermissionError:
                print(f"[WARNING] No permission to create symlink in: {cache_root}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Unexpected error in symlink creation: {type(e).__name__}: {e}")
            return False

    def _fallback_copy_includes(self):
        """Fallback method: copy includes directory if symlink creation fails"""
        try:
            import shutil
            
            cache_root = PathManager.get_cache_dir() if PathManager else os.path.expanduser("~/.lv_linux_learn/script_cache")
            includes_cache = os.path.join(cache_root, "includes")
            
            # Try remote includes first
            if self._ensure_remote_includes(cache_root):
                return True
            
            # Fall back to local repository includes
            repo_includes = os.path.join(os.path.dirname(os.path.abspath(__file__)), "includes")
            if not os.path.exists(repo_includes):
                print(f"[WARNING] Local repository includes directory not found: {repo_includes}")
                return False
                
            # Remove existing includes if it exists
            if os.path.exists(includes_cache):
                try:
                    if os.path.isdir(includes_cache):
                        shutil.rmtree(includes_cache)
                    else:
                        os.remove(includes_cache)
                except (OSError, PermissionError) as e:
                    print(f"[WARNING] Cannot remove existing includes directory: {e}")
                    return False
            
            # Copy the includes directory
            try:
                shutil.copytree(repo_includes, includes_cache)
                print(f"[INFO] Copied includes directory to cache (symlink fallback): {includes_cache}")
                return True
            except (OSError, PermissionError, shutil.Error) as e:
                print(f"[WARNING] Cannot copy includes directory: {e}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Unexpected error in includes copy fallback: {type(e).__name__}: {e}")
            return False

    def _check_includes_freshness(self):
        """Check if cached includes directory is fresh (supports both remote and local)"""
        try:
            cache_root = PathManager.get_cache_dir() if PathManager else os.path.expanduser("~/.lv_linux_learn/script_cache")
            includes_cache = os.path.join(cache_root, "includes")
            
            if not os.path.exists(includes_cache):
                return False
                
            # If it's a symlink to local repo, check if target exists
            if os.path.islink(includes_cache):
                target = os.readlink(includes_cache)
                if os.path.exists(target):
                    return True
                else:
                    # Symlink is broken
                    return False
                    
            # For cached remote includes, check age and origin
            origin_file = os.path.join(includes_cache, ".origin")
            timestamp_file = os.path.join(includes_cache, ".timestamp")
            
            if os.path.exists(origin_file) and os.path.exists(timestamp_file):
                try:
                    with open(timestamp_file, 'r') as f:
                        cache_time = int(f.read().strip())
                    current_time = int(time.time())
                    age = current_time - cache_time
                    
                    # Consider fresh if less than 24 hours old
                    if age < 86400:
                        return True
                except Exception:
                    pass
                    
            # For local copied includes, compare with local repository
            repo_includes = os.path.join(os.path.dirname(os.path.abspath(__file__)), "includes")
            if os.path.exists(repo_includes):
                cache_main = os.path.join(includes_cache, "main.sh")
                repo_main = os.path.join(repo_includes, "main.sh")
                
                if os.path.exists(cache_main) and os.path.exists(repo_main):
                    cache_mtime = os.path.getmtime(cache_main)
                    repo_mtime = os.path.getmtime(repo_main)
                    
                    # Consider fresh if cache is newer or equal (within 1 second tolerance)
                    return cache_mtime >= (repo_mtime - 1)
                else:
                    return False
            else:
                # No local repository to compare with, assume cached version is fresh
                return True
                
            return False
            
        except Exception as e:
            print(f"[WARNING] Cannot check includes freshness: {e}")
            return False

    def _ensure_includes_available(self):
        """Ensure includes directory is available in cache (repository-aware)"""
        if not self.repository:
            return False
            
        # Try repository-aware includes download first
        if self.repository.ensure_includes_available():
            return True
            
        # Fall back to local methods if repository method fails
        # Check if we already have fresh includes
        if self._check_includes_freshness():
            return True
            
        # Try symlink first (for local development)
        if self._ensure_cache_includes_symlink():
            return True
            
        # Fall back to copying if symlink fails
        print("[INFO] Symlink failed, trying copy fallback...")
        if self._fallback_copy_includes():
            return True
            
        print("[ERROR] All includes methods failed - cached scripts may not work properly")
        return False

    def _repopulate_tab_stores(self):
        """
        Repopulate liststores for all main tabs.
        Uses global manifest data (SCRIPTS, TOOLS_SCRIPTS, etc.)
        """
        try:
            # Clear and repopulate install tab
            if hasattr(self, 'install_liststore'):
                self.install_liststore.clear()
                for i, script_path in enumerate(SCRIPTS):
                    if i < len(SCRIPT_NAMES) and i < len(DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, "install", SCRIPT_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category="install")
                        
                        # Check for updates if cached
                        has_update = False
                        if is_cached and self.repository and script_id:
                            script_info = self.repository.get_script_by_id(script_id)
                            if script_info:
                                remote_checksum = script_info.get('checksum', '').replace('sha256:', '')
                                cached_path = self.repository.get_cached_script_path(script_id)
                                if cached_path and os.path.exists(cached_path) and remote_checksum:
                                    import hashlib
                                    try:
                                        with open(cached_path, 'rb') as f:
                                            local_checksum = hashlib.sha256(f.read()).hexdigest()
                                        has_update = local_checksum != remote_checksum
                                    except:
                                        pass
                        
                        icon = "📥" if has_update else ("✓" if is_cached else "☁️")
                        
                        # Prefer cached full path when available
                        path_to_store = script_path
                        if is_cached and self.repository:
                            cached_path = None
                            if script_id:
                                cached_path = self.repository.get_cached_script_path(script_id)
                            else:
                                filename = os.path.basename(script_path)
                                cached_path = self.repository.get_cached_script_path(category="install", filename=filename)
                            if cached_path and os.path.exists(cached_path):
                                path_to_store = cached_path
                                metadata["type"] = "cached"
                                metadata["file_exists"] = True
                        self.install_liststore.append([icon, SCRIPT_NAMES[i], path_to_store, DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
            
            # Clear and repopulate tools tab  
            if hasattr(self, 'tools_liststore'):
                self.tools_liststore.clear()
                for i, script_path in enumerate(TOOLS_SCRIPTS):
                    if i < len(TOOLS_NAMES) and i < len(TOOLS_DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, "tools", TOOLS_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category="tools")
                        
                        # Check for updates if cached
                        has_update = False
                        if is_cached and self.repository and script_id:
                            script_info = self.repository.get_script_by_id(script_id)
                            if script_info:
                                remote_checksum = script_info.get('checksum', '').replace('sha256:', '')
                                cached_path = self.repository.get_cached_script_path(script_id)
                                if cached_path and os.path.exists(cached_path) and remote_checksum:
                                    import hashlib
                                    try:
                                        with open(cached_path, 'rb') as f:
                                            local_checksum = hashlib.sha256(f.read()).hexdigest()
                                        has_update = local_checksum != remote_checksum
                                    except:
                                        pass
                        
                        icon = "📥" if has_update else ("✓" if is_cached else "☁️")
                        
                        path_to_store = script_path
                        if is_cached and self.repository:
                            cached_path = None
                            if script_id:
                                cached_path = self.repository.get_cached_script_path(script_id)
                            else:
                                filename = os.path.basename(script_path)
                                cached_path = self.repository.get_cached_script_path(category="tools", filename=filename)
                            if cached_path and os.path.exists(cached_path):
                                path_to_store = cached_path
                                metadata["type"] = "cached"
                                metadata["file_exists"] = True
                        self.tools_liststore.append([icon, TOOLS_NAMES[i], path_to_store, TOOLS_DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
            
            # Clear and repopulate exercises tab
            if hasattr(self, 'exercises_liststore'):
                self.exercises_liststore.clear()
                for i, script_path in enumerate(EXERCISES_SCRIPTS):
                    if i < len(EXERCISES_NAMES) and i < len(EXERCISES_DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, "exercises", EXERCISES_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category="exercises")
                        
                        # Check for updates if cached
                        has_update = False
                        if is_cached and self.repository and script_id:
                            script_info = self.repository.get_script_by_id(script_id)
                            if script_info:
                                remote_checksum = script_info.get('checksum', '').replace('sha256:', '')
                                cached_path = self.repository.get_cached_script_path(script_id)
                                if cached_path and os.path.exists(cached_path) and remote_checksum:
                                    import hashlib
                                    try:
                                        with open(cached_path, 'rb') as f:
                                            local_checksum = hashlib.sha256(f.read()).hexdigest()
                                        has_update = local_checksum != remote_checksum
                                    except:
                                        pass
                        
                        icon = "📥" if has_update else ("✓" if is_cached else "☁️")
                        
                        path_to_store = script_path
                        if is_cached and self.repository:
                            cached_path = None
                            if script_id:
                                cached_path = self.repository.get_cached_script_path(script_id)
                            else:
                                filename = os.path.basename(script_path)
                                cached_path = self.repository.get_cached_script_path(category="exercises", filename=filename)
                            if cached_path and os.path.exists(cached_path):
                                path_to_store = cached_path
                                metadata["type"] = "cached"
                                metadata["file_exists"] = True
                        self.exercises_liststore.append([icon, EXERCISES_NAMES[i], path_to_store, EXERCISES_DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
            
            # Clear and repopulate uninstall tab
            if hasattr(self, 'uninstall_liststore'):
                self.uninstall_liststore.clear()
                for i, script_path in enumerate(UNINSTALL_SCRIPTS):
                    if i < len(UNINSTALL_NAMES) and i < len(UNINSTALL_DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, "uninstall", UNINSTALL_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category="uninstall")
                        
                        # Check for updates if cached
                        has_update = False
                        if is_cached and self.repository and script_id:
                            script_info = self.repository.get_script_by_id(script_id)
                            if script_info:
                                remote_checksum = script_info.get('checksum', '').replace('sha256:', '')
                                cached_path = self.repository.get_cached_script_path(script_id)
                                if cached_path and os.path.exists(cached_path) and remote_checksum:
                                    import hashlib
                                    try:
                                        with open(cached_path, 'rb') as f:
                                            local_checksum = hashlib.sha256(f.read()).hexdigest()
                                        has_update = local_checksum != remote_checksum
                                    except:
                                        pass
                        
                        icon = "📥" if has_update else ("✓" if is_cached else "☁️")
                        
                        path_to_store = script_path
                        if is_cached and self.repository:
                            cached_path = None
                            if script_id:
                                cached_path = self.repository.get_cached_script_path(script_id)
                            else:
                                filename = os.path.basename(script_path)
                                cached_path = self.repository.get_cached_script_path(category="uninstall", filename=filename)
                            if cached_path and os.path.exists(cached_path):
                                path_to_store = cached_path
                                metadata["type"] = "cached"
                                metadata["file_exists"] = True
                        self.uninstall_liststore.append([icon, UNINSTALL_NAMES[i], path_to_store, UNINSTALL_DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
                        
        except Exception as e:
            print(f"Error repopulating tab stores: {e}")

    # ========================================================================
    # PACKAGE INSTALLATION HELPERS
    # ========================================================================

    def install_packages_in_terminal(self, pkgs, required=True):
        """Install packages by running commands in the embedded terminal"""
        pkg_list = " ".join(pkgs)
        pkg_type = "required" if required else "optional"
        
        # Clear screen first
        self.terminal.feed_child(b"clear\n")
        
        # Just run the installation command
        install_cmd = f"sudo apt-get update && sudo apt-get install -y {pkg_list}\n"
        self.terminal.feed_child(install_cmd.encode())
        
        # Show info dialog with option to restart when done
        GLib.idle_add(self._show_install_started_dialog, pkg_type, pkg_list, required)
    
    def _send_install_commands(self, pkg_list, pkg_type):
        """Send installation commands to terminal after clearing"""
        # This method is no longer used but kept to avoid breaking references
        pass
    
    def _show_install_started_dialog(self, pkg_type, pkg_list, required=True):
        """Show dialog that installation has started - uses UI helper"""
        if UI:
            UI.show_install_started_dialog(self, pkg_type, pkg_list.split(', '), required)
        # No fallback needed - non-critical dialog
        return False
    
    def _restart_application(self):
        """Restart the application"""
        import sys
        python = sys.executable
        script = os.path.abspath(__file__)
        os.execl(python, python, script)
    
    def _show_install_completion(self):
        """Show completion message in terminal"""
        # This method is no longer used but kept to avoid breaking references
        pass

    def install_packages(self, pkgs):
        """Legacy method - kept for backward compatibility"""
        # This method is no longer used but kept to avoid breaking changes
        self.install_packages_in_terminal(pkgs, required=True)

    # ========================================================================
    # EVENT HANDLERS - USER INTERACTIONS
    # ========================================================================

    def on_selection_changed(self, selection):
        model, treeiter = selection.get_selected()
        widgets = self.get_current_widgets()
        
        if treeiter is not None:
            # model is filtered -> get data from model columns
            # Column 0 is icon, 1 is name, 2 is path, 3 is description
            basename = model[treeiter][1]
            fullpath = model[treeiter][2]
            desc_markup_raw = model[treeiter][3]
            
            # Build a compact header: bold filename + monospaced path, then description.
            safe_name = GLib.markup_escape_text(basename)
            safe_path = GLib.markup_escape_text(fullpath)
            desc_markup = (
                f"<big><b>{safe_name}</b></big>\n"
                f"<tt>{safe_path}</tt>\n\n"
                f"{desc_markup_raw}"
            )
            widgets['description_label'].set_markup(desc_markup)
            widgets['run_button'].set_sensitive(True)
            widgets['view_button'].set_sensitive(True)
            widgets['cd_button'].set_sensitive(True)
        else:
            widgets['description_label'].set_text("Select a script to see description.")
            widgets['run_button'].set_sensitive(False)
            widgets['view_button'].set_sensitive(False)
            widgets['cd_button'].set_sensitive(False)

    def on_run_clicked(self, button):
        """Handle Run button - delegates to ScriptActionHandler for unified execution"""
        script_path, metadata = self._get_selected_script_data()
        if not script_path:
            return
        
        # Use centralized action handler
        if hasattr(self, 'script_actions'):
            self.script_actions.run_script(script_path, metadata)
        else:
            # Fallback if handler not initialized
            self._execute_script_unified(script_path, metadata)

    def on_cd_clicked(self, button):
        """Handle Go to Directory button - delegates to ScriptActionHandler for unified navigation"""
        script_path, metadata = self._get_selected_script_data()
        if not script_path:
            return
        
        # Use centralized action handler
        if hasattr(self, 'script_actions'):
            self.script_actions.navigate_to_directory(script_path, metadata)
        else:
            # Fallback if handler not initialized
            self._navigate_to_directory_unified(script_path, metadata)

    def on_view_clicked(self, button):
        """Handle View Script button - delegates to ScriptActionHandler for unified viewing"""
        script_path, metadata = self._get_selected_script_data()
        if not script_path:
            return
        
        # Use centralized action handler
        if hasattr(self, 'script_actions'):
            self.script_actions.view_script(script_path, metadata)
        else:
            # Fallback: basic view if handler not initialized
            if os.path.isfile(script_path):
                self.terminal.feed_child(f"cat {shlex.quote(script_path)}\n".encode())
    
    def _get_selected_script_data(self):
        """
        Centralized method to extract script path and metadata from selected row.
        Handles all tab types: standard tabs, repository tabs, and local repository tabs.
        
        Returns:
            tuple: (script_path, metadata) or (None, None) if no selection
        """
        # Get the currently active treeview - needs special handling for different tab types
        current_page = self.notebook.get_current_page()
        current_page_widget = self.notebook.get_nth_page(current_page)
        
        # Helper to find widget in container tree
        def find_widget(container, target):
            if container == target:
                return True
            if isinstance(container, Gtk.Container):
                for child in container.get_children():
                    if find_widget(child, target):
                        return True
            return False
        
        # Detect which tab type we're on
        is_local_repo_tab = False
        is_repository_tab = False
        
        if hasattr(self, 'local_repo_tree'):
            is_local_repo_tab = find_widget(current_page_widget, self.local_repo_tree)
        
        if hasattr(self, 'repo_tree') and not is_local_repo_tab:
            is_repository_tab = find_widget(current_page_widget, self.repo_tree)
        
        # Get selection based on which tab we're on
        if is_local_repo_tab:
            selection = self.local_repo_tree.get_selection()
        elif is_repository_tab:
            selection = self.repo_tree.get_selection()
        else:
            widgets = self.get_current_widgets()
            selection = widgets['treeview'].get_selection()
        
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return None, None
        
        # Extract script data using appropriate column indices based on tab type
        if is_local_repo_tab:
            # LOCAL REPOSITORY TAB: Direct file access, path at column 4
            # Columns: 0=selected, 1=id, 2=name, 3=version, 4=path, 5=category, 6=source, 7=size
            script_path = model[treeiter][C.LOCAL_REPO_COL_PATH if C else 4]
            metadata = self._get_script_metadata(model, treeiter)
            
            # Build metadata if missing (local repo tab doesn't store full metadata)
            if not metadata or metadata.get("source_type") == "unknown":
                display_name = model[treeiter][C.LOCAL_REPO_COL_NAME if C else 2]
                category = self.current_tab if hasattr(self, 'current_tab') else "install"
                metadata = self._build_script_metadata(script_path, category, display_name)
                
        elif is_repository_tab:
            # REPOSITORY TAB: Cache engine, script_id at column 1
            # Columns: 0=selected, 1=id, 2=name, 3=version, 4=status, 5=category, 6=size, 7=modified, 8=source
            script_id = model[treeiter][1]
            display_name = model[treeiter][2]
            category = model[treeiter][5]
            source_name = model[treeiter][8]
            
            # Build metadata for repository script
            metadata = {
                'script_id': script_id,
                'name': display_name,
                'category': category.lower(),
                'type': 'remote',  # Repository scripts use cache
                'source_type': 'custom_repo' if source_name != 'Public Repository' else 'public_repo',
                'source_name': source_name
            }
            script_path = script_id  # For repository scripts, use script_id as identifier
            
        else:
            # STANDARD/DYNAMIC TABS: Script tabs (install, tools, exercises, uninstall, custom, etc.)
            # Columns: 0=icon, 1=name, 2=path, 3=description, 4=is_custom, 5=metadata, 6=script_id
            script_path = model[treeiter][C.COL_PATH if C else 2]
            display_name = model[treeiter][C.COL_NAME if C else 1]
            metadata = self._get_script_metadata(model, treeiter)
            
            # Build metadata if missing
            if not metadata or metadata.get("source_type") == "unknown":
                category = self.current_tab if hasattr(self, 'current_tab') else "install"
                metadata = self._build_script_metadata(script_path, category, display_name)
        
        return script_path, metadata
    
    def on_terminal_clear(self, button):
        """Clear the terminal"""
        self.terminal.feed_child(b"clear\n")
    
    def on_terminal_button_press(self, widget, event):
        """Handle right-click on terminal to show context menu"""
        if event.button == 3:  # Right-click
            menu = Gtk.Menu()
            
            # Copy menu item
            copy_item = Gtk.MenuItem(label="Copy")
            copy_item.connect("activate", self.on_terminal_copy)
            menu.append(copy_item)
            
            # Paste menu item
            paste_item = Gtk.MenuItem(label="Paste")
            paste_item.connect("activate", self.on_terminal_paste)
            menu.append(paste_item)
            
            menu.append(Gtk.SeparatorMenuItem())
            
            # Select All menu item
            select_all_item = Gtk.MenuItem(label="Select All")
            select_all_item.connect("activate", self.on_terminal_select_all)
            menu.append(select_all_item)
            
            menu.append(Gtk.SeparatorMenuItem())
            
            # Clear menu item
            clear_item = Gtk.MenuItem(label="Clear")
            clear_item.connect("activate", lambda w: self.terminal.feed_child(b"clear\n"))
            menu.append(clear_item)
            
            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        return False
    
    def on_terminal_copy(self, menu_item):
        """Copy selected text from terminal to clipboard"""
        self.terminal.copy_clipboard_format(Vte.Format.TEXT)
    
    def on_terminal_paste(self, menu_item):
        """Paste text from clipboard to terminal"""
        self.terminal.paste_clipboard()
    
    def on_terminal_select_all(self, menu_item):
        """Select all text in terminal"""
        self.terminal.select_all()
    
    def _scroll_terminal_to_top(self):
        """Scroll the terminal viewport to the top"""
        adj = self.terminal.get_vadjustment()
        if adj:
            adj.set_value(adj.get_lower())
        return False  # Don't repeat the timeout

    def on_link_clicked(self, label, uri):
        webbrowser.open(uri)
        return True

    def on_row_activated(self, tree_view, path, column):
        # emulate run on double-click or Enter
        sel = tree_view.get_selection()
        sel.select_path(path)
        self.on_run_clicked(None)

    def on_add_custom_script(self, button, category):
        """Show dialog to add a custom script"""
        dialog = Gtk.Dialog(title="Add Custom Script", parent=self, flags=0)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(500, 400)
        
        box = dialog.get_content_area()
        box.set_border_width(12)
        box.set_spacing(12)
        
        # Script Name
        name_label = Gtk.Label(label="Script Name:", xalign=0)
        box.pack_start(name_label, False, False, 0)
        
        name_entry = Gtk.Entry()
        name_entry.set_placeholder_text("e.g., My Custom Installer")
        box.pack_start(name_entry, False, False, 0)
        
        # Script Path
        path_label = Gtk.Label(label="Script Path:", xalign=0)
        box.pack_start(path_label, False, False, 0)
        
        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        path_entry = Gtk.Entry()
        path_entry.set_placeholder_text("/path/to/script.sh")
        path_entry.set_hexpand(True)
        path_box.pack_start(path_entry, True, True, 0)
        
        browse_button = Gtk.Button(label="Browse...")
        browse_button.connect("clicked", lambda b: self._browse_for_script(path_entry))
        path_box.pack_start(browse_button, False, False, 0)
        box.pack_start(path_box, False, False, 0)
        
        # Description
        desc_label = Gtk.Label(label="Description (Markdown supported):", xalign=0)
        box.pack_start(desc_label, False, False, 0)
        
        desc_scroll = Gtk.ScrolledWindow()
        desc_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        desc_scroll.set_min_content_height(150)
        
        desc_buffer = Gtk.TextBuffer()
        desc_buffer.set_text(
            f"<b>My Custom Script</b>\n"
            f"Script: <tt>path/to/script.sh</tt>\n\n"
            f"• Add your description here\n"
            f"• Use bullet points\n"
            f"• <b>Bold</b> and <tt>monospace</tt> formatting supported"
        )
        desc_view = Gtk.TextView(buffer=desc_buffer)
        desc_view.set_wrap_mode(Gtk.WrapMode.WORD)
        desc_scroll.add(desc_view)
        box.pack_start(desc_scroll, True, True, 0)
        
        # Requires sudo checkbox
        sudo_check = Gtk.CheckButton(label="Requires sudo privileges")
        box.pack_start(sudo_check, False, False, 0)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            name = name_entry.get_text().strip()
            script_path = path_entry.get_text().strip()
            start_iter, end_iter = desc_buffer.get_bounds()
            description = desc_buffer.get_text(start_iter, end_iter, True)
            requires_sudo = sudo_check.get_active()
            
            # Validate inputs
            if not name:
                self.show_error_dialog("Script name cannot be empty")
            elif not script_path:
                self.show_error_dialog("Script path cannot be empty")
            elif not os.path.isfile(script_path):
                self.show_error_dialog(f"Script file not found: {script_path}")
            elif not os.access(script_path, os.X_OK):
                self.show_error_dialog(f"Script is not executable: {script_path}")
            else:
                # Add the script
                self.custom_manager.add_script(
                    name=name,
                    category=category,
                    script_path=script_path,
                    description=description,
                    requires_sudo=requires_sudo
                )
                # Refresh the current tab
                self._refresh_tab(category)
        
        dialog.destroy()
    
    def _browse_for_script(self, entry):
        """Show file chooser dialog for script selection"""
        dialog = Gtk.FileChooserDialog(
            title="Select Script File",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Filter for shell scripts
        filter_sh = Gtk.FileFilter()
        filter_sh.set_name("Shell scripts")
        filter_sh.add_pattern("*.sh")
        dialog.add_filter(filter_sh)
        
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def _refresh_tab(self, category):
        """Refresh the script list for a specific tab"""
        # Get the appropriate liststore
        if category == "install":
            liststore = self.install_liststore
        elif category == "tools":
            liststore = self.tools_liststore
        elif category == "exercises":
            liststore = self.exercises_liststore
        else:
            liststore = self.uninstall_liststore
        
        # Clear existing custom scripts (keep only built-in)
        iter = liststore.get_iter_first()
        while iter:
            # Get metadata from column 4 to check if custom
            metadata_str = liststore.get_value(iter, 4)
            try:
                metadata = json.loads(metadata_str) if metadata_str else {}
                is_custom = metadata.get('is_custom', False)
            except json.JSONDecodeError:
                is_custom = liststore.get_value(iter, 3)  # Fallback to column 3
            
            if is_custom:
                if not liststore.remove(iter):
                    break
            else:
                iter = liststore.iter_next(iter)
        
        # Add custom scripts only if custom sources/manifests are configured
        if self._has_custom_sources():
            custom_scripts = self.custom_script_manager.get_scripts(category)
            for script in custom_scripts:
                display_name = f"📝 {script['name']}"
                # Build metadata for custom script
                metadata = {
                    "type": "local",
                    "source_type": "custom_script",
                    "source_name": "Custom Script",
                    "source_url": "",
                    "file_exists": os.path.isfile(script['script_path']),
                    "is_custom": True,
                    "script_id": script['id']
                }
                liststore.append([
                    display_name,
                    script['script_path'],
                    script['description'],
                    True,  # is_custom (column 3 for backward compatibility)
                    json.dumps(metadata)  # metadata JSON (column 4 - authoritative)
                ])

    def on_treeview_button_press(self, treeview, event):
        """Handle right-click on tree view for script context menu"""
        if event.button == 3:  # Right-click
            # Get the clicked row
            path_info = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path_info is None:
                return False
            
            path = path_info[0]
            model = treeview.get_model()
            iter = model.get_iter(path)
            
            # Get metadata from column 5 (JSON string)
            metadata_str = model.get_value(iter, 5)
            try:
                metadata = json.loads(metadata_str) if metadata_str else {}
            except json.JSONDecodeError:
                metadata = {}
            
            # Check if it's a custom script from metadata
            is_custom = metadata.get('is_custom', False)
            script_id = metadata.get('script_id', '')
            
            # Show context menu
            menu = Gtk.Menu()
            
            if is_custom:
                # Custom script menu items
                edit_item = Gtk.MenuItem(label="✏️ Edit Script")
                edit_item.connect("activate", lambda w: self._edit_custom_script(script_id))
                menu.append(edit_item)
                
                delete_item = Gtk.MenuItem(label="🗑️ Delete Script")
                delete_item.connect("activate", lambda w: self._delete_custom_script(script_id))
                menu.append(delete_item)
            else:
                # Manifest script menu items (repository scripts)
                if self.repository and self.repo_enabled:
                    COL_NAME = C.COL_NAME if C else 1
                    COL_PATH = C.COL_PATH if C else 2
                    
                    script_name = model.get_value(iter, COL_NAME)
                    script_path = model.get_value(iter, COL_PATH)
                    
                    # Get script_id from metadata (already stored)
                    manifest_script_id = metadata.get('script_id', '')
                    
                    # If no script_id in metadata, try to look it up
                    if not manifest_script_id:
                        manifest_script_id, manifest_path_for_download = self._get_manifest_script_id(script_name, script_path)
                    else:
                        # Get manifest_path for download operations
                        _, manifest_path_for_download = self._get_manifest_script_id(script_name, script_path)
                    
                    if manifest_script_id:
                        # CENTRALIZED: Check cache status using single source of truth
                        is_cached = self._is_script_cached(script_id=manifest_script_id, script_path=script_path, category=self.current_tab)
                        
                        if is_cached:
                            # Script is cached - offer removal and update options
                            update_item = Gtk.MenuItem(label="🔄 Update Script")
                            update_item.connect("activate", lambda w: self._update_single_script(manifest_script_id, script_name, manifest_path_for_download))
                            menu.append(update_item)
                            
                            remove_item = Gtk.MenuItem(label="🗑️ Remove from Cache")
                            remove_item.connect("activate", lambda w: self._remove_script_from_cache(manifest_script_id, script_name, script_path))
                            menu.append(remove_item)
                        else:
                            # Script not cached - offer download
                            download_item = Gtk.MenuItem(label="⬇️ Download to Cache")
                            download_item.connect("activate", lambda w: self._download_single_script(manifest_script_id, script_name, manifest_path_for_download))
                            menu.append(download_item)
                    else:
                        # Not a manifest script, no repository options
                        return False
                else:
                    # Repository not available
                    return False
            
            if menu.get_children():  # Only show menu if it has items
                menu.show_all()
                menu.popup_at_pointer(event)
                return True
        
        return False
    
    def _edit_custom_script(self, script_id):
        """Show dialog to edit an existing custom script"""
        script = self.custom_script_manager.get_script_by_id(script_id)
        if not script:
            self.show_error_dialog("Script not found")
            return
        
        dialog = Gtk.Dialog(title="Edit Custom Script", parent=self, flags=0)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(500, 400)
        
        box = dialog.get_content_area()
        box.set_border_width(12)
        box.set_spacing(12)
        
        # Script Name
        name_label = Gtk.Label(label="Script Name:", xalign=0)
        box.pack_start(name_label, False, False, 0)
        
        name_entry = Gtk.Entry()
        name_entry.set_text(script['name'])
        box.pack_start(name_entry, False, False, 0)
        
        # Script Path
        path_label = Gtk.Label(label="Script Path:", xalign=0)
        box.pack_start(path_label, False, False, 0)
        
        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        path_entry = Gtk.Entry()
        path_entry.set_text(script['script_path'])
        path_entry.set_hexpand(True)
        path_box.pack_start(path_entry, True, True, 0)
        
        browse_button = Gtk.Button(label="Browse...")
        browse_button.connect("clicked", lambda b: self._browse_for_script(path_entry))
        path_box.pack_start(browse_button, False, False, 0)
        box.pack_start(path_box, False, False, 0)
        
        # Description
        desc_label = Gtk.Label(label="Description (Markdown supported):", xalign=0)
        box.pack_start(desc_label, False, False, 0)
        
        desc_scroll = Gtk.ScrolledWindow()
        desc_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        desc_scroll.set_min_content_height(150)
        
        desc_buffer = Gtk.TextBuffer()
        desc_buffer.set_text(script['description'])
        desc_view = Gtk.TextView(buffer=desc_buffer)
        desc_view.set_wrap_mode(Gtk.WrapMode.WORD)
        desc_scroll.add(desc_view)
        box.pack_start(desc_scroll, True, True, 0)
        
        # Requires sudo checkbox
        sudo_check = Gtk.CheckButton(label="Requires sudo privileges")
        sudo_check.set_active(script['requires_sudo'])
        box.pack_start(sudo_check, False, False, 0)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            name = name_entry.get_text().strip()
            script_path = path_entry.get_text().strip()
            start_iter, end_iter = desc_buffer.get_bounds()
            description = desc_buffer.get_text(start_iter, end_iter, True)
            requires_sudo = sudo_check.get_active()
            
            # Validate inputs
            if not name:
                self.show_error_dialog("Script name cannot be empty")
            elif not script_path:
                self.show_error_dialog("Script path cannot be empty")
            elif not os.path.isfile(script_path):
                self.show_error_dialog(f"Script file not found: {script_path}")
            elif not os.access(script_path, os.X_OK):
                self.show_error_dialog(f"Script is not executable: {script_path}")
            else:
                # Update the script
                self.custom_script_manager.update_script(
                    script_id,
                    name=name,
                    script_path=script_path,
                    description=description,
                    requires_sudo=requires_sudo
                )
                # Refresh the current tab
                self._refresh_tab(script['category'])
        
        dialog.destroy()
    
    def _delete_custom_script(self, script_id):
        """Delete a custom script after confirmation"""
        script = self.custom_script_manager.get_script_by_id(script_id)
        if not script:
            return
        
        # Confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete '{script['name']}'?",
        )
        dialog.format_secondary_text(
            "This will remove the script from the menu. "
            "The actual script file will not be deleted."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.custom_script_manager.delete_script(script_id)
            self._refresh_tab(script['category'])

    # ========================================================================
    # SCRIPT CACHE OPERATIONS (Download/Update/Remove)
    # ========================================================================

    def _download_single_script(self, script_id, script_name, manifest_path=None):
        """Download a single script to cache"""
        if not self.repository:
            return
        
        self.terminal.feed(f"\r\n\x1b[33m[*] Downloading {script_name} to cache...\x1b[0m\r\n".encode())
        
        try:
            # Debug: Show what we're passing
            if manifest_path:
                self.terminal.feed(f"\x1b[36m[DEBUG] Using custom manifest: {manifest_path}\x1b[0m\r\n".encode())
            self.terminal.feed(f"\x1b[36m[DEBUG] Script ID: {script_id}\x1b[0m\r\n".encode())
            
            result = self.repository.download_script(script_id, manifest_path=manifest_path)
            success = result[0] if isinstance(result, tuple) else result
            url = result[1] if isinstance(result, tuple) and len(result) > 1 else None
            
            if success:
                if url:
                    self.terminal.feed(f"\x1b[36m[*] URL: {url}\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[32m[✓] Successfully downloaded {script_name}\x1b[0m\r\n".encode())
                # Refresh UI silently to avoid verbose output
                GLib.timeout_add(500, self._refresh_ui_silent)
            else:
                if url:
                    self.terminal.feed(f"\x1b[33m[!] Attempted URL: {url}\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[31m[✗] Failed to download {script_name}\x1b[0m\r\n".encode())
                # Check logs for more info
                self.terminal.feed(f"\x1b[33m[!] Check ~/.lv_linux_learn/logs/repository.log for details\x1b[0m\r\n".encode())
        except Exception as e:
            if "Checksum verification failed" in str(e):
                self.terminal.feed(f"\x1b[31m[✗] Checksum verification failed for {script_name}\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[33m[!] Script may have been updated since manifest was generated\x1b[0m\r\n".encode())
            else:
                self.terminal.feed(f"\x1b[31m[✗] Error downloading {script_name}: {e}\x1b[0m\r\n".encode())
        
        # Auto-complete after short delay
        GLib.timeout_add(1500, self._complete_terminal_operation)

    def _update_single_script(self, script_id, script_name, manifest_path=None):
        """Force update a single cached script"""
        if not self.repository:
            return
        
        self.terminal.feed(f"\r\n\x1b[33m[*] Updating {script_name}...\x1b[0m\r\n".encode())
        
        try:
            # Remove from cache first, then re-download
            cached_path = self.repository.get_cached_script_path(script_id)
            if cached_path and os.path.isfile(cached_path):
                os.remove(cached_path)
            
            result = self.repository.download_script(script_id, manifest_path=manifest_path)
            success = result[0] if isinstance(result, tuple) else result
            url = result[1] if isinstance(result, tuple) and len(result) > 1 else None
            
            if success:
                if url:
                    self.terminal.feed(f"\x1b[36m[*] URL: {url}\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[32m[✓] Successfully updated {script_name}\x1b[0m\r\n".encode())
                # Refresh UI silently
                GLib.timeout_add(500, self._refresh_ui_silent)
            else:
                self.terminal.feed(f"\x1b[31m[✗] Failed to update {script_name}\x1b[0m\r\n".encode())
        except Exception as e:
            if "Checksum verification failed" in str(e):
                self.terminal.feed(f"\x1b[31m[✗] Checksum verification failed for {script_name}\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[33m[!] Script may have been updated since manifest was generated\x1b[0m\r\n".encode())
            else:
                self.terminal.feed(f"\x1b[31m[✗] Error updating {script_name}: {e}\x1b[0m\r\n".encode())
        
        # Auto-complete after short delay
        GLib.timeout_add(1500, self._complete_terminal_operation)

    def _remove_script_from_cache(self, script_id, script_name, script_path=None):
        """Remove a single script from cache after confirmation"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Remove from Cache"
        )
        dialog.format_secondary_text(f"Remove '{script_name}' from local cache?\n\nThe script can be downloaded again later.")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            try:
                # Try to get cached path from repository lookup
                cached_path = self.repository.get_cached_script_path(script_id)
                
                # If repository lookup failed but we have script_path, try to use it directly
                if not cached_path and script_path:
                    # Check if script_path is already the cached path
                    if script_path.startswith(str(self.repository.script_cache_dir)):
                        cached_path = script_path
                    else:
                        # Try to construct cached path from script_path
                        filename = os.path.basename(script_path)
                        # Try common categories
                        for category in ['install', 'tools', 'exercises', 'uninstall']:
                            potential_path = self.repository.script_cache_dir / category / filename
                            if potential_path.exists():
                                cached_path = str(potential_path)
                                break
                
                if cached_path and os.path.isfile(cached_path):
                    os.remove(cached_path)
                    self.terminal.feed(f"\r\n\x1b[32m[✓] Removed {script_name} from cache\x1b[0m\r\n".encode())
                    # Refresh UI silently
                    GLib.timeout_add(500, self._refresh_ui_silent)
                else:
                    self.terminal.feed(f"\r\n\x1b[33m[!] {script_name} was not in cache\x1b[0m\r\n".encode())
            except Exception as e:
                self.terminal.feed(f"\r\n\x1b[31m[✗] Error removing {script_name}: {e}\x1b[0m\r\n".encode())
        
        # Auto-complete after short delay
        GLib.timeout_add(1500, self._complete_terminal_operation)

    # ========================================================================
    # MENU BAR & DIALOGS
    # ========================================================================

    def _create_menubar(self):
        """Create application menu bar"""
        menubar = Gtk.MenuBar()

        # File Menu
        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="File")
        file_item.set_submenu(file_menu)
        
        # Refresh Manifest Cache
        refresh_manifest_item = Gtk.MenuItem(label="Refresh Manifest")
        refresh_manifest_item.connect("activate", self._on_refresh_manifest_cache)
        file_menu.append(refresh_manifest_item)
        
        # Separator
        separator = Gtk.SeparatorMenuItem()
        file_menu.append(separator)
        
        # Exit
        exit_item = Gtk.MenuItem(label="Exit")
        exit_item.connect("activate", lambda w: self.destroy())
        file_menu.append(exit_item)
        
        menubar.append(file_item)
        
        # Settings Menu
        settings_menu = Gtk.Menu()
        settings_item = Gtk.MenuItem(label="Settings")
        settings_item.set_submenu(settings_menu)
        
        # Repository Settings
        repo_settings_item = Gtk.MenuItem(label="Repository Settings")
        repo_settings_item.connect("activate", lambda w: self._on_repo_settings(None))
        settings_menu.append(repo_settings_item)
        
        menubar.append(settings_item)
        
        # Help Menu  
        help_menu = Gtk.Menu()
        help_item = Gtk.MenuItem(label="Help")
        help_item.set_submenu(help_menu)
        
        # About
        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", lambda w: self._show_about_dialog())
        help_menu.append(about_item)
        
        menubar.append(help_item)
        
        return menubar

    def _refresh_all_script_data(self):
        """Refresh all script data from repository and local sources (background refresh)"""
        try:
            # Reload scripts from manifest with repository configuration
            global _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT
            global SCRIPTS, SCRIPT_NAMES, TOOLS_SCRIPTS, TOOLS_NAMES
            global EXERCISES_SCRIPTS, EXERCISES_NAMES, UNINSTALL_SCRIPTS, UNINSTALL_NAMES
            global DESCRIPTIONS, TOOLS_DESCRIPTIONS, EXERCISES_DESCRIPTIONS, UNINSTALL_DESCRIPTIONS
            
            # Refresh repository's cached config to pick up any changes
            if self.repository:
                self.repository.config = self.repository.load_config()
            
            # Force refresh manifest and reload with repository configuration
            global _SCRIPT_ID_MAP
            _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, _SCRIPT_ID_MAP = load_scripts_from_manifest(self.terminal, self.repository)
            
            # Update global arrays
            SCRIPTS[:] = _SCRIPTS_DICT.get('install', [])
            SCRIPT_NAMES[:] = _NAMES_DICT.get('install', [])
            DESCRIPTIONS[:] = _DESCRIPTIONS_DICT.get('install', [])
            
            TOOLS_SCRIPTS[:] = _SCRIPTS_DICT.get('tools', [])
            TOOLS_NAMES[:] = _NAMES_DICT.get('tools', [])
            TOOLS_DESCRIPTIONS[:] = _DESCRIPTIONS_DICT.get('tools', [])
            
            EXERCISES_SCRIPTS[:] = _SCRIPTS_DICT.get('exercises', [])
            EXERCISES_NAMES[:] = _NAMES_DICT.get('exercises', [])
            EXERCISES_DESCRIPTIONS[:] = _DESCRIPTIONS_DICT.get('exercises', [])
            
            UNINSTALL_SCRIPTS[:] = _SCRIPTS_DICT.get('uninstall', [])
            UNINSTALL_NAMES[:] = _NAMES_DICT.get('uninstall', [])
            UNINSTALL_DESCRIPTIONS[:] = _DESCRIPTIONS_DICT.get('uninstall', [])
            
            # Clear dynamic tabs and repopulate with fresh data
            self._create_dynamic_category_tabs()
            
            # Repopulate all tab stores
            self._repopulate_tab_stores()
            
            # Refresh UI
            if hasattr(self, '_refresh_ui_silent'):
                GLib.timeout_add(100, self._refresh_ui_silent)
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[✗] Error refreshing scripts: {e}\x1b[0m\r\n\r\n".encode())
        
        # No terminal completion needed for background refresh operations
        
        return False  # Remove from GLib timeout

    def _schedule_manifest_auto_refresh(self):
        """Schedule periodic manifest refresh to keep UI tabs current"""
        if not self.repository or not self.repo_config:
            print("[*] Auto-refresh not scheduled: repository or config missing")
            return

        interval_minutes = self.repo_config.get('update_check_interval_minutes', 1)
        try:
            interval_minutes = max(1, int(interval_minutes))
        except Exception:
            interval_minutes = 1

        # Store timeout ID to prevent garbage collection
        self._auto_refresh_timeout_id = GLib.timeout_add_seconds(interval_minutes * 60, self._run_manifest_auto_refresh)
        print(f"[+] Auto-refresh scheduled: interval={interval_minutes} minute(s), timeout_id={self._auto_refresh_timeout_id}", flush=True)

    def _run_manifest_auto_refresh(self):
        """Refresh manifest cache and update all tabs"""
        if not self.repository or not refresh_manifest_cache:
            print("[!] Auto-refresh skipped: missing repository or refresh_manifest_cache")
            return True

        try:
            print("[*] Auto-refresh triggered - refreshing manifest cache...")
            # Refresh manifest cache (public + custom manifests)
            refresh_manifest_cache(manifest_url=DEFAULT_MANIFEST_URL, terminal_callback=None)
            print("[+] Manifest cache refreshed")
            
            # Clear repository's internal manifest cache to force reload from disk
            if hasattr(self.repository, '_manifest_cache'):
                self.repository._manifest_cache = None
            if hasattr(self.repository, '_scripts'):
                self.repository._scripts = None
            print("[+] Repository cache cleared")
            
            # Reload all script data and update UI
            self._refresh_all_script_data()
            print("[+] Script data reloaded")

            # Refresh repository tab/status if available
            if hasattr(self, '_update_repo_status'):
                self._update_repo_status()
            if hasattr(self, '_populate_repository_tree'):
                self._populate_repository_tree()
                print("[+] Repository tree refreshed")
        except Exception as e:
            print(f"[!] Auto-refresh error: {e}", flush=True)

        return True
    
    def _on_refresh_manifest_cache(self, widget=None):
        """Clear manifest cache and fetch fresh from configured URL"""
        self.terminal.feed(b"\x1b[36m[*] Clearing and rebuilding manifest cache...\x1b[0m\r\n")
        
        try:
            # Terminal output callback
            def terminal_output(msg):
                self.terminal.feed(f"{msg}\r\n".encode())
            
            # Use library function to refresh cache
            if refresh_manifest_cache(manifest_url=DEFAULT_MANIFEST_URL, terminal_callback=terminal_output):
                # Reload scripts from fresh manifest
                self.terminal.feed(b"\x1b[36m[*] Reloading scripts...\x1b[0m\r\n")
                self._refresh_all_script_data()
                self.terminal.feed(b"\x1b[32m[+] Manifest cache refreshed successfully\x1b[0m\r\n\r\n")
            else:
                self.terminal.feed(b"\x1b[31m[!] Failed to refresh manifest cache\x1b[0m\r\n\r\n")
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error refreshing manifest: {e}\x1b[0m\r\n\r\n".encode())
        
        # Return to prompt
        self.terminal.feed_child(b"\n")
        return False

    def _show_about_dialog(self):
        """Show about dialog with application information"""
        # Count scripts
        counts = {
            'install': len(SCRIPTS),
            'tools': len(TOOLS_SCRIPTS),
            'exercises': len(EXERCISES_SCRIPTS),
            'uninstall': len(UNINSTALL_SCRIPTS),
            'total': len(SCRIPTS) + len(TOOLS_SCRIPTS) + len(EXERCISES_SCRIPTS) + len(UNINSTALL_SCRIPTS)
        }
        
        # Define sections
        sections = [
            ("LV Script Manager", "title"),
            ("Advanced Ubuntu Linux Setup &amp; Management Utility", "subtitle"),
            ("", "double_spacer"),
            (f"<b>Version:</b> 2.2.2 (Multi-Repository System)   •   <b>Scripts:</b> {counts['total']} total", "info"),
            ("", "spacer"),
            ("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "divider"),
            ("", "double_spacer"),
            ("📋 About", "header"),
            ("This tool provides a modern, GitHub-integrated interface for installing and managing software packages on Ubuntu Linux. It features an advanced caching system, repository management, and streamlined script execution.", "body"),
            ("", "double_spacer"),
            ("🚀 Core Features", "header"),
            ("• <b>GitHub Integration:</b> Scripts hosted on GitHub as Single Source of Truth\n• <b>Smart Caching:</b> Local cache management with selective download/removal\n• <b>Multi-Repository:</b> Support for public and custom script repositories\n• <b>Automatic Updates:</b> Check for script updates and apply selectively\n• <b>Custom Scripts:</b> Add and manage user-defined scripts\n• <b>Terminal Integration:</b> Professional command execution with proper formatting", "body"),
            ("", "double_spacer"),
            ("📦 Available Categories", "header"),
            (f"• <b>Install:</b> {counts['install']} scripts — Development tools, browsers, editors\n• <b>Tools:</b> {counts['tools']} scripts — File extraction, media conversion, utilities\n• <b>Exercises:</b> {counts['exercises']} scripts — Bash learning and practice tools\n• <b>Uninstall:</b> {counts['uninstall']} scripts — Safe removal with complete cleanup", "body"),
            ("", "double_spacer"),
            ("⚙️ Advanced Features", "header"),
            ("• <b>Real-time Status:</b> Live cache indicators (✓ cached, ☁️ not cached)\n• <b>Bulk Operations:</b> Download all, remove all, or select individual scripts\n• <b>Directory Navigation:</b> Intelligent script directory access\n• <b>Search &amp; Filter:</b> Quick filtering across all tabs and categories\n• <b>Multi-Manifest Support:</b> Local and online repository sources", "body"),
            ("", "double_spacer"),
            ("🏗️ Architecture", "header"),
            ("• <b>Source:</b> All scripts hosted on GitHub with manifest.json metadata\n• <b>Cache Location:</b> ~/.lv_linux_learn/script_cache/\n• <b>Interfaces:</b> GUI (menu.py) &amp; CLI (menu.sh) with feature parity", "body"),
            ("", "double_spacer"),
            ("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "divider"),
            ("", "double_spacer"),
            ("👨‍💼 Credits", "header"),
            ("<b>Developer:</b> Adam Matson\n<b>GitHub:</b> <a href='https://github.com/amatson97'>@amatson97</a>\n<b>Repository:</b> <a href='https://github.com/amatson97/lv_linux_learn'>lv_linux_learn</a>\n<b>License:</b> MIT License\n<b>Platform:</b> Ubuntu Desktop 24.04.3 LTS", "body"),
            ("", "double_spacer"),
            ("© 2025 Adam Matson. Built for the Linux learning community.", "footer"),
        ]
        
        # Build markup from sections
        markup_parts = []
        style_map = {
            'title': "<span size='32000' weight='bold'>{}</span>",
            'subtitle': "<span size='large' style='italic'>{}</span>",
            'header': "<span size='large' weight='bold'>{}</span>",
            'body': "<span>{}</span>",
            'info': "<span>{}</span>",
            'divider': "<span>{}</span>",
            'footer': "<span size='small' style='italic'>{}</span>",
            'spacer': "\n",
            'double_spacer': "\n\n",
        }
        
        for content, style_type in sections:
            if style_type in ('spacer', 'double_spacer'):
                markup_parts.append(style_map[style_type])
            else:
                markup_parts.append(style_map[style_type].format(content))
                markup_parts.append("\n")
        
        about_text = "".join(markup_parts)
        
        # Create dialog
        dialog = Gtk.Dialog(title="About LV Script Manager", transient_for=self, modal=True)
        dialog.set_default_size(700, 650)
        dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        
        # Create scrolled label
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_xalign(0)
        label.set_yalign(0)
        label.set_margin_start(24)
        label.set_margin_end(24)
        label.set_margin_top(12)
        label.set_margin_bottom(12)
        label.set_name("about-label")
        label.set_markup(about_text)
        label.connect("activate-link", self.on_link_clicked)
        
        # Apply CSS for white text
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"#about-label { color: #ffffff; }")
        label.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        scroll.add(label)
        dialog.get_content_area().pack_start(scroll, True, True, 0)
        dialog.show_all()
        dialog.run()
        dialog.destroy()


    def _refresh_ui_for_repo_setting(self):
        """Refresh UI when repository setting is toggled"""
        # Remove all tabs except the first few
        num_pages = self.notebook.get_n_pages()
        
        # Remove repository tab if it exists (should be the last main tab)
        for i in range(num_pages - 1, -1, -1):
            page = self.notebook.get_nth_page(i)
            label = self.notebook.get_tab_label(page)
            if label:
                # Handle different label widget types
                label_text = ""
                if hasattr(label, 'get_text'):
                    label_text = label.get_text()
                elif hasattr(label, 'get_label'):
                    label_text = label.get_label()
                
                if "Repository" in label_text:
                    self.notebook.remove_page(i)
                    break
        
        # Add repository tab if now enabled
        if self.repo_enabled:
            repository_box = self._create_repository_tab()
            repository_label = Gtk.Label(label="📥 Repository")
            # Insert before the last position to keep it in the right order
            insert_pos = self.notebook.get_n_pages()
            self.notebook.insert_page(repository_box, repository_label, insert_pos)
            
            # Force the notebook to show all pages and refresh
            self.notebook.show_all()
            
            # Switch to the repository tab to make it visible
            self.notebook.set_current_page(insert_pos)
            
            # Repopulate repository tree to reflect new manifest configuration
            if hasattr(self, 'repo_store'):
                self._populate_repository_tree()
            
        # Update menu item states based on repository status
        if hasattr(self, 'refresh_item'):
            self.refresh_item.set_sensitive(self.repo_enabled)
        
        # Refresh all tab contents to update cache status indicators
        self._repopulate_tab_stores()
        
        # Force a complete UI refresh
        while Gtk.events_pending():
            Gtk.main_iteration()

    def _get_manifest_script_id(self, script_name, script_path):
        """Get script ID and manifest path from manifest for cache operations
        
        Searches both public and custom manifests to find the script.
        Strips source tags like [Public Repository] or [Custom: name] from script name.
        
        Returns: tuple (script_id, manifest_path) or (None, None)
                manifest_path is None for public repo, path string for custom manifests
        """
        if not self.repository:
            return None, None

        # Fast-path: pending cache URI encodes the script id
        try:
            sp = str(script_path)
            if sp.startswith("cache://pending/"):
                return sp.split("/")[-1], None
        except Exception:
            pass
        
        # Strip status icons and source tags from name for matching
        clean_name = script_name
        # Remove status icons
        for icon in ['✓', '☁️', '📁', '❌', '📝']:
            clean_name = clean_name.replace(icon, '').strip()
        
        # Detect source from script name tag
        source_type = None
        if '[Public Repository]' in clean_name:
            source_type = 'public'
            clean_name = clean_name.replace('[Public Repository]', '').strip()
        elif '[Custom:' in clean_name:
            source_type = 'custom'
            # Strip [Custom: anything]
            import re
            clean_name = re.sub(r'\[Custom:.*?\]', '', clean_name).strip()
        
        # Get the script filename from path and possible id from pending path
        script_filename = os.path.basename(script_path)
        pending_id = script_filename if str(script_path).startswith("cache://pending/") else None
        
        # If source is public or unspecified, try public manifest first
        if source_type == 'public' or source_type is None:
            try:
                manifest = self.repository.load_local_manifest()
                if manifest:
                    scripts = manifest.get('scripts', [])
                    # Handle nested format
                    if isinstance(scripts, dict):
                        all_scripts = []
                        for category_scripts in scripts.values():
                            all_scripts.extend(category_scripts)
                        scripts = all_scripts
                    
                    for script in scripts:
                        # Match by id, name or filename
                        if ((pending_id and script.get('id') == pending_id) or
                            (script.get('name') == clean_name) or
                            (script.get('file_name') == script_filename)):
                            # Return with None manifest_path for public repo
                            return script.get('id'), None
            except Exception as e:
                pass
        
        # If source is custom or we haven't found it yet, search custom manifests
        # FIRST: Check custom_manifests in config (these use temp files)
        try:
            config = self.repository.load_config()
            custom_manifests_config = config.get('custom_manifests', {})
            
            for manifest_name, manifest_config in custom_manifests_config.items():
                manifest_data = manifest_config.get('manifest_data')
                if not manifest_data:
                    continue
                
                scripts = manifest_data.get('scripts', {})
                # Handle nested format
                if isinstance(scripts, dict):
                    all_scripts = []
                    for category_scripts in scripts.values():
                        all_scripts.extend(category_scripts)
                    scripts = all_scripts
                
                for script in scripts:
                    # Match by name (with source tag), id, or path
                    script_display_name = f"{script.get('name', '')} [Local: {manifest_name}]"
                    if (script.get('name') == clean_name or
                        script_display_name == script_name or
                        script.get('id') == pending_id):
                        # Return with temp manifest path
                        cache_dir = PathManager.get_config_dir() if PathManager else Path.home() / '.lv_linux_learn'
                        temp_manifest_path = str(cache_dir / f"temp_{manifest_name}_manifest.json")
                        # Ensure temp file exists
                        with open(temp_manifest_path, 'w') as f:
                            json.dump(manifest_data, f, indent=2)
                        return script.get('id'), temp_manifest_path
        except Exception as e:
            print(f"[DEBUG] Error searching config manifests: {e}")
            pass
        
        # THEN: Check filesystem-based custom manifests
        try:
            custom_manifests_dir = PathManager.get_custom_manifests_dir() if PathManager else Path.home() / '.lv_linux_learn' / 'custom_manifests'
            if custom_manifests_dir.exists():
                for manifest_file in custom_manifests_dir.glob('*/manifest.json'):
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest = json.load(f)
                            scripts = manifest.get('scripts', [])
                            # Handle nested format
                            if isinstance(scripts, dict):
                                all_scripts = []
                                for category_scripts in scripts.values():
                                    all_scripts.extend(category_scripts)
                                scripts = all_scripts
                            
                            for script in scripts:
                                # Match by name or filename
                                if (script.get('name') == clean_name or 
                                    script.get('file_name') == script_filename):
                                    # Return with manifest path for custom repo
                                    return script.get('id'), str(manifest_file)
                                # Also try matching by download_url for file:// custom manifests
                                elif script.get('download_url', '').startswith('file://') and script_path in script.get('download_url', ''):
                                    return script.get('id'), str(manifest_file)
                    except Exception:
                        continue
                
                # Also check direct JSON files in custom_manifests
                for manifest_file in custom_manifests_dir.glob('*.json'):
                    if manifest_file.name == 'manifest.json':
                        continue  # Skip if it's a stray manifest.json in root
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest = json.load(f)
                            scripts = manifest.get('scripts', [])
                            # Handle nested format
                            if isinstance(scripts, dict):
                                all_scripts = []
                                for category_scripts in scripts.values():
                                    all_scripts.extend(category_scripts)
                                scripts = all_scripts
                            
                            for script in scripts:
                                # Match by name or filename
                                if (script.get('name') == clean_name or 
                                    script.get('file_name') == script_filename):
                                    return script.get('id'), str(manifest_file)
                                # Also try matching by download_url for file:// custom manifests
                                elif script.get('download_url', '').startswith('file://') and script_path in script.get('download_url', ''):
                                    return script.get('id'), str(manifest_file)
                    except Exception:
                        continue
        except Exception as e:
            pass
        
        return None, None

    def show_error_dialog(self, message):
        """Show error message in terminal instead of dialog"""
        self.terminal.feed(f"\x1b[31m[✗] Error: {message}\x1b[0m\r\n".encode())


# ============================================================================
# APPLICATION INITIALIZATION
# ============================================================================

def on_activate(app):
    # set a default application icon for better GNOME integration (if available)
    assets_dir = Path(__file__).parent / "assets"
    icon_file = assets_dir / "menu_icon.png"
    if icon_file.exists():
        try:
            app.set_default_icon_from_file(str(icon_file))
        except Exception:
            pass

    win = ScriptMenuGTK(app)
    win.show_all()


def main():
    application_id = "com.lv.script_manager"
    app = Gtk.Application(application_id=application_id)
    app.connect("activate", on_activate)
    # run() handles main loop and integrates with the session (startup notification, WM association)
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())