# -*- coding: utf-8 -*-
"""
Dialog factory for GUI message and confirmation dialogs.

Extracts common dialog creation patterns into reusable factory methods.
Provides:
- DialogFactory: Central factory for creating dialogs
- StandardDialogs: Common dialog patterns (info, warning, error, confirmation)

Usage:
    factory = DialogFactory(parent_window)
    factory.info("Title", "Message")
    factory.confirm("Are you sure?", "This cannot be undone")
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from typing import Optional, Tuple


class DialogFactory:
    """Factory for creating consistent dialogs throughout the application.
    
    Encapsulates common dialog patterns and ensures consistent styling.
    
    Args:
        parent: Parent window for transient_for property
    """
    
    def __init__(self, parent=None):
        """Initialize factory with optional parent window.
        
        Args:
            parent: Parent GTK window (optional)
        """
        self.parent = parent
    
    def info(self, title: str, message: str, details: Optional[str] = None) -> None:
        """Show information dialog.
        
        Args:
            title: Dialog title
            message: Primary message
            details: Optional secondary/detailed message
        """
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        if details:
            dialog.format_secondary_text(message)
            if details:
                dialog.format_secondary_text(f"{message}\n\n{details}")
        else:
            dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def warning(self, title: str, message: str, details: Optional[str] = None) -> None:
        """Show warning dialog.
        
        Args:
            title: Dialog title
            message: Primary message
            details: Optional secondary/detailed message
        """
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        if details:
            dialog.format_secondary_text(f"{message}\n\n{details}")
        else:
            dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def error(self, title: str, message: str, details: Optional[str] = None) -> None:
        """Show error dialog.
        
        Args:
            title: Dialog title (usually "Error" or similar)
            message: Primary error message
            details: Optional secondary/detailed error message
        """
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        if details:
            dialog.format_secondary_text(f"{message}\n\n{details}")
        else:
            dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def confirm(self, title: str, message: str, details: Optional[str] = None) -> bool:
        """Show confirmation dialog with Yes/No buttons.
        
        Args:
            title: Dialog title
            message: Primary message
            details: Optional secondary/detailed message
            
        Returns:
            True if user clicked YES, False if NO or cancelled
        """
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=title
        )
        if details:
            dialog.format_secondary_text(f"{message}\n\n{details}")
        else:
            dialog.format_secondary_text(message)
        
        response = dialog.run()
        dialog.destroy()
        
        return response == Gtk.ResponseType.YES
    
    def confirm_destructive(self, title: str, message: str, 
                          details: Optional[str] = None) -> bool:
        """Show destructive action confirmation dialog.
        
        Similar to confirm() but with WARNING icon to emphasize destructive nature.
        
        Args:
            title: Dialog title (usually "Remove X" or "Delete Y")
            message: Primary message explaining what will be removed
            details: Optional secondary message with consequences
            
        Returns:
            True if user clicked YES (confirmed destructive action), False otherwise
        """
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=title
        )
        if details:
            dialog.format_secondary_text(f"{message}\n\n{details}")
        else:
            dialog.format_secondary_text(message)
        
        response = dialog.run()
        dialog.destroy()
        
        return response == Gtk.ResponseType.YES


class StandardDialogs:
    """Static convenience methods for common dialog patterns.
    
    Provides module-level functions for dialogs without needing factory instance.
    Uses None for parent (not transient), suitable for simple scripts or fallback.
    """
    
    @staticmethod
    def info(title: str, message: str, details: Optional[str] = None) -> None:
        """Show information dialog (static method)."""
        factory = DialogFactory(parent=None)
        factory.info(title, message, details)
    
    @staticmethod
    def warning(title: str, message: str, details: Optional[str] = None) -> None:
        """Show warning dialog (static method)."""
        factory = DialogFactory(parent=None)
        factory.warning(title, message, details)
    
    @staticmethod
    def error(title: str, message: str, details: Optional[str] = None) -> None:
        """Show error dialog (static method)."""
        factory = DialogFactory(parent=None)
        factory.error(title, message, details)
    
    @staticmethod
    def confirm(title: str, message: str, details: Optional[str] = None) -> bool:
        """Show confirmation dialog (static method)."""
        factory = DialogFactory(parent=None)
        return factory.confirm(title, message, details)
    
    @staticmethod
    def confirm_destructive(title: str, message: str, 
                           details: Optional[str] = None) -> bool:
        """Show destructive action confirmation dialog (static method)."""
        factory = DialogFactory(parent=None)
        return factory.confirm_destructive(title, message, details)


__all__ = ['DialogFactory', 'StandardDialogs']
