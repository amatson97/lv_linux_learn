"""LV Script Manager Python Library

Organized into three main packages:
- core: Repository, manifest, script management
- ui: Dialogs, handlers, and UI components
- utilities: Common utilities, path management, helpers
"""

__version__ = "2.4.0"

# Re-export core components for convenience
from .core import (
    ScriptRepository,
    ManifestLoader,
    ScriptMetadata,
    ScriptCache,
    ScriptEnvironmentManager,
    ScriptExecutionContext,
    ScriptValidator,
)

# Backward compatibility - expose core modules at package level
from . import core
from . import utilities

# UI module is optional (may fail if GTK/gi not available)
try:
    from . import ui
except ImportError:
    ui = None

# Module aliases for backward compatibility with patch paths
from .core import repository
from .core import manifest
from .core import script
from .core import script_execution

__all__ = [
    'ScriptRepository',
    'ManifestLoader',
    'ScriptMetadata',
    'ScriptCache',
    'ScriptEnvironmentManager',
    'ScriptExecutionContext',
    'ScriptValidator',
    'core',
    'ui',
    'utilities',
    'repository',
    'manifest',
    'script',
    'script_execution',
]
