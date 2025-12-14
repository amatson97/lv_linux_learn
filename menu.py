#!/usr/bin/env python3
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
from pathlib import Path
from datetime import datetime
import uuid

# Import repository management
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
try:
    from lib.repository import ScriptRepository, ChecksumVerificationError
except ImportError:
    print("Warning: Repository module not available")
    ScriptRepository = None
    ChecksumVerificationError = Exception

try:
    # optional nicer icons / pixbuf usage if available
    from gi.repository import GdkPixbuf
except Exception:
    GdkPixbuf = None


# ============================================================================
# Custom Script Manager
# ============================================================================

class CustomScriptManager:
    """Manages user-created custom scripts"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.lv_linux_learn'
        self.scripts_dir = self.config_dir / 'scripts'
        self.config_file = self.config_dir / 'custom_scripts.json'
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Create config directories if they don't exist"""
        self.config_dir.mkdir(exist_ok=True)
        self.scripts_dir.mkdir(exist_ok=True)
        if not self.config_file.exists():
            self._save_config({"scripts": []})
    
    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load custom scripts config: {e}")
            return {"scripts": []}
    
    def _save_config(self, config):
        """Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error: Failed to save custom scripts config: {e}")
            return False
    
    def get_scripts(self, category=None):
        """Get all custom scripts, optionally filtered by category"""
        config = self._load_config()
        scripts = config.get("scripts", [])
        if category:
            scripts = [s for s in scripts if s.get("category") == category]
        return scripts
    
    def add_script(self, name, category, script_path, description, requires_sudo=True):
        """Add a new custom script"""
        config = self._load_config()
        
        script_obj = {
            "id": str(uuid.uuid4()),
            "name": name,
            "category": category,
            "script_path": str(script_path),
            "description": description,
            "requires_sudo": requires_sudo,
            "created_date": datetime.now().isoformat(),
            "is_custom": True
        }
        
        config["scripts"].append(script_obj)
        return self._save_config(config)
    
    def update_script(self, script_id, **kwargs):
        """Update an existing custom script"""
        config = self._load_config()
        scripts = config.get("scripts", [])
        
        for script in scripts:
            if script.get("id") == script_id:
                script.update(kwargs)
                return self._save_config(config)
        return False
    
    def delete_script(self, script_id):
        """Delete a custom script"""
        config = self._load_config()
        scripts = config.get("scripts", [])
        
        config["scripts"] = [s for s in scripts if s.get("id") != script_id]
        return self._save_config(config)
    
    def get_script_by_id(self, script_id):
        """Get a single script by ID"""
        scripts = self.get_scripts()
        for script in scripts:
            if script.get("id") == script_id:
                return script
        return None


# ============================================================================
# Script Definitions
# ============================================================================

REQUIRED_PACKAGES = ["bash", "zenity", "sudo"]
# Note: bat package installs as 'batcat' command on Ubuntu/Debian
# We check for 'batcat' command but install 'bat' package
OPTIONAL_PACKAGES = ["bat", "pygmentize", "highlight"]  # For syntax highlighting in View Script
OPTIONAL_COMMANDS = ["batcat", "pygmentize", "highlight"]  # Actual commands to check for

# Manifest configuration (can be overridden by config)
DEFAULT_MANIFEST_URL = "https://raw.githubusercontent.com/amatson97/lv_linux_learn/main/manifest.json"
MANIFEST_URL = os.environ.get('CUSTOM_MANIFEST_URL', DEFAULT_MANIFEST_URL)
MANIFEST_CACHE_DIR = Path.home() / '.lv_linux_learn'
MANIFEST_CACHE_FILE = MANIFEST_CACHE_DIR / 'manifest.json'
MANIFEST_CACHE_MAX_AGE = 3600  # 1 hour in seconds


def fetch_manifest(terminal_widget=None, repository=None):
    """
    Fetch manifest.json from configured repository
    Returns Path to manifest file (cached)
    
    Args:
        terminal_widget: Optional terminal widget to send output to
        repository: Optional repository instance for custom configuration
    """
    # Determine manifest URL - prioritize repository config, then global, then default
    manifest_url = DEFAULT_MANIFEST_URL  # Final fallback
    
    # Check repository config first (most authoritative)
    if repository:
        try:
            config = repository.load_config()
            custom_url = config.get('custom_manifest_url', '').strip()
            if custom_url:
                manifest_url = custom_url
            else:
                # No custom URL in config, use global MANIFEST_URL
                manifest_url = MANIFEST_URL
        except Exception:
            # Config reading failed, use global MANIFEST_URL
            manifest_url = MANIFEST_URL
    else:
        # No repository instance, use global MANIFEST_URL
        manifest_url = MANIFEST_URL
    
    # Ensure cache directory exists
    MANIFEST_CACHE_DIR.mkdir(exist_ok=True)
    
    # Check if cache exists and is recent
    if MANIFEST_CACHE_FILE.exists():
        cache_age = (datetime.now().timestamp() - MANIFEST_CACHE_FILE.stat().st_mtime)
        if cache_age < MANIFEST_CACHE_MAX_AGE:
            return MANIFEST_CACHE_FILE
    
    def terminal_output(msg):
        if terminal_widget:
            # Write directly to terminal output without shell prompt
            terminal_widget.feed(f"{msg}\r\n".encode())
        else:
            print(msg)
    
    # Fetch from configured repository
    terminal_output("[*] Fetching latest manifest from repository...")
    terminal_output(f"[*] Connecting to: {manifest_url}")
    try:
        with urllib.request.urlopen(manifest_url, timeout=10) as response:
            terminal_output(f"[*] Connection successful (HTTP {response.getcode()})")
            manifest_data = response.read()
            terminal_output(f"[*] Downloaded {len(manifest_data)} bytes")
        
        # Save to cache
        with open(MANIFEST_CACHE_FILE, 'wb') as f:
            f.write(manifest_data)
        
        terminal_output(f"[*] Cached to: {MANIFEST_CACHE_FILE}")
        terminal_output("[+] Manifest updated successfully")
        return MANIFEST_CACHE_FILE
        
    except urllib.error.URLError as e:
        terminal_output(f"[!] Failed to fetch manifest from repository: {e}")
        if MANIFEST_CACHE_FILE.exists():
            terminal_output("[*] Using cached manifest")
            return MANIFEST_CACHE_FILE
        raise Exception("No manifest available (cannot fetch and no cache exists)")
    except Exception as e:
        terminal_output(f"[!] Error fetching manifest: {e}")
        if MANIFEST_CACHE_FILE.exists():
            terminal_output("[*] Using cached manifest")
            return MANIFEST_CACHE_FILE
        raise


def load_scripts_from_manifest(terminal_widget=None, repository=None):
    """
    Load scripts dynamically from manifest.json (fetched from repository)
    Returns: tuple of (scripts_dict, names_dict, descriptions_dict)
    Each dict has keys: 'install', 'tools', 'exercises', 'uninstall'
    
    Args:
        terminal_widget: Optional terminal widget to send output to
        repository: Optional repository instance for custom configuration
    """
    # Initialize empty structures
    scripts = {'install': [], 'tools': [], 'exercises': [], 'uninstall': []}
    names = {'install': [], 'tools': [], 'exercises': [], 'uninstall': []}
    descriptions = {'install': [], 'tools': [], 'exercises': [], 'uninstall': []}
    
    def terminal_output(msg):
        if terminal_widget:
            # Write directly to terminal output without shell prompt
            terminal_widget.feed(f"{msg}\r\n".encode())
        else:
            print(msg)
    
    try:
        # Fetch manifest from configured repository (uses cache if recent)
        manifest_path = fetch_manifest(terminal_widget, repository)
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Display manifest information
        version = manifest.get('version', 'unknown')
        repo_version = manifest.get('repository_version', 'unknown')
        last_updated = manifest.get('last_updated', 'unknown')
        total_scripts = len(manifest.get('scripts', []))
        
        terminal_output(f"[*] Loaded manifest version {version} (repo: {repo_version})")
        terminal_output(f"[*] Last updated: {last_updated}")
        terminal_output(f"[*] Processing {total_scripts} scripts...")
        
        # Initialize repository for cache management
        from lib.repository import ScriptRepository, ChecksumVerificationError
        repository = ScriptRepository()
        
        # Track scripts per category and cache status
        category_counts = {'install': 0, 'tools': 0, 'exercises': 0, 'uninstall': 0}
        cached_counts = {'install': 0, 'tools': 0, 'exercises': 0, 'uninstall': 0}
        
        # Group scripts by category and use cached paths when available
        for script in manifest.get('scripts', []):
            category = script.get('category', 'tools')
            if category not in scripts:
                continue
            
            script_id = script.get('id')
            cached_path = repository.get_cached_script_path(script_id) if script_id else None
            
            # Use cached path if available, otherwise fall back to relative path
            if cached_path:
                scripts[category].append(cached_path)
                cached_counts[category] += 1
                status_indicator = "✓ "
            else:
                # Fall back to relative path (local filesystem)
                scripts[category].append(script.get('relative_path', ''))
                status_indicator = "☁️ "
            
            names[category].append(f"{status_indicator}{script.get('name', '')}")
            category_counts[category] += 1
            
            # Build description markup with cache status
            desc = f"<b>{script.get('name', 'Unknown')}</b>\n"
            if cached_path:
                desc += f"Script: <tt>{cached_path}</tt> (cached)\n\n"
            else:
                desc += f"Script: <tt>{script.get('relative_path', '')}</tt> (local)\n\n"
            desc += script.get('description', 'No description available')
            descriptions[category].append(desc)
        
        # Display category breakdown with cache status
        terminal_output("[*] Script breakdown:")
        total_cached = sum(cached_counts.values())
        total_scripts_actual = sum(category_counts.values())
        
        for category, count in category_counts.items():
            if count > 0:
                cached = cached_counts[category]
                terminal_output(f"    {category.capitalize()}: {count} scripts ({cached} cached)")
        
        terminal_output(f"[*] Cache status: {total_cached}/{total_scripts_actual} scripts cached")
        if total_cached < total_scripts_actual:
            terminal_output("[!] Some scripts not cached - use 'Download All Scripts' to cache them")
        
        return scripts, names, descriptions
        
    except Exception as e:
        if terminal_widget:
            terminal_widget.feed(f"Error loading manifest.json: {e}\r\n".encode())
        else:
            print(f"Error loading manifest.json: {e}")
        return scripts, names, descriptions


# Load scripts from manifest.json (single source of truth)
# Note: Global loading doesn't use terminal widget (goes to stdout)
# Try to initialize with repository for custom configuration
try:
    from lib.repository import ScriptRepository
    _temp_repo = ScriptRepository()
    _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT = load_scripts_from_manifest(repository=_temp_repo)
except Exception:
    # Fallback to default loading if repository initialization fails
    _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT = load_scripts_from_manifest()

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

class ScriptMenuGTK(Gtk.ApplicationWindow):
    def __init__(self, app):
        global MANIFEST_URL
        # Use ApplicationWindow so GNOME/WM can associate the window with the Gtk.Application.
        Gtk.ApplicationWindow.__init__(self, application=app, title="LV Script Manager")
        self.set_default_size(1150, 1165)
        # Set minimum size to ensure usability
        self.set_size_request(800, 600)
        self.set_border_width(12)
        self.set_resizable(True)
        
        # Initialize custom script manager
        self.custom_manager = CustomScriptManager()
        
        # Initialize repository system
        self.repository = None
        self.repo_enabled = False
        if ScriptRepository:
            try:
                self.repository = ScriptRepository()
                self.repo_config = self.repository.load_config()
                self.repo_enabled = self.repo_config.get('use_remote_scripts', True)
                
                # Load custom manifest URL if configured
                custom_url = self.repo_config.get('custom_manifest_url', '')
                if custom_url and (custom_url.startswith('http://') or custom_url.startswith('https://')):
                    os.environ['CUSTOM_MANIFEST_URL'] = custom_url
                    global MANIFEST_URL
                    MANIFEST_URL = custom_url
                    
                # Check for updates in background if enabled
                if self.repo_enabled and self.repo_config.get('auto_check_updates', True):
                    GLib.idle_add(self._check_updates_background)
            except Exception as e:
                print(f"Warning: Failed to initialize repository: {e}")

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

        # Create notebook (tabs)
        self.notebook = Gtk.Notebook()
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        top_box.pack_start(self.notebook, True, True, 0)

        # Create Install tab
        install_box = self._create_script_tab(SCRIPTS, DESCRIPTIONS, "install")
        install_tab_label = self._create_tab_label("📦 Install", "install")
        self.notebook.append_page(install_box, install_tab_label)

        # Create Tools tab
        tools_box = self._create_script_tab(TOOLS_SCRIPTS, TOOLS_DESCRIPTIONS, "tools")
        tools_tab_label = self._create_tab_label("🔧 Tools", "tools")
        self.notebook.append_page(tools_box, tools_tab_label)

        # Create Exercises tab
        exercises_box = self._create_script_tab(EXERCISES_SCRIPTS, EXERCISES_DESCRIPTIONS, "exercises")
        exercises_tab_label = self._create_tab_label("📚 Exercises", "exercises")
        self.notebook.append_page(exercises_box, exercises_tab_label)

        # Create Uninstall tab
        uninstall_box = self._create_script_tab(UNINSTALL_SCRIPTS, UNINSTALL_DESCRIPTIONS, "uninstall")
        uninstall_tab_label = self._create_tab_label("⚠️ Uninstall", "uninstall")
        self.notebook.append_page(uninstall_box, uninstall_tab_label)
        
        # Create Repository tab (if enabled)
        if self.repo_enabled:
            repository_box = self._create_repository_tab()
            repository_label = Gtk.Label(label="📥 Repository")
            self.notebook.append_page(repository_box, repository_label)

        # Add top section to paned widget
        main_paned.pack1(top_box, True, True)

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
        self.terminal.set_scrollback_lines(10000)
        self.terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
        
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
        
        terminal_frame.add(terminal_box)
        
        # Add sections to paned widget
        main_paned.pack1(top_box, True, False)
        main_paned.pack2(terminal_frame, False, True)
        main_paned.set_position(339)  # User's preferred divider position

        # Track current tab
        self.current_tab = "install"
        self.notebook.connect("switch-page", self.on_tab_switched)

        # wire search -> both filters
        self.header_search.connect("search-changed", self.on_search_changed)

        # Initialize terminal with bash shell
        GLib.idle_add(self._init_terminal)

        # Check required packages on launch
        GLib.idle_add(self.check_required_packages)

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

    def _create_script_tab(self, scripts, descriptions, tab_name):
        """Create a tab with script list and description panel"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        main_box.set_border_width(12)

        # Get the appropriate names array
        if tab_name == "install":
            names = SCRIPT_NAMES
        elif tab_name == "tools":
            names = TOOLS_NAMES
        elif tab_name == "exercises":
            names = EXERCISES_NAMES
        else:
            names = UNINSTALL_NAMES

        # store: display name, full path, description, is_custom (bool), script_id (str)
        liststore = Gtk.ListStore(str, str, str, bool, str)
        
        # Add built-in scripts
        for i, script_path in enumerate(scripts):
            liststore.append([names[i], script_path, descriptions[i], False, ""])
        
        # Add custom scripts for this category
        custom_scripts = self.custom_manager.get_scripts(tab_name)
        for script in custom_scripts:
            display_name = f"📝 {script['name']}"  # Icon to indicate custom script
            liststore.append([
                display_name,
                script['script_path'],
                script['description'],
                True,  # is_custom
                script['id']  # script_id for edit/delete
            ])

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
        else:
            self.uninstall_liststore = liststore
            self.uninstall_filter = filter_model

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
        
        column = Gtk.TreeViewColumn(column_header, renderer, text=0)
        treeview.append_column(column)
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
        else:
            self.uninstall_treeview = treeview

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
        else:
            self.uninstall_description_label = description_label

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
        else:
            self.uninstall_view_button = view_button
            self.uninstall_cd_button = cd_button
            self.uninstall_run_button = run_button

        return main_box

    def on_tab_switched(self, notebook, page, page_num):
        """Handle tab switching"""
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
            return  # About tab, no filter needed
        
        # Reapply search filter
        self.on_search_changed(self.header_search)
        
        # Auto-select first item if nothing is selected
        selection = treeview.get_selection()
        if selection.count_selected_rows() == 0:
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
        else:
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

    def _create_tab_label(self, label_text, category):
        """Create a tab label with a '+' button for adding custom scripts"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        label = Gtk.Label(label=label_text)
        box.pack_start(label, True, True, 0)
        
        # Add '+' button for custom scripts (not for About tab)
        if category in ["install", "tools", "exercises", "uninstall"]:
            add_button = Gtk.Button()
            add_button.set_label("+")
            add_button.set_relief(Gtk.ReliefStyle.NONE)
            add_button.set_tooltip_text(f"Add custom script to {label_text}")
            add_button.connect("clicked", self.on_add_custom_script, category)
            box.pack_start(add_button, False, False, 0)
        
        box.show_all()
        return box

    def _create_help_tab(self):
        """Create About tab"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_border_width(20)
        
        # Scrollable container for content
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        
        # Create a viewport to hold the label (required for proper scrolling)
        viewport = Gtk.Viewport()
        
        # Content label with markup
        content = Gtk.Label()
        content.set_use_markup(True)
        content.set_line_wrap(True)
        content.set_xalign(0)
        content.set_yalign(0)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        
        # Get dynamic script counts
        install_count = len(SCRIPTS)
        tools_count = len(TOOLS_SCRIPTS)
        exercises_count = len(EXERCISES_SCRIPTS)
        uninstall_count = len(UNINSTALL_SCRIPTS)
        total_count = install_count + tools_count + exercises_count + uninstall_count
        
        about_text = (
            "<big><b>Linux Learning Setup Tool</b></big>\n"
            "<i>Advanced Ubuntu Linux Setup &amp; Management Utility</i>\n\n"
            f"<b>Version:</b> 2.0.0 (GitHub SOT Architecture)\n"
            f"<b>Repository:</b> lv_linux_learn ({total_count} total scripts)\n\n"
            "<span size='large'><b>About</b></span>\n\n"
            "This tool provides a modern, GitHub-integrated interface for installing and managing "
            "software packages on Ubuntu Linux. It features an advanced caching system, "
            "repository management, and streamlined script execution with enhanced user experience.\n\n"
            "<b>🚀 Core Features:</b>\n"
            "  • <b>GitHub Integration:</b> Scripts hosted on GitHub as Single Source of Truth\n"
            "  • <b>Smart Caching:</b> Local cache management with selective download/removal\n"
            "  • <b>Enhanced Repository Tab:</b> Browse, search, and manage all available scripts\n"
            "  • <b>Automatic Updates:</b> Check for script updates and apply selectively\n"
            "  • <b>Custom Scripts:</b> Add and manage user-defined scripts\n"
            "  • <b>Clean Terminal Integration:</b> Professional command execution with proper formatting\n\n"
            "<b>📦 Application Categories:</b>\n"
            f"  • <b>Install ({install_count} scripts):</b> Development tools, browsers, editors, package managers\n"
            f"  • <b>Tools ({tools_count} scripts):</b> File extraction, media conversion, system utilities\n"
            f"  • <b>Exercises ({exercises_count} scripts):</b> Bash learning scripts and practice tools\n"
            f"  • <b>Uninstall ({uninstall_count} scripts):</b> Safe removal with complete cleanup\n\n"
            "<b>🔧 Advanced Features:</b>\n"
            "  • <b>Secure API Key Storage:</b> Fernet AES-128 encryption with PBKDF2\n"
            "  • <b>Path Resolution:</b> Automatic includes symlinks with filesystem fallbacks\n"
            "  • <b>Real-time Status:</b> Live cache indicators (✓ cached, ☁️ not cached)\n"
            "  • <b>Bulk Operations:</b> Download all, remove all, or select individual scripts\n"
            "  • <b>Directory Navigation:</b> Intelligent script directory access\n"
            "  • <b>Search Functionality:</b> Filter scripts across all tabs\n\n"
            "<span size='large'><b>Architecture</b></span>\n\n"
            "<b>GitHub as SOT:</b> All scripts are hosted on GitHub with manifest.json for metadata\n"
            "<b>Local Cache:</b> ~/.lv_linux_learn/script_cache/ with organized subdirectories\n"
            "<b>Dual Interface:</b> GUI (menu.py) and CLI (menu.sh) with feature parity\n"
            "<b>Security:</b> Encrypted storage for sensitive data, safe script execution\n\n"
            "<span size='large'><b>Credits</b></span>\n\n"
            "<b>Developer:</b> Adam Matson\n"
            "<b>GitHub:</b> <a href='https://github.com/amatson97'>@amatson97</a>\n"
            "<b>Repository:</b> <a href='https://github.com/amatson97/lv_linux_learn'>lv_linux_learn</a>\n\n"
            "<b>Target Platform:</b> Ubuntu Desktop 24.04.3 LTS\n"
            "<b>Dependencies:</b> Python 3.10+, GTK3, VTE, cryptography\n\n"
            "<span size='large'><b>License &amp; Support</b></span>\n\n"
            "Open source under MIT License. For issues, features, or contributions:\n"
            "Visit the GitHub repository or check the comprehensive documentation.\n\n"
            "<small><i>© 2025 Adam Matson. Built for the Linux learning community.</i></small>"
        )
        
        content.set_markup(about_text)
        content.connect("activate-link", self.on_link_clicked)
        
        # Add label to viewport, then viewport to scroll
        viewport.add(content)
        scroll.add(viewport)
        box.pack_start(scroll, True, True, 0)
        
        return box

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
        # Also filter repository tab if it exists
        if hasattr(self, 'repo_filter'):
            self.repo_filter.refilter()
        # Also filter repository tab if it exists
        if hasattr(self, 'repo_filter'):
            self.repo_filter.refilter()

    def command_exists(self, cmd):
        from shutil import which
        return which(cmd) is not None

    def show_install_prompt(self, missing_pkgs):
        """Prompt user to install missing required packages"""
        pkg_list = ", ".join(missing_pkgs)
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Missing Required Packages",
        )
        dialog.format_secondary_text(
            f"The following packages are required for this application:\n\n{pkg_list}\n\n"
            "Would you like to install them now?\n"
            "(Installation will be shown in the terminal below)"
        )
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            self.install_packages_in_terminal(missing_pkgs, required=True)
        else:
            # User declined install, warn and exit
            warn = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Cannot continue without required packages. Exiting.",
            )
            warn.run()
            warn.destroy()
            Gtk.main_quit()
            sys.exit(1)
    
    def show_optional_packages_info(self, missing_optional):
        """Inform user about missing optional packages"""
        pkg_list = ", ".join(missing_optional)
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Optional Packages Available",
        )
        dialog.format_secondary_text(
            f"The following optional packages can enhance your experience:\n\n{pkg_list}\n\n"
            "These provide syntax highlighting when viewing scripts.\n\n"
            "Would you like to install them now?\n"
            "(Installation will be shown in the terminal below)"
        )
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            self.install_packages_in_terminal(missing_optional, required=False)

    # ========================================================================
    # Repository Management Methods
    # ========================================================================
    
    def _create_repository_tab(self):
        """Create the repository management tab"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        
        # Header with status
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.repo_status_label = Gtk.Label()
        self._update_repo_status()
        header_box.pack_start(self.repo_status_label, False, False, 0)
        
        # Control buttons - Row 1: Bulk Operations
        button_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        update_all_btn = Gtk.Button(label="Refresh & Update")
        update_all_btn.connect("clicked", self._on_update_all_scripts)
        button_box1.pack_start(update_all_btn, False, False, 0)
        
        check_updates_btn = Gtk.Button(label="Check for Updates")
        check_updates_btn.connect("clicked", self._on_check_updates)
        button_box1.pack_start(check_updates_btn, False, False, 0)
        
        download_all_btn = Gtk.Button(label="Download All")
        download_all_btn.connect("clicked", self._on_download_all)
        button_box1.pack_start(download_all_btn, False, False, 0)
        
        clear_cache_btn = Gtk.Button(label="Remove All")
        clear_cache_btn.connect("clicked", self._on_clear_cache)
        button_box1.pack_start(clear_cache_btn, False, False, 0)
        
        # Control buttons - Row 2: Selection Operations
        button_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        select_all_btn = Gtk.Button(label="Select All")
        select_all_btn.connect("clicked", self._on_select_all)
        button_box2.pack_start(select_all_btn, False, False, 0)
        
        select_none_btn = Gtk.Button(label="Select None")
        select_none_btn.connect("clicked", self._on_select_none)
        button_box2.pack_start(select_none_btn, False, False, 0)
        
        invert_selection_btn = Gtk.Button(label="Invert Selection")
        invert_selection_btn.connect("clicked", self._on_invert_selection)
        button_box2.pack_start(invert_selection_btn, False, False, 0)
        
        button_box2.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 5)
        
        install_selected_btn = Gtk.Button(label="Download Selected")
        install_selected_btn.get_style_context().add_class("suggested-action")
        install_selected_btn.connect("clicked", self._on_download_selected)
        button_box2.pack_start(install_selected_btn, False, False, 0)
        
        remove_selected_btn = Gtk.Button(label="Remove Selected")
        remove_selected_btn.get_style_context().add_class("destructive-action")
        remove_selected_btn.connect("clicked", self._on_remove_selected)
        button_box2.pack_start(remove_selected_btn, False, False, 0)
        
        header_box.pack_end(button_box1, False, False, 0)
        
        vbox.pack_start(header_box, False, False, 0)
        vbox.pack_start(button_box2, False, False, 0)
        
        # Scripts list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Store: selected(bool), id(str), name(str), version(str), status(str), category(str), size(str), modified(str)
        self.repo_store = Gtk.ListStore(bool, str, str, str, str, str, str, str)
        
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
    
    def _update_repo_status(self):
        """Update repository status label"""
        if not self.repository:
            return
        
        try:
            total = len(self.repository.parse_manifest())
            cached = self.repository.count_cached_scripts()
            updates = len(self.repository.list_available_updates())
            
            status_text = f"<b>Repository Status:</b>  Total: {total}  |  Cached: {cached}  |  Updates: {updates}"
            self.repo_status_label.set_markup(status_text)
        except Exception as e:
            self.repo_status_label.set_markup(f"<b>Status:</b> Error - {e}")
    
    def _populate_repository_tree(self):
        """Populate repository tree view with enhanced information"""
        if not self.repository:
            return
        
        self.repo_store.clear()
        
        try:
            scripts = self.repository.parse_manifest()
            
            for script in scripts:
                script_id = script.get('id')
                name = script.get('name')
                version = script.get('version')
                category = script.get('category', 'tools')
                file_name = script.get('file_name', '')
                
                # Determine cache status
                status = self.repository.get_script_status(file_name)
                status_text = {
                    'cached': '✓ Cached',
                    'outdated': '📥 Update Available', 
                    'not_installed': '☁️ Not Cached'
                }.get(status, 'Unknown')
                
                # Get cached file info if available
                cached_path = self.repository.get_cached_script_path(script_id)
                if cached_path:
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
                
                # Add to store: [selected, id, name, version, status, category, size, modified]
                self.repo_store.append([
                    False,  # checkbox not selected by default
                    script_id, 
                    name, 
                    version, 
                    status_text, 
                    category.capitalize(),
                    size_text,
                    modified_text
                ])
                
        except Exception as e:
            print(f"Error populating repository tree: {e}")
    
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
        
        self.terminal.feed(b"\x1b[2J\x1b[H")  # Clear screen and move cursor to top
        self.terminal.feed(b"\x1b[32m[*] Updating all cached scripts...\x1b[0m\r\n")
        
        try:
            # Refresh manifest with terminal output
            load_scripts_from_manifest(terminal_widget=self.terminal)
            
            updated, failed = self.repository.update_all_scripts()
            self.terminal.feed(f"\x1b[32m[*] Update complete: {updated} updated, {failed} failed\x1b[0m\r\n".encode())
            
            # Auto-complete after short delay
            GLib.timeout_add(1500, self._complete_terminal_operation)
            
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
        
        self.terminal.feed(b"\x1b[2J\x1b[H")  # Clear screen and move cursor to top
        self.terminal.feed(b"\x1b[32m[*] Checking for updates...\x1b[0m\r\n")
        
        try:
            update_count = self.repository.check_for_updates()
            self.terminal.feed(f"\x1b[32m[*] Found {update_count} updates available\x1b[0m\r\n".encode())
            
            # Auto-complete after short delay
            GLib.timeout_add(1500, self._complete_terminal_operation)
            
            # Refresh display
            self._update_repo_status()
            self._populate_repository_tree()
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            GLib.timeout_add(1500, self._complete_terminal_operation)
    
    def _complete_terminal_operation(self):
        """Auto-complete terminal operation and show completion message"""
        self.terminal.feed(b"\x1b[32m[*] Operation completed. Terminal ready.\x1b[0m\r\n")
        # Send newline to complete the current command and return to prompt
        self.terminal.feed_child(b"\n")
        # Return False to stop the timeout from repeating
        return False
    
    def _complete_directory_navigation(self):
        """Complete directory navigation silently (pwd output confirms success)"""
        # Just send newline to complete the command - no additional message needed
        # since pwd already confirms successful navigation
        self.terminal.feed_child(b"\n")
        # Return False to stop the timeout from repeating
        return False
    
    def _on_download_all(self, button):
        """Download all scripts from repository"""
        if not self.repository:
            return
        
        # Confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Download All Scripts"
        )
        
        total = len(self.repository.parse_manifest())
        dialog.format_secondary_text(
            f"This will download all {total} scripts to the cache.\n\n"
            "This may take a few minutes. Continue?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        self.terminal.feed(b"\x1b[2J\x1b[H")  # Clear screen and move cursor to top
        self.terminal.feed(f"\x1b[32m[*] Downloading all {total} scripts...\x1b[0m\r\n".encode())
        
        try:
            downloaded, failed = self.repository.download_all_scripts()
            self.terminal.feed(f"\x1b[32m[*] Download complete: {downloaded} downloaded, {failed} failed\x1b[0m\r\n".encode())
            
            # Auto-complete after short delay
            GLib.timeout_add(1500, self._complete_terminal_operation)
            
            # Refresh display
            self._update_repo_status()
            self._populate_repository_tree()
            
            # Reload main tabs to reflect changes
            self._reload_main_tabs()
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
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
            self.repository.clear_cache()
            self.terminal.feed(b"\x1b[2J\x1b[H")  # Clear screen and move cursor to top
            self.terminal.feed(b"\x1b[32m[*] Cache cleared successfully\x1b[0m\r\n")
            
            # Auto-complete after short delay
            GLib.timeout_add(1500, self._complete_terminal_operation)
            
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
        use_remote = Gtk.CheckButton(label="Use remote scripts")
        use_remote.set_active(self.repo_config.get('use_remote_scripts', True))
        content.pack_start(use_remote, False, False, 0)
        
        auto_check = Gtk.CheckButton(label="Auto-check for updates")
        auto_check.set_active(self.repo_config.get('auto_check_updates', True))
        content.pack_start(auto_check, False, False, 0)
        
        auto_install = Gtk.CheckButton(label="Auto-install updates")
        auto_install.set_active(self.repo_config.get('auto_install_updates', True))
        content.pack_start(auto_install, False, False, 0)
        
        # Security settings section
        security_separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content.pack_start(security_separator, False, False, 5)
        
        security_label = Gtk.Label()
        security_label.set_markup("<b>Security Settings</b>")
        security_label.set_xalign(0)
        content.pack_start(security_label, False, False, 0)
        
        verify_checksums = Gtk.CheckButton(label="Verify script checksums (recommended)")
        verify_checksums.set_active(self.repo_config.get('verify_checksums', True))
        verify_checksums.set_tooltip_text("Verify downloaded scripts match expected checksums for security. Disable only for custom repositories with incorrect checksums.")
        content.pack_start(verify_checksums, False, False, 0)
        
        interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        interval_label = Gtk.Label(label="Check interval (minutes):")
        interval_spin = Gtk.SpinButton()
        interval_spin.set_range(1, 1440)
        interval_spin.set_increments(1, 10)
        interval_spin.set_value(self.repo_config.get('update_check_interval_minutes', 30))
        interval_box.pack_start(interval_label, False, False, 0)
        interval_box.pack_start(interval_spin, False, False, 0)
        content.pack_start(interval_box, False, False, 0)
        
        # Manifest URL configuration
        manifest_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        manifest_label = Gtk.Label(label="Manifest URL:")
        manifest_label.set_xalign(0)
        manifest_entry = Gtk.Entry()
        # Show the currently active manifest URL (could be custom or default)
        current_manifest_url = self.repo_config.get('custom_manifest_url', '').strip()
        if not current_manifest_url:
            current_manifest_url = DEFAULT_MANIFEST_URL
        manifest_entry.set_text(current_manifest_url)
        manifest_entry.set_placeholder_text("Enter custom manifest URL or leave for default")
        manifest_box.pack_start(manifest_label, False, False, 0)
        manifest_box.pack_start(manifest_entry, False, False, 0)
        
        # Reset button for manifest URL
        reset_manifest_btn = Gtk.Button(label="Reset to Default")
        reset_manifest_btn.connect("clicked", lambda btn: manifest_entry.set_text(DEFAULT_MANIFEST_URL))
        manifest_box.pack_start(reset_manifest_btn, False, False, 0)
        
        content.pack_start(manifest_box, False, False, 0)
        
        dialog.show_all()
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Check if use_remote_scripts setting changed
            old_repo_enabled = self.repo_enabled
            new_repo_enabled = use_remote.get_active()
            
            # Save settings
            self.repo_config['use_remote_scripts'] = new_repo_enabled
            self.repo_config['auto_check_updates'] = auto_check.get_active()
            self.repo_config['auto_install_updates'] = auto_install.get_active()
            self.repo_config['update_check_interval_minutes'] = int(interval_spin.get_value())
            self.repo_config['verify_checksums'] = verify_checksums.get_active()
            
            # Handle manifest URL
            new_manifest_url = manifest_entry.get_text().strip()
            # Get the currently active manifest URL
            current_custom_url = self.repo_config.get('custom_manifest_url', '').strip()
            old_manifest_url = current_custom_url or DEFAULT_MANIFEST_URL
            manifest_url_changed = False
            
            if new_manifest_url == DEFAULT_MANIFEST_URL:
                # Reset to default, remove custom setting
                if old_manifest_url != DEFAULT_MANIFEST_URL:
                    manifest_url_changed = True
                self.repo_config['custom_manifest_url'] = ''
                os.environ.pop('CUSTOM_MANIFEST_URL', None)
                MANIFEST_URL = DEFAULT_MANIFEST_URL
            elif new_manifest_url and (new_manifest_url.startswith('http://') or new_manifest_url.startswith('https://')):
                # Valid custom URL
                if old_manifest_url != new_manifest_url:
                    manifest_url_changed = True
                self.repo_config['custom_manifest_url'] = new_manifest_url
                os.environ['CUSTOM_MANIFEST_URL'] = new_manifest_url
                MANIFEST_URL = new_manifest_url
            else:
                # Invalid URL, show error
                error_dialog = Gtk.MessageDialog(
                    transient_for=dialog,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Invalid manifest URL. Please use http:// or https://"
                )
                error_dialog.run()
                error_dialog.destroy()
                dialog.destroy()
                return
            
            self.repository.save_config(self.repo_config)
            
            # Update repository URL if manifest URL changed
            if manifest_url_changed and self.repository:
                # Refresh the repository's effective URL
                self.repository.repo_url = self.repository.get_effective_repository_url()
            
            # Update repo_enabled and refresh UI if setting changed
            self.repo_enabled = new_repo_enabled
            if old_repo_enabled != new_repo_enabled:
                self._refresh_ui_for_repo_setting()
            
            # Clear manifest cache if URL changed to force fresh download
            if manifest_url_changed:
                try:
                    if MANIFEST_CACHE_FILE.exists():
                        MANIFEST_CACHE_FILE.unlink()
                        self.terminal.feed("\x1b[33m[*] Cleared manifest cache for new repository\x1b[0m\r\n".encode())
                except Exception as e:
                    self.terminal.feed(f"\x1b[31m[!] Error clearing cache: {e}\x1b[0m\r\n".encode())
            
            if self.repo_config.get('custom_manifest_url'):
                self.terminal.feed("\x1b[2J\x1b[H\x1b[32m[*] Repository settings saved\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[33m[*] Switching to custom repository: {new_manifest_url}\x1b[0m\r\n".encode())
                # Refresh all script data to load from new repository
                self._refresh_all_script_data()
            else:
                self.terminal.feed("\x1b[2J\x1b[H\x1b[32m[*] Repository settings saved\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[33m[*] Switching to default repository: {DEFAULT_MANIFEST_URL}\x1b[0m\r\n".encode())
                # Refresh to use default repository
                self._refresh_all_script_data()
            
            # Auto-complete after short delay
            GLib.timeout_add(1500, self._complete_terminal_operation)
        
        dialog.destroy()

    # ========================================================================
    # Enhanced Repository Selection Methods
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
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="No Scripts Selected"
            )
            dialog.format_secondary_text("Please select one or more scripts to download.")
            dialog.run()
            dialog.destroy()
            return
        
        # Confirmation dialog
        script_names = [name for _, name in selected_scripts]
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Download Selected Scripts"
        )
        dialog.format_secondary_text(
            f"Download {len(selected_scripts)} selected scripts to cache?\n\n"
            f"Scripts: {', '.join(script_names[:3])}"
            f"{'...' if len(script_names) > 3 else ''}"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        # Download selected scripts
        self.terminal.feed(b"\x1b[2J\x1b[H")
        self.terminal.feed(f"\x1b[32m[*] Downloading {len(selected_scripts)} selected scripts...\x1b[0m\r\n".encode())
        
        success_count = 0
        failed_count = 0
        
        for script_id, script_name in selected_scripts:
            try:
                if self.repository.download_script(script_id):
                    self.terminal.feed(f"  ✓ {script_name}\r\n".encode())
                    success_count += 1
                else:
                    self.terminal.feed(f"  ✗ {script_name} (failed)\r\n".encode())
                    failed_count += 1
            except Exception as e:
                error_msg = "checksum verification failed" if "Checksum verification failed" in str(e) else f"error: {e}"
                self.terminal.feed(f"  ✗ {script_name} ({error_msg})\r\n".encode())
                failed_count += 1
        
        self.terminal.feed(f"\x1b[32m[*] Download complete: {success_count} downloaded, {failed_count} failed\x1b[0m\r\n".encode())
        
        # Auto-complete and refresh
        GLib.timeout_add(1500, self._complete_terminal_operation)
        self._update_repo_status()
        self._populate_repository_tree()
        
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
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="No Cached Scripts Selected"
            )
            dialog.format_secondary_text("Please select one or more cached scripts to remove.")
            dialog.run()
            dialog.destroy()
            return
        
        # Confirmation dialog
        script_names = [name for _, name in selected_scripts]
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Remove Selected Scripts"
        )
        dialog.format_secondary_text(
            f"Remove {len(selected_scripts)} selected scripts from cache?\n\n"
            f"Scripts: {', '.join(script_names[:3])}"
            f"{'...' if len(script_names) > 3 else ''}\n\n"
            "This will remove the cached files. You can download them again later."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        # Remove selected scripts
        self.terminal.feed(b"\x1b[2J\x1b[H")
        self.terminal.feed(f"\x1b[32m[*] Removing {len(selected_scripts)} selected scripts...\x1b[0m\r\n".encode())
        
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
            
            # Reload from manifest with repository configuration (this will show cache status in terminal)
            _scripts, _names, _descriptions = load_scripts_from_manifest(terminal_widget=self.terminal, repository=self.repository)
            
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
            
            # Use a small delay to ensure the UI updates are visible
            GLib.timeout_add(100, self._delayed_repopulate)
            
            # Provide feedback about the reload
            self.terminal.feed(b"\x1b[32m[*] Main tabs refreshed with updated cache status\x1b[0m\r\n")
            
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
            
            # Reload from manifest silently with repository configuration (pass None for terminal_widget to suppress output)
            _scripts, _names, _descriptions = load_scripts_from_manifest(terminal_widget=None, repository=self.repository)
            
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
        """Refresh all UI elements after a cache change (download/remove)"""
        try:
            # Update repository status and tree
            self._update_repo_status()
            self._populate_repository_tree()
            
            # Reload main tabs to reflect cache changes
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
            self._populate_repository_tree()
            
            # Reload main tabs silently
            self._reload_main_tabs_silent()
            
            return False  # Don't repeat the timeout
        except Exception as e:
            print(f"Error in silent UI refresh: {e}")
            return False

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
            cache_root = os.path.expanduser("~/.lv_linux_learn/script_cache")
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
            
            cache_root = os.path.expanduser("~/.lv_linux_learn/script_cache")
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
            cache_root = os.path.expanduser("~/.lv_linux_learn/script_cache")
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
        """Repopulate all main tab list stores with updated data"""
        try:
            # Clear and repopulate install tab
            if hasattr(self, 'install_liststore'):
                self.install_liststore.clear()
                # Only add repository scripts if repository is enabled
                if self.repo_enabled:
                    for i, script_path in enumerate(SCRIPTS):
                        if i < len(SCRIPT_NAMES) and i < len(DESCRIPTIONS):
                            self.install_liststore.append([SCRIPT_NAMES[i], script_path, DESCRIPTIONS[i], False, ""])
                # Add custom scripts
                custom_scripts = self.custom_manager.get_scripts("install")
                for script in custom_scripts:
                    display_name = f"📝 {script['name']}"
                    self.install_liststore.append([display_name, script['script_path'], script['description'], True, script['id']])
            
            # Clear and repopulate tools tab  
            if hasattr(self, 'tools_liststore'):
                self.tools_liststore.clear()
                # Only add repository scripts if repository is enabled
                if self.repo_enabled:
                    for i, script_path in enumerate(TOOLS_SCRIPTS):
                        if i < len(TOOLS_NAMES) and i < len(TOOLS_DESCRIPTIONS):
                            self.tools_liststore.append([TOOLS_NAMES[i], script_path, TOOLS_DESCRIPTIONS[i], False, ""])
                # Add custom scripts
                custom_scripts = self.custom_manager.get_scripts("tools")
                for script in custom_scripts:
                    display_name = f"📝 {script['name']}"
                    self.tools_liststore.append([display_name, script['script_path'], script['description'], True, script['id']])
            
            # Clear and repopulate exercises tab
            if hasattr(self, 'exercises_liststore'):
                self.exercises_liststore.clear()
                # Only add repository scripts if repository is enabled
                if self.repo_enabled:
                    for i, script_path in enumerate(EXERCISES_SCRIPTS):
                        if i < len(EXERCISES_NAMES) and i < len(EXERCISES_DESCRIPTIONS):
                            self.exercises_liststore.append([EXERCISES_NAMES[i], script_path, EXERCISES_DESCRIPTIONS[i], False, ""])
                # Add custom scripts
                custom_scripts = self.custom_manager.get_scripts("exercises")
                for script in custom_scripts:
                    display_name = f"📝 {script['name']}"
                    self.exercises_liststore.append([display_name, script['script_path'], script['description'], True, script['id']])
            
            # Clear and repopulate uninstall tab
            if hasattr(self, 'uninstall_liststore'):
                self.uninstall_liststore.clear()
                # Only add repository scripts if repository is enabled
                if self.repo_enabled:
                    for i, script_path in enumerate(UNINSTALL_SCRIPTS):
                        if i < len(UNINSTALL_NAMES) and i < len(UNINSTALL_DESCRIPTIONS):
                            self.uninstall_liststore.append([UNINSTALL_NAMES[i], script_path, UNINSTALL_DESCRIPTIONS[i], False, ""])
                # Add custom scripts
                custom_scripts = self.custom_manager.get_scripts("uninstall")
                for script in custom_scripts:
                    display_name = f"📝 {script['name']}"
                    self.uninstall_liststore.append([display_name, script['script_path'], script['description'], True, script['id']])
                        
        except Exception as e:
            print(f"Error repopulating tab stores: {e}")

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
        """Show dialog that installation has started"""
        info = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=f"Installing {pkg_type.title()} Packages",
        )
        
        if required:
            info.format_secondary_text(
                f"Installing: {pkg_list}\n\n"
                f"Please enter your password if prompted.\n"
                f"Check the terminal below for installation progress."
            )
        else:
            info.format_secondary_text(
                f"Installing: {pkg_list}\n\n"
                f"Please enter your password if prompted.\n"
                f"Check the terminal below for installation progress.\n\n"
                f"💡 Tip: Restart the application after installation completes\n"
                f"to use the newly installed packages for syntax highlighting."
            )
        
        info.run()
        info.destroy()
        return False
    
    def _restart_application(self):
        """Restart the application"""
        print("[DEBUG] Restarting application...")
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

    def on_selection_changed(self, selection):
        model, treeiter = selection.get_selected()
        widgets = self.get_current_widgets()
        
        if treeiter is not None:
            # model is filtered -> get data from model columns
            basename = model[treeiter][0]
            fullpath = model[treeiter][1]
            desc_markup_raw = model[treeiter][2]
            
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
        widgets = self.get_current_widgets()
        selection = widgets['treeview'].get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        # model is filtered -> get full path from model column 1
        script_path = model[treeiter][1]
        script_name = os.path.basename(script_path)
        
        # Check if this is a repository script that needs to be cached
        if self.repository and self.repo_enabled:
            # Try to find the script in the manifest
            manifest_script_id = self._get_manifest_script_id(script_name, script_path)
            
            if manifest_script_id:
                # This is a repository script - check if it's cached
                cached_path = self.repository.get_cached_script_path(manifest_script_id)
                
                if cached_path and os.path.isfile(cached_path):
                    # Script is cached - execute from cache
                    self._ensure_includes_available()
                    cache_root = os.path.expanduser("~/.lv_linux_learn/script_cache")
                    command = f"cd '{cache_root}' && bash '{cached_path}'\n"
                    self.terminal.feed(f"\x1b[33m[*] Executing cached script with includes support\x1b[0m\r\n".encode())
                    self.terminal.feed_child(command.encode())
                    return
                else:
                    # Script is not cached - prompt user to download
                    dialog = Gtk.MessageDialog(
                        transient_for=self,
                        flags=0,
                        message_type=Gtk.MessageType.QUESTION,
                        buttons=Gtk.ButtonsType.YES_NO,
                        text="☁️ Download Script?"
                    )
                    dialog.format_secondary_text(
                        f"The script '{script_name}' needs to be downloaded to your cache.\n\n"
                        "Download and run from cache? This provides better performance\n"
                        "and includes support for repository scripts."
                    )
                    response = dialog.run()
                    dialog.destroy()
                    
                    if response == Gtk.ResponseType.YES:
                        # Download the script
                        self.terminal.feed(f"\x1b[32m[*] Downloading ☁️ {script_name} to cache...\x1b[0m\r\n".encode())
                        try:
                            success = self.repository.download_script(manifest_script_id)
                            if success:
                                # Get the cached script path and run it
                                cached_path = self.repository.get_cached_script_path(manifest_script_id)
                                if cached_path and os.path.isfile(cached_path):
                                    self._ensure_includes_available()
                                    cache_root = os.path.expanduser("~/.lv_linux_learn/script_cache")
                                    command = f"cd '{cache_root}' && bash '{cached_path}'\n"
                                    self.terminal.feed(f"\x1b[32m[✓] Downloaded successfully! Executing...\x1b[0m\r\n".encode())
                                    # Refresh UI to show updated cache status
                                    GLib.timeout_add(500, self._refresh_ui_after_cache_change)
                                    self.terminal.feed_child(command.encode())
                                    return
                                else:
                                    self.terminal.feed(f"\x1b[31m[✗] Failed to locate cached script\x1b[0m\r\n".encode())
                            else:
                                self.terminal.feed(f"\x1b[31m[✗] Failed to download {script_name}\x1b[0m\r\n".encode())
                        except Exception as e:
                            if "Checksum verification failed" in str(e):
                                self.terminal.feed(f"\x1b[31m[✗] Checksum verification failed\x1b[0m\r\n".encode())
                                self.terminal.feed(f"\x1b[33m[!] Try disabling checksum verification in Repository Settings\x1b[0m\r\n".encode())
                            else:
                                self.terminal.feed(f"\x1b[31m[✗] Download error: {e}\x1b[0m\r\n".encode())
                        return
                    else:
                        # User chose not to download
                        self.terminal.feed(f"\x1b[33m[!] Download cancelled by user\x1b[0m\r\n".encode())
                        return
        
        # Fallback: try to execute as local script if it exists
        if os.path.isfile(script_path):
            abs_path = os.path.abspath(script_path)
            command = f"bash '{abs_path}'\n"
            self.terminal.feed(f"\x1b[33m[*] Executing local script\x1b[0m\r\n".encode())
            self.terminal.feed_child(command.encode())
        else:
            self.show_error_dialog(f"Script not found:\n{script_path}")

    def on_cd_clicked(self, button):
        widgets = self.get_current_widgets()
        selection = widgets['treeview'].get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        script_path = model[treeiter][1]
        if not os.path.isfile(script_path):
            self.show_error_dialog(f"Script not found:\n{script_path}")
            return
        
        # Get absolute path to check for cached scripts
        abs_path = os.path.abspath(script_path)
        
        # Check if this is a cached script
        if '.lv_linux_learn/script_cache/' in abs_path:
            # Cached script - navigate to script's directory in cache
            self._ensure_includes_available()
            script_dir = os.path.dirname(abs_path)
            safe_dir = shlex.quote(script_dir)
            self.terminal.feed(f"\x1b[33m[*] Navigating to script directory in cache\x1b[0m\r\n".encode())
        else:
            # Local script - check if user wants to download it first
            if self.repository and self.repo_enabled:
                script_name = os.path.basename(script_path)
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="Script Not Cached"
                )
                dialog.format_secondary_text(
                    f"The script '{script_name}' is not in your local cache.\n\n"
                    "Would you like to download it to the cache first?\n"
                    "This will allow you to navigate to the cache directory with includes support."
                )
                response = dialog.run()
                dialog.destroy()
                
                if response == Gtk.ResponseType.YES:
                    # Try to download the script first
                    try:
                        # Find the script in manifest and download it
                        manifest = self.repository.parse_manifest()
                        script_id = None
                        for script in manifest:
                            if script['relative_path'].endswith(script_name) or script['relative_path'] == script_path:
                                script_id = script['id']
                                break
                        
                        if script_id:
                            self.terminal.feed(f"\r\n\x1b[32m[*] Downloading {script_name}...\x1b[0m\r\n".encode())
                            success = self.repository.download_script(script_id)
                            if success:
                                # Navigate to the specific script directory in cache
                                cached_path = self.repository.get_cached_script_path(script_id)
                                if cached_path and os.path.isfile(cached_path):
                                    self._ensure_includes_available()
                                    script_cache_dir = os.path.dirname(cached_path)
                                    safe_dir = shlex.quote(script_cache_dir)
                                    self.terminal.feed(f"\x1b[33m[*] Downloaded successfully! Navigating to script directory\x1b[0m\r\n".encode())
                                    # Refresh UI silently to avoid terminal interference
                                    GLib.timeout_add(500, self._refresh_ui_silent)
                                else:
                                    # Fallback to cache root if can't find specific directory
                                    self._ensure_includes_available()
                                    cache_root = os.path.expanduser("~/.lv_linux_learn/script_cache")
                                    safe_dir = shlex.quote(cache_root)
                                    self.terminal.feed(f"\x1b[33m[*] Downloaded successfully! Navigating to cache root\x1b[0m\r\n".encode())
                                    # Refresh UI silently to avoid terminal interference
                                    GLib.timeout_add(500, self._refresh_ui_silent)
                            else:
                                self.terminal.feed(f"\x1b[31m[!] Download failed, navigating to local directory\x1b[0m\r\n".encode())
                                script_dir = os.path.dirname(abs_path)
                                safe_dir = shlex.quote(script_dir)
                        else:
                            self.terminal.feed(f"\x1b[31m[!] Script not found in manifest, navigating to local directory\x1b[0m\r\n".encode())
                            script_dir = os.path.dirname(abs_path)
                            safe_dir = shlex.quote(script_dir)
                    except Exception as e:
                        self.terminal.feed(f"\x1b[31m[!] Error downloading: {e}\x1b[0m\r\n".encode())
                        script_dir = os.path.dirname(abs_path)
                        safe_dir = shlex.quote(script_dir)
                else:
                    # User chose not to download, navigate to local directory
                    script_dir = os.path.dirname(abs_path)
                    safe_dir = shlex.quote(script_dir)
            else:
                # Repository not available, navigate to local directory
                script_dir = os.path.dirname(abs_path)
                safe_dir = shlex.quote(script_dir)
        
        # Change directory in terminal
        cd_cmd = f"cd {safe_dir} && pwd\n"
        self.terminal.feed_child(cd_cmd.encode())
        
        # No completion needed - the cd && pwd command completes naturally
    
    def on_view_clicked(self, button):
        widgets = self.get_current_widgets()
        selection = widgets['treeview'].get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        script_path = model[treeiter][1]
        script_name = os.path.basename(script_path)
        
        # Check if this is a repository script that needs to be cached first
        if self.repository and self.repo_enabled:
            manifest_script_id = self._get_manifest_script_id(script_name, script_path)
            
            if manifest_script_id:
                cached_path = self.repository.get_cached_script_path(manifest_script_id)
                
                if cached_path and os.path.isfile(cached_path):
                    # Use cached version
                    script_path = cached_path
                else:
                    # Prompt to download first
                    dialog = Gtk.MessageDialog(
                        transient_for=self,
                        flags=0,
                        message_type=Gtk.MessageType.QUESTION,
                        buttons=Gtk.ButtonsType.YES_NO,
                        text="☁️ Download Script to View?"
                    )
                    dialog.format_secondary_text(
                        f"The script '{script_name}' needs to be downloaded to view.\n\n"
                        "Download to cache first?"
                    )
                    response = dialog.run()
                    dialog.destroy()
                    
                    if response == Gtk.ResponseType.YES:
                        try:
                            success = self.repository.download_script(manifest_script_id)
                            if success:
                                cached_path = self.repository.get_cached_script_path(manifest_script_id)
                                if cached_path and os.path.isfile(cached_path):
                                    script_path = cached_path
                                    # Refresh UI to show updated cache status
                                    GLib.timeout_add(500, self._refresh_ui_after_cache_change)
                                else:
                                    self.show_error_dialog("Failed to locate downloaded script")
                                    return
                            else:
                                self.show_error_dialog(f"Failed to download {script_name}")
                                return
                        except Exception as e:
                            if "Checksum verification failed" in str(e):
                                self.show_error_dialog(f"Checksum verification failed for {script_name}.\n\nTry disabling checksum verification in Repository Settings.")
                            else:
                                self.show_error_dialog(f"Download error: {e}")
                            return
                    else:
                        return  # User cancelled
        
        # Check if file exists before viewing
        if not os.path.isfile(script_path):
            self.show_error_dialog(f"Script not found:\n{script_path}")
            return
        
        # Convert to absolute path to work regardless of terminal's current directory
        abs_path = os.path.abspath(script_path)
        safe_path = shlex.quote(abs_path)
        
        # Clear screen first, then view file with a clean header
        viewer_cmd = (
            f"clear; "
            f"echo ''; "
            f"echo '{'=' * 80}'; "
            f"echo 'Viewing: {abs_path}'; "
            f"echo '{'=' * 80}'; "
            f"echo ''; "
            f"if command -v batcat >/dev/null 2>&1; then "
            f"batcat --paging=never --style=plain --color=always {safe_path}; "
            f"elif command -v bat >/dev/null 2>&1; then "
            f"bat --paging=never --style=plain --color=always {safe_path}; "
            f"elif command -v pygmentize >/dev/null 2>&1; then "
            f"pygmentize -g -f terminal256 {safe_path}; "
            f"elif command -v highlight >/dev/null 2>&1; then "
            f"highlight -O ansi {safe_path}; "
            f"else cat -n {safe_path}; fi 2>/dev/null\n"
        )
        
        self.terminal.feed_child(viewer_cmd.encode())
        
        # Scroll terminal to top after a brief delay
        GLib.timeout_add(100, self._scroll_terminal_to_top)
    
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
            is_custom = liststore.get_value(iter, 3)  # Column 3 is is_custom
            if is_custom:
                if not liststore.remove(iter):
                    break
            else:
                iter = liststore.iter_next(iter)
        
        # Add custom scripts
        custom_scripts = self.custom_manager.get_scripts(category)
        for script in custom_scripts:
            display_name = f"📝 {script['name']}"
            liststore.append([
                display_name,
                script['script_path'],
                script['description'],
                True,  # is_custom
                script['id']
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
            
            # Check if it's a custom script
            is_custom = model.get_value(iter, 3)
            script_id = model.get_value(iter, 4)
            
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
                    script_name = model.get_value(iter, 0)
                    script_path = model.get_value(iter, 1)
                    
                    # Get the manifest script ID by matching script path or name
                    manifest_script_id = self._get_manifest_script_id(script_name, script_path)
                    
                    if manifest_script_id:
                        # Check if script is cached
                        cached_path = self.repository.get_cached_script_path(manifest_script_id)
                        is_cached = cached_path and os.path.isfile(cached_path)
                        
                        if is_cached:
                            # Script is cached - offer removal and update options
                            update_item = Gtk.MenuItem(label="🔄 Update Script")
                            update_item.connect("activate", lambda w: self._update_single_script(manifest_script_id, script_name))
                            menu.append(update_item)
                            
                            remove_item = Gtk.MenuItem(label="🗑️ Remove from Cache")
                            remove_item.connect("activate", lambda w: self._remove_script_from_cache(manifest_script_id, script_name))
                            menu.append(remove_item)
                        else:
                            # Script not cached - offer download
                            download_item = Gtk.MenuItem(label="⬇️ Download to Cache")
                            download_item.connect("activate", lambda w: self._download_single_script(manifest_script_id, script_name))
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
        script = self.custom_manager.get_script_by_id(script_id)
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
                self.custom_manager.update_script(
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
        script = self.custom_manager.get_script_by_id(script_id)
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
            self.custom_manager.delete_script(script_id)
            self._refresh_tab(script['category'])

    def _download_single_script(self, script_id, script_name):
        """Download a single script to cache"""
        if not self.repository:
            return
        
        self.terminal.feed(f"\r\n\x1b[33m[*] Downloading {script_name} to cache...\x1b[0m\r\n".encode())
        
        try:
            success = self.repository.download_script(script_id)
            if success:
                self.terminal.feed(f"\x1b[32m[✓] Successfully downloaded {script_name}\x1b[0m\r\n".encode())
                # Refresh UI to show updated cache status
                GLib.timeout_add(500, self._refresh_ui_after_cache_change)
            else:
                self.terminal.feed(f"\x1b[31m[✗] Failed to download {script_name}\x1b[0m\r\n".encode())
        except Exception as e:
            if "Checksum verification failed" in str(e):
                self.terminal.feed(f"\x1b[31m[✗] Checksum verification failed for {script_name}\x1b[0m\r\n".encode())
                self.terminal.feed(f"\x1b[33m[!] Script may have been updated since manifest was generated\x1b[0m\r\n".encode())
            else:
                self.terminal.feed(f"\x1b[31m[✗] Error downloading {script_name}: {e}\x1b[0m\r\n".encode())
        
        # Auto-complete after short delay
        GLib.timeout_add(1500, self._complete_terminal_operation)

    def _update_single_script(self, script_id, script_name):
        """Force update a single cached script"""
        if not self.repository:
            return
        
        self.terminal.feed(f"\r\n\x1b[33m[*] Updating {script_name}...\x1b[0m\r\n".encode())
        
        try:
            # Remove from cache first, then re-download
            cached_path = self.repository.get_cached_script_path(script_id)
            if cached_path and os.path.isfile(cached_path):
                os.remove(cached_path)
            
            success = self.repository.download_script(script_id)
            if success:
                self.terminal.feed(f"\x1b[32m[✓] Successfully updated {script_name}\x1b[0m\r\n".encode())
                # Refresh UI to show updated cache status
                GLib.timeout_add(500, self._refresh_ui_after_cache_change)
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

    def _remove_script_from_cache(self, script_id, script_name):
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
                cached_path = self.repository.get_cached_script_path(script_id)
                if cached_path and os.path.isfile(cached_path):
                    os.remove(cached_path)
                    self.terminal.feed(f"\r\n\x1b[32m[✓] Removed {script_name} from cache\x1b[0m\r\n".encode())
                    # Refresh UI to show updated cache status
                    GLib.timeout_add(500, self._refresh_ui_after_cache_change)
                else:
                    self.terminal.feed(f"\r\n\x1b[33m[!] {script_name} was not in cache\x1b[0m\r\n".encode())
            except Exception as e:
                self.terminal.feed(f"\r\n\x1b[31m[✗] Error removing {script_name}: {e}\x1b[0m\r\n".encode())
        
        # Auto-complete after short delay
        GLib.timeout_add(1500, self._complete_terminal_operation)

    def _create_menubar(self):
        """Create application menu bar"""
        menubar = Gtk.MenuBar()

        # File Menu
        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="File")
        file_item.set_submenu(file_menu)
        
        # Refresh Scripts
        self.refresh_item = Gtk.MenuItem(label="Refresh Scripts")
        self.refresh_item.connect("activate", lambda w: self._refresh_all_script_data())
        self.refresh_item.set_sensitive(self.repo_enabled)  # Enable/disable based on repository state
        file_menu.append(self.refresh_item)
        
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
        """Refresh all script data from repository and local sources"""
        try:
            # Show progress in terminal
            self.terminal.feed(b"\r\n\x1b[33m[*] Refreshing script data...\x1b[0m\r\n")
            
            # Reload scripts from manifest with repository configuration
            global _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT
            global SCRIPTS, SCRIPT_NAMES, TOOLS_SCRIPTS, TOOLS_NAMES
            global EXERCISES_SCRIPTS, EXERCISES_NAMES, UNINSTALL_SCRIPTS, UNINSTALL_NAMES
            global DESCRIPTIONS, TOOLS_DESCRIPTIONS, EXERCISES_DESCRIPTIONS, UNINSTALL_DESCRIPTIONS
            
            # Force refresh manifest and reload with repository configuration
            _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT = load_scripts_from_manifest(self.terminal, self.repository)
            
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
            
            # Refresh custom scripts (reload from disk)
            self.terminal.feed(b"\x1b[33m[*] Refreshing custom scripts...\x1b[0m\r\n")
            # Custom manager automatically loads from disk on each get_scripts() call
            
            # Repopulate all tab stores
            self._repopulate_tab_stores()
            
            # Refresh UI
            if hasattr(self, '_refresh_ui_after_cache_change'):
                GLib.timeout_add(100, self._refresh_ui_after_cache_change)
            
            self.terminal.feed(b"\x1b[32m[*] Script data refreshed successfully!\x1b[0m\r\n")
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[✗] Error refreshing script data: {e}\x1b[0m\r\n".encode())
        
        # Auto-complete after short delay
        GLib.timeout_add(1500, self._complete_terminal_operation)

    def _show_about_dialog(self):
        """Show about dialog with application information"""
        dialog = Gtk.AboutDialog()
        dialog.set_transient_for(self)
        dialog.set_program_name("LV Script Manager")
        dialog.set_version("2.1.0")
        dialog.set_comments("Ubuntu setup and utility script collection with multi-repository support")
        dialog.set_website("https://github.com/amatson97/lv_linux_learn")
        dialog.set_website_label("GitHub Repository")
        dialog.set_license_type(Gtk.License.MIT_X11)
        dialog.set_authors(["Adam Matson"])
        dialog.set_copyright("© 2025 Adam Matson")
        
        # Add logo if available
        try:
            logo = GdkPixbuf.Pixbuf.new_from_file_at_scale("images/logo.png", 64, 64, True)
            dialog.set_logo(logo)
        except:
            pass  # No logo file, that's fine
        
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
            
        # Update menu item states based on repository status
        if hasattr(self, 'refresh_item'):
            self.refresh_item.set_sensitive(self.repo_enabled)
        
        # Refresh all tab contents to update cache status indicators
        self._repopulate_tab_stores()
        
        # Force a complete UI refresh
        while Gtk.events_pending():
            Gtk.main_iteration()

    def _get_manifest_script_id(self, script_name, script_path):
        """Get the manifest script ID by matching script name or path"""
        if not self.repository:
            return None
            
        try:
            manifest = self.repository.parse_manifest()
            
            # Clean the script name by removing status indicators
            clean_name = script_name
            if script_name.startswith("✓ "):
                clean_name = script_name[2:]
            elif script_name.startswith("☁️ "):
                clean_name = script_name[3:]
            
            for script in manifest:
                # Try to match by name first
                if script.get('name') == clean_name:
                    return script.get('id')
                    
                # Try to match by relative path
                if script.get('relative_path') == script_path:
                    return script.get('id')
                    
                # Try to match by file name
                script_filename = os.path.basename(script_path)
                manifest_filename = script.get('file_name', '')
                if manifest_filename and manifest_filename == script_filename:
                    return script.get('id')
            
            return None
            
        except Exception as e:
            print(f"Error getting manifest script ID: {e}")
            return None

    def show_error_dialog(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()


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