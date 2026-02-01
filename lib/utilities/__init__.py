"""
Utility modules for centralized common operations
"""

from .path_manager import PathManager
from .terminal_messenger import TerminalMessenger
from .file_loader import FileLoader

try:
    from .timer_manager import TimerManager
except ImportError:
    TimerManager = None

try:
    from .ai_categorizer import OllamaAnalyzer, check_ollama_available
except ImportError:
    OllamaAnalyzer = None
    check_ollama_available = None

from .user_scripts import CustomScriptManager

__all__ = [
    'PathManager',
    'TerminalMessenger',
    'FileLoader',
    'TimerManager',
    'OllamaAnalyzer',
    'check_ollama_available',
    'CustomScriptManager',
]
