"""
Repository Tab Handler - Manages the online repository (Public + Custom Online) tab
Handles downloading, caching, and management of scripts from configured manifest sources
"""

import os
import json
import shlex
import hashlib
from pathlib import Path
from gi.repository import Gtk, GLib

# Debug flag
DEBUG_CACHE = os.environ.get("LV_DEBUG_CACHE") == "1"


class RepositoryTabHandler:
    """Handles repository tab creation and operations"""
    
    def __init__(self, parent_window):
        """Initialize repository tab handler"""
        self.parent = parent_window
        self.repository = parent_window.repository
        self.repo_store = None
        self.repo_filter = None
        self.repo_tree = None
    
    def create_tab(self):
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
        self.repo_filter.set_visible_func(self.parent._filter_func, "repository")
        
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
        self.populate_tree()
        
        # Store reference in parent for access
        self.parent.repo_store = self.repo_store
        self.parent.repo_filter = self.repo_filter
        self.parent.repo_tree = self.repo_tree
        
        return vbox
    
    def populate_tree(self):
        """Populate repository tree view with enhanced information"""
        if not self.repository:
            return
        
        self.repo_store.clear()
        
        try:
            # Check which manifest sources to use
            config = self.repository.load_config()
            use_public_repo = config.get('use_public_repository', True)
            custom_manifest_url = config.get('custom_manifest_url', '')
            
            # If public repo is enabled but manifest doesn't exist, download it
            if use_public_repo:
                if not self.repository.manifest_file.exists():
                    if hasattr(self.parent, 'terminal'):
                        self.parent.terminal.feed(b"\x1b[36m[*] Downloading public repository manifest for first time...\x1b[0m\r\n")
                    try:
                        self.repository.check_for_updates()
                    except Exception as e:
                        if hasattr(self.parent, 'terminal'):
                            self.parent.terminal.feed(f"\x1b[31m[!] Failed to download manifest: {e}\x1b[0m\r\n".encode())
            
            # Determine which scripts to display - can be multiple sources
            all_scripts = []
            script_ids_seen = set()  # Track to avoid duplicates
            
            # Track which sources have checksum verification disabled
            manifest_verify_settings = {}
            
            # Get list of custom manifests from Custom Manifests tab system
            custom_manifests_to_load = []
            
            # 1a. Check for custom_manifest_url in config (legacy/direct URL configuration)
            if custom_manifest_url and custom_manifest_url.startswith(('http://', 'https://')):
                custom_name = config.get('custom_manifest_name', 'Custom Repository')
                custom_manifests_to_load.append(('custom_manifest_url', custom_manifest_url, custom_name))
            
            # 1b. Check for manifests in config['custom_manifests'] (new system)
            custom_manifests_from_config = config.get('custom_manifests', {})
            for manifest_name, manifest_config in custom_manifests_from_config.items():
                if 'manifest_data' not in manifest_config:
                    continue
                # Add all custom manifests from config (they'll be loaded from manifest_data)
                custom_manifests_to_load.append((manifest_name, manifest_name, manifest_name))
                if hasattr(self.parent, 'terminal'):
                    self.parent.terminal.feed(f"\x1b[36m[*] Found custom manifest from config: {manifest_name}\x1b[0m\r\n".encode())
            
            # 1c. Check for manifests created through Custom Manifests tab (filesystem)
            if hasattr(self.parent, 'custom_manifest_creator') and self.parent.custom_manifest_creator:
                try:
                    manifests_dir = Path.home() / '.lv_linux_learn' / 'custom_manifests'
                    if manifests_dir.exists():
                        for manifest_file in manifests_dir.glob('*.json'):
                            try:
                                with open(manifest_file) as f:
                                    manifest_data = json.load(f)
                                
                                repo_url = manifest_data.get('repository_url')
                                if repo_url and repo_url.startswith(('http://', 'https://')):
                                    manifest_name = manifest_file.stem.replace('_', ' ').title()
                                    custom_manifests_to_load.append((manifest_file.stem, str(manifest_file), manifest_name))
                                    if hasattr(self.parent, 'terminal'):
                                        self.parent.terminal.feed(f"\x1b[36m[*] Found custom online manifest: {manifest_name} ({repo_url})\x1b[0m\r\n".encode())
                            except Exception as e:
                                if hasattr(self.parent, 'terminal'):
                                    self.parent.terminal.feed(f"\x1b[33m[!] Could not load manifest {manifest_file.name}: {e}\x1b[0m\r\n".encode())
                except Exception as e:
                    if hasattr(self.parent, 'terminal'):
                        self.parent.terminal.feed(f"\x1b[33m[!] Error scanning custom manifests: {e}\x1b[0m\r\n".encode())
            
            # Load all custom manifests
            for manifest_id, manifest_path, custom_manifest_name in custom_manifests_to_load:
                custom_scripts = []
                try:
                    # Try to load from config first (new system)
                    custom_manifest = None
                    if custom_manifest_name in config.get('custom_manifests', {}):
                        custom_manifest = config['custom_manifests'][custom_manifest_name].get('manifest_data')
                    
                    # Fall back to loading from file (old system)
                    if not custom_manifest and Path(manifest_path).exists():
                        with open(manifest_path, 'r') as f:
                            custom_manifest = json.load(f)
                    
                    if not custom_manifest:
                        if hasattr(self.parent, 'terminal'):
                            self.parent.terminal.feed(f"\x1b[33m[!] Could not load manifest: {custom_manifest_name}\x1b[0m\r\n".encode())
                        continue
                    
                    verify_checksums = config.get('custom_manifests', {}).get(custom_manifest_name, {}).get('verify_checksums', True)
                    manifest_verify_settings[custom_manifest_name] = verify_checksums
                    
                    if hasattr(self.parent, 'terminal'):
                        self.parent.terminal.feed(f"\x1b[36m[*] Loaded custom manifest: {custom_manifest_name}\x1b[0m\r\n".encode())
                        if not verify_checksums:
                            self.parent.terminal.feed(f"\x1b[33m[*] Note: Checksum verification disabled for '{custom_manifest_name}'\x1b[0m\r\n".encode())
                    
                    if custom_manifest:
                        manifest_scripts = custom_manifest.get('scripts', [])
                        
                        if isinstance(manifest_scripts, dict):
                            for category, category_scripts in manifest_scripts.items():
                                if isinstance(category_scripts, list):
                                    for script in category_scripts:
                                        script['category'] = category
                                        script['_source'] = 'custom'
                                        script['_source_name'] = custom_manifest_name
                                        custom_scripts.append(script)
                        else:
                            for script in manifest_scripts:
                                script['_source'] = 'custom'
                                script['_source_name'] = custom_manifest_name
                                custom_scripts.append(script)
                        
                        for script in custom_scripts:
                            script_id = script.get('id')
                            if script_id:
                                if script_id not in script_ids_seen:
                                    all_scripts.append(script)
                                    script_ids_seen.add(script_id)
                                else:
                                    if hasattr(self.parent, 'terminal'):
                                        self.parent.terminal.feed(f"\x1b[33m[!] Skipping duplicate script ID: {script_id}\x1b[0m\r\n".encode())
                            else:
                                if hasattr(self.parent, 'terminal'):
                                    self.parent.terminal.feed(f"\x1b[33m[!] Script missing ID: {script.get('name', 'unknown')}\x1b[0m\r\n".encode())
                        
                except Exception as e:
                    if hasattr(self.parent, 'terminal'):
                        self.parent.terminal.feed(f"\x1b[31m[!] Could not load custom manifest: {e}\x1b[0m\r\n".encode())
                        import traceback
                        error_details = traceback.format_exc()
                        self.parent.terminal.feed(f"\x1b[31m{error_details}\x1b[0m\r\n".encode())
            
            # 2. Load public repository scripts if enabled
            if use_public_repo:
                try:
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
                    if hasattr(self.parent, 'terminal'):
                        self.parent.terminal.feed(f"\x1b[33m[!] Could not load public repository: {e}\x1b[0m\r\n".encode())
            
            # If no scripts from any source, return silently (empty state)
            if not all_scripts:
                return
            
            # Process all scripts from all sources
            for script in all_scripts:
                script_id = script.get('id')
                name = script.get('name')
                version = script.get('version', '1.0')
                category = script.get('category', 'tools')
                file_name = script.get('file_name') or script.get('name', '')  # Fallback to 'name' field
                source = script.get('_source', 'unknown')
                source_name = script.get('_source_name', 'Unknown Source')
                source_type = script.get('source_type', '')
                
                # If file_name is still missing, try to extract from download_url or path
                if not file_name:
                    download_url = script.get('download_url') or script.get('path', '')
                    if download_url:
                        file_name = download_url.split('/')[-1]
                
                # Build cached path directly for all manifest types
                if file_name:
                    cached_path = self.repository.script_cache_dir / category / file_name
                else:
                    cached_path = None
                
                # Determine cache status
                if cached_path and cached_path.exists():
                    manifest_has_verification = manifest_verify_settings.get(source_name, True)
                    
                    remote_checksum = script.get('checksum', '').replace('sha256:', '')
                    if remote_checksum and manifest_has_verification:
                        try:
                            with open(cached_path, 'rb') as f:
                                local_checksum = hashlib.sha256(f.read()).hexdigest()
                            if local_checksum == remote_checksum:
                                status_text = '✓ Cached'
                            else:
                                status_text = '📥 Update Available'
                        except Exception:
                            status_text = '✓ Cached'
                    else:
                        status_text = '✓ Cached'
                else:
                    status_text = '☁️ Not Cached'
                
                # Get cached file info if available
                if cached_path and cached_path.exists():
                    try:
                        stat_info = os.stat(cached_path)
                        size_kb = round(stat_info.st_size / 1024, 1)
                        size_text = f"{size_kb} KB"
                        from datetime import datetime
                        modified_time = datetime.fromtimestamp(stat_info.st_mtime)
                        modified_text = modified_time.strftime("%Y-%m-%d %H:%M")
                    except:
                        size_text = "-"
                        modified_text = "-"
                else:
                    size = script.get('size', 0)
                    size_text = f"{round(size/1024, 1)} KB" if size > 0 else "-"
                    modified_text = "-"
                
                # Add to store
                self.repo_store.append([
                    False,
                    script_id, 
                    name, 
                    version, 
                    status_text, 
                    category.capitalize(),
                    size_text,
                    modified_text,
                    source_name
                ])
                
        except Exception as e:
            print(f"Error populating repository tree: {e}")
            import traceback
            traceback.print_exc()
    
    # Selection handlers
    def _on_script_toggled(self, cell_renderer, path):
        """Handle script checkbox toggle"""
        iter = self.repo_store.get_iter(path)
        current_value = self.repo_store.get_value(iter, 0)
        self.repo_store.set_value(iter, 0, not current_value)
    
    def _on_select_all(self, button):
        """Select all scripts in the repository view"""
        for row in self.repo_store:
            row[0] = True
    
    def _on_select_none(self, button):
        """Deselect all scripts in the repository view"""
        for row in self.repo_store:
            row[0] = False
    
    def _on_invert_selection(self, button):
        """Invert script selection"""
        for row in self.repo_store:
            row[0] = not row[0]
    
    def _on_download_selected(self, button):
        """Download selected scripts to cache"""
        selected_scripts = []
        
        for row in self.repo_store:
            if row[0]:
                script_id = row[1]
                script_name = row[2]
                selected_scripts.append((script_id, script_name))
        
        if not selected_scripts:
            self.parent.terminal.feed(b"\x1b[33m[!] No scripts selected - please select one or more scripts to download\x1b[0m\r\n")
            return
        
        script_names = [name for _, name in selected_scripts]
        self.parent.terminal.feed(f"\x1b[32m[*] Downloading {len(selected_scripts)} selected scripts: {', '.join(script_names[:3])}{'...' if len(script_names) > 3 else ''}\x1b[0m\r\n".encode())
        
        success_count = 0
        failed_count = 0
        local_count = 0
        
        for script_id, script_name in selected_scripts:
            try:
                script_info = self.repository.get_script_by_id(script_id)
                if script_info and script_info.get('download_url', '').startswith('file://'):
                    self.parent.terminal.feed(f"  📁 {script_name} (local file - no download needed)\r\n".encode())
                    local_count += 1
                    success_count += 1
                    while Gtk.events_pending():
                        Gtk.main_iteration()
                    continue
                
                self.parent.terminal.feed(f"\x1b[36m[*] Downloading {script_name}...\x1b[0m\r\n".encode())
                while Gtk.events_pending():
                    Gtk.main_iteration()
                
                result = self.repository.download_script(script_id)
                success = result[0] if isinstance(result, tuple) else result
                url = result[1] if isinstance(result, tuple) and len(result) > 1 else None
                
                if success:
                    if url:
                        self.parent.terminal.feed(f"  ✓ {script_name}\r\n    URL: {url}\r\n".encode())
                    else:
                        self.parent.terminal.feed(f"  ✓ {script_name}\r\n".encode())
                    success_count += 1
                else:
                    self.parent.terminal.feed(f"  ✗ {script_name} (failed)\r\n".encode())
                    failed_count += 1
                
                while Gtk.events_pending():
                    Gtk.main_iteration()
                    
            except Exception as e:
                error_msg = "checksum verification failed" if "Checksum verification failed" in str(e) else f"error: {e}"
                self.parent.terminal.feed(f"  ✗ {script_name} ({error_msg})\r\n".encode())
                failed_count += 1
                while Gtk.events_pending():
                    Gtk.main_iteration()
        
        summary_parts = [f"{success_count - local_count} downloaded"]
        if local_count > 0:
            summary_parts.append(f"{local_count} local")
        if failed_count > 0:
            summary_parts.append(f"{failed_count} failed")
        
        self.parent.terminal.feed(f"\x1b[32m[*] Complete: {', '.join(summary_parts)}\x1b[0m\r\n".encode())
        
        GLib.timeout_add(1500, self.parent._complete_terminal_operation)
        self.parent._update_repo_status()
        self.populate_tree()
        self.parent._reload_main_tabs()
    
    def _on_remove_selected(self, button):
        """Remove selected scripts from cache"""
        selected_scripts = []
        
        for row in self.repo_store:
            if row[0]:
                script_id = row[1]
                script_name = row[2]
                status = row[4]
                
                if "Cached" in status or "Update Available" in status:
                    selected_scripts.append((script_id, script_name))
        
        if not selected_scripts:
            self.parent.terminal.feed(b"\x1b[33m[!] No cached scripts selected - please select one or more cached scripts to remove\x1b[0m\r\n")
            return
        
        script_names = [name for _, name in selected_scripts]
        self.parent.terminal.feed(f"\x1b[33m[*] Removing {len(selected_scripts)} cached scripts: {', '.join(script_names[:3])}{'...' if len(script_names) > 3 else ''}\x1b[0m\r\n".encode())
        
        success_count = 0
        failed_count = 0
        
        for script_id, script_name in selected_scripts:
            try:
                cached_path = self.repository.get_cached_script_path(script_id)
                if cached_path and os.path.exists(cached_path):
                    os.remove(cached_path)
                    self.parent.terminal.feed(f"  ✓ {script_name}\r\n".encode())
                    success_count += 1
                else:
                    self.parent.terminal.feed(f"  - {script_name} (not cached)\r\n".encode())
            except Exception as e:
                self.parent.terminal.feed(f"  ✗ {script_name} (error: {e})\r\n".encode())
                failed_count += 1
        
        self.parent.terminal.feed(f"\x1b[32m[*] Removal complete: {success_count} removed, {failed_count} failed\x1b[0m\r\n".encode())
        
        # Schedule UI refresh after cache operations complete (100ms delay to ensure filesystem sync)
        def refresh_ui():
            self.populate_tree()
            self.parent._reload_main_tabs()
            self.parent._update_repo_status()
            return False
        
        GLib.timeout_add(100, refresh_ui)
        GLib.timeout_add(1500, self.parent._complete_terminal_operation)
    
    def _on_check_updates(self, button):
        """Manually check for updates"""
        if not self.repository:
            return
        
        self.parent.terminal.feed(b"\r\n\x1b[32m[*] Checking for updates...\x1b[0m\r\n")
        
        try:
            update_count = self.repository.check_for_updates()
            self.parent.terminal.feed(f"\x1b[32m[*] Found {update_count} updates available\x1b[0m\r\n".encode())
            
            GLib.timeout_add(500, self.parent._complete_terminal_operation)
            
            self.parent._update_repo_status()
            self.populate_tree()
            
        except Exception as e:
            self.parent.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            GLib.timeout_add(1500, self.parent._complete_terminal_operation)
    
    def _on_download_all(self, button):
        """Download all scripts from repository"""
        total = len(self.repo_store)
        
        if total == 0:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
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
        
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
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
        
        self.parent.terminal.feed(f"\r\n\x1b[32m[*] Downloading {total} scripts from configured sources...\x1b[0m\r\n".encode())
        
        downloaded = 0
        failed = 0
        
        try:
            for row in self.repo_store:
                script_id = row[1]
                script_name = row[2]
                category = row[5].lower()
                
                try:
                    self.parent.terminal.feed(f"\x1b[36m[*] Downloading {script_name}...\x1b[0m\r\n".encode())
                    while Gtk.events_pending():
                        Gtk.main_iteration()
                    
                    result = self.repository.download_script(script_id)
                    success = result[0] if isinstance(result, tuple) else bool(result)
                    
                    if success:
                        downloaded += 1
                        script_info = self.repository.get_script_by_id(script_id)
                        file_name = script_info.get('file_name', '') if script_info else ''
                        category_name = script_info.get('category', category) if script_info else category
                        cache_path = os.path.join(str(self.repository.script_cache_dir), category_name, file_name)
                        self.parent.terminal.feed(f"\x1b[32m  ✓ Cached to {cache_path}\x1b[0m\r\n".encode())
                    else:
                        failed += 1
                        self.parent.terminal.feed(f"\x1b[33m  ! Failed to download\x1b[0m\r\n".encode())
                    
                    while Gtk.events_pending():
                        Gtk.main_iteration()
                        
                except Exception as e:
                    failed += 1
                    self.parent.terminal.feed(f"\x1b[31m  ✗ Error: {e}\x1b[0m\r\n".encode())
                    while Gtk.events_pending():
                        Gtk.main_iteration()
            
            self.parent.terminal.feed(f"\x1b[32m[*] Download complete: {downloaded} downloaded, {failed} failed\x1b[0m\r\n".encode())
            
            GLib.timeout_add(500, self.parent._complete_terminal_operation)
            
            self.populate_tree()
            self.parent._reload_main_tabs()
            
        except Exception as e:
            self.parent.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            import traceback
            self.parent.terminal.feed(f"\x1b[31m{traceback.format_exc()}\x1b[0m\r\n".encode())
            GLib.timeout_add(1500, self.parent._complete_terminal_operation)
    
    def _on_clear_cache(self, button):
        """Clear script cache"""
        if not self.repository:
            return
        
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
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
            self.parent.terminal.feed(b"\r\n\x1b[32m[*] Script cache cleared successfully\x1b[0m\r\n")
            
            self.parent.terminal.feed(b"\x1b[36m[*] Cleaning up manifest cache files...\x1b[0m\r\n")
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
                    self.parent.terminal.feed(f"\x1b[32m[*] Removed {removed_count} cached manifest file(s)\x1b[0m\r\n".encode())
            except Exception as e:
                self.parent.terminal.feed(f"\x1b[33m[!] Manifest cache cleanup warning: {e}\x1b[0m\r\n".encode())
            
            # Schedule UI refresh after cache operations complete (100ms delay to ensure filesystem sync)
            def refresh_ui():
                self.populate_tree()
                self.parent._reload_main_tabs()
                self.parent._update_repo_status()
                return False
            
            GLib.timeout_add(100, refresh_ui)
            GLib.timeout_add(500, self.parent._complete_terminal_operation)
            
        except Exception as e:
            self.parent.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            GLib.timeout_add(1500, self.parent._complete_terminal_operation)
