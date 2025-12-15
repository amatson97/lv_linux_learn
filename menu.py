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
import hashlib
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
    from lib.custom_manifest import CustomManifestCreator, ScriptScanner
except ImportError:
    print("Warning: Custom manifest module not available")
    CustomManifestCreator = None
    ScriptScanner = None

try:
    from lib.custom_scripts import CustomScriptManager
except ImportError:
    print("Warning: Custom scripts module not available")
    CustomScriptManager = None

try:
    from lib import constants as C
except ImportError:
    print("Warning: Constants module not available")
    C = None

try:
    from lib import manifest_loader
except ImportError:
    print("Warning: Manifest loader module not available")
    manifest_loader = None

try:
    from lib import script_handler
except ImportError:
    print("Warning: Script handler module not available")
    script_handler = None

try:
    from lib import ui_helpers as UI
except ImportError:
    print("Warning: UI helpers module not available")
    UI = None

try:
    from lib import repository_ops as RepoOps
except ImportError:
    print("Warning: Repository operations module not available")
    RepoOps = None

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
    MANIFEST_CACHE_DIR = Path.home() / '.lv_linux_learn'
    MANIFEST_CACHE_FILE = MANIFEST_CACHE_DIR / 'manifest.json'
    MANIFEST_CACHE_MAX_AGE = 3600

MANIFEST_URL = os.environ.get('CUSTOM_MANIFEST_URL', DEFAULT_MANIFEST_URL)


# ============================================================================
# MANIFEST LOADING FUNCTIONS
# ============================================================================

# Use imported manifest_loader module (required for operation)
fetch_manifest = manifest_loader.fetch_manifest
load_scripts_from_manifest = manifest_loader.load_scripts_from_manifest


# Note: Global loading doesn't use terminal widget (goes to stdout)
# Try to initialize with repository for custom configuration
try:
    from lib.repository import ScriptRepository
    _temp_repo = ScriptRepository()
    _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, _SCRIPT_ID_MAP = load_scripts_from_manifest(repository=_temp_repo)
except Exception as e:
    print(f'[!] Error loading scripts: {e}')
    _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, _SCRIPT_ID_MAP = load_scripts_from_manifest()
# Try to initialize with repository for custom configuration
try:
    from lib.repository import ScriptRepository
    _temp_repo = ScriptRepository()
    if manifest_loader:
        # New manifest_loader returns 4 values including script_id_map
        _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, _SCRIPT_ID_MAP = load_scripts_from_manifest(repository=_temp_repo)
    else:
        # Fallback to original function (returns 3 values)
        _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT = load_scripts_from_manifest(repository=_temp_repo)
        _SCRIPT_ID_MAP = {}
except Exception:
    # Fallback to default loading if repository initialization fails
    if manifest_loader:
        _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, _SCRIPT_ID_MAP = load_scripts_from_manifest()
    else:
        _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT = load_scripts_from_manifest()
        _SCRIPT_ID_MAP = {}

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

# Track non-standard categories for dynamic tab creation
NON_STANDARD_CATEGORIES = {}
for category in _SCRIPTS_DICT.keys():
    if category not in ['install', 'tools', 'exercises', 'uninstall']:
        NON_STANDARD_CATEGORIES[category] = {
            'scripts': _SCRIPTS_DICT.get(category, []),
            'names': _NAMES_DICT.get(category, []),
            'descriptions': _DESCRIPTIONS_DICT.get(category, [])
        }

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
# MAIN APPLICATION CLASS
# ============================================================================

