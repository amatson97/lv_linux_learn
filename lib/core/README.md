# Core Business Logic

The `core/` module contains the fundamental business logic for managing scripts and repositories in lv_linux_learn.

## Modules

### repository.py
**ScriptRepository** - Main class for repository management

**Responsibilities:**
- Multi-repository script management
- Remote manifest fetching and parsing
- Script downloading with checksum verification
- Caching with update detection
- Repository configuration

**Key Methods:**
- `fetch_remote_manifest()` - Get manifest from remote repository
- `download_script()` - Download and verify script
- `get_available_updates()` - Check for script updates
- `update_all_scripts()` - Batch update cached scripts
- `get_scripts()` - Enumerate available scripts

### manifest.py
**ManifestLoader** - Manifest parsing and management

**Responsibilities:**
- Remote and local manifest loading
- Script enumeration from manifests
- Dependency resolution
- Manifest validation

**Key Classes:**
- `ManifestLoader` - Load and parse manifests
- `Manifest` - Manifest data container
- `ScriptEntry` - Individual script metadata

### script.py
**Script Metadata & Caching**

**Key Classes:**
- `ScriptMetadata` - Script information and attributes
- `ScriptCache` - Cached script management
- Script enumeration utilities

**Responsibilities:**
- Script metadata handling
- Cache operations
- Script path resolution

### script_execution.py
**Script Execution Environment**

**Key Classes:**
- `ScriptEnvironmentManager` - Environment variable setup
- `ScriptExecutionContext` - Execution context
- `ScriptValidator` - Script validation

**Responsibilities:**
- Environment variable injection
- Script validation
- Command building
- Execution context setup

## Dependencies

```
script.py
  └─ (no internal dependencies)

repository.py
  ├─ script.py
  └─ manifest.py

manifest.py
  └─ script.py

script_execution.py
  └─ script.py
```

## Usage Example

```python
from lib.core.repository import ScriptRepository
from lib.core.script_execution import ScriptExecutionContext

# Initialize repository
repo = ScriptRepository()

# Get available scripts
scripts = repo.get_scripts()

# Download a script
repo.download_script(script_id, source='remote')

# Prepare execution
context = ScriptExecutionContext(script_path)
command = context.build_execution_command()
```

## Testing

Unit tests for core modules:
- `tests/unit/test_repository.py` - Repository operations
- `tests/unit/test_manifest.py` - Manifest parsing
- `tests/unit/test_script_execution.py` - Script execution

Run tests:
```bash
pytest tests/unit/test_repository.py
pytest tests/unit/test_manifest.py
pytest tests/unit/test_script_execution.py
```

## Related Modules

- **../ui/** - User interface components
- **../utilities/** - Helper utilities
- **../../tests/** - Test suite
