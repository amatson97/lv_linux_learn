# Utility Modules & Helpers

The `utilities/` module contains reusable helper functions and utility classes used across the library.

## Modules

### path_manager.py
**PathManager** - Path resolution and management

**Responsibilities:**
- Cache directory management
- Configuration directory management
- Ensure directories exist
- Path normalization

**Key Methods:**
- `get_cache_dir()` - Get script cache directory
- `get_config_dir()` - Get configuration directory
- `ensure_dir()` - Create directory if needed
- `resolve_path()` - Resolve absolute paths

### terminal_messenger.py
**TerminalMessenger** - Terminal I/O and messaging

**Responsibilities:**
- Colored terminal output
- Progress messages
- Status indicators
- Message formatting

**Key Functions:**
- Print colored messages
- Progress bars
- Status updates

### file_loader.py
**FileLoader** - File operations and parsing

**Responsibilities:**
- JSON file loading
- YAML file parsing
- File validation
- Safe file operations

**Key Methods:**
- `load_json()` - Parse JSON files
- `load_yaml()` - Parse YAML files
- `save_json()` - Write JSON files

### user_scripts.py
**CustomScriptManager** - Custom script management

**Responsibilities:**
- Custom script enumeration
- Custom manifest parsing
- Script configuration
- Repository configuration

**Key Class:**
- `CustomScriptManager` - Manage user-defined scripts

### ai_categorizer.py (Optional)
**OllamaAnalyzer** - AI-based script categorization

**Responsibilities:**
- Ollama integration
- Script categorization
- AI-powered features
- Smart filtering

**Key Functions:**
- `check_ollama_available()` - Check if Ollama is running
- `OllamaAnalyzer` - Category detection

**Requirements:**
- Ollama installed and running
- Network access to Ollama API

### timer_manager.py (Optional)
**TimerManager** - GTK timer utilities

**Responsibilities:**
- Event scheduling
- Periodic task execution
- GTK integration

**Requirements:**
- GTK/GLib with PyGObject

## Dependencies

```
path_manager.py
  └─ (no dependencies)

terminal_messenger.py
  └─ (no dependencies)

file_loader.py
  └─ (no dependencies)

user_scripts.py
  ├─ path_manager.py
  ├─ file_loader.py
  └─ (core modules)

ai_categorizer.py (optional)
  └─ (requests, ollama)

timer_manager.py (optional)
  └─ (PyGObject, GTK)
```

## Usage Examples

### Path Management

```python
from lib.utilities.path_manager import PathManager

pm = PathManager()
cache_dir = pm.get_cache_dir()
config_dir = pm.get_config_dir()
pm.ensure_dir(cache_dir)
```

### File Operations

```python
from lib.utilities.file_loader import FileLoader

loader = FileLoader()
config = loader.load_json("config.json")
loader.save_json("config.json", config)
```

### Terminal Output

```python
from lib.utilities.terminal_messenger import TerminalMessenger

messenger = TerminalMessenger()
messenger.print_success("Operation completed!")
messenger.print_error("Something went wrong")
```

### Custom Script Management

```python
from lib.utilities.user_scripts import CustomScriptManager

manager = CustomScriptManager()
scripts = manager.get_custom_scripts()
```

### AI Categorization (if available)

```python
from lib.utilities.ai_categorizer import check_ollama_available, OllamaAnalyzer

if check_ollama_available():
    analyzer = OllamaAnalyzer()
    category = analyzer.categorize_script("script_code")
```

## Testing

Utilities are tested with:
- Unit tests in `tests/unit/`
- Mock external dependencies
- Headless testing environment

## Error Handling

Optional modules gracefully fail if dependencies are unavailable:
- `ai_categorizer.py` - Skipped if Ollama not available
- `timer_manager.py` - Skipped if GTK not available

## Related Modules

- **../core/** - Business logic
- **../ui/** - User interface
- **../../lib/** - Main library
- **../../tests/** - Test suite

## Performance Considerations

- **Path operations** - Cached where possible
- **File loading** - Lazy loading for large files
- **AI operations** - Async where applicable
- **Memory** - Stream processing for large files
