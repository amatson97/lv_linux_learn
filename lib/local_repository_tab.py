"""
Local Repository Tab Handler - Manages the local repository (file-based) tab
Handles management of scripts from local file manifests
"""

import os
import json
import shlex
import stat
from pathlib import Path
from gi.repository import Gtk, GLib

# Debug flag
DEBUG_CACHE = os.environ.get("LV_DEBUG_CACHE") == "1"


class LocalRepositoryTabHandler:
    """Handles local repository tab creation and operations"""
    
    def __init__(self, parent_window):
        """Initialize local repository tab handler"""
        self.parent = parent_window
        self.repository = parent_window.repository
        self.local_repo_store = None
        self.local_repo_filter = None
        self.local_repo_tree = None
        self.ollama_available = False
    
    def create_tab(self):
        """Create the local repository management tab (direct execution, no cache)"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        
        # Check Ollama availability
        try:
            from lib.ai_categorizer import check_ollama_available
            self.ollama_available = check_ollama_available()
        except ImportError:
            self.ollama_available = False
        
        # Control buttons at the top
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Selection group
        select_all_btn = Gtk.Button(label="Select All")
        select_all_btn.connect("clicked", self._on_select_all)
        button_box.pack_start(select_all_btn, False, False, 0)
        
        select_none_btn = Gtk.Button(label="Select None")
        select_none_btn.connect("clicked", self._on_select_none)
        button_box.pack_start(select_none_btn, False, False, 0)
        
        # Delete button for removing scripts from local repositories
        delete_btn = Gtk.Button(label="Delete Selected")
        delete_btn.get_style_context().add_class("destructive-action")
        delete_btn.connect("clicked", self._on_delete_selected)
        button_box.pack_start(delete_btn, False, False, 0)
        
        # AI Analyze button
        if self.ollama_available:
            analyze_btn = Gtk.Button(label="AI Analyze Selected")
            analyze_btn.get_style_context().add_class("suggested-action")
            analyze_btn.connect("clicked", self._on_ai_analyze_scripts)
            button_box.pack_start(analyze_btn, False, False, 0)
        
        # Refresh operations
        refresh_btn = Gtk.Button(label="Refresh List")
        refresh_btn.connect("clicked", self._on_refresh_repos)
        button_box.pack_start(refresh_btn, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        # AI Analysis banner
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
        self.local_repo_filter.set_visible_func(self.parent._filter_func, "local_repositories")
        
        self.local_repo_tree = Gtk.TreeView(model=self.local_repo_filter)
        
        # Checkbox column
        checkbox_renderer = Gtk.CellRendererToggle()
        checkbox_renderer.set_property("activatable", True)
        checkbox_renderer.connect("toggled", self._on_script_toggled)
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
        
        # Double-click handler for direct execution
        self.local_repo_tree.connect("row-activated", self._on_row_activated)
        
        # Populate tree
        self.populate_tree()
        
        # Store reference in parent for access
        self.parent.local_repo_store = self.local_repo_store
        self.parent.local_repo_filter = self.local_repo_filter
        self.parent.local_repo_tree = self.local_repo_tree
        
        return vbox
    
    def populate_tree(self):
        """Populate local repository tree view (scripts from file-based manifests)"""
        if not self.repository:
            return
        
        self.local_repo_store.clear()
        
        try:
            local_scripts = []
            
            if hasattr(self.parent, 'terminal'):
                self.parent.terminal.feed(b"\x1b[36m[*] Scanning for local repositories...\x1b[0m\r\n")
            
            script_ids_seen = set()
            
            # Method 1: Check config.json for local repository
            config = self.repository.load_config()
            custom_manifest_url = config.get('custom_manifest_url', '')
            custom_manifests_config = config.get('custom_manifests', {})
            use_public_repo = config.get('use_public_repository', True)
            
            # CRITICAL: If we're using public repository with no custom manifests, exit early
            if use_public_repo and not custom_manifests_config:
                if hasattr(self.parent, 'terminal'):
                    self.parent.terminal.feed(b"\x1b[36m[i] No local repositories configured (using public repository)\x1b[0m\r\n")
                return
            
            if custom_manifest_url and custom_manifest_url.startswith('file://'):
                manifest_path = custom_manifest_url.replace('file://', '').strip()
                manifest_name = config.get('custom_manifest_name', 'Local Repository')
                
                try:
                    manifest_file = Path(manifest_path)
                    if manifest_file.exists():
                        with open(manifest_file) as f:
                            manifest_data = json.load(f)
                        
                        repository_url = manifest_data.get('repository_url', '')
                        
                        # If the repository_url is http/https, this is an ONLINE custom repo
                        if repository_url.startswith(('http://', 'https://')):
                            if hasattr(self.parent, 'terminal'):
                                self.parent.terminal.feed(f"\x1b[36m[*] Skipping {manifest_name} (online repository, not local)\x1b[0m\r\n".encode())
                        else:
                            # This is truly a local file-based repository
                            if hasattr(self.parent, 'terminal'):
                                self.parent.terminal.feed(f"\x1b[32m[*] Found local repository in config: {manifest_name}\x1b[0m\r\n".encode())
                                self.parent.terminal.feed(f"\x1b[36m[*] Manifest path: {manifest_path}\x1b[0m\r\n".encode())
                            
                            base_path = str(manifest_file.parent)
                            scripts = manifest_data.get('scripts', [])
                            
                            # Handle both flat and nested structures
                            if isinstance(scripts, dict):
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
                                for script in scripts:
                                    script_id = script.get('id', '')
                                    if script_id and script_id not in script_ids_seen:
                                        script['_manifest_name'] = manifest_name
                                        script['_manifest_type'] = 'local'
                                        script['_base_path'] = base_path
                                        local_scripts.append(script)
                                        script_ids_seen.add(script_id)
                except Exception as e:
                    if hasattr(self.parent, 'terminal'):
                        self.parent.terminal.feed(f"\x1b[31m[!] Error loading manifest from config: {e}\x1b[0m\r\n".encode())
            
            # Method 2: Scan custom_manifests directory for all local file-based repositories
            custom_manifests_dir = Path.home() / '.lv_linux_learn' / 'custom_manifests'
            use_public_repo = config.get('use_public_repository', True)
            has_custom_manifests = bool(custom_manifests_config) and len(custom_manifests_config) > 0
            
            if custom_manifests_dir.exists() and has_custom_manifests:
                manifest_files = list(custom_manifests_dir.glob('*/manifest.json')) + list(custom_manifests_dir.glob('*_manifest.json'))
                
                for manifest_file in manifest_files:
                    try:
                        with open(manifest_file) as f:
                            manifest_data = json.load(f)
                        
                        repository_url = manifest_data.get('repository_url', '')
                        manifest_name = manifest_file.parent.name.replace('_', ' ').title()
                        
                        # CRITICAL: Skip online repositories
                        if repository_url.startswith(('http://', 'https://')):
                            if hasattr(self.parent, 'terminal') and DEBUG_CACHE:
                                self.parent.terminal.feed(f"\x1b[36m[DEBUG] Skipping online repository: {manifest_name}\x1b[0m\r\n".encode())
                            continue
                        
                        # Skip if empty or public repo manifest
                        if not repository_url or repository_url == '':
                            manifest_version = manifest_data.get('version', '')
                            if 'github.com/amatson97/lv_linux_learn' in str(manifest_data.get('repository_url', '')):
                                if hasattr(self.parent, 'terminal') and DEBUG_CACHE:
                                    self.parent.terminal.feed(f"\x1b[36m[DEBUG] Skipping public repo manifest: {manifest_file.name}\x1b[0m\r\n".encode())
                                continue
                        
                        # This is a local file-based repository
                        base_path = str(manifest_file.parent) if manifest_file.name == 'manifest.json' else str(manifest_file.parent / manifest_name.lower().replace(' ', '_'))
                        
                        scripts = manifest_data.get('scripts', [])
                        
                        # Handle both flat and nested structures
                        if isinstance(scripts, dict):
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
                            for script in scripts:
                                script_id = script.get('id', '')
                                if script_id and script_id not in script_ids_seen:
                                    script['_manifest_name'] = manifest_name
                                    script['_manifest_type'] = 'local'
                                    script['_base_path'] = base_path
                                    local_scripts.append(script)
                                    script_ids_seen.add(script_id)
                    
                    except Exception as e:
                        if hasattr(self.parent, 'terminal'):
                            self.parent.terminal.feed(f"\x1b[33m[!] Error loading {manifest_file.name}: {e}\x1b[0m\r\n".encode())
            
            if not local_scripts:
                if hasattr(self.parent, 'terminal'):
                    self.parent.terminal.feed(b"\x1b[33m[!] No scripts found in local repositories\x1b[0m\r\n")
                    self.parent.terminal.feed(b"\x1b[36m[i] Make sure your local repository has a valid manifest.json\x1b[0m\r\n")
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
                            full_path = str(Path(base_path) / category / file_name)
                
                # Method 3: Try just file_name as relative path from base_path
                if not full_path:
                    file_name = script.get('file_name', '')
                    if file_name and base_path:
                        full_path = str(Path(base_path) / file_name)
                
                if full_path:
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
                        if hasattr(self.parent, 'terminal'):
                            self.parent.terminal.feed(f"\x1b[33m[!] Error checking path for {name}: {e}\x1b[0m\r\n".encode())
                else:
                    full_path = "Path not available"
                    size_text = "-"
                
                # Add to store
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
                
        except Exception as e:
            print(f"Error populating local repository tree: {e}")
            import traceback
            traceback.print_exc()
    
    # Selection handlers
    def _on_script_toggled(self, cell_renderer, path):
        """Handle local script checkbox toggle"""
        iter = self.local_repo_store.get_iter(path)
        current_value = self.local_repo_store.get_value(iter, 0)
        self.local_repo_store.set_value(iter, 0, not current_value)
    
    def _on_select_all(self, button):
        """Select all scripts in the local repository view"""
        for row in self.local_repo_store:
            row[0] = True
    
    def _on_select_none(self, button):
        """Deselect all scripts in the local repository view"""
        for row in self.local_repo_store:
            row[0] = False
    
    def _on_refresh_repos(self, button):
        """Refresh the local repository list"""
        self.parent.terminal.feed(b"\x1b[32m[*] Refreshing local repositories...\x1b[0m\r\n")
        self.populate_tree()
        GLib.timeout_add(200, self.parent._reload_main_tabs_silent)
        GLib.timeout_add(500, self.parent._complete_terminal_operation)
    
    def _on_delete_selected(self, button):
        """Delete selected scripts from local repositories"""
        selected_scripts = []
        
        for row in self.local_repo_store:
            if row[0]:
                script_name = row[2]
                script_id = row[1]
                script_path = row[4]
                source = row[6]
                selected_scripts.append((script_id, script_name, script_path, source))
        
        if not selected_scripts:
            self.parent.terminal.feed(b"\x1b[33m[!] No scripts selected for deletion\x1b[0m\r\n")
            GLib.timeout_add(100, self.parent._complete_terminal_silent)
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
            transient_for=self.parent,
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
        
        self.parent.terminal.feed(f"\x1b[33m[*] Removing {count} script(s) from manifest files...\x1b[0m\r\n".encode())
        
        success_count = 0
        
        for script_id, script_name, script_path, source in selected_scripts:
            try:
                custom_manifests_dir = Path.home() / '.lv_linux_learn' / 'custom_manifests'
                manifest_files = list(custom_manifests_dir.glob('*/manifest.json')) + list(custom_manifests_dir.glob('*_manifest.json'))
                
                script_removed = False
                for manifest_file in manifest_files:
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest_data = json.load(f)
                        
                        modified = False
                        scripts = manifest_data.get('scripts', {})
                        
                        if isinstance(scripts, dict):
                            for category, category_scripts in scripts.items():
                                if isinstance(category_scripts, list):
                                    original_count = len(category_scripts)
                                    category_scripts[:] = [s for s in category_scripts if s.get('id') != script_id]
                                    if len(category_scripts) < original_count:
                                        modified = True
                                        scripts[category] = category_scripts
                        else:
                            original_count = len(scripts)
                            scripts[:] = [s for s in scripts if s.get('id') != script_id]
                            if len(scripts) < original_count:
                                modified = True
                        
                        if modified:
                            manifest_data['scripts'] = scripts
                            with open(manifest_file, 'w') as f:
                                json.dump(manifest_data, f, indent=2)
                            
                            script_removed = True
                            success_count += 1
                            self.parent.terminal.feed(f"\x1b[32m[✓] Removed {script_name} from {manifest_file.name}\x1b[0m\r\n".encode())
                            break
                    
                    except Exception as e:
                        self.parent.terminal.feed(f"\x1b[31m[!] Error checking {manifest_file.name}: {e}\x1b[0m\r\n".encode())
                        continue
                
                if not script_removed:
                    self.parent.terminal.feed(f"\x1b[33m[!] Could not find {script_name} in any manifest\x1b[0m\r\n".encode())
            
            except Exception as e:
                self.parent.terminal.feed(f"\x1b[31m[✗] Error removing {script_name}: {e}\x1b[0m\r\n".encode())
        
        if success_count > 0:
            self.parent.terminal.feed(f"\x1b[32m[✓] Successfully removed {success_count} of {count} script(s)\x1b[0m\r\n".encode())
            
            self.parent.terminal.feed(b"\x1b[36m[*] Refreshing UI...\x1b[0m\r\n")
            GLib.timeout_add(100, self.populate_tree)
            GLib.timeout_add(200, self.parent._reload_main_tabs_silent)
            GLib.timeout_add(400, self.parent._complete_terminal_silent)
        else:
            self.parent.terminal.feed(b"\x1b[31m[!] No scripts were removed\x1b[0m\r\n")
            GLib.timeout_add(100, self.parent._complete_terminal_silent)
    
    def _on_row_activated(self, tree_view, path, column):
        """Handle double-click on local repository script (execute directly)"""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        
        script_name = model.get_value(iter, 2)
        script_path = model.get_value(iter, 4)
        
        # Check if path is valid
        if "(NOT FOUND)" in script_path or "not available" in script_path.lower():
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
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
        self.parent.terminal.feed(b"\x1b[2J\x1b[H")
        self.parent.terminal.feed(f"\x1b[32m[*] Executing local script: {script_name}\x1b[0m\r\n\r\n".encode())
        
        try:
            path_obj = Path(script_path)
            if not path_obj.exists():
                self.parent.terminal.feed(f"\x1b[31m[!] File not found: {script_path}\x1b[0m\r\n".encode())
                return
            
            # Make executable
            current_permissions = path_obj.stat().st_mode
            path_obj.chmod(current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            
            # Execute in terminal
            cmd = f"source {shlex.quote(str(path_obj))}\n"
            self.parent.terminal.feed_child(cmd.encode())
            
            GLib.timeout_add(1000, self.parent._complete_terminal_operation)
            
        except Exception as e:
            self.parent.terminal.feed(f"\x1b[31m[!] Error executing script: {e}\x1b[0m\r\n".encode())
    
    def _on_install_ollama(self, button):
        """Guide user through Ollama installation"""
        self.parent.terminal.feed(b"\r\n\x1b[36m" + b"="*80 + b"\x1b[0m\r\n")
        self.parent.terminal.feed(b"\x1b[36m  Install Ollama AI Engine\x1b[0m\r\n")
        self.parent.terminal.feed(b"\x1b[36m" + b"="*80 + b"\x1b[0m\r\n\r\n")
        self.parent.terminal.feed(b"\x1b[32mOllama provides local AI-powered script analysis:\x1b[0m\r\n")
        self.parent.terminal.feed("  • Automatic script categorization\r\n".encode())
        self.parent.terminal.feed("  • AI-generated descriptions\r\n".encode())
        self.parent.terminal.feed("  • Dependency detection\r\n".encode())
        self.parent.terminal.feed("  • Security analysis\r\n\r\n".encode())
        self.parent.terminal.feed(b"\x1b[33m[*] Installing Ollama...\x1b[0m\r\n")
        self.parent.terminal.feed(b"curl https://ollama.ai/install.sh | sh\n")
        self.parent.terminal.feed_child(b"curl https://ollama.ai/install.sh | sh\n")
        
        GLib.timeout_add(3000, self._show_ollama_next_steps)
    
    def _show_ollama_next_steps(self):
        """Show Ollama post-installation steps"""
        self.parent.terminal.feed(b"\r\n\x1b[32m" + b"="*80 + b"\x1b[0m\r\n")
        self.parent.terminal.feed(b"\x1b[32m  Ollama Installation Next Steps\x1b[0m\r\n")
        self.parent.terminal.feed(b"\x1b[32m" + b"="*80 + b"\x1b[0m\r\n\r\n")
        self.parent.terminal.feed(b"After installation completes:\r\n\r\n")
        self.parent.terminal.feed(b"\x1b[33m1. Pull an AI model:\x1b[0m\r\n")
        self.parent.terminal.feed(b"   ollama pull llama3.2  (recommended, ~2GB)\r\n")
        self.parent.terminal.feed(b"   Or: ollama pull codellama  (code-focused, ~4GB)\r\n\r\n")
        self.parent.terminal.feed(b"\x1b[33m2. Test the installation:\x1b[0m\r\n")
        self.parent.terminal.feed(b"   ollama list\r\n\r\n")
        self.parent.terminal.feed(b"\x1b[33m3. Restart this application\x1b[0m to enable AI features\r\n\r\n")
        self.parent.terminal.feed(b"Visit https://ollama.ai for more information\r\n")
        GLib.timeout_add(100, self.parent._complete_terminal_silent)
        return False
    
    def _on_ai_analyze_scripts(self, button):
        """Analyze selected scripts using AI"""
        selected_scripts = []
        for row in self.local_repo_store:
            if row[0]:
                script_name = row[2]
                script_path = row[4]
                script_id = row[1]
                if "(NOT FOUND)" not in script_path and "not available" not in script_path.lower():
                    selected_scripts.append((script_id, script_name, script_path))
        
        if not selected_scripts:
            self.parent.terminal.feed(b"\x1b[33m[!] No scripts selected for analysis\x1b[0m\r\n")
            self.parent.terminal.feed(b"Please select at least one script from the Repository (Local) tab\r\n")
            GLib.timeout_add(100, self.parent._complete_terminal_silent)
            return
        
        self.parent.terminal.feed(b"\r\n\x1b[36m" + b"="*70 + b"\x1b[0m\r\n")
        self.parent.terminal.feed(f"\x1b[36m  Starting AI analysis of {len(selected_scripts)} script(s)...\x1b[0m\r\n".encode())
        self.parent.terminal.feed(b"\x1b[36m" + b"="*70 + b"\x1b[0m\r\n\r\n")
