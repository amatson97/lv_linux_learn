"""
Extended Dialog Helpers - Consolidated dialog patterns
Provides factory methods for common dialog creation across tab handlers
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from gi.repository import Gtk, GLib


class DialogFactory:
    """Factory for creating common dialogs across the application"""
    
    @staticmethod
    def create_manifest_dialog(parent, title, is_edit=False, manifest_info=None):
        """
        Create a manifest creation/editing dialog
        
        Args:
            parent: Parent window
            title: Dialog title
            is_edit: Whether this is an edit dialog
            manifest_info: Manifest info dict (for edit mode)
            
        Returns:
            Gtk.Dialog configured for manifest management
        """
        dialog = Gtk.Dialog(
            title=title,
            parent=parent,
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
        
        return dialog, content
    
    @staticmethod
    def create_confirmation_dialog(parent, title, message, secondary_text=None, 
                                   message_type=Gtk.MessageType.WARNING):
        """
        Create a confirmation dialog
        
        Args:
            parent: Parent window
            title: Dialog title/primary text
            message: Dialog title text
            secondary_text: Secondary explanation text
            message_type: Gtk.MessageType (INFO, WARNING, QUESTION, ERROR)
            
        Returns:
            Response (Gtk.ResponseType.YES or Gtk.ResponseType.NO)
        """
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            flags=0,
            message_type=message_type,
            buttons=Gtk.ButtonsType.YES_NO,
            text=message
        )
        if secondary_text:
            dialog.format_secondary_text(secondary_text)
        
        return dialog
    
    @staticmethod
    def create_info_dialog(parent, title, message, secondary_text=None):
        """
        Create an info/notification dialog
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Primary message text
            secondary_text: Secondary explanation text
            
        Returns:
            Gtk.MessageDialog
        """
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        if secondary_text:
            dialog.format_secondary_text(secondary_text)
        
        return dialog
    
    @staticmethod
    def create_error_dialog(parent, title, message, secondary_text=None):
        """
        Create an error dialog
        
        Args:
            parent: Parent window
            title: Dialog title
            message: Error message text
            secondary_text: Additional error details
            
        Returns:
            Gtk.MessageDialog
        """
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        if secondary_text:
            dialog.format_secondary_text(secondary_text)
        
        return dialog
    
    @staticmethod
    def create_directory_chooser(parent, title="Select Directory", 
                                 initial_folder=None):
        """
        Create a directory chooser dialog
        
        Args:
            parent: Parent window
            title: Dialog title
            initial_folder: Initial folder to show (defaults to home)
            
        Returns:
            Gtk.FileChooserDialog
        """
        dialog = Gtk.FileChooserDialog(
            title=title,
            parent=parent,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        if initial_folder and os.path.isdir(initial_folder):
            dialog.set_current_folder(initial_folder)
        else:
            dialog.set_current_folder(str(Path.home()))
        
        return dialog
    
    @staticmethod
    def create_file_chooser(parent, title="Select File", 
                           action=Gtk.FileChooserAction.OPEN):
        """
        Create a file chooser dialog
        
        Args:
            parent: Parent window
            title: Dialog title
            action: Gtk.FileChooserAction (OPEN, SAVE, SELECT_FOLDER, CREATE_FOLDER)
            
        Returns:
            Gtk.FileChooserDialog
        """
        dialog = Gtk.FileChooserDialog(
            title=title,
            parent=parent,
            action=action
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN if action == Gtk.FileChooserAction.OPEN else Gtk.STOCK_SAVE,
            Gtk.ResponseType.OK
        )
        
        return dialog


class DialogInputBuilder:
    """Helper for building input components in dialogs"""
    
    @staticmethod
    def create_text_input(parent_box, label, placeholder="", initial_value=""):
        """
        Create a labeled text input field
        
        Args:
            parent_box: Parent Gtk.Box to add to
            label: Label text
            placeholder: Placeholder text
            initial_value: Initial text value
            
        Returns:
            Gtk.Entry widget
        """
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        label_widget = Gtk.Label(label=label)
        label_widget.set_size_request(120, -1)
        
        entry = Gtk.Entry()
        entry.set_placeholder_text(placeholder)
        if initial_value:
            entry.set_text(initial_value)
        
        box.pack_start(label_widget, False, False, 0)
        box.pack_start(entry, True, True, 0)
        parent_box.pack_start(box, False, False, 0)
        
        return entry
    
    @staticmethod
    def create_checkbox(parent_box, label, active=True, tooltip=""):
        """
        Create a checkbox
        
        Args:
            parent_box: Parent Gtk.Box to add to
            label: Checkbox label
            active: Initial state
            tooltip: Tooltip text
            
        Returns:
            Gtk.CheckButton widget
        """
        checkbox = Gtk.CheckButton(label=label)
        checkbox.set_active(active)
        if tooltip:
            checkbox.set_tooltip_text(tooltip)
        checkbox.set_margin_top(10)
        parent_box.pack_start(checkbox, False, False, 0)
        
        return checkbox
    
    @staticmethod
    def create_separator(parent_box):
        """
        Create a horizontal separator line
        
        Args:
            parent_box: Parent Gtk.Box to add to
        """
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        parent_box.pack_start(separator, False, False, 5)
    
    @staticmethod
    def create_label(parent_box, text, markup=False, wrap=True, xalign=0):
        """
        Create a label widget
        
        Args:
            parent_box: Parent Gtk.Box to add to
            text: Label text
            markup: Whether to use Pango markup
            wrap: Whether to wrap text
            xalign: Horizontal alignment (0=left, 1=right, 0.5=center)
            
        Returns:
            Gtk.Label widget
        """
        label = Gtk.Label()
        if markup:
            label.set_markup(text)
        else:
            label.set_text(text)
        
        label.set_line_wrap(wrap)
        label.set_xalign(xalign)
        parent_box.pack_start(label, False, False, 0)
        
        return label


class URLVerificationDialog:
    """Handles URL verification in dialogs"""
    
    @staticmethod
    def create_verification_section(parent_box, url_entry):
        """
        Create URL verification UI section
        
        Args:
            parent_box: Parent Gtk.Box to add to
            url_entry: Gtk.Entry containing the URL
            
        Returns:
            (verify_button, status_label) tuple
        """
        verify_btn = Gtk.Button(label="Verify URL")
        status_label = Gtk.Label()
        status_label.set_line_wrap(True)
        status_label.set_xalign(0)
        
        parent_box.pack_start(verify_btn, False, False, 0)
        parent_box.pack_start(status_label, False, False, 0)
        
        return verify_btn, status_label
    
    @staticmethod
    def verify_url(url, status_label):
        """
        Verify that a manifest URL is accessible and valid
        
        Args:
            url: URL to verify
            status_label: Gtk.Label to show status
        """
        if not url:
            status_label.set_markup("<span color='red'>Please enter a URL</span>")
            return
        
        status_label.set_markup("<span color='blue'>Verifying URL...</span>")
        GLib.timeout_add(100, URLVerificationDialog._do_verify, url, status_label)
    
    @staticmethod
    def _do_verify(url, status_label):
        """Perform the actual URL verification (non-blocking)"""
        try:
            # Handle file:// URLs
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
                    status_label.set_markup("<span color='orange'>⚠ File may not be valid manifest</span>")
                return False
            
            # Handle HTTP/HTTPS URLs
            elif url.startswith(('http://', 'https://')):
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'lv_linux_learn/2.1.0')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = response.read()
                    manifest = json.loads(data)
                    
                    if 'scripts' in manifest or 'version' in manifest:
                        status_label.set_markup("<span color='green'>✓ Valid manifest URL</span>")
                    else:
                        status_label.set_markup("<span color='orange'>⚠ URL may not be valid</span>")
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


# ============================================================================
# QUICK DIALOG HELPERS - Simplified one-liners for common dialogs
# ============================================================================

def show_confirmation(parent, title: str, message: str, secondary: str = None) -> bool:
    """
    Show yes/no confirmation dialog (simplified interface)
    
    Args:
        parent: Parent window
        title: Primary message text
        message: Dialog title (legacy - kept for compatibility)
        secondary: Secondary explanation text
    
    Returns:
        True if YES clicked, False otherwise
    """
    dialog = DialogFactory.create_confirmation_dialog(
        parent, message, title, secondary, Gtk.MessageType.QUESTION
    )
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.YES


def show_error(parent, title: str, message: str, secondary: str = None):
    """
    Show error dialog (simplified interface)
    
    Args:
        parent: Parent window
        title: Primary error message
        message: Dialog title (legacy - kept for compatibility)  
        secondary: Secondary explanation text
    """
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        flags=0,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text=title
    )
    if secondary:
        dialog.format_secondary_text(secondary)
    dialog.run()
    dialog.destroy()


def show_info(parent, title: str, message: str, secondary: str = None):
    """
    Show info dialog (simplified interface)
    
    Args:
        parent: Parent window
        title: Primary message text
        message: Dialog title (legacy - kept for compatibility)
        secondary: Secondary explanation text
    """
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=title
    )
    if secondary:
        dialog.format_secondary_text(secondary)
    dialog.run()
    dialog.destroy()


def show_warning(parent, title: str, message: str, secondary: str = None) -> bool:
    """
    Show warning dialog with OK/Cancel (simplified interface)
    
    Args:
        parent: Parent window
        title: Primary warning message
        message: Dialog title (legacy - kept for compatibility)
        secondary: Secondary explanation text
    
    Returns:
        True if OK clicked, False if cancelled
    """
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        flags=0,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.OK_CANCEL,
        text=title
    )
    if secondary:
        dialog.format_secondary_text(secondary)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK

