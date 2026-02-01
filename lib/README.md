# Python Library - lv_linux_learn

The `lib/` directory contains the Python library that powers the GUI and CLI interfaces of lv_linux_learn.

## Directory Structure

```
lib/
├── __init__.py              # Main package initialization and exports
├── config.py                # Configuration management
├── core/                    # Core business logic
│   ├── repository.py        # Script repository management
│   ├── manifest.py          # Manifest loading and parsing
│   ├── script.py            # Script metadata and caching
│   └── script_execution.py  # Script execution environment
├── ui/                      # User interface components
│   ├── handlers.py          # Event handlers
│   ├── dialogs.py           # Dialog factories
│   ├── dialog_helpers.py    # GTK dialog utilities
│   ├── ui_components.py     # UI widget components
│   └── *_tab.py             # Tab handlers
└── utilities/               # Helper utilities
    ├── path_manager.py      # Path management
    ├── terminal_messenger.py # Terminal I/O
    ├── file_loader.py       # File operations
    ├── user_scripts.py      # Custom script management
    ├── ai_categorizer.py    # AI categorization
    └── timer_manager.py     # GTK timer utilities
```

## Modules

### Core - Business Logic

**repository.py** - Main repository class for managing scripts
- Multi-repository support
- Remote manifest handling
- Script caching
- Update detection and management

**manifest.py** - Manifest loading and parsing
- Remote manifest fetching
- JSON/YAML parsing
- Script enumeration
- Dependency resolution

**script.py** - Script metadata and caching
- Script metadata classes
- Cache management
- Script enumeration
- Path resolution

**script_execution.py** - Script execution environment
- Environment variable management
- Script validation
- Command building
- Execution context setup

### UI - User Interface

**handlers.py** - Event handlers
- Repository action handlers
- Script execution handlers
- Error handling and user feedback

**dialogs.py** - Dialog factory and wrappers
- Standard dialogs (error, warning, info)
- Custom dialogs
- Dialog builders

**dialog_helpers.py** - GTK dialog utilities
- Basic dialog creation
- Input dialogs
- Selection dialogs

**ui_components.py** - UI widgets
- Custom GTK components
- Filtering treeviews
- Progress displays

Tab Handlers:
- **repository_tab.py** - Main repository tab
- **local_repository_tab.py** - Local script management
- **custom_manifest_tab.py** - Custom manifest configuration

### Utilities - Helper Functions

**path_manager.py** - Path management
- Cache path resolution
- Directory creation
- Path validation

**terminal_messenger.py** - Terminal I/O
- Progress output
- Colored messages
- Status updates

**file_loader.py** - File operations
- JSON loading
- YAML parsing
- File validation

**user_scripts.py** - Custom script management
- Custom script configuration
- Script enumeration
- Manifest generation

**ai_categorizer.py** - AI categorization (optional)
- Ollama integration
- Script categorization
- AI-powered features

**timer_manager.py** - GTK timers (optional)
- Event scheduling
- Periodic tasks
- GTK integration

## Usage

### Importing Components

```python
# Core functionality
from lib.core.repository import ScriptRepository
from lib.core.manifest import ManifestLoader
from lib.core.script import ScriptMetadata

# UI components
from lib.ui.dialogs import DialogFactory
from lib.ui.handlers import RepositoryActionHandler

# Utilities
from lib.utilities.path_manager import PathManager
from lib.utilities.user_scripts import CustomScriptManager

# Backward compatibility - Direct imports also work
from lib import ScriptRepository, ManifestLoader
```

### Configuration

```python
from lib import config as C

# Access configuration values
C.CACHE_DIR
C.CONFIG_FILE
C.DEFAULT_REPOSITORY_URL
```

## Testing

All modules are thoroughly tested:
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- E2E tests in `tests/e2e/`

Run tests with:
```bash
pytest tests/
```

## Requirements

### Required
- Python 3.8+
- requests (HTTP operations)
- PyYAML (YAML parsing)

### Optional (GUI)
- PyGObject (GTK bindings)
- GTK3 libraries
- Pango (text rendering)

### Optional (AI features)
- Ollama (for AI categorization)

## Architecture

- **Modular design** - Clear separation of concerns
- **Dependency injection** - Flexible component composition
- **Error handling** - Comprehensive exception handling
- **Caching** - Efficient resource management
- **Backward compatibility** - Module aliases for ease of use

## Related Directories

- **../menu.py** - GUI main application
- **../menu.sh** - CLI main application  
- **../tests/** - Test suite
- **../docs/refactors/LIB_RESTRUCTURING_2024.md** - Architecture details
