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
    from gi.repository import Gtk, Gdk, GLib, Vte, Pango
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
from pathlib import Path
from datetime import datetime
import uuid

# Import repository management
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
try:
    from lib.repository import ScriptRepository
except ImportError:
    print("Warning: Repository module not available")
    ScriptRepository = None

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


def load_scripts_from_manifest():
    """
    Load scripts dynamically from manifest.json
    Returns: tuple of (scripts_dict, names_dict, descriptions_dict)
    Each dict has keys: 'install', 'tools', 'exercises', 'uninstall'
    """
    manifest_path = Path(__file__).parent / 'manifest.json'
    
    # Initialize empty structures
    scripts = {'install': [], 'tools': [], 'exercises': [], 'uninstall': []}
    names = {'install': [], 'tools': [], 'exercises': [], 'uninstall': []}
    descriptions = {'install': [], 'tools': [], 'exercises': [], 'uninstall': []}
    
    if not manifest_path.exists():
        print(f"Warning: manifest.json not found at {manifest_path}")
        return scripts, names, descriptions
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Group scripts by category
        for script in manifest.get('scripts', []):
            category = script.get('category', 'tools')
            if category not in scripts:
                continue
            
            scripts[category].append(script.get('relative_path', ''))
            names[category].append(script.get('name', ''))
            
            # Build description markup
            desc = f"<b>{script.get('name', 'Unknown')}</b>\n"
            desc += f"Script: <tt>{script.get('relative_path', '')}</tt>\n\n"
            desc += script.get('description', 'No description available')
            descriptions[category].append(desc)
        
        return scripts, names, descriptions
        
    except Exception as e:
        print(f"Error loading manifest.json: {e}")
        return scripts, names, descriptions


