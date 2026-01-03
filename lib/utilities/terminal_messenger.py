"""
TerminalMessenger - Centralized terminal messaging with consistent formatting

Eliminates 20+ duplicate terminal.feed() calls with ANSI color codes
"""
from typing import Optional


class TerminalMessenger:
    """
    Centralized terminal messaging with consistent formatting and colors
    
    Provides semantic methods for success, error, info, and warning messages
    with automatic ANSI color coding and formatting.
    """
    
    # ANSI color codes
    COLORS = {
        'reset': '\x1b[0m',
        'red': '\x1b[31m',
        'green': '\x1b[32m',
        'yellow': '\x1b[33m',
        'cyan': '\x1b[36m',
        'white': '\x1b[37m',
    }
    
    # Message icons
    ICONS = {
        'success': '✓',
        'error': '✗',
        'info': '*',
        'warning': '!',
        'download': '☁️',
    }
    
    def __init__(self, terminal):
        """
        Initialize TerminalMessenger
        
        Args:
            terminal: VTE terminal widget instance
        """
        self.terminal = terminal
    
    def success(self, message: str):
        """
        Print success message in green with checkmark icon
        
        Args:
            message: Success message to display
        """
        self._print('green', self.ICONS['success'], message)
    
    def error(self, message: str):
        """
        Print error message in red with X icon
        
        Args:
            message: Error message to display
        """
        self._print('red', self.ICONS['error'], message)
    
    def info(self, message: str):
        """
        Print info message in cyan with asterisk icon
        
        Args:
            message: Info message to display
        """
        self._print('cyan', self.ICONS['info'], message)
    
    def warning(self, message: str):
        """
        Print warning message in yellow with exclamation icon
        
        Args:
            message: Warning message to display
        """
        self._print('yellow', self.ICONS['warning'], message)
    
    def download(self, message: str):
        """
        Print download message in green with cloud icon
        
        Args:
            message: Download message to display
        """
        self._print('green', self.ICONS['download'], message)
    
    def custom(self, message: str, color: str = 'white', icon: Optional[str] = None):
        """
        Print custom message with specified color and optional icon
        
        Args:
            message: Message to display
            color: Color name from COLORS dict
            icon: Optional icon to display
        """
        self._print(color, icon, message)
    
    def _print(self, color: str, icon: Optional[str], message: str):
        """
        Internal print helper with color and icon formatting
        
        Args:
            color: Color name from COLORS dict
            icon: Icon to display (can be None)
            message: Message to display
        """
        color_code = self.COLORS.get(color, self.COLORS['white'])
        icon_str = f"[{icon}] " if icon else ""
        formatted = f"{color_code}{icon_str}{message}{self.COLORS['reset']}\r\n"
        self.terminal.feed(formatted.encode())
    
    def raw(self, text: str):
        """
        Send raw text to terminal without formatting
        
        Args:
            text: Raw text to send
        """
        self.terminal.feed(text.encode())
