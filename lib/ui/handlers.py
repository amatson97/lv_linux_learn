# -*- coding: utf-8 -*-
"""
Event handlers for GUI script actions.

Extracted from menu.py for better maintainability and testability.
These handlers encapsulate logic for:
- Repository operations (check updates, download scripts, clear cache)
- User interactions with terminal and dialogs
- State management and UI refresh

Usage:
    handler = RepositoryActionHandler(repository, terminal_view, app_instance)
    handler.on_check_updates()
    handler.on_download_all()
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import os
import traceback
from pathlib import Path
from typing import Optional, Callable, Tuple

from lib.utilities import TimerManager


class RepositoryActionHandler:
    """Handler for repository-related button actions.
    
    Encapsulates:
    - Check for updates
    - Download all scripts
    - Clear script cache
    - Repository settings management
    
    Args:
        repository: ScriptRepository instance
        terminal_view: VTE terminal widget for output
        app_instance: Main application window for context
    """
    
    def __init__(self, repository, terminal_view, app_instance):
        """Initialize handler with dependencies.
        
        Args:
            repository: ScriptRepository instance
            terminal_view: VTE terminal for feedback
            app_instance: Main menu window
        """
        self.repository = repository
        self.terminal = terminal_view
        self.app = app_instance
    
    def on_check_updates(self) -> None:
        """Manually check for updates.
        
        Clears repository cache and triggers fresh manifest refresh.
        Displays update count in terminal and updates UI.
        
        Raises:
            Exception: Propagated from repository or UI operations
        """
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
            
            # Schedule UI refresh
            if TimerManager:
                TimerManager.schedule_ui_refresh(self._complete_operation)
            else:
                GLib.timeout_add(500, self._complete_operation)
            
            # Refresh display with fresh data
            if hasattr(self.app, '_update_repo_status'):
                self.app._update_repo_status()
            if hasattr(self.app, '_populate_repository_tree'):
                self.app._populate_repository_tree()
            print("[DEBUG] Repository tree refreshed after check", flush=True)
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            if TimerManager:
                TimerManager.schedule_completion(self._complete_operation)
            else:
                GLib.timeout_add(1500, self._complete_operation)
    
    def on_download_all(self) -> None:
        """Download all scripts from repository.
        
        Shows confirmation dialog, then downloads all scripts currently shown.
        Updates terminal with progress and final summary.
        Refreshes UI to show cached status.
        
        Raises:
            Exception: Propagated from repository operations
        """
        if not self.repository:
            return
        
        # Get count of scripts from app's repo_store (respects current filtering)
        total = len(self.app.repo_store) if hasattr(self.app, 'repo_store') else 0
        
        if total == 0:
            self._show_warning_dialog(
                "No Scripts Available",
                "No scripts are currently available to download.\n\n"
                "Please configure a manifest source:\n"
                "• Enable Public Repository in settings, or\n"
                "• Add a Custom Manifest in the Sources tab"
            )
            return
        
        # Confirmation dialog
        if not self._show_confirmation_dialog(
            "Download All Scripts",
            f"This will download all {total} scripts shown in the Repository tab.\n\n"
            "This may take a few minutes. Continue?"
        ):
            return
        
        self.terminal.feed(
            f"\r\n\x1b[32m[*] Downloading {total} scripts from configured sources...\x1b[0m\r\n".encode()
        )
        
        downloaded, failed = self._download_scripts_from_store()
        
        self.terminal.feed(
            f"\x1b[32m[*] Download complete: {downloaded} downloaded, {failed} failed\x1b[0m\r\n".encode()
        )
        
        # Schedule completion and UI refresh
        if TimerManager:
            TimerManager.schedule_ui_refresh(self._complete_operation)
        else:
            GLib.timeout_add(500, self._complete_operation)
        
        # Refresh display
        if hasattr(self.app, '_populate_repository_tree'):
            self.app._populate_repository_tree()
        if hasattr(self.app, '_reload_main_tabs'):
            self.app._reload_main_tabs()
    
    def on_clear_cache(self) -> None:
        """Clear all scripts from cache.
        
        Shows confirmation dialog, then removes cached scripts.
        Also cleans up stale manifest files.
        Updates UI to reflect cleared cache.
        
        Raises:
            Exception: Propagated from repository operations
        """
        if not self.repository:
            return
        
        # Confirmation dialog
        if not self._show_confirmation_dialog(
            "Remove All Scripts",
            "This will remove all scripts from the cache.\n\n"
            "You can download them again later. Continue?"
        ):
            return
        
        try:
            # Clear script cache
            self.repository.clear_cache()
            self.terminal.feed(b"\r\n\x1b[32m[*] Script cache cleared successfully\x1b[0m\r\n")
            
            # Also clear manifest cache files
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
                    self.terminal.feed(
                        f"\x1b[32m[*] Removed {removed_count} cached manifest file(s)\x1b[0m\r\n".encode()
                    )
            except Exception as e:
                self.terminal.feed(f"\x1b[33m[!] Manifest cache cleanup warning: {e}\x1b[0m\r\n".encode())
            
            # Schedule completion and refresh UI
            if TimerManager:
                TimerManager.schedule_completion(self._complete_operation)
            else:
                GLib.timeout_add(500, self._complete_operation)
            
            # Refresh display
            if hasattr(self.app, '_update_repo_status'):
                self.app._update_repo_status()
            if hasattr(self.app, '_populate_repository_tree'):
                self.app._populate_repository_tree()
            if hasattr(self.app, '_reload_main_tabs'):
                self.app._reload_main_tabs()
            
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            if TimerManager:
                TimerManager.schedule_completion(self._complete_operation)
            else:
                GLib.timeout_add(1500, self._complete_operation)
    
    # Private helper methods
    
    def _download_scripts_from_store(self) -> Tuple[int, int]:
        """Download scripts from app's repo_store.
        
        Returns:
            Tuple of (downloaded_count, failed_count)
        """
        downloaded = 0
        failed = 0
        
        try:
            if not hasattr(self.app, 'repo_store'):
                return 0, 1
            
            for row in self.app.repo_store:
                script_id = row[1]
                script_name = row[2]
                category = row[5].lower() if row[5] else 'install'
                
                try:
                    self.terminal.feed(f"\x1b[36m[*] Downloading {script_name}...\x1b[0m\r\n".encode())
                    
                    # Process pending GTK events
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
                        self.terminal.feed(f"\x1b[32m  ✓ Cached to {cache_path}\x1b[0m\r\n".encode())
                    else:
                        failed += 1
                        self.terminal.feed(f"\x1b[33m  ! Failed to download\x1b[0m\r\n".encode())
                    
                    # Process pending GTK events
                    while Gtk.events_pending():
                        Gtk.main_iteration()
                        
                except Exception as e:
                    failed += 1
                    self.terminal.feed(f"\x1b[31m  ✗ Error: {e}\x1b[0m\r\n".encode())
                    while Gtk.events_pending():
                        Gtk.main_iteration()
                        
        except Exception as e:
            self.terminal.feed(f"\x1b[31m[!] Error: {e}\x1b[0m\r\n".encode())
            self.terminal.feed(f"\x1b[31m{traceback.format_exc()}\x1b[0m\r\n".encode())
            if TimerManager:
                TimerManager.schedule_completion(self._complete_operation)
            else:
                GLib.timeout_add(1500, self._complete_operation)
        
        return downloaded, failed
    
    def _complete_operation(self) -> bool:
        """Auto-complete terminal operation by sending newline.
        
        Returns:
            False to stop timeout from repeating
        """
        self.terminal.feed_child(b"\n")
        return False
    
    def _show_warning_dialog(self, title: str, message: str) -> None:
        """Show warning dialog.
        
        Args:
            title: Dialog title
            message: Dialog message
        """
        dialog = Gtk.MessageDialog(
            transient_for=self.app if hasattr(self.app, 'get_toplevel') else None,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _show_confirmation_dialog(self, title: str, message: str) -> bool:
        """Show confirmation dialog.
        
        Args:
            title: Dialog title
            message: Dialog message
            
        Returns:
            True if user clicked YES, False otherwise
        """
        dialog = Gtk.MessageDialog(
            transient_for=self.app if hasattr(self.app, 'get_toplevel') else None,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=title
        )
        dialog.format_secondary_text(message)
        
        response = dialog.run()
        dialog.destroy()
        
        return response == Gtk.ResponseType.YES


__all__ = ['RepositoryActionHandler']