# Load scripts from manifest.json (single source of truth)
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

        # Create About tab
        help_box = self._create_help_tab()
        help_label = Gtk.Label(label="ℹ️ About")
        self.notebook.append_page(help_box, help_label)

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
        
        about_text = (
            "<big><b>Setup Tool</b></big>\n"
            "<i>Ubuntu Linux Setup &amp; Management Utility</i>\n\n"
            "<b>Version:</b> 2.0\n"
            "<b>Repository:</b> lv_linux_learn\n\n"
            "<span size='large'><b>About</b></span>\n\n"
            "This tool provides a graphical interface for installing and managing "
            "software packages on Ubuntu Linux. It simplifies the setup process for "
            "common development tools, applications, and utilities.\n\n"
            "<b>Features:</b>\n"
            "  • Install popular applications and development tools\n"
            "  • Safely uninstall packages with complete cleanup\n"
            "  • VPN setup and management (ZeroTier, NordVPN)\n"
            "  • Docker and container tools\n"
            "  • Git and GitHub CLI integration\n"
            "  • Desktop application installers\n\n"
            "<span size='large'><b>Credits</b></span>\n\n"
            "<b>Developer:</b> Adam Matson\n"
            "<b>GitHub:</b> <a href='https://github.com/amatson97'>@amatson97</a>\n"
            "<b>Repository:</b> <a href='https://github.com/amatson97/lv_linux_learn'>lv_linux_learn</a>\n\n"
            "<b>Target Platform:</b> Ubuntu Desktop 24.04.3 LTS\n\n"
            "<span size='large'><b>License</b></span>\n\n"
            "This project is open source and available under the MIT License.\n\n"
            "<span size='large'><b>Support</b></span>\n\n"
            "For issues, feature requests, or contributions, please visit the GitHub repository.\n\n"
            "<small><i>© 2025 Adam Matson. All rights reserved.</i></small>"
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
        name = model[iter][0].lower()
        path = model[iter][1].lower()
        return self.filter_text in name or self.filter_text in path

    def on_search_changed(self, entry):
        self.filter_text = entry.get_text().strip().lower()
        self.install_filter.refilter()
        self.tools_filter.refilter()
        self.exercises_filter.refilter()
        self.uninstall_filter.refilter()

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
        
        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        update_all_btn = Gtk.Button(label="Update All Scripts")
        update_all_btn.connect("clicked", self._on_update_all_scripts)
        button_box.pack_start(update_all_btn, False, False, 0)
        
        check_updates_btn = Gtk.Button(label="Check Updates")
        check_updates_btn.connect("clicked", self._on_check_updates)
        button_box.pack_start(check_updates_btn, False, False, 0)
        
        download_all_btn = Gtk.Button(label="Download All")
        download_all_btn.connect("clicked", self._on_download_all)
        button_box.pack_start(download_all_btn, False, False, 0)
        
        clear_cache_btn = Gtk.Button(label="Clear Cache")
        clear_cache_btn.connect("clicked", self._on_clear_cache)
        button_box.pack_start(clear_cache_btn, False, False, 0)
        
        settings_btn = Gtk.Button(label="Settings")
        settings_btn.connect("clicked", self._on_repo_settings)
        button_box.pack_end(settings_btn, False, False, 0)
        
        header_box.pack_end(button_box, False, False, 0)
        
        vbox.pack_start(header_box, False, False, 0)
        
        # Scripts list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.repo_store = Gtk.ListStore(str, str, str, str, str)  # id, name, version, status, category
        self.repo_tree = Gtk.TreeView(model=self.repo_store)
        
        # Columns
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Script Name", name_renderer, text=1)
        name_column.set_resizable(True)
        name_column.set_min_width(200)
        self.repo_tree.append_column(name_column)
        
        cat_renderer = Gtk.CellRendererText()
        cat_column = Gtk.TreeViewColumn("Category", cat_renderer, text=4)
        cat_column.set_resizable(True)
        self.repo_tree.append_column(cat_column)
        
        ver_renderer = Gtk.CellRendererText()
        ver_column = Gtk.TreeViewColumn("Version", ver_renderer, text=2)
        self.repo_tree.append_column(ver_column)
        
        status_renderer = Gtk.CellRendererText()
        status_column = Gtk.TreeViewColumn("Status", status_renderer, text=3)
        self.repo_tree.append_column(status_column)
        
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
        """Populate repository tree view"""
        if not self.repository:
            return
        
        self.repo_store.clear()
        
        try:
            scripts = self.repository.parse_manifest()
            
            for script in scripts:
                script_id = script.get('id')
                name = script.get('name')
                version = script.get('version')
                category = script.get('category')
                
                # Determine status
                status = self.repository.get_script_status(script.get('file_name'))
                
                status_text = {
                    'cached': '✓ Up to date',
                    'outdated': '📥 Update available',
                    'not_installed': '☁️ Not installed'
                }.get(status, 'Unknown')
                
                self.repo_store.append([script_id, name, version, status_text, category])
                
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
        
        self.terminal.feed_child(b"clear\n")
        self.terminal.feed_child(b"echo 'Updating all cached scripts...'\n")
        
        try:
            updated, failed = self.repository.update_all_scripts()
            self.terminal.feed_child(f"echo 'Update complete: {updated} updated, {failed} failed'\n".encode())
            
            # Refresh display
            self._update_repo_status()
            self._populate_repository_tree()
            
        except Exception as e:
            self.terminal.feed_child(f"echo 'Error: {e}'\n".encode())
    
    def _on_check_updates(self, button):
        """Manually check for updates"""
        if not self.repository:
            return
        
        self.terminal.feed_child(b"clear\n")
        self.terminal.feed_child(b"echo 'Checking for updates...'\n")
        
        try:
            update_count = self.repository.check_for_updates()
            self.terminal.feed_child(f"echo 'Found {update_count} updates available'\n".encode())
            
            # Refresh display
            self._update_repo_status()
            self._populate_repository_tree()
            
        except Exception as e:
            self.terminal.feed_child(f"echo 'Error: {e}'\n".encode())
    
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
            f"This will download all {total} scripts from the repository.\\n\\n"
            "This may take a few minutes. Continue?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        self.terminal.feed_child(b"clear\n")
        self.terminal.feed_child(f"echo 'Downloading all {total} scripts...'\n".encode())
        
        try:
            downloaded, failed = self.repository.download_all_scripts()
            self.terminal.feed_child(f"echo 'Download complete: {downloaded} downloaded, {failed} failed'\n".encode())
            
            # Refresh display
            self._update_repo_status()
            self._populate_repository_tree()
            
        except Exception as e:
            self.terminal.feed_child(f"echo 'Error: {e}'\n".encode())
    
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
            text="Clear Script Cache"
        )
        
        dialog.format_secondary_text(
            "This will remove all cached scripts.\\n\\n"
            "You will need to download them again. Continue?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        try:
            self.repository.clear_cache()
            self.terminal.feed_child(b"clear\n")
            self.terminal.feed_child(b"echo 'Cache cleared successfully'\n")
            
            # Refresh display
            self._update_repo_status()
            self._populate_repository_tree()
            
        except Exception as e:
            self.terminal.feed_child(f"echo 'Error: {e}'\n".encode())
    
    def _on_repo_settings(self, button):
        """Show repository settings dialog"""
        if not self.repository:
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
        
        interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        interval_label = Gtk.Label(label="Check interval (minutes):")
        interval_spin = Gtk.SpinButton()
        interval_spin.set_range(1, 1440)
        interval_spin.set_increments(1, 10)
        interval_spin.set_value(self.repo_config.get('update_check_interval_minutes', 30))
        interval_box.pack_start(interval_label, False, False, 0)
        interval_box.pack_start(interval_spin, False, False, 0)
        content.pack_start(interval_box, False, False, 0)
        
        dialog.show_all()
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Save settings
            self.repo_config['use_remote_scripts'] = use_remote.get_active()
            self.repo_config['auto_check_updates'] = auto_check.get_active()
            self.repo_config['auto_install_updates'] = auto_install.get_active()
            self.repo_config['update_check_interval_minutes'] = int(interval_spin.get_value())
            self.repository.save_config(self.repo_config)
            
            self.terminal.feed_child(b"echo 'Repository settings saved'\n")
        
        dialog.destroy()

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
        if not os.path.isfile(script_path):
            self.show_error_dialog(f"Script not found:\n{script_path}")
            return
        
        # Convert to absolute path to work regardless of terminal's current directory
        abs_path = os.path.abspath(script_path)
        
        # Send command to terminal
        command = f"bash '{abs_path}'\n"
        self.terminal.feed_child(command.encode())

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
        
        # Get the directory containing the script
        script_dir = os.path.dirname(os.path.abspath(script_path))
        safe_dir = shlex.quote(script_dir)
        
        # Change directory in terminal
        cd_cmd = f"cd {safe_dir} && pwd\n"
        self.terminal.feed_child(cd_cmd.encode())
    
    def on_view_clicked(self, button):
        widgets = self.get_current_widgets()
        selection = widgets['treeview'].get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        script_path = model[treeiter][1]
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
            f"<b>My Custom Script</b>\\n"
            f"Script: <tt>path/to/script.sh</tt>\\n\\n"
            f"• Add your description here\\n"
            f"• Use bullet points\\n"
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
        """Handle right-click on tree view for custom script menu"""
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
            if not is_custom:
                return False  # Only show menu for custom scripts
            
            script_id = model.get_value(iter, 4)
            
            # Show context menu
            menu = Gtk.Menu()
            
            edit_item = Gtk.MenuItem(label="✏️ Edit Script")
            edit_item.connect("activate", lambda w: self._edit_custom_script(script_id))
            menu.append(edit_item)
            
            delete_item = Gtk.MenuItem(label="🗑️ Delete Script")
            delete_item.connect("activate", lambda w: self._delete_custom_script(script_id))
            menu.append(delete_item)
            
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