class ScriptMenuGTK(Gtk.ApplicationWindow):
    def __init__(self, app):
        global MANIFEST_URL
        # Use ApplicationWindow so GNOME/WM can associate the window with the Gtk.Application.
        Gtk.ApplicationWindow.__init__(self, application=app, title="LV Script Manager")
        
        # Initialize window state config
        self.config_dir = Path.home() / '.lv_linux_learn'
        self.ui_config_file = self.config_dir / 'ui_state.json'
        
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
        if ScriptRepository:
            try:
                self.repository = ScriptRepository()
                self.repo_config = self.repository.load_config()
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
            except Exception as e:
                print(f"Warning: Failed to initialize repository: {e}")
        
        # CRITICAL: Reload scripts with repository configuration
        # This ensures custom manifest settings are properly loaded
        if self.repository:
            global _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, NON_STANDARD_CATEGORIES
            global SCRIPTS, SCRIPT_NAMES, DESCRIPTIONS, TOOLS_SCRIPTS, TOOLS_NAMES, TOOLS_DESCRIPTIONS
            global EXERCISES_SCRIPTS, EXERCISES_NAMES, EXERCISES_DESCRIPTIONS
            global UNINSTALL_SCRIPTS, UNINSTALL_NAMES, UNINSTALL_DESCRIPTIONS
            
            try:
                print("[*] Reloading scripts with repository configuration...")
                # Reload with repository instance for proper cache status and custom manifests
                global _SCRIPT_ID_MAP
                _SCRIPTS_DICT, _NAMES_DICT, _DESCRIPTIONS_DICT, _SCRIPT_ID_MAP = load_scripts_from_manifest(repository=self.repository)
                
                print(f"[*] Loaded categories: {list(_SCRIPTS_DICT.keys())}")
                print(f"[*] Install scripts: {len(_SCRIPTS_DICT.get('install', []))}")
                print(f"[*] Tools scripts: {len(_SCRIPTS_DICT.get('tools', []))}")
                print(f"[*] Exercises scripts: {len(_SCRIPTS_DICT.get('exercises', []))}")
                print(f"[*] Uninstall scripts: {len(_SCRIPTS_DICT.get('uninstall', []))}")
                
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
                
                # Update non-standard categories
                NON_STANDARD_CATEGORIES.clear()
                for category in _SCRIPTS_DICT.keys():
                    if category not in ['install', 'tools', 'exercises', 'uninstall']:
                        NON_STANDARD_CATEGORIES[category] = {
                            'scripts': _SCRIPTS_DICT.get(category, []),
                            'names': _NAMES_DICT.get(category, []),
                            'descriptions': _DESCRIPTIONS_DICT.get(category, [])
                        }
                print(f"[✓] Scripts reloaded successfully. Non-standard categories: {list(NON_STANDARD_CATEGORIES.keys())}")
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
        
        # Create dynamic tabs for non-standard categories
        self.dynamic_category_tabs = {}  # Store references to dynamic tabs
        for category, data in NON_STANDARD_CATEGORIES.items():
            category_box = self._create_script_tab(data['scripts'], data['descriptions'], category)
            # Get appropriate emoji for category
            category_emoji = {
                'custom': '📦',
                'ai': '🤖',
                'network': '🌐',
                'security': '🔒',
                'database': '🗄',
                'docker': '🐳',
                'other': '📝'
            }.get(category.lower(), '📦')
            category_label = self._create_tab_label(f"{category_emoji} {category.capitalize()}", category)
            self.notebook.append_page(category_box, category_label)
            self.dynamic_category_tabs[category] = {
                'box': category_box,
                'label': category_label
            }
        
        # Create Repository tab (if enabled)
        if self.repo_enabled:
            repository_box = self._create_repository_tab()
            repository_label = Gtk.Label(label="📥 Repository")
            self.notebook.append_page(repository_box, repository_label)
        
        # Create Custom Manifests tab
        if CustomManifestCreator:
            custom_manifest_box = self._create_custom_manifest_tab()
            custom_manifest_label = Gtk.Label(label="📁 Custom Manifests")
            self.notebook.append_page(custom_manifest_box, custom_manifest_label)

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
        scrollback_lines = C.TERMINAL_SCROLLBACK_LINES if C else 10000
        self.terminal.set_scrollback_lines(scrollback_lines)
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
        # Use script_handler module if available
        if script_handler:
            return script_handler.is_script_cached(self.repository, script_id, script_path, category)
        
        # Fallback implementation
        if not self.repository or not self.repository.script_cache_dir:
            return False
        
        # Method 1: Use script_id (most reliable)
        if script_id:
            cached_path = self.repository.get_cached_script_path(script_id)
            if cached_path and os.path.isfile(cached_path):
                return True
        
        # Method 2: Check if script_path IS a cache path
        if script_path and str(self.repository.script_cache_dir) in str(script_path):
            return os.path.isfile(script_path)
        
        # Method 3: Construct cache path from script_path and category
        if script_path and category:
            if script_path.startswith(('http://', 'https://')):
                filename = script_path.rstrip('/').split('/')[-1]
            else:
                filename = os.path.basename(script_path)
            
            cache_path = self.repository.script_cache_dir / category / filename
            if cache_path.exists():
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
        
        # Use script_handler module if available
        if script_handler:
            return script_handler.build_script_metadata(
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
                    source_type = "custom_repo"
                    source_name = mapping_source_name
        
        # Override with script_name tag if present (more authoritative)
        if script_name:
            if "[Public Repository]" in script_name:
                source_type = "public_repo"
                source_name = "Public Repository"
            elif "[Custom:" in script_name:
                # Extract custom manifest name
                start = script_name.find("[Custom:")
                end = script_name.find("]", start)
                if end > start:
                    source_name = script_name[start+8:end].strip()
                    source_type = "custom_repo"
        
        # CRITICAL: Check cache using centralized cache checker
        if self._is_script_cached(script_id=metadata["script_id"], script_path=script_path, category=category):
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
        
        # Now check if it's a local file (not in cache)
        if script_path.startswith('/') or script_path.startswith('file://'):
            actual_path = script_path[7:] if script_path.startswith('file://') else script_path
            metadata["type"] = "local"
            metadata["file_exists"] = os.path.isfile(actual_path)
            metadata["source_url"] = f"file://{actual_path}"
            
            # Check if it's from a custom manifest directory
            if source_type == "unknown":
                custom_manifests_dir = Path.home() / '.lv_linux_learn' / 'custom_manifests'
                if custom_manifests_dir in Path(actual_path).parents:
                    source_type = "custom_local"
                    # Try to extract manifest name from path
                    try:
                        relative = Path(actual_path).relative_to(custom_manifests_dir)
                        source_name = relative.parts[0] if relative.parts else "Custom Local"
                    except ValueError:
                        source_name = "Custom Local"
            
            metadata["source_type"] = source_type if source_type != "unknown" else "custom_local"
            metadata["source_name"] = source_name if source_name else "Local File"
            return metadata
        
        # Default to remote (not yet downloaded)
        metadata["type"] = "remote"
        metadata["source_type"] = source_type if source_type != "unknown" else "public_repo"
        metadata["source_name"] = source_name if source_name else "Public Repository"
        return metadata

    def _get_script_metadata(self, model, treeiter) -> dict:
        """Extract and parse metadata from liststore row"""
        try:
            metadata_json = model[treeiter][4]  # Column 4 is metadata
            if metadata_json:
                return json.loads(metadata_json)
        except (IndexError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to parse script metadata: {e}")
        return {}

    def _execute_script_unified(self, script_path: str, metadata: dict = None) -> bool:
        """
        Centralized script execution logic handling all manifest types.
        
        Logic:
        - Local files (custom_local): Execute directly from source
        - Cached files (public/custom_online): Execute from cache with includes
        - Remote files (public/custom_online): Prompt to download first
        """
        script_name = os.path.basename(script_path)
        
        # If no metadata, try to infer from path
        if not metadata:
            metadata = {"type": "remote" if not os.path.isfile(script_path) else "local"}
        
        script_type = metadata.get("type", "remote")
        
        # Handle local files - execute directly (no caching)
        if script_type == "local":
            file_path = script_path[7:] if script_path.startswith('file://') else script_path
            if os.path.isfile(file_path):
                abs_path = os.path.abspath(file_path)
                command = f"bash '{abs_path}'\n"
                self.terminal.feed(f"\x1b[33m[*] Executing local script: {script_name}\x1b[0m\r\n".encode())
                self.terminal.feed_child(command.encode())
                return True
            else:
                self.terminal.feed(f"\x1b[31m[!] Local file not found: {file_path}\x1b[0m\r\n".encode())
                return False
        
        # Handle cached files - execute from cache
        elif script_type == "cached":
            if os.path.isfile(script_path):
                self._ensure_includes_available()
                cache_root = os.path.expanduser("~/.lv_linux_learn/script_cache")
                command = f"cd '{cache_root}' && bash '{script_path}'\n"
                self.terminal.feed(f"\x1b[33m[*] Executing cached script: {script_name}\x1b[0m\r\n".encode())
                self.terminal.feed_child(command.encode())
                return True
            else:
                self.terminal.feed(f"\x1b[31m[!] Cached file not found: {script_path}\x1b[0m\r\n".encode())
                return False
        
        # Handle remote files - need to download first
        else:
            self.terminal.feed(f"\x1b[33m[*] Script not cached. Use Download button first.\x1b[0m\r\n".encode())
            return False

    def _navigate_to_directory_unified(self, script_path: str, metadata: dict = None) -> bool:
        """
        Centralized directory navigation logic handling all manifest types.
        
        Logic:
        - Local files: Navigate directly to parent directory in terminal
        - Cached files: Navigate to cache directory in terminal
        - Remote files: Prompt to download first
        """
        script_name = os.path.basename(script_path)
        
        if not metadata:
            metadata = {"type": "remote" if not os.path.isfile(script_path) else "local"}
        
        script_type = metadata.get("type", "remote")
        
        # Handle local files - cd to parent directory in terminal
        if script_type == "local":
            file_path = script_path[7:] if script_path.startswith('file://') else script_path
            if os.path.isfile(file_path):
                directory = os.path.dirname(os.path.abspath(file_path))
                command = f"cd '{directory}' && pwd\n"
                self.terminal.feed(f"\x1b[33m[*] Navigating to: {directory}\x1b[0m\r\n".encode())
                self.terminal.feed_child(command.encode())
                GLib.timeout_add(1000, self._complete_directory_navigation)
                return True
            else:
                self.terminal.feed(f"\x1b[31m[!] Local file not found: {file_path}\x1b[0m\r\n".encode())
                return False
        
        # Handle cached files - cd to cache directory in terminal
        elif script_type == "cached":
            if os.path.isfile(script_path):
                directory = os.path.dirname(script_path)
                command = f"cd '{directory}' && pwd\n"
                self.terminal.feed(f"\x1b[33m[*] Navigating to cache: {directory}\x1b[0m\r\n".encode())
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
        if script_handler:
            return script_handler.should_use_cache_engine(metadata)
        
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
        """Create a tab with script list and description panel"""
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
                # For dynamic categories, use names from global NON_STANDARD_CATEGORIES
                names = NON_STANDARD_CATEGORIES.get(tab_name, {}).get('names', [])

        # store: icon, display name, full path, description, is_custom (bool), metadata (str as JSON), script_id
        # Use constants for column indices to prevent bugs
        # COL_ICON=0, COL_NAME=1, COL_PATH=2, COL_DESCRIPTION=3, COL_IS_CUSTOM=4, COL_METADATA=5, COL_SCRIPT_ID=6
        liststore = Gtk.ListStore(str, str, str, str, bool, str, str)
        
        # Add scripts from manifest with metadata
        for i, script_path in enumerate(scripts):
            if i < len(names) and i < len(descriptions):
                # Determine script metadata (pass script_name for source detection)
                metadata = self._build_script_metadata(script_path, tab_name, names[i])
                script_id = metadata.get('script_id', '')
                
                # Get cache status icon
                is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category=tab_name)
                icon = "✓" if is_cached else "☁️"
                
                # CRITICAL: If script is cached, use the cached path instead of relative path
                path_to_store = script_path
                if is_cached and self.repository and script_id:
                    cached_path = self.repository.get_cached_script_path(script_id)
                    if cached_path and os.path.exists(cached_path):
                        path_to_store = cached_path
                        # Update metadata to reflect cached path
                        metadata["type"] = "cached"
                        metadata["file_exists"] = True
                
                liststore.append([icon, names[i], path_to_store, descriptions[i], False, json.dumps(metadata), script_id])

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
            # Check if this is a dynamic category tab
            tab_label = notebook.get_tab_label_text(page)
            if tab_label:
                # Convert tab label (e.g., "Custom") to category name (e.g., "custom")
                category = tab_label.lower()
                if category in NON_STANDARD_CATEGORIES:
                    self.current_tab = category
                    treeview = getattr(self, f'{category}_treeview', None)
                    if treeview:
                        # Reapply search filter for dynamic tab
                        self.on_search_changed(self.header_search)
                    return
            # Not a dynamic category - might be Repository/About/etc., no filter needed
            return
        
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
            # Handle dynamic categories
            global NON_STANDARD_CATEGORIES
            if self.current_tab in NON_STANDARD_CATEGORIES:
                category_data = NON_STANDARD_CATEGORIES[self.current_tab]
                # Get stored widget references for this dynamic category
                treeview_name = f'{self.current_tab}_treeview'
                description_label_name = f'{self.current_tab}_description_label'
                run_button_name = f'{self.current_tab}_run_button'
                view_button_name = f'{self.current_tab}_view_button'
                cd_button_name = f'{self.current_tab}_cd_button'
                filter_name = f'{self.current_tab}_filter'
                
                return {
                    'treeview': getattr(self, treeview_name, None),
                    'description_label': getattr(self, description_label_name, None),
                    'run_button': getattr(self, run_button_name, None),
                    'view_button': getattr(self, view_button_name, None),
                    'cd_button': getattr(self, cd_button_name, None),
                    'filter': getattr(self, filter_name, None),
                    'scripts': category_data.get('scripts', []),
                    'descriptions': category_data.get('descriptions', [])
                }
            
            # Fallback - shouldn't reach here
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
        """Create a tab label with a '+' button for adding custom scripts"""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        
        label = Gtk.Label(label=label_text)
        box.pack_start(label, True, True, 0)
        
        # Add '+' button for custom scripts (not for About tab)
        if category in ["install", "tools", "exercises", "uninstall"]:
            add_button = Gtk.Button()
            add_button.set_label("+")
            add_button.set_relief(Gtk.ReliefStyle.NONE)
    def _create_tab_label(self, label_text, category):
        """Create a tab label"""
        label = Gtk.Label(label=label_text)
        return label

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
        
        vbox.pack_start(button_box1, False, False, 0)
        vbox.pack_start(button_box2, False, False, 0)
        
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
        if not self.repository:
            return
        
        self.repo_store.clear()
        
        try:
            # Check which manifest sources to use
            config = self.repository.load_config()
            use_public_repo = config.get('use_public_repository', True)
            custom_manifest_url = config.get('custom_manifest_url', '')
            
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
            
            # 1b. Check for manifests created through Custom Manifests tab
            if hasattr(self, 'custom_manifest_creator') and self.custom_manifest_creator:
                try:
                    # Load manifest metadata file
                    manifests_dir = Path.home() / '.lv_linux_learn' / 'custom_manifests'
                    if manifests_dir.exists():
                        for manifest_file in manifests_dir.glob('*.json'):
                            try:
                                import json
                                with open(manifest_file) as f:
                                    manifest_data = json.load(f)
                                
                                # Get repository URL from manifest
                                repo_url = manifest_data.get('repository_url')
                                if repo_url and repo_url.startswith(('http://', 'https://')):
                                    manifest_name = manifest_file.stem.replace('_', ' ').title()
                                    custom_manifests_to_load.append((manifest_file.stem, repo_url + '/manifest.json', manifest_name))
                                    if hasattr(self, 'terminal'):
                                        self.terminal.feed(f"\x1b[36m[*] Found custom manifest: {manifest_name} ({repo_url})\x1b[0m\r\n".encode())
                            except Exception as e:
                                if hasattr(self, 'terminal'):
                                    self.terminal.feed(f"\x1b[33m[!] Could not load manifest {manifest_file.name}: {e}\x1b[0m\r\n".encode())
                except Exception as e:
                    if hasattr(self, 'terminal'):
                        self.terminal.feed(f"\x1b[33m[!] Error scanning custom manifests: {e}\x1b[0m\r\n".encode())
            
            # Load all custom manifests
            for manifest_id, manifest_url, custom_manifest_name in custom_manifests_to_load:
                import json
                import urllib.request
                
                custom_scripts = []
                try:
                    # Load online manifest
                    with urllib.request.urlopen(manifest_url, timeout=10) as response:
                        custom_manifest = json.loads(response.read().decode())
                    
                    # Track checksum verification setting for this manifest
                    verify_checksums = custom_manifest.get('verify_checksums', True)
                    manifest_verify_settings[custom_manifest_name] = verify_checksums
                    
                    if hasattr(self, 'terminal'):
                        self.terminal.feed(f"\x1b[36m[*] Loaded custom manifest from: {custom_manifest_url}\x1b[0m\r\n".encode())
                        if not verify_checksums:
                            self.terminal.feed(f"\x1b[33m[*] Note: Checksum verification disabled for '{custom_manifest_name}'\x1b[0m\r\n".encode())
                    
                    if custom_manifest:
                        # Handle both flat and nested script structures
                        manifest_scripts = custom_manifest.get('scripts', [])
                        
                        if hasattr(self, 'terminal'):
                            self.terminal.feed(f"\x1b[36m[*] Found {len(manifest_scripts) if isinstance(manifest_scripts, list) else len(manifest_scripts.keys())} items in manifest\x1b[0m\r\n".encode())
                        
                        if isinstance(manifest_scripts, dict):
                            # Nested structure (by category)
                            if hasattr(self, 'terminal'):
                                self.terminal.feed(f"\x1b[36m[*] Processing nested structure with categories: {list(manifest_scripts.keys())}\x1b[0m\r\n".encode())
                            
                            for category, category_scripts in manifest_scripts.items():
                                if hasattr(self, 'terminal'):
                                    self.terminal.feed(f"\x1b[36m[*] Category '{category}': {len(category_scripts) if isinstance(category_scripts, list) else 0} scripts\x1b[0m\r\n".encode())
                                
                                if isinstance(category_scripts, list):
                                    for script in category_scripts:
                                        script['category'] = category
                                        script['_source'] = 'custom'
                                        script['_source_name'] = custom_manifest_name
                                        custom_scripts.append(script)
                        else:
                            # Flat structure (list of scripts)
                            if hasattr(self, 'terminal'):
                                self.terminal.feed(f"\x1b[36m[*] Processing flat structure with {len(manifest_scripts)} scripts\x1b[0m\r\n".encode())
                            
                            for script in manifest_scripts:
                                script['_source'] = 'custom'
                                script['_source_name'] = custom_manifest_name
                                custom_scripts.append(script)
                        
                        # Add custom scripts and track IDs
                        if hasattr(self, 'terminal'):
                            self.terminal.feed(f"\x1b[36m[*] Processed {len(custom_scripts)} scripts from custom manifest\x1b[0m\r\n".encode())
                        
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
            
            # If no scripts from any source, show message
            if not all_scripts:
                if hasattr(self, 'terminal'):
                    self.terminal.feed("\x1b[33m+--------------------------------------------------------+\x1b[0m\r\n".encode())
                    self.terminal.feed("\x1b[33m|        No Repository Scripts Available                 |\x1b[0m\r\n".encode())
                    self.terminal.feed("\x1b[33m+--------------------------------------------------------+\x1b[0m\r\n".encode())
                    self.terminal.feed(b"\x1b[36m[!] No manifest sources are currently configured\x1b[0m\r\n\r\n")
                    
                    config = self.repository.load_config()
                    use_public = config.get('use_public_repository', False)
                    custom_url = config.get('custom_manifest_url', '')
                    
                    self.terminal.feed(b"\x1b[36mCurrent Configuration:\x1b[0m\r\n")
                    self.terminal.feed(f"  • Public Repository: {'✓ Enabled' if use_public else '✗ Disabled'}\r\n".encode())
                    self.terminal.feed(f"  • Custom Manifest URL: {custom_url if custom_url else '(not set)'}\r\n\r\n".encode())
                    
                    self.terminal.feed(b"\x1b[32mTo add scripts, please:\x1b[0m\r\n")
                    self.terminal.feed(b"  1. Go to 'Custom Manifests' tab to add an online manifest\r\n")
                    self.terminal.feed(b"  2. Click 'Create New Manifest' and enter a manifest URL\r\n")
                    self.terminal.feed(b"  3. Or enable Public Repository in Settings menu\r\n\r\n")
                return
            
            # Process all scripts from all sources
            for script in all_scripts:
                script_id = script.get('id')
                name = script.get('name')
                version = script.get('version', '1.0')
                category = script.get('category', 'tools')
                file_name = script.get('file_name', '')
                source = script.get('_source', 'unknown')
                source_name = script.get('_source_name', 'Unknown Source')
                
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
            
            if status_parts:
                sources_text = " + ".join(status_parts)
                if hasattr(self, 'terminal'):
                    self.terminal.feed(f"\x1b[32m[*] Repository tab: {sources_text}\x1b[0m\r\n".encode())
                    self.terminal.feed(f"\x1b[32m[*] Total: {total_count} scripts, {cached_count} cached\x1b[0m\r\n".encode())
                
        except Exception as e:
            print(f"Error populating repository tree: {e}")
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
        
        self.terminal.feed(b"\x1b[2J\x1b[H")  # Clear screen and move cursor to top
        self.terminal.feed(b"\x1b[32m[*] Updating all cached scripts...\x1b[0m\r\n")
        
        try:
            # Refresh manifest with terminal output (returns 4 values)
            global _SCRIPT_ID_MAP
            _, _, _, _SCRIPT_ID_MAP = load_scripts_from_manifest(terminal_widget=self.terminal)
            
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
                "• Add a Custom Manifest in the Custom Manifests tab"
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
        
        self.terminal.feed(b"\x1b[2J\x1b[H")  # Clear screen and move cursor to top
        self.terminal.feed(f"\x1b[32m[*] Downloading {total} scripts from configured sources...\x1b[0m\r\n".encode())
        
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
                    cached_path = self.repository.download_script(script_id)
                    if cached_path:
                        downloaded += 1
                        self.terminal.feed(f"\x1b[32m  ✓ Cached to {cached_path}\x1b[0m\r\n".encode())
                    else:
                        failed += 1
                        self.terminal.feed(f"\x1b[33m  ! Failed to download\x1b[0m\r\n".encode())
                except Exception as e:
                    failed += 1
                    self.terminal.feed(f"\x1b[31m  ✗ Error: {e}\x1b[0m\r\n".encode())
            
            self.terminal.feed(f"\x1b[32m[*] Download complete: {downloaded} downloaded, {failed} failed\x1b[0m\r\n".encode())
            
            # Auto-complete after short delay
            GLib.timeout_add(1500, self._complete_terminal_operation)
            
            # Refresh display
            self._populate_repository_tree()
            
            # Reload main tabs to reflect changes
            self._reload_main_tabs()
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            import traceback
            self.terminal.feed(f"\x1b[31m{traceback.format_exc()}\x1b[0m\r\n".encode())
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
        auto_check = Gtk.CheckButton(label="Auto-check for updates")
        auto_check.set_active(self.repo_config.get('auto_check_updates', True))
        content.pack_start(auto_check, False, False, 0)
        
        auto_install = Gtk.CheckButton(label="Auto-install updates")
        auto_install.set_active(self.repo_config.get('auto_install_updates', True))
        content.pack_start(auto_install, False, False, 0)
        
        interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        interval_label = Gtk.Label(label="Check interval (minutes):")
        interval_spin = Gtk.SpinButton()
        interval_spin.set_range(1, 1440)
        interval_spin.set_increments(1, 10)
        interval_spin.set_value(self.repo_config.get('update_check_interval_minutes', 30))
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
        public_repo_note.set_markup("<small><i>Note: Custom manifests can be configured in the 'Custom Manifests' tab.\nThis includes both local directory scanning and online manifest URLs.</i></small>")
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
            
            self.terminal.feed("\x1b[2J\x1b[H\x1b[32m[*] Repository settings saved successfully\x1b[0m\r\n".encode())
            
            # Check if public repository setting changed and refresh UI
            if old_public_repo != new_public_repo:
                # Check if custom manifest is configured
                has_custom_manifest = bool(self.repo_config.get('custom_manifest_url', ''))
                
                if not new_public_repo:
                    if has_custom_manifest:
                        self.terminal.feed("\x1b[33m[*] Public repository disabled - custom manifest active\x1b[0m\r\n".encode())
                    else:
                        self.terminal.feed("\x1b[33m[*] Public repository disabled - no scripts available (configure custom manifest)\x1b[0m\r\n".encode())
                else:
                    if has_custom_manifest:
                        self.terminal.feed("\x1b[33m[*] Public repository enabled - showing scripts from both sources\x1b[0m\r\n".encode())
                    else:
                        self.terminal.feed("\x1b[33m[*] Public repository enabled - showing lv_linux_learn scripts\x1b[0m\r\n".encode())
                
                # Refresh UI to reflect public repository setting change
                self.terminal.feed("\x1b[33m[*] Refreshing interface to show updated script sources...\x1b[0m\r\n".encode())
                GLib.timeout_add(500, self._refresh_all_script_data)
            
            # Auto-complete after short delay
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
        self.terminal.feed(f"\x1b[32m[*] Processing {len(selected_scripts)} selected scripts...\x1b[0m\r\n".encode())
        
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
                    continue
                
                # Remote script - download to cache
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
            except Exception as e:
                error_msg = "checksum verification failed" if "Checksum verification failed" in str(e) else f"error: {e}"
                self.terminal.feed(f"  ✗ {script_name} ({error_msg})\r\n".encode())
                failed_count += 1
        
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
            global NON_STANDARD_CATEGORIES
            
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
            
            # Update NON_STANDARD_CATEGORIES for dynamic tabs
            NON_STANDARD_CATEGORIES.clear()
            for category in _scripts.keys():
                if category not in ['install', 'tools', 'exercises', 'uninstall']:
                    NON_STANDARD_CATEGORIES[category] = {
                        'scripts': _scripts.get(category, []),
                        'names': _names.get(category, []),
                        'descriptions': _descriptions.get(category, [])
                    }
            
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
            global NON_STANDARD_CATEGORIES
            
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
            
            # Update NON_STANDARD_CATEGORIES for dynamic tabs
            NON_STANDARD_CATEGORIES.clear()
            for category in _scripts.keys():
                if category not in ['install', 'tools', 'exercises', 'uninstall']:
                    NON_STANDARD_CATEGORIES[category] = {
                        'scripts': _scripts.get(category, []),
                        'names': _names.get(category, []),
                        'descriptions': _descriptions.get(category, [])
                    }  
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
                self.terminal.feed(f"\x1b[36m[*] Cache status: {cached_count} scripts cached\x1b[0m\r\n".encode())
        except Exception as e:
            # Silently handle errors, don't interrupt operations
            pass

    def _create_custom_manifest_tab(self):
        """Create the custom manifest management tab"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        
        # Control buttons - All actions in one row
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_homogeneous(True)
        
        create_btn = Gtk.Button(label="Create New Manifest")
        create_btn.get_style_context().add_class("suggested-action")
        create_btn.connect("clicked", self._on_create_custom_manifest)
        button_box.pack_start(create_btn, True, True, 0)
        
        refresh_btn = Gtk.Button(label="Refresh List")
        refresh_btn.connect("clicked", self._on_refresh_custom_manifests)
        button_box.pack_start(refresh_btn, True, True, 0)
        
        edit_btn = Gtk.Button(label="Edit Selected")
        edit_btn.connect("clicked", self._on_edit_custom_manifest)
        button_box.pack_start(edit_btn, True, True, 0)
        
        delete_btn = Gtk.Button(label="Delete Selected")
        delete_btn.get_style_context().add_class("destructive-action")
        delete_btn.connect("clicked", self._on_delete_selected_manifest)
        button_box.pack_start(delete_btn, True, True, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        # Custom manifests list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Store: name(str), description(str), version(str), created(str), total_scripts(int), categories(str)
        self.custom_manifest_store = Gtk.ListStore(str, str, str, str, int, str)
        
        self.custom_manifest_tree = Gtk.TreeView(model=self.custom_manifest_store)
        
        # Name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Name", name_renderer, text=0)
        name_column.set_resizable(True)
        name_column.set_min_width(150)
        self.custom_manifest_tree.append_column(name_column)
        
        # Description column
        desc_renderer = Gtk.CellRendererText()
        desc_renderer.set_property("ellipsize", 3)  # End ellipsize
        desc_column = Gtk.TreeViewColumn("Description", desc_renderer, text=1)
        desc_column.set_resizable(True)
        desc_column.set_min_width(200)
        self.custom_manifest_tree.append_column(desc_column)
        
        # Scripts count column
        count_renderer = Gtk.CellRendererText()
        count_column = Gtk.TreeViewColumn("Scripts", count_renderer, text=4)
        count_column.set_min_width(60)
        self.custom_manifest_tree.append_column(count_column)
        
        # Categories column
        categories_renderer = Gtk.CellRendererText()
        categories_renderer.set_property("ellipsize", 3)  # End ellipsize
        categories_column = Gtk.TreeViewColumn("Categories", categories_renderer, text=5)
        categories_column.set_resizable(True)
        categories_column.set_min_width(100)
        self.custom_manifest_tree.append_column(categories_column)
        
        # Created column
        created_renderer = Gtk.CellRendererText()
        created_column = Gtk.TreeViewColumn("Created", created_renderer, text=3)
        created_column.set_min_width(100)
        self.custom_manifest_tree.append_column(created_column)
        
        # Connect row activation (double-click to activate)
        self.custom_manifest_tree.connect("row-activated", self._on_manifest_row_activated)
        
        scrolled.add(self.custom_manifest_tree)
        vbox.pack_start(scrolled, True, True, 0)
        
        # Instructions
        instructions_label = Gtk.Label()
        instructions_label.set_markup(
            "<i>All custom manifests are automatically loaded with scripts from all active sources.\n"
            "Double-click to activate. Use buttons above for edit/delete. Configure public repository via Settings menu.</i>"
        )
        instructions_label.set_line_wrap(True)
        vbox.pack_start(instructions_label, False, False, 0)
        
        # Populate tree
        self._populate_custom_manifest_tree()
        
        return vbox
    
    def _populate_custom_manifest_tree(self):
        """Populate custom manifest tree view"""
        if not self.custom_manifest_creator:
            return
        
        self.custom_manifest_store.clear()
        
        try:
            manifests = self.custom_manifest_creator.list_custom_manifests()
            
            for manifest in manifests:
                name = manifest['name']
                description = manifest['description']
                version = manifest['version']
                created = manifest['created']
                total_scripts = manifest['total_scripts']
                categories = ', '.join(manifest['categories'])
                
                # Format created date
                try:
                    from datetime import datetime
                    created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    created_text = created_dt.strftime("%Y-%m-%d %H:%M")
                except:
                    created_text = created[:16] if len(created) > 16 else created
                
                self.custom_manifest_store.append([
                    name,
                    description,
                    version,
                    created_text,
                    total_scripts,
                    categories
                ])
                
        except Exception as e:
            print(f"Error populating custom manifest tree: {e}")
    
    def _on_create_custom_manifest(self, button):
        """Show create custom manifest dialog"""
        if not self.custom_manifest_creator:
            return
        
        dialog = Gtk.Dialog(
            title="Create Custom Manifest",
            parent=self,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Create", Gtk.ResponseType.OK
        )
        dialog.set_default_size(600, 500)
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(10)
        content.set_margin_end(10)
        content.set_margin_top(10)
        content.set_margin_bottom(10)
        
        # Name entry (common to both methods)
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        name_label = Gtk.Label(label="Manifest Name:")
        name_label.set_size_request(120, -1)
        name_entry = Gtk.Entry()
        name_entry.set_placeholder_text("my_custom_scripts")
        name_box.pack_start(name_label, False, False, 0)
        name_box.pack_start(name_entry, True, True, 0)
        content.pack_start(name_box, False, False, 0)
        
        # Description entry (common to both methods)
        desc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        desc_label = Gtk.Label(label="Description:")
        desc_label.set_size_request(120, -1)
        desc_entry = Gtk.Entry()
        desc_entry.set_placeholder_text("My collection of custom scripts")
        desc_box.pack_start(desc_label, False, False, 0)
        desc_box.pack_start(desc_entry, True, True, 0)
        content.pack_start(desc_box, False, False, 0)
        
        # Method selection notebook
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(Gtk.PositionType.TOP)
        content.pack_start(notebook, True, True, 0)
        
        # Tab 1: Directory Scanning
        dir_scan_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        dir_scan_box.set_margin_start(10)
        dir_scan_box.set_margin_end(10)
        dir_scan_box.set_margin_top(10)
        dir_scan_box.set_margin_bottom(10)
        
        # Recursive checkbox
        recursive_check = Gtk.CheckButton(label="Scan directories recursively")
        recursive_check.set_active(True)
        dir_scan_box.pack_start(recursive_check, False, False, 0)
        
        # Directories list
        dir_scan_box.pack_start(Gtk.Label(label="Directories to scan:"), False, False, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        
        # Store: directory path
        dir_store = Gtk.ListStore(str)
        dir_tree = Gtk.TreeView(model=dir_store)
        
        path_renderer = Gtk.CellRendererText()
        path_column = Gtk.TreeViewColumn("Directory Path", path_renderer, text=0)
        dir_tree.append_column(path_column)
        
        scrolled.add(dir_tree)
        dir_scan_box.pack_start(scrolled, True, True, 0)
        
        # Directory buttons
        dir_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_dir_btn = Gtk.Button(label="Add Directory")
        add_dir_btn.connect("clicked", lambda b: self._add_directory_to_scan(dir_store, dialog))
        dir_button_box.pack_start(add_dir_btn, False, False, 0)
        
        remove_dir_btn = Gtk.Button(label="Remove Selected")
        remove_dir_btn.connect("clicked", lambda b: self._remove_selected_directory(dir_tree, dir_store))
        dir_button_box.pack_start(remove_dir_btn, False, False, 0)
        
        dir_scan_box.pack_start(dir_button_box, False, False, 0)
        
        # Checksum verification toggle for directory scan
        dir_verify_checksums = Gtk.CheckButton(label="Verify script checksums (recommended for security)")
        dir_verify_checksums.set_active(True)  # Default to enabled
        dir_verify_checksums.set_margin_top(10)
        dir_verify_checksums.set_tooltip_text("Verify scripts match checksums during execution. Recommended for security.")
        dir_scan_box.pack_start(dir_verify_checksums, False, False, 0)
        
        # Add directory scanning tab to notebook
        dir_tab_label = Gtk.Label(label="📁 Directory Scan")
        notebook.append_page(dir_scan_box, dir_tab_label)
        
        # Tab 2: Online Manifest
        online_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        online_box.set_margin_start(10)
        online_box.set_margin_end(10)
        online_box.set_margin_top(10)
        online_box.set_margin_bottom(10)
        
        # Instructions
        instruction_label = Gtk.Label()
        instruction_label.set_markup(
            "<b>Import from Online Manifest</b>\n\n"
            "Enter the URL of an existing manifest.json file to import.\n"
            "This can be from a GitHub repository, web server, or local file.\n\n"
            "<i>Examples:</i>\n"
            "• https://raw.githubusercontent.com/user/repo/main/manifest.json\n"
            "• https://example.com/my-scripts/manifest.json\n"
            "• file:///home/user/my-manifest.json"
        )
        instruction_label.set_line_wrap(True)
        instruction_label.set_xalign(0)
        online_box.pack_start(instruction_label, False, False, 0)
        
        # URL entry
        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        url_label = Gtk.Label(label="Manifest URL:")
        url_label.set_size_request(100, -1)
        url_entry = Gtk.Entry()
        url_entry.set_placeholder_text("https://raw.githubusercontent.com/user/repo/main/manifest.json")
        url_box.pack_start(url_label, False, False, 0)
        url_box.pack_start(url_entry, True, True, 0)
        online_box.pack_start(url_box, False, False, 0)
        
        # Verify button
        verify_btn = Gtk.Button(label="Verify URL")
        verify_btn.connect("clicked", lambda b: self._verify_manifest_url(url_entry, verify_status_label))
        online_box.pack_start(verify_btn, False, False, 0)
        
        # Status label
        verify_status_label = Gtk.Label()
        verify_status_label.set_line_wrap(True)
        verify_status_label.set_xalign(0)
        online_box.pack_start(verify_status_label, False, False, 0)
        
        # Checksum verification toggle for online manifest
        url_verify_checksums = Gtk.CheckButton(label="Verify script checksums (recommended for security)")
        url_verify_checksums.set_active(True)  # Default to enabled
        url_verify_checksums.set_margin_top(10)
        url_verify_checksums.set_tooltip_text("Verify downloaded scripts match expected checksums. Disable only if checksums are unavailable.")
        online_box.pack_start(url_verify_checksums, False, False, 0)
        
        # Add online manifest tab to notebook
        online_tab_label = Gtk.Label(label="🌐 Online Manifest")
        notebook.append_page(online_box, online_tab_label)
        
        content.show_all()
        
        while True:
            response = dialog.run()
            
            if response != Gtk.ResponseType.OK:
                dialog.destroy()
                return
            
            # Validate inputs
            name = name_entry.get_text().strip()
            description = desc_entry.get_text().strip()
            current_tab = notebook.get_current_page()
            
            if not name:
                self._show_error_dialog(dialog, "Please enter a manifest name.")
                continue
            
            # Handle based on current tab
            if current_tab == 0:  # Directory Scan tab
                recursive = recursive_check.get_active()
                directories = []
                for row in dir_store:
                    directories.append(row[0])
                
                if not directories:
                    self._show_error_dialog(dialog, "Please add at least one directory to scan.")
                    continue
                
                # Create manifest from directories
                dialog.destroy()
                
                success, message = self.custom_manifest_creator.create_manifest(
                    name, directories, description, recursive, dir_verify_checksums.get_active()
                )
                
            else:  # Online Manifest tab
                url = url_entry.get_text().strip()
                
                if not url:
                    self._show_error_dialog(dialog, "Please enter a manifest URL.")
                    continue
                
                if not (url.startswith(('http://', 'https://', 'file://'))):
                    self._show_error_dialog(dialog, "URL must start with http://, https://, or file://")
                    continue
                
                # Import manifest from URL
                dialog.destroy()
                
                success, message = self.custom_manifest_creator.import_manifest_from_url(
                    name, url, description, url_verify_checksums.get_active()
                )
            
            if success:
                self.terminal.feed(f"\x1b[32m[✓] {message}\x1b[0m\r\n".encode())
                # Auto-activate the imported manifest
                self.custom_manifest_creator.switch_to_custom_manifest(name)
                # Refresh repository system
                if self.repository:
                    self.repository.refresh_repository_url()
                # Reload all tabs to create dynamic tabs for new manifest
                self._reload_main_tabs()
                self._populate_custom_manifest_tree()
            else:
                self.terminal.feed(f"\x1b[31m[✗] {message}\x1b[0m\r\n".encode())
            
            return
    
    def _show_edit_manifest_dialog(self, manifest_name):
        """Show edit dialog for existing custom manifest"""
        if not self.custom_manifest_creator:
            return
        
        # Get manifest info
        manifests = self.custom_manifest_creator.list_custom_manifests()
        manifest_info = next((m for m in manifests if m['name'] == manifest_name), None)
        
        if not manifest_info:
            self._show_error_dialog(self, f"Manifest '{manifest_name}' not found")
            return
        
        dialog = Gtk.Dialog(
            title=f"Edit Manifest: {manifest_name}",
            parent=self,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Save Changes", Gtk.ResponseType.OK
        )
        dialog.set_default_size(600, 500)
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(10)
        content.set_margin_end(10)
        content.set_margin_top(10)
        content.set_margin_bottom(10)
        
        # Show manifest type
        type_label = Gtk.Label()
        manifest_type = manifest_info.get('type', 'directory_scan')
        type_text = "Directory Scan" if manifest_type == 'directory_scan' else f"Imported URL ({manifest_info.get('source_url', 'unknown')})"
        type_label.set_markup(f"<b>Manifest Type:</b> {type_text}")
        type_label.set_xalign(0)
        content.pack_start(type_label, False, False, 0)
        
        # Name entry (allow editing)
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        name_label = Gtk.Label(label="Manifest Name:")
        name_label.set_size_request(120, -1)
        name_entry = Gtk.Entry()
        name_entry.set_text(manifest_name)
        name_box.pack_start(name_label, False, False, 0)
        name_box.pack_start(name_entry, True, True, 0)
        content.pack_start(name_box, False, False, 0)
        
        # Description entry (allow editing)
        desc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        desc_label = Gtk.Label(label="Description:")
        desc_label.set_size_request(120, -1)
        desc_entry = Gtk.Entry()
        desc_entry.set_text(manifest_info.get('description', ''))
        desc_box.pack_start(desc_label, False, False, 0)
        desc_box.pack_start(desc_entry, True, True, 0)
        content.pack_start(desc_box, False, False, 0)
        
        # Checksum verification toggle (for all types)
        content.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)
        
        verify_checksums = Gtk.CheckButton(label="Verify script checksums (recommended for security)")
        verify_checksums.set_active(manifest_info.get('verify_checksums', True))
        verify_checksums.set_tooltip_text("Verify scripts match checksums during execution. Recommended for security.")
        content.pack_start(verify_checksums, False, False, 0)
        
        # Type-specific editing
        if manifest_type == 'imported_url':
            # URL manifest - allow URL editing
            url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            url_label = Gtk.Label(label="Source URL:")
            url_label.set_size_request(120, -1)
            url_entry = Gtk.Entry()
            url_entry.set_text(manifest_info.get('source_url', ''))
            url_box.pack_start(url_label, False, False, 0)
            url_box.pack_start(url_entry, True, True, 0)
            content.pack_start(url_box, False, False, 0)
            
            # Verify button
            verify_btn = Gtk.Button(label="Verify URL")
            verify_status_label = Gtk.Label()
            verify_btn.connect("clicked", lambda b: self._verify_manifest_url(url_entry, verify_status_label))
            content.pack_start(verify_btn, False, False, 0)
            content.pack_start(verify_status_label, False, False, 0)
            
        else:
            # Directory-based manifest - show read-only info for now
            # (Could be enhanced later to allow directory modification)
            info_label = Gtk.Label()
            info_label.set_markup(
                f"<b>Statistics:</b>\n"
                f"• Total Scripts: {manifest_info.get('total_scripts', 0)}\n"
                f"• Categories: {', '.join(manifest_info.get('categories', []))}\n"
                f"• Created: {manifest_info.get('created', 'Unknown')}\n\n"
                f"<i>Note: Directory-based manifests can only have name and description edited.\n"
                f"To modify directories, delete and recreate the manifest.</i>"
            )
            info_label.set_line_wrap(True)
            info_label.set_xalign(0)
            content.pack_start(info_label, True, True, 0)
        
        dialog.show_all()
        
        while True:
            response = dialog.run()
            
            if response != Gtk.ResponseType.OK:
                dialog.destroy()
                return
            
            # Validate inputs
            new_name = name_entry.get_text().strip()
            new_description = desc_entry.get_text().strip()
            new_verify_checksums = verify_checksums.get_active()
            
            if not new_name:
                self._show_error_dialog(dialog, "Please enter a manifest name.")
                continue
            
            if manifest_type == 'imported_url':
                new_url = url_entry.get_text().strip()
                if not new_url:
                    self._show_error_dialog(dialog, "Please enter a manifest URL.")
                    continue
                if not (new_url.startswith(('http://', 'https://', 'file://'))):
                    self._show_error_dialog(dialog, "URL must start with http://, https://, or file://")
                    continue
            
            # Apply changes
            dialog.destroy()
            
            if manifest_type == 'imported_url':
                # For URL manifests, we need to re-import if URL changed or update metadata
                if new_url != manifest_info.get('source_url', '') or new_name != manifest_name:
                    # Delete old manifest and create new one
                    self.custom_manifest_creator.delete_custom_manifest(manifest_name)
                    success, message = self.custom_manifest_creator.import_manifest_from_url(
                        new_name, new_url, new_description, new_verify_checksums
                    )
                else:
                    # Just update description and checksum setting
                    success, message = self.custom_manifest_creator.update_manifest_metadata(
                        manifest_name, new_name, new_description, new_url, new_verify_checksums
                    )
            else:
                # For directory manifests, just update metadata
                success, message = self.custom_manifest_creator.update_manifest_metadata(
                    manifest_name, new_name, new_description, None, new_verify_checksums
                )
            
            if success:
                self.terminal.feed(f"\x1b[32m[✓] {message}\x1b[0m\r\n".encode())
                self._populate_custom_manifest_tree()
                self._update_repo_status()
            else:
                self.terminal.feed(f"\x1b[31m[✗] {message}\x1b[0m\r\n".encode())
            
            return
    
    def _add_directory_to_scan(self, dir_store, parent_dialog):
        """Add a directory to the scan list"""
        dialog = Gtk.FileChooserDialog(
            title="Select Directory to Scan",
            parent=parent_dialog,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Set default to home directory
        dialog.set_current_folder(str(Path.home()))
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            directory = dialog.get_filename()
            # Check if directory is already in the list
            for row in dir_store:
                if row[0] == directory:
                    dialog.destroy()
                    return
            dir_store.append([directory])
        
        dialog.destroy()
    
    def _remove_selected_directory(self, tree_view, dir_store):
        """Remove selected directory from the scan list"""
        selection = tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            model.remove(tree_iter)
    
    def _verify_manifest_url(self, url_entry, status_label):
        """Verify that a manifest URL is accessible and valid"""
        url = url_entry.get_text().strip()
        
        if not url:
            status_label.set_markup("<span color='red'>Please enter a URL</span>")
            return
        
        status_label.set_markup("<span color='blue'>Verifying URL...</span>")
        
        # Use GLib.timeout_add to do this in a non-blocking way
        GLib.timeout_add(100, self._do_verify_url, url, status_label)
    
    def _do_verify_url(self, url, status_label):
        """Perform the actual URL verification"""
        try:
            import urllib.request
            import json
            
            # Handle file:// URLs
            if url.startswith('file://'):
                file_path = url[7:]  # Remove 'file://' prefix
                if not os.path.exists(file_path):
                    status_label.set_markup("<span color='red'>✗ File not found</span>")
                    return False
                
                # Try to load and validate JSON
                with open(file_path, 'r') as f:
                    manifest = json.load(f)
                
                # Basic validation
                if 'scripts' in manifest or 'version' in manifest:
                    status_label.set_markup("<span color='green'>✓ Valid manifest file</span>")
                else:
                    status_label.set_markup("<span color='orange'>⚠ File exists but may not be a valid manifest</span>")
                return False
            
            # Handle HTTP/HTTPS URLs
            elif url.startswith(('http://', 'https://')):
                # Try to fetch the URL
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'lv_linux_learn/2.1.0')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = response.read()
                    manifest = json.loads(data)
                    
                    # Basic validation
                    if 'scripts' in manifest or 'version' in manifest:
                        status_label.set_markup("<span color='green'>✓ Valid manifest URL</span>")
                    else:
                        status_label.set_markup("<span color='orange'>⚠ URL accessible but may not be a valid manifest</span>")
                return False
            
            else:
                status_label.set_markup("<span color='red'>✗ URL must start with http://, https://, or file://</span>")
                return False
                
        except json.JSONDecodeError:
            status_label.set_markup("<span color='red'>✗ Invalid JSON format</span>")
        except urllib.error.URLError as e:
            status_label.set_markup(f"<span color='red'>✗ Cannot access URL: {e.reason}</span>")
        except Exception as e:
            status_label.set_markup(f"<span color='red'>✗ Error: {str(e)}</span>")
        
        return False  # Remove the timeout
    
    def _show_error_dialog(self, parent, message):
        """Show an error dialog - uses UI helper module"""
        if UI:
            UI.show_error_dialog(parent, message)
        else:
            # Fallback
            error_dialog = Gtk.MessageDialog(
                transient_for=parent,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error"
            )
            error_dialog.format_secondary_text(message)
            error_dialog.run()
            error_dialog.destroy()
    
    def _on_edit_custom_manifest(self, button):
        """Edit the selected custom manifest"""
        selection = self.custom_manifest_tree.get_selection()
        model, tree_iter = selection.get_selected()
        
        if not tree_iter:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="No Manifest Selected"
            )
            dialog.format_secondary_text("Please select a custom manifest to edit.")
            dialog.run()
            dialog.destroy()
            return
        
        manifest_name = model.get_value(tree_iter, 0)
        self._show_edit_manifest_dialog(manifest_name)
    
    def _on_refresh_custom_manifests(self, button):
        """Refresh the custom manifests list"""
        self._populate_custom_manifest_tree()
        self.terminal.feed(b"\x1b[32m[*] Custom manifests refreshed\x1b[0m\r\n")
    
    def _on_delete_selected_manifest(self, button):
        """Delete the selected custom manifest"""
        selection = self.custom_manifest_tree.get_selection()
        model, tree_iter = selection.get_selected()
        
        if not tree_iter:
            if UI:
                UI.show_no_selection_dialog(self, "manifest")
            return
        
        manifest_name = model.get_value(tree_iter, 0)
        self._delete_manifest_by_name(manifest_name)
    
    def _on_manifest_row_activated(self, tree_view, path, column):
        """Handle double-click on manifest row - edit manifest"""
        model = tree_view.get_model()
        tree_iter = model.get_iter(path)
        manifest_name = model.get_value(tree_iter, 0)
        
        if not self.custom_manifest_creator:
            return
        
        # Edit the manifest
        self._show_edit_manifest_dialog(manifest_name)
    
    def _delete_manifest_by_name(self, manifest_name):
        """Delete a custom manifest"""
        if not self.custom_manifest_creator:
            return
        
        # Confirmation dialog
        if UI:
            confirmed = UI.show_confirmation_dialog(
                self,
                f"Delete Manifest '{manifest_name}'?",
                "Confirm Deletion",
                "This will permanently delete the manifest and all associated files.\nThis action cannot be undone."
            )
        else:
            # Fallback
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Delete Manifest '{manifest_name}'?"
            )
            dialog.format_secondary_text(
                "This will permanently delete the manifest and all associated files.\n"
                "This action cannot be undone."
            )
            response = dialog.run()
            dialog.destroy()
            confirmed = response == Gtk.ResponseType.YES
        
        if not confirmed:
            return
        
        self.terminal.feed(b"\x1b[2J\x1b[H")  # Clear screen
        self.terminal.feed(f"\x1b[33m[*] Deleting manifest '{manifest_name}'...\x1b[0m\r\n".encode())
        
        try:
            success, message = self.custom_manifest_creator.delete_custom_manifest(manifest_name)
            
            if success:
                self.terminal.feed(f"\x1b[32m[✓] {message}\x1b[0m\r\n".encode())
                # Refresh the manifest list
                self._populate_custom_manifest_tree()
                
                # Refresh main script tabs to remove scripts from deleted manifest
                self.terminal.feed(b"\x1b[33m[*] Refreshing script tabs...\x1b[0m\r\n")
                GLib.timeout_add(200, self._reload_main_tabs)
                
                # Update repository view
                if hasattr(self, '_populate_repository_tree'):
                    GLib.timeout_add(400, self._populate_repository_tree)
            else:
                self.terminal.feed(f"\x1b[31m[!] {message}\x1b[0m\r\n".encode())
                self._show_error_dialog(self, message)
        
        except Exception as e:
            error_msg = f"Failed to delete manifest: {e}"
            self.terminal.feed(f"\x1b[31m[!] {error_msg}\x1b[0m\r\n".encode())
            self._show_error_dialog(self, error_msg)
    
    def _activate_custom_manifest(self, manifest_name):
        """Activate a custom manifest"""
        if not self.custom_manifest_creator:
            return
        
        self.terminal.feed(b"\x1b[2J\x1b[H")  # Clear screen
        self.terminal.feed(f"\x1b[32m[*] Activating manifest '{manifest_name}'...\x1b[0m\r\n".encode())
        
        try:
            # Disable public repository when activating custom manifest
            if self.repository:
                config = self.repository.load_config()
                config['use_public_repository'] = False
                self.repository.save_config(config)
            
            # Switch to the custom manifest
            success, message = self.custom_manifest_creator.switch_to_custom_manifest(manifest_name)
            
            if success:
                self.terminal.feed(f"\x1b[32m[✓] {message}\x1b[0m\r\n".encode())
                self.terminal.feed(b"\x1b[32m[*] Reloading scripts...\x1b[0m\r\n")
                
                # Refresh the manifest list to show active indicator
                self._populate_custom_manifest_tree()
                
                # Refresh UI to load scripts from the new manifest
                self._refresh_ui_after_manifest_switch()
                
                self.terminal.feed("\x1b[32m[*] Manifest activated successfully\x1b[0m\r\n".encode())
            else:
                self.terminal.feed(f"\x1b[31m[!] {message}\x1b[0m\r\n".encode())
                self._show_error_dialog(self, message)
        
        except Exception as e:
            error_msg = f"Failed to activate manifest: {e}"
            self.terminal.feed(f"\x1b[31m[!] {error_msg}\x1b[0m\r\n".encode())
            import traceback
            traceback.print_exc()
            self._show_error_dialog(self, error_msg)
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
        """Refresh UI after switching manifests - this is the key method for updating main tabs"""
        try:
            # Clear manifest cache to force reload from new source
            global MANIFEST_CACHE_FILE
            if MANIFEST_CACHE_FILE.exists():
                MANIFEST_CACHE_FILE.unlink()
                self.terminal.feed(b"\x1b[33m[*] Cleared manifest cache\x1b[0m\r\n")
            
            # Refresh repository system to use new manifest URL
            if self.repository:
                self.repository.refresh_repository_url()
                self.terminal.feed(b"\x1b[33m[*] Refreshed repository configuration\x1b[0m\r\n")
            
            # Force refresh of repository tree if available
            if self.repo_enabled and hasattr(self, '_populate_repository_tree'):
                self._populate_repository_tree()
                self._update_repo_status()
                self.terminal.feed(b"\x1b[33m[*] Updated repository view\x1b[0m\r\n")
            
            # The most important part: reload main script tabs with new manifest data
            self._reload_main_tabs()
            self.terminal.feed(b"\x1b[32m[+] Main script tabs refreshed with new manifest\x1b[0m\r\n")
            
            return False  # Don't repeat the timeout
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
        """
        Repopulate liststores for all main tabs and dynamic category tabs.
        Uses global manifest data (SCRIPTS, TOOLS_SCRIPTS, etc.)
        """
        try:
            # First, check if we need to create new dynamic tabs
            self._ensure_dynamic_tabs_exist()
            
            # Clear and repopulate install tab
            if hasattr(self, 'install_liststore'):
                self.install_liststore.clear()
                for i, script_path in enumerate(SCRIPTS):
                    if i < len(SCRIPT_NAMES) and i < len(DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, "install", SCRIPT_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category="install")
                        icon = "✓" if is_cached else "☁️"
                        self.install_liststore.append([icon, SCRIPT_NAMES[i], script_path, DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
            
            # Clear and repopulate tools tab  
            if hasattr(self, 'tools_liststore'):
                self.tools_liststore.clear()
                for i, script_path in enumerate(TOOLS_SCRIPTS):
                    if i < len(TOOLS_NAMES) and i < len(TOOLS_DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, "tools", TOOLS_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category="tools")
                        icon = "✓" if is_cached else "☁️"
                        self.tools_liststore.append([icon, TOOLS_NAMES[i], script_path, TOOLS_DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
            
            # Clear and repopulate exercises tab
            if hasattr(self, 'exercises_liststore'):
                self.exercises_liststore.clear()
                for i, script_path in enumerate(EXERCISES_SCRIPTS):
                    if i < len(EXERCISES_NAMES) and i < len(EXERCISES_DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, "exercises", EXERCISES_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category="exercises")
                        icon = "✓" if is_cached else "☁️"
                        self.exercises_liststore.append([icon, EXERCISES_NAMES[i], script_path, EXERCISES_DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
            
            # Clear and repopulate uninstall tab
            if hasattr(self, 'uninstall_liststore'):
                self.uninstall_liststore.clear()
                for i, script_path in enumerate(UNINSTALL_SCRIPTS):
                    if i < len(UNINSTALL_NAMES) and i < len(UNINSTALL_DESCRIPTIONS):
                        metadata = self._build_script_metadata(script_path, "uninstall", UNINSTALL_NAMES[i])
                        script_id = metadata.get('script_id', '')
                        is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category="uninstall")
                        icon = "✓" if is_cached else "☁️"
                        self.uninstall_liststore.append([icon, UNINSTALL_NAMES[i], script_path, UNINSTALL_DESCRIPTIONS[i], False, json.dumps(metadata), script_id])
            
            # Repopulate dynamic category tabs
            if hasattr(self, 'dynamic_category_tabs'):
                global NON_STANDARD_CATEGORIES
                for category, data in NON_STANDARD_CATEGORIES.items():
                    # Find the liststore for this category
                    if category in self.dynamic_category_tabs:
                        liststore = self.dynamic_category_tabs[category].get('liststore')
                        if liststore:
                            liststore.clear()
                            scripts = data.get('scripts', [])
                            names = data.get('names', [])
                            descriptions = data.get('descriptions', [])
                            for i, script_path in enumerate(scripts):
                                if i < len(names) and i < len(descriptions):
                                    metadata = self._build_script_metadata(script_path, category, names[i])
                                    script_id = metadata.get('script_id', '')
                                    is_cached = self._is_script_cached(script_id=script_id, script_path=script_path, category=category)
                                    icon = "✓" if is_cached else "☁️"
                                    liststore.append([icon, names[i], script_path, descriptions[i], False, json.dumps(metadata), script_id])
                        
        except Exception as e:
            print(f"Error repopulating tab stores: {e}")
    
    def _ensure_dynamic_tabs_exist(self):
        """Ensure dynamic tabs exist for all non-standard categories"""
        try:
            global NON_STANDARD_CATEGORIES
            
            if not hasattr(self, 'dynamic_category_tabs'):
                self.dynamic_category_tabs = {}
            
            # Check which categories need tabs created
            for category, data in NON_STANDARD_CATEGORIES.items():
                if category not in self.dynamic_category_tabs:
                    # Create new tab for this category
                    category_box = self._create_script_tab(data['scripts'], data['descriptions'], category)
                    
                    # Get appropriate emoji for category
                    category_emoji = {
                        'custom': '📦',
                        'ai': '🤖',
                        'network': '🌐',
                        'security': '🔒',
                        'database': '🗄',
                        'docker': '🐳',
                        'other': '📝'
                    }.get(category.lower(), '📦')
                    
                    category_label = self._create_tab_label(f"{category_emoji} {category.capitalize()}", category)
                    
                    # Find the position to insert (before Repository and Custom Manifests tabs)
                    # These are always the last 2 tabs
                    n_pages = self.notebook.get_n_pages()
                    insert_position = n_pages - 2 if n_pages >= 2 else n_pages
                    
                    self.notebook.insert_page(category_box, category_label, insert_position)
                    self.notebook.show_all()
                    
                    self.dynamic_category_tabs[category] = {
                        'box': category_box,
                        'label': category_label
                    }
            
            # Remove tabs for categories that no longer exist
            categories_to_remove = []
            for category in list(self.dynamic_category_tabs.keys()):
                if category not in NON_STANDARD_CATEGORIES:
                    categories_to_remove.append(category)
            
            for category in categories_to_remove:
                tab_data = self.dynamic_category_tabs[category]
                page_num = self.notebook.page_num(tab_data['box'])
                if page_num >= 0:
                    self.notebook.remove_page(page_num)
                del self.dynamic_category_tabs[category]
                
        except Exception as e:
            print(f"Error ensuring dynamic tabs exist: {e}")

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
        """Handle Run button - uses centralized execution logic"""
        widgets = self.get_current_widgets()
        selection = widgets['treeview'].get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        
        # Get script path and metadata (use column 2 for path)
        COL_PATH = C.COL_PATH if C else 2
        script_path = model[treeiter][COL_PATH]
        metadata = self._get_script_metadata(model, treeiter)
        script_name = os.path.basename(script_path)
        
        # Use centralized execution logic
        success = self._execute_script_unified(script_path, metadata)
        
        # If remote/uncached, offer to download
        if not success and metadata.get("type") == "remote":
            if self.repository and self.repo_enabled:
                manifest_script_id, manifest_path = self._get_manifest_script_id(script_name, script_path)
                
                if manifest_script_id:
                    # Use UI helper for download confirmation
                    confirmed = UI.show_download_confirmation_dialog(self, script_name) if UI else False
                    
                    if not confirmed and not UI:
                        # Fallback if UI module not available
                        dialog = Gtk.MessageDialog(
                            transient_for=self,
                            flags=0,
                            message_type=Gtk.MessageType.QUESTION,
                            buttons=Gtk.ButtonsType.YES_NO,
                            text="☁️ Download Script?"
                        )
                        dialog.format_secondary_text(
                            f"The script '{script_name}' needs to be downloaded to your cache.\n\n"
                            "Download and run from cache?"
                        )
                        response = dialog.run()
                        dialog.destroy()
                        confirmed = response == Gtk.ResponseType.YES
                    
                    if confirmed:
                        self.terminal.feed(f"\x1b[32m[*] Downloading ☁️ {script_name}...\x1b[0m\r\n".encode())
                        try:
                            result = self.repository.download_script(manifest_script_id, manifest_path=manifest_path)
                            success = result[0] if isinstance(result, tuple) else result
                            url = result[1] if isinstance(result, tuple) and len(result) > 1 else None
                            
                            if success:
                                if url:
                                    self.terminal.feed(f"\x1b[36m[*] URL: {url}\x1b[0m\r\n".encode())
                                cached_path = self.repository.get_cached_script_path(manifest_script_id)
                                if cached_path and os.path.isfile(cached_path):
                                    # Update metadata and execute
                                    updated_metadata = metadata.copy()
                                    updated_metadata["type"] = "cached"
                                    self._execute_script_unified(str(cached_path), updated_metadata)
                                    GLib.timeout_add(500, self._refresh_ui_after_cache_change)
                                else:
                                    self.terminal.feed(f"\x1b[31m[✗] Failed to locate cached script\x1b[0m\r\n".encode())
                            else:
                                self.terminal.feed(f"\x1b[31m[✗] Download failed\x1b[0m\r\n".encode())
                        except Exception as e:
                            if "Checksum verification failed" in str(e):
                                self.terminal.feed(f"\x1b[31m[✗] Checksum verification failed\x1b[0m\r\n".encode())
                            else:
                                self.terminal.feed(f"\x1b[31m[✗] Error: {e}\x1b[0m\r\n".encode())
        
        # Fallback: try to execute as local script if it exists
        if os.path.isfile(script_path):
            abs_path = os.path.abspath(script_path)
            command = f"bash '{abs_path}'\n"
            self.terminal.feed(f"\x1b[33m[*] Executing local script\x1b[0m\r\n".encode())
            self.terminal.feed_child(command.encode())
        else:
            self.show_error_dialog(f"Script not found:\n{script_path}")

    def on_cd_clicked(self, button):
        """Handle Go to Directory button - uses centralized navigation logic"""
        widgets = self.get_current_widgets()
        selection = widgets['treeview'].get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        
        # Get script path and metadata (use column 2 for path, not column 1)
        COL_PATH = C.COL_PATH if C else 2
        script_path = model[treeiter][COL_PATH]
        metadata = self._get_script_metadata(model, treeiter)
        script_name = os.path.basename(script_path)
        
        # Use centralized navigation logic
        success = self._navigate_to_directory_unified(script_path, metadata)
        
        # If remote/uncached, offer to download
        if not success and metadata.get("type") == "remote":
            if self.repository and self.repo_enabled:
                manifest_script_id, manifest_path = self._get_manifest_script_id(script_name, script_path)
                
                if manifest_script_id:
                    dialog = Gtk.MessageDialog(
                        transient_for=self,
                        flags=0,
                        message_type=Gtk.MessageType.QUESTION,
                        buttons=Gtk.ButtonsType.YES_NO,
                        text="Download Script?"
                    )
                    dialog.format_secondary_text(
                        f"The script '{script_name}' needs to be downloaded to cache.\n\n"
                        "Download and navigate to cache directory?"
                    )
                    response = dialog.run()
                    dialog.destroy()
                    
                    if response == Gtk.ResponseType.YES:
                        self.terminal.feed(f"\x1b[32m[*] Downloading {script_name}...\x1b[0m\r\n".encode())
                        try:
                            result = self.repository.download_script(manifest_script_id, manifest_path=manifest_path)
                            success = result[0] if isinstance(result, tuple) else result
                            url = result[1] if isinstance(result, tuple) and len(result) > 1 else None
                            
                            if success:
                                if url:
                                    self.terminal.feed(f"\x1b[36m[*] URL: {url}\x1b[0m\r\n".encode())
                                cached_path = self.repository.get_cached_script_path(manifest_script_id)
                                if cached_path and os.path.isfile(cached_path):
                                    # Update metadata and navigate
                                    updated_metadata = metadata.copy()
                                    updated_metadata["type"] = "cached"
                                    self._navigate_to_directory_unified(str(cached_path), updated_metadata)
                                    GLib.timeout_add(500, self._refresh_ui_silent)
                                else:
                                    self.terminal.feed(f"\x1b[31m[✗] Failed to locate cached script\x1b[0m\r\n".encode())
                            else:
                                self.terminal.feed(f"\x1b[31m[✗] Download failed\x1b[0m\r\n".encode())
                        except Exception as e:
                            self.terminal.feed(f"\x1b[31m[✗] Error: {e}\x1b[0m\r\n".encode())

    def on_view_clicked(self, button):
        widgets = self.get_current_widgets()
        selection = widgets['treeview'].get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        
        # Get script path (use column 2 for path)
        COL_PATH = C.COL_PATH if C else 2
        script_path = model[treeiter][COL_PATH]
        script_name = os.path.basename(script_path)
        
        # Check if this is a repository script that needs to be cached first
        if self.repository and self.repo_enabled:
            manifest_script_id, manifest_path = self._get_manifest_script_id(script_name, script_path)
            
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
                            result = self.repository.download_script(manifest_script_id, manifest_path=manifest_path)
                            success = result[0] if isinstance(result, tuple) else result
                            url = result[1] if isinstance(result, tuple) and len(result) > 1 else None
                            
                            if success:
                                if url:
                                    self.terminal.feed(f"\x1b[36m[*] URL: {url}\x1b[0m\r\n".encode())
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
        
        # Add custom scripts
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
                # Refresh UI to show updated cache status
                GLib.timeout_add(500, self._refresh_ui_after_cache_change)
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
                    # Refresh UI to show updated cache status
                    GLib.timeout_add(500, self._refresh_ui_after_cache_change)
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
            global NON_STANDARD_CATEGORIES
            
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
            
            # Update NON_STANDARD_CATEGORIES for dynamic tabs
            NON_STANDARD_CATEGORIES.clear()
            for category in _SCRIPTS_DICT.keys():
                if category not in ['install', 'tools', 'exercises', 'uninstall']:
                    NON_STANDARD_CATEGORIES[category] = {
                        'scripts': _SCRIPTS_DICT.get(category, []),
                        'names': _NAMES_DICT.get(category, []),
                        'descriptions': _DESCRIPTIONS_DICT.get(category, [])
                    }
            
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
        
        # Get the script filename from path
        script_filename = os.path.basename(script_path)
        
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
                        # Match by name or filename
                        if (script.get('name') == clean_name or 
                            script.get('file_name') == script_filename):
                            # Return with None manifest_path for public repo
                            return script.get('id'), None
            except Exception as e:
                pass
        
        # If source is custom or we haven't found it yet, search custom manifests
        try:
            custom_manifests_dir = Path.home() / '.lv_linux_learn' / 'custom_manifests'
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
        """Wrapper for UI helper error dialog"""
        if UI:
            UI.show_error_dialog(self, message)
        else:
            # Fallback if UI module not available
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=message,
            )
            dialog.run()
            dialog.destroy()


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