"""
TerminalMessenger - Centralized terminal messaging with consistent formatting

Eliminates 20+ duplicate terminal.feed() calls with ANSI color codes
"""
from typing import Any, Optional


class TerminalMessenger:
    """
    Centralized terminal messaging with consistent formatting and colors
    
    Provides semantic methods for success, error, info, and warning messages
    with automatic ANSI color coding and formatting.
    """
    
    # ANSI color codes
    COLORS: dict[str, str] = {
        'reset': '\x1b[0m',
        'red': '\x1b[31m',
        'green': '\x1b[32m',
        'yellow': '\x1b[33m',
        'cyan': '\x1b[36m',
        'white': '\x1b[37m',
    }
    
    # Message icons
    ICONS: dict[str, str] = {
        'success': '✓',
        'error': '✗',
        'info': '*',
        'warning': '!',
        'download': '☁️',
    }
    
    def __init__(self, terminal) -> None:
        """
        Initialize TerminalMessenger
        
        Args:
            terminal: VTE terminal widget instance
        """
        self.terminal: Any = terminal
    
    def success(self, message: str) -> None:
        """
        Print success message in green with checkmark icon
        
        Args:
            message: Success message to display
        """
        self._print('green', self.ICONS['success'], message)
    
    def error(self, message: str) -> None:
        """
        Print error message in red with X icon
        
        Args:
            message: Error message to display
        """
        self._print('red', self.ICONS['error'], message)
    
    def info(self, message: str) -> None:
        """
        Print info message in cyan with asterisk icon
        
        Args:
            message: Info message to display
        """
        self._print('cyan', self.ICONS['info'], message)
    
    def warning(self, message: str) -> None:
        """
        Print warning message in yellow with exclamation icon
        
        Args:
            message: Warning message to display
        """
        self._print('yellow', self.ICONS['warning'], message)
    
    def download(self, message: str) -> None:
        """
        Print download message in green with cloud icon
        
        Args:
            message: Download message to display
        """
        self._print('green', self.ICONS['download'], message)
    
    def custom(self, message: str, color: str = 'white', icon: Optional[str] = None) -> None:
        """
        Print custom message with specified color and optional icon
        
        Args:
            message: Message to display
            color: Color name from COLORS dict
            icon: Optional icon to display
        """
        self._print(color, icon, message)
    
    def _print(self, color: str, icon: Optional[str], message: str) -> None:
        """
        Internal print helper with color and icon formatting
        
        Args:
            color: Color name from COLORS dict
            icon: Icon to display (can be None)
            message: Message to display
        """
        color_code: str = self.COLORS.get(color, self.COLORS['white'])
        icon_str: str = f"[{icon}] " if icon else ""
        formatted: str = f"{color_code}{icon_str}{message}{self.COLORS['reset']}\r\n"
        self.terminal.feed(formatted.encode())
    
    def raw(self, text: str) -> None:
        """
        Send raw text to terminal without formatting
        
        Args:
            text: Raw text to send
        """
        self.terminal.feed(text.encode())
