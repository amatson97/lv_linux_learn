"""
Custom Manifest Tab Handler - Manages the sources/custom manifest tab
Handles creation, editing, and deletion of custom script repositories
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from gi.repository import Gtk, GLib

# Debug flag
DEBUG_CACHE = os.environ.get("LV_DEBUG_CACHE") == "1"


class CustomManifestTabHandler:
    """Handles custom manifest tab creation and operations"""
    
    def __init__(self, parent_window):
        """Initialize custom manifest tab handler"""
        self.parent = parent_window
        self.custom_manifest_creator = parent_window.custom_manifest_creator
        self.custom_manifest_store = None
        self.custom_manifest_tree = None
    
    def create_tab(self):
        """Create the custom manifest management tab"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        
        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Add operation
        create_btn = Gtk.Button(label="Add New Source")
        create_btn.get_style_context().add_class("suggested-action")
        create_btn.connect("clicked", self._on_create_manifest)
        button_box.pack_start(create_btn, False, False, 0)
        
        # Edit/Delete operations
        edit_btn = Gtk.Button(label="Edit Selected")
        edit_btn.connect("clicked", self._on_edit_manifest)
        button_box.pack_start(edit_btn, False, False, 0)
        
        delete_btn = Gtk.Button(label="Delete Selected")
        delete_btn.get_style_context().add_class("destructive-action")
        delete_btn.connect("clicked", self._on_delete_selected)
        button_box.pack_start(delete_btn, False, False, 0)
        
        # Refresh operation
        refresh_btn = Gtk.Button(label="Refresh List")
        refresh_btn.connect("clicked", self._on_refresh_manifests)
        button_box.pack_start(refresh_btn, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        # Custom manifests list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Store: name(str), description(str), version(str), created(str), total_scripts(int), categories(str)
        self.custom_manifest_store = Gtk.ListStore(str, str, str, str, int, str)
        
        self.custom_manifest_tree = Gtk.TreeView(model=self.custom_manifest_store)
        
        # Enable multiple selection
        self.custom_manifest_tree.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        
        # Name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Name", name_renderer, text=0)
        name_column.set_resizable(True)
        name_column.set_min_width(150)
        self.custom_manifest_tree.append_column(name_column)
        
        # Description column
        desc_renderer = Gtk.CellRendererText()
        desc_renderer.set_property("ellipsize", 3)
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
        categories_renderer.set_property("ellipsize", 3)
        categories_column = Gtk.TreeViewColumn("Categories", categories_renderer, text=5)
        categories_column.set_resizable(True)
        categories_column.set_min_width(100)
        self.custom_manifest_tree.append_column(categories_column)
        
        # Created column
        created_renderer = Gtk.CellRendererText()
        created_column = Gtk.TreeViewColumn("Created", created_renderer, text=3)
        created_column.set_min_width(100)
        self.custom_manifest_tree.append_column(created_column)
        
        # Connect row activation
        self.custom_manifest_tree.connect("row-activated", self._on_row_activated)
        
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
        self.populate_tree()
        
        # Store reference in parent
        self.parent.custom_manifest_store = self.custom_manifest_store
        self.parent.custom_manifest_tree = self.custom_manifest_tree
        
        return vbox
    
    def populate_tree(self):
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
    
    # Event handlers
    def _on_create_manifest(self, button):
        """Show create custom manifest dialog"""
        if not self.custom_manifest_creator:
            return
        
        dialog = self._create_manifest_dialog(None, is_edit=False)
        dialog.show_all()
        self._run_manifest_dialog(dialog, None, is_edit=False)
    
    def _on_edit_manifest(self, button):
        """Edit the selected custom manifest"""
        selection = self.custom_manifest_tree.get_selection()
        selected_rows = selection.get_selected_rows()
        model, paths = selected_rows
        
        if not paths or len(paths) == 0:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="No Manifest Selected"
            )
            dialog.format_secondary_text("Please select a custom manifest to edit.")
            dialog.run()
            dialog.destroy()
            return
        
        # Get the first selected row
        tree_iter = model.get_iter(paths[0])
        manifest_name = model.get_value(tree_iter, 0)
        self._show_edit_manifest_dialog(manifest_name)
    
    def _on_refresh_manifests(self, button):
        """Refresh the custom manifests list"""
        self.populate_tree()
        self.parent._populate_local_repository_tree()
        self.parent.terminal.feed(b"\x1b[32m[*] Custom manifests refreshed\x1b[0m\r\n")
    
    def _on_delete_selected(self, button):
        """Delete the selected custom manifest(s)"""
        selection = self.custom_manifest_tree.get_selection()
        model, tree_paths = selection.get_selected_rows()
        
        if not tree_paths:
            self.parent.terminal.feed(b"\x1b[33m[!] No manifests selected for deletion\x1b[0m\r\n")
            return
        
        # Get manifest names for all selected items
        manifest_names = []
        for path in tree_paths:
            tree_iter = model.get_iter(path)
            manifest_name = model.get_value(tree_iter, 0)
            manifest_names.append(manifest_name)
        
        # Confirm deletion
        count = len(manifest_names)
        if count == 1:
            confirm_msg = f"Delete manifest '{manifest_names[0]}'?"
            detail_msg = "This will permanently delete the manifest and all associated files.\nThis action cannot be undone."
        else:
            confirm_msg = f"Delete {count} manifests?"
            detail_msg = f"Manifests to delete:\n" + "\n".join(f"  • {name}" for name in manifest_names)
            detail_msg += "\n\nThis will permanently delete all selected manifests.\nThis action cannot be undone."
        
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
        
        # Delete all selected manifests
        self.parent.terminal.feed(f"\x1b[33m[*] Deleting {count} manifest(s)...\x1b[0m\r\n".encode())
        
        success_count = 0
        for manifest_name in manifest_names:
            try:
                success, message = self.custom_manifest_creator.delete_custom_manifest(manifest_name)
                if success:
                    self.parent.terminal.feed(f"\x1b[32m[✓] Deleted: {manifest_name}\x1b[0m\r\n".encode())
                    success_count += 1
                else:
                    self.parent.terminal.feed(f"\x1b[31m[✗] Failed to delete {manifest_name}: {message}\x1b[0m\r\n".encode())
            except Exception as e:
                self.parent.terminal.feed(f"\x1b[31m[✗] Error deleting {manifest_name}: {e}\x1b[0m\r\n".encode())
        
        if success_count > 0:
            self.parent.terminal.feed(f"\x1b[32m[✓] Successfully deleted {success_count} of {count} manifest(s)\x1b[0m\r\n".encode())
            
            # Cleanup cache
            self.parent.terminal.feed(b"\x1b[36m[*] Performing comprehensive cache cleanup...\x1b[0m\r\n")
            try:
                cache_dir = Path.home() / '.lv_linux_learn'
                total_removed = 0
                
                for manifest_name in manifest_names[:success_count]:
                    safe_name = manifest_name.lower().replace(' ', '_')
                    
                    for pattern in ['manifest_*.json', 'temp_*_manifest.json']:
                        for cache_file in cache_dir.glob(pattern):
                            if safe_name in cache_file.name.lower():
                                cache_file.unlink(missing_ok=True)
                                total_removed += 1
                
                if total_removed > 0:
                    self.parent.terminal.feed(f"\x1b[32m[*] Cleaned up {total_removed} cached file(s)\x1b[0m\r\n".encode())
            except Exception as e:
                self.parent.terminal.feed(f"\x1b[33m[!] Cache cleanup warning: {e}\x1b[0m\r\n".encode())
            
            self.populate_tree()
            GLib.timeout_add(200, self.parent._reload_main_tabs)
            if hasattr(self.parent, '_populate_repository_tree'):
                GLib.timeout_add(400, self.parent._populate_repository_tree)
            GLib.timeout_add(400, self.parent._populate_local_repository_tree)
            GLib.timeout_add(600, self.parent._complete_terminal_silent)
    
    def _on_row_activated(self, tree_view, path, column):
        """Handle double-click on manifest row - edit manifest"""
        model = tree_view.get_model()
        tree_iter = model.get_iter(path)
        manifest_name = model.get_value(tree_iter, 0)
        
        if not self.custom_manifest_creator:
            return
        
        self._show_edit_manifest_dialog(manifest_name)
    
    # Dialog creation helpers
    def _create_manifest_dialog(self, manifest_info=None, is_edit=False):
        """Create the manifest creation/editing dialog"""
        title = f"Edit Manifest: {manifest_info['name']}" if is_edit and manifest_info else "Create Custom Source"
        
        dialog = Gtk.Dialog(
            title=title,
            parent=self.parent,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            ("Save Changes" if is_edit else "Create"), Gtk.ResponseType.OK
        )
        dialog.set_default_size(600, 500)
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(10)
        content.set_margin_end(10)
        content.set_margin_top(10)
        content.set_margin_bottom(10)
        
        # If editing, show manifest type
        if is_edit and manifest_info:
            type_label = Gtk.Label()
            manifest_type = manifest_info.get('type', 'directory_scan')
            type_text = "Directory Scan" if manifest_type == 'directory_scan' else "Remote Manifest"
            type_label.set_markup(f"<b>Manifest Type:</b> {type_text}")
            type_label.set_xalign(0)
            content.pack_start(type_label, False, False, 0)
        
        # Name entry
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        name_label = Gtk.Label(label="Repository Name:")
        name_label.set_size_request(120, -1)
        name_entry = Gtk.Entry()
        name_entry.set_placeholder_text("my_custom_scripts_repo")
        if is_edit and manifest_info:
            name_entry.set_text(manifest_info.get('name', ''))
        name_box.pack_start(name_label, False, False, 0)
        name_box.pack_start(name_entry, True, True, 0)
        content.pack_start(name_box, False, False, 0)
        
        # Description entry
        desc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        desc_label = Gtk.Label(label="Description:")
        desc_label.set_size_request(120, -1)
        desc_entry = Gtk.Entry()
        desc_entry.set_placeholder_text("My collection of custom scripts")
        if is_edit and manifest_info:
            desc_entry.set_text(manifest_info.get('description', ''))
        desc_box.pack_start(desc_label, False, False, 0)
        desc_box.pack_start(desc_entry, True, True, 0)
        content.pack_start(desc_box, False, False, 0)
        
        # Method selection notebook (only for creation)
        if not is_edit:
            notebook = Gtk.Notebook()
            content.pack_start(notebook, True, True, 0)
            
            # Tab 1: Directory Scanning
            dir_scan_box = self._create_directory_scan_box()
            notebook.append_page(dir_scan_box, Gtk.Label(label="📁 Directory Scan"))
            
            # Tab 2: Online Manifest
            online_box = self._create_online_manifest_box()
            notebook.append_page(online_box, Gtk.Label(label="🌐 Online Manifest"))
            
            content._notebook = notebook
        else:
            # For editing, show appropriate controls based on type
            if manifest_info.get('type') == 'remote':
                url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                url_label = Gtk.Label(label="Source URL:")
                url_label.set_size_request(120, -1)
                url_entry = Gtk.Entry()
                url_entry.set_text(manifest_info.get('source_url', ''))
                url_box.pack_start(url_label, False, False, 0)
                url_box.pack_start(url_entry, True, True, 0)
                content.pack_start(url_box, False, False, 0)
                
                verify_btn = Gtk.Button(label="Verify URL")
                verify_status_label = Gtk.Label()
                verify_btn.connect("clicked", lambda b: self._verify_url(url_entry, verify_status_label))
                content.pack_start(verify_btn, False, False, 0)
                content.pack_start(verify_status_label, False, False, 0)
                
                content._url_entry = url_entry
            else:
                info_label = Gtk.Label()
                info_label.set_markup(
                    f"<b>Statistics:</b>\n"
                    f"• Total Scripts: {manifest_info.get('total_scripts', 0)}\n"
                    f"• Categories: {', '.join(manifest_info.get('categories', []))}\n"
                    f"• Created: {manifest_info.get('created', 'Unknown')}\n\n"
                    f"<i>Note: Directory-based manifests can only have name and description edited.</i>"
                )
                info_label.set_line_wrap(True)
                info_label.set_xalign(0)
                content.pack_start(info_label, True, True, 0)
        
        # Checksum verification toggle
        verify_checksums = Gtk.CheckButton(label="Verify script checksums (recommended for security)")
        verify_checksums.set_active(True if not manifest_info else manifest_info.get('verify_checksums', True))
        verify_checksums.set_margin_top(10)
        verify_checksums.set_tooltip_text("Verify scripts match checksums during execution. Recommended for security.")
        content.pack_start(verify_checksums, False, False, 0)
        
        # Store references
        content._name_entry = name_entry
        content._desc_entry = desc_entry
        content._verify_checksums = verify_checksums
        content._manifest_info = manifest_info
        content._is_edit = is_edit
        
        return dialog
    
    def _create_directory_scan_box(self):
        """Create directory scanning tab"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Recursive checkbox
        recursive_check = Gtk.CheckButton(label="Scan directories recursively")
        recursive_check.set_active(True)
        box.pack_start(recursive_check, False, False, 0)
        
        # Directories list
        box.pack_start(Gtk.Label(label="Directories to scan:"), False, False, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        
        dir_store = Gtk.ListStore(str)
        dir_tree = Gtk.TreeView(model=dir_store)
        
        path_renderer = Gtk.CellRendererText()
        path_column = Gtk.TreeViewColumn("Directory Path", path_renderer, text=0)
        dir_tree.append_column(path_column)
        
        scrolled.add(dir_tree)
        box.pack_start(scrolled, True, True, 0)
        
        # Directory buttons
        dir_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_dir_btn = Gtk.Button(label="Add Directory")
        add_dir_btn.connect("clicked", lambda b: self._add_directory(dir_store))
        dir_button_box.pack_start(add_dir_btn, False, False, 0)
        
        remove_dir_btn = Gtk.Button(label="Remove Selected")
        remove_dir_btn.connect("clicked", lambda b: self._remove_directory(dir_tree, dir_store))
        dir_button_box.pack_start(remove_dir_btn, False, False, 0)
        
        box.pack_start(dir_button_box, False, False, 0)
        
        # Store references
        box._dir_store = dir_store
        box._recursive_check = recursive_check
        
        return box
    
    def _create_online_manifest_box(self):
        """Create online manifest tab"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Instructions
        instruction_label = Gtk.Label()
        instruction_label.set_markup(
            "<b>Import from Online Manifest</b>\n\n"
            "Enter the URL of an existing manifest.json file to import.\n\n"
            "<i>Examples:</i>\n"
            "• https://raw.githubusercontent.com/user/repo/main/manifest.json\n"
            "• https://example.com/my-scripts/manifest.json\n"
            "• file:///home/user/my-manifest.json"
        )
        instruction_label.set_line_wrap(True)
        instruction_label.set_xalign(0)
        box.pack_start(instruction_label, False, False, 0)
        
        # URL entry
        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        url_label = Gtk.Label(label="Manifest URL:")
        url_label.set_size_request(100, -1)
        url_entry = Gtk.Entry()
        url_entry.set_placeholder_text("https://raw.githubusercontent.com/user/repo/main/manifest.json")
        url_box.pack_start(url_label, False, False, 0)
        url_box.pack_start(url_entry, True, True, 0)
        box.pack_start(url_box, False, False, 0)
        
        # Verify button
        verify_status_label = Gtk.Label()
        verify_btn = Gtk.Button(label="Verify URL")
        verify_btn.connect("clicked", lambda b: self._verify_url(url_entry, verify_status_label))
        box.pack_start(verify_btn, False, False, 0)
        box.pack_start(verify_status_label, False, False, 0)
        
        # Store references
        box._url_entry = url_entry
        
        return box
    
    def _add_directory(self, dir_store):
        """Add a directory to the scan list"""
        dialog = Gtk.FileChooserDialog(
            title="Select Directory to Scan",
            parent=self.parent,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        dialog.set_current_folder(str(Path.home()))
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            directory = dialog.get_filename()
            for row in dir_store:
                if row[0] == directory:
                    dialog.destroy()
                    return
            dir_store.append([directory])
        
        dialog.destroy()
    
    def _remove_directory(self, tree_view, dir_store):
        """Remove selected directory from the scan list"""
        selection = tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            model.remove(tree_iter)
    
    def _verify_url(self, url_entry, status_label):
        """Verify that a manifest URL is accessible and valid"""
        url = url_entry.get_text().strip()
        
        if not url:
            status_label.set_markup("<span color='red'>Please enter a URL</span>")
            return
        
        status_label.set_markup("<span color='blue'>Verifying URL...</span>")
        GLib.timeout_add(100, self._do_verify_url, url, status_label)
    
    def _do_verify_url(self, url, status_label):
        """Perform the actual URL verification"""
        try:
            if url.startswith('file://'):
                file_path = url[7:]
                if not os.path.exists(file_path):
                    status_label.set_markup("<span color='red'>✗ File not found</span>")
                    return False
                
                with open(file_path, 'r') as f:
                    manifest = json.load(f)
                
                if 'scripts' in manifest or 'version' in manifest:
                    status_label.set_markup("<span color='green'>✓ Valid manifest file</span>")
                else:
                    status_label.set_markup("<span color='orange'>⚠ File may not be a valid manifest</span>")
                return False
            
            elif url.startswith(('http://', 'https://')):
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'lv_linux_learn/2.1.0')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = response.read()
                    manifest = json.loads(data)
                    
                    if 'scripts' in manifest or 'version' in manifest:
                        status_label.set_markup("<span color='green'>✓ Valid manifest URL</span>")
                    else:
                        status_label.set_markup("<span color='orange'>⚠ URL may not be a valid manifest</span>")
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
        
        return False
    
    def _run_manifest_dialog(self, dialog, manifest_info=None, is_edit=False):
        """Run the manifest dialog and handle responses"""
        content = dialog.get_content_area()
        
        while True:
            response = dialog.run()
            
            if response != Gtk.ResponseType.OK:
                dialog.destroy()
                return
            
            # Get inputs
            name = content._name_entry.get_text().strip()
            description = content._desc_entry.get_text().strip()
            verify_checksums = content._verify_checksums.get_active()
            
            if not name:
                self._show_error("Please enter a manifest name.")
                continue
            
            if not is_edit:
                # New manifest - handle based on active tab
                notebook = content._notebook
                current_tab = notebook.get_current_page()
                
                if current_tab == 0:  # Directory Scan
                    dir_box = notebook.get_nth_page(0)
                    directories = [row[0] for row in dir_box._dir_store]
                    recursive = dir_box._recursive_check.get_active()
                    
                    if not directories:
                        self._show_error("Please add at least one directory to scan.")
                        continue
                    
                    dialog.destroy()
                    
                    success, message = self.custom_manifest_creator.create_manifest(
                        name, directories, description, recursive, verify_checksums
                    )
                
                else:  # Online Manifest
                    online_box = notebook.get_nth_page(1)
                    url = online_box._url_entry.get_text().strip()
                    
                    if not url:
                        self._show_error("Please enter a manifest URL.")
                        continue
                    
                    if not url.startswith(('http://', 'https://', 'file://')):
                        self._show_error("URL must start with http://, https://, or file://")
                        continue
                    
                    dialog.destroy()
                    
                    success, message = self.custom_manifest_creator.import_manifest_from_url(
                        name, url, description, verify_checksums
                    )
            
            else:
                # Editing existing manifest - READ VALUES BEFORE DESTROYING DIALOG
                manifest_type = manifest_info.get('type', 'directory_scan')
                
                if manifest_type == 'remote':
                    url = content._url_entry.get_text().strip()
                    if not url:
                        self._show_error("Please enter a manifest URL.")
                        dialog.destroy()
                        continue
                
                dialog.destroy()
                
                if manifest_type == 'remote':
                    old_name = manifest_info['name']
                    old_url = manifest_info.get('source_url', '')
                    
                    # If name or URL changed, need to recreate the manifest
                    if url != old_url or name != old_name:
                        self.custom_manifest_creator.delete_custom_manifest(old_name)
                        success, message = self.custom_manifest_creator.import_manifest_from_url(
                            name, url, description, verify_checksums
                        )
                    else:
                        # Just updating description/verify_checksums
                        success, message = self.custom_manifest_creator.update_manifest_metadata(
                            old_name, description, verify_checksums
                        )
                else:
                    # Directory scan manifest - can only update description and verify_checksums
                    # TODO: Add support for renaming directory scan manifests
                    success, message = self.custom_manifest_creator.update_manifest_metadata(
                        manifest_info['name'], description, verify_checksums
                    )
            
            # Handle result
            if success:
                self.parent.terminal.feed(f"\x1b[32m[✓] {message}\x1b[0m\r\n".encode())
                
                # Refresh UI to show updated manifest
                self.populate_tree()
                self.parent._reload_main_tabs()
                
                # Switch to the updated manifest if name didn't change
                if name == manifest_info.get('name'):
                    self.custom_manifest_creator.switch_to_custom_manifest(name)
                    if self.parent.repository:
                        self.parent.repository.refresh_repository_url()
                
                GLib.timeout_add(100, self.parent._complete_terminal_silent)
            else:
                self.parent.terminal.feed(f"\x1b[31m[✗] {message}\x1b[0m\r\n".encode())
                GLib.timeout_add(100, self.parent._complete_terminal_silent)
            
            return
    
    def _show_edit_manifest_dialog(self, manifest_name):
        """Show edit dialog for existing custom manifest"""
        if not self.custom_manifest_creator:
            return
        
        manifests = self.custom_manifest_creator.list_custom_manifests()
        manifest_info = next((m for m in manifests if m['name'] == manifest_name), None)
        
        if not manifest_info:
            self._show_error(f"Manifest '{manifest_name}' not found")
            return
        
        dialog = self._create_manifest_dialog(manifest_info, is_edit=True)
        dialog.show_all()
        self._run_manifest_dialog(dialog, manifest_info, is_edit=True)
    
    def _show_error(self, message):
        """Show error message in terminal"""
        self.parent.terminal.feed(f"\x1b[31m[✗] Error: {message}\x1b[0m\r\n".encode())
