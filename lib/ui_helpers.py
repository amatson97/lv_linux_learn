"""
UI Helpers Module
Centralizes GTK dialog creation, terminal output formatting, and UI refresh operations
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import Optional, List, Callable


# ============================================================================
# DIALOG HELPERS
# ============================================================================

def show_error_dialog(parent_window: Optional[Gtk.Window], message: str, title: str = "Error") -> None:
    """Show a generic error dialog"""
    dialog = Gtk.MessageDialog(
        transient_for=parent_window,
        flags=0,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text=title
    )
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()


def show_info_dialog(parent_window: Optional[Gtk.Window], message: str, title: str = "Information") -> None:
    """Show an information dialog"""
    dialog = Gtk.MessageDialog(
        transient_for=parent_window,
        flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=title
    )
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()


def show_warning_dialog(parent_window: Optional[Gtk.Window], message: str, title: str = "Warning") -> None:
    """Show a warning dialog"""
    dialog = Gtk.MessageDialog(
        transient_for=parent_window,
        flags=0,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.OK,
        text=title
    )
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()


def show_confirmation_dialog(
    parent_window: Optional[Gtk.Window], 
    message: str, 
    title: str = "Confirm Action",
    secondary_text: Optional[str] = None
) -> bool:
    """
    Show a yes/no confirmation dialog
    
    Returns:
        True if user clicked Yes, False otherwise
    """
    dialog = Gtk.MessageDialog(
        transient_for=parent_window,
        flags=0,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text=title
    )
    if secondary_text:
        dialog.format_secondary_text(secondary_text)
    else:
        dialog.format_secondary_text(message)
    
    response = dialog.run()
    dialog.destroy()
    
    return response == Gtk.ResponseType.YES


def show_install_prompt_dialog(
    parent_window: Optional[Gtk.Window],
    missing_packages: List[str],
    package_type: str = "required"
) -> bool:
    """
    Show package installation prompt dialog
    
    Args:
        parent_window: Parent GTK window
        missing_packages: List of package names
        package_type: "required" or "optional"
        
    Returns:
        True if user wants to install, False otherwise
    """
    dialog = Gtk.MessageDialog(
        transient_for=parent_window,
        flags=0,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.YES_NO,
        text=f"Missing {package_type.capitalize()} Packages"
    )
    
    pkg_list = "\n".join(f"  • {pkg}" for pkg in missing_packages)
    secondary_text = f"The following packages are missing:\n\n{pkg_list}\n\n"
    
    if package_type == "required":
        secondary_text += "These packages are required for core functionality.\n"
    else:
        secondary_text += "These packages are optional but recommended.\n"
    
    secondary_text += "Would you like to install them now?"
    
    dialog.format_secondary_text(secondary_text)
    response = dialog.run()
    dialog.destroy()
    
    return response == Gtk.ResponseType.YES


def show_install_started_dialog(
    parent_window: Optional[Gtk.Window],
    package_type: str,
    package_list: List[str],
    required: bool = True
) -> None:
    """Show dialog indicating package installation has started"""
    dialog = Gtk.MessageDialog(
        transient_for=parent_window,
        flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=f"Installing {package_type.capitalize()} Packages"
    )
    
    pkg_names = ", ".join(package_list)
    message = f"Installing {len(package_list)} package(s): {pkg_names}\n\n"
    
    if required:
        message += "Please check the terminal for installation progress.\n"
        message += "The application will be ready once installation completes."
    else:
        message += "Installation is running in the terminal.\n"
        message += "You can continue using the application."
    
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()


def show_install_completion_dialog(parent_window: Optional[Gtk.Window]) -> None:
    """Show dialog indicating package installation completed"""
    dialog = Gtk.MessageDialog(
        transient_for=parent_window,
        flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text="Installation Complete"
    )
    dialog.format_secondary_text(
        "Package installation completed successfully.\n"
        "Check the terminal for details."
    )
    dialog.run()
    dialog.destroy()


def show_download_confirmation_dialog(
    parent_window: Optional[Gtk.Window],
    script_name: str
) -> bool:
    """Show confirmation dialog for downloading a script"""
    dialog = Gtk.MessageDialog(
        transient_for=parent_window,
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
    
    return response == Gtk.ResponseType.YES


# ============================================================================
# TERMINAL OUTPUT HELPERS
# ============================================================================

def terminal_clear(terminal_widget) -> None:
    """Clear terminal screen"""
    if terminal_widget:
        terminal_widget.feed(b"\x1b[2J\x1b[H")


def terminal_info(terminal_widget, message: str) -> None:
    """Output info message to terminal (blue)"""
    if terminal_widget:
        terminal_widget.feed(f"\x1b[36m{message}\x1b[0m\r\n".encode())


def terminal_success(terminal_widget, message: str) -> None:
    """Output success message to terminal (green)"""
    if terminal_widget:
        terminal_widget.feed(f"\x1b[32m{message}\x1b[0m\r\n".encode())


def terminal_warning(terminal_widget, message: str) -> None:
    """Output warning message to terminal (yellow)"""
    if terminal_widget:
        terminal_widget.feed(f"\x1b[33m{message}\x1b[0m\r\n".encode())


def terminal_error(terminal_widget, message: str) -> None:
    """Output error message to terminal (red)"""
    if terminal_widget:
        terminal_widget.feed(f"\x1b[31m{message}\x1b[0m\r\n".encode())


def terminal_command(terminal_widget, command: str) -> None:
    """Send command to terminal"""
    if terminal_widget:
        terminal_widget.feed_child(f"{command}\n".encode())


def terminal_section_header(terminal_widget, title: str, width: int = 60) -> None:
    """Output a formatted section header"""
    if not terminal_widget:
        return
    
    border = "=" * width
    terminal_widget.feed(f"\x1b[36m{border}\x1b[0m\r\n".encode())
    terminal_widget.feed(f"\x1b[36m{title.center(width)}\x1b[0m\r\n".encode())
    terminal_widget.feed(f"\x1b[36m{border}\x1b[0m\r\n".encode())


def terminal_box(terminal_widget, message: str, width: int = 50, color: str = "yellow") -> None:
    """Output a formatted box message"""
    if not terminal_widget:
        return
    
    # Color codes
    colors = {
        "yellow": "\x1b[33m",
        "green": "\x1b[32m",
        "red": "\x1b[31m",
        "blue": "\x1b[36m",
        "reset": "\x1b[0m"
    }
    
    color_code = colors.get(color, colors["yellow"])
    reset = colors["reset"]
    
    # Truncate message if too long
    if len(message) > width - 6:
        message = message[:width - 9] + "..."
    
    terminal_widget.feed(f"{color_code}╔{'═' * (width - 2)}╗{reset}\r\n".encode())
    terminal_widget.feed(f"{color_code}║ {message.center(width - 4)} ║{reset}\r\n".encode())
    terminal_widget.feed(f"{color_code}╚{'═' * (width - 2)}╝{reset}\r\n".encode())


# ============================================================================
# UI REFRESH HELPERS
# ============================================================================

def schedule_ui_update(callback: Callable, delay_ms: int = 500) -> int:
    """
    Schedule a UI update callback
    
    Args:
        callback: Function to call
        delay_ms: Delay in milliseconds
        
    Returns:
        GLib timeout ID
    """
    return GLib.timeout_add(delay_ms, callback)


def schedule_terminal_complete(callback: Callable, delay_ms: int = 1500) -> int:
    """Schedule terminal operation completion (default 1.5s delay)"""
    return GLib.timeout_add(delay_ms, callback)


# ============================================================================
# SELECTION HELPERS
# ============================================================================

def get_selected_item(treeview: Gtk.TreeView, column_index: int = 0):
    """
    Get selected item from treeview
    
    Args:
        treeview: GTK TreeView widget
        column_index: Column to extract value from
        
    Returns:
        tuple: (value, model, treeiter) or (None, None, None) if nothing selected
    """
    selection = treeview.get_selection()
    model, treeiter = selection.get_selected()
    
    if treeiter:
        value = model.get_value(treeiter, column_index)
        return value, model, treeiter
    
    return None, None, None


def get_selected_items(treeview: Gtk.TreeView) -> List[tuple]:
    """
    Get all selected items from treeview (for multi-select)
    
    Returns:
        List of (model, treeiter) tuples
    """
    selection = treeview.get_selection()
    model, paths = selection.get_selected_rows()
    
    result = []
    for path in paths:
        treeiter = model.get_iter(path)
        result.append((model, treeiter))
    
    return result


# ============================================================================
# NO-SELECTION HELPERS
# ============================================================================

def show_no_selection_dialog(parent_window: Optional[Gtk.Window], item_type: str = "item") -> None:
    """Show dialog when no item is selected"""
    show_info_dialog(
        parent_window,
        f"Please select a {item_type} from the list.",
        f"No {item_type.capitalize()} Selected"
    )